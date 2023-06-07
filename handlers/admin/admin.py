import datetime
import os
from typing import List
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc, get_rates_text
from loader import MDB, Consts, bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher.filters import ContentTypeFilter
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from aiogram.dispatcher.filters import Text
from models.cash_flow import CashFlow

from services.sheets_api import GoogleSheetsService
from services.sheets_syncer import SheetsSyncer

async def send_currencies(message: Message, user: TgUser, is_edit = False):
    currencies: List[Currency] = Currency.objects.all()
    c_text = ""
    for currency in currencies:
        c_text += f"<code>{currency.symbol}</code> — <code>{currency.pool_balance:.2f}</code>, курс {currency.rub_rate:.2f} ₽\n"
        
    func = message.edit_text if is_edit else message.answer
    await func("💎 Список ваших валют\n"+c_text, reply_markup=Keyboards.Admin.Currencies.all_pool_currencies(currencies))


@dp.callback_query_handler(lambda c: c.data.startswith('|admin:'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "main":
        if state:
            await state.finish()
        await c.message.edit_text("Админ меню", reply_markup=Keyboards.admin_menu(user))
        
        return

    if actions[0] == "setup_exchange_rates":
        currencies: List[Currency] = Currency.objects.raw({"is_available": True})
        await c.message.edit_text("💎 Выберите валюту чтобы установить её курс\n\nТекущие курсы:\n" + get_rates_text(), 
                                  reply_markup=Keyboards.Admin.choose_target_currency_change_rate(currencies))
    
    if actions[0] == "set_new_exchange_rate":
        currency: Currency = Currency.objects.get({"_id": int(actions[1])})
        await AdminInputStates.ChangeRate.set()
        await state.update_data(currency=currency)
        await c.message.edit_text(f"✏️ Установите новый курс валюты {currency.symbol}")
    
    if actions[0] == "my_currencies":
        await send_currencies(c.message, user, True)
    
    if actions[0] == "my_deals":
        deals = Deal.objects.all()
        await c.message.edit_text("💎 Выберите тип свапов", reply_markup=Keyboards.Admin.dealsTypes(deals))
        
    # region rates
    if actions[0] == "accept_rate":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        rate = float(actions[2])

        should_have_to_receive = deal.deal_value * deal.rate
        will_have_to_give = should_have_to_receive / rate
        # If user wants to receive
        if deal.dir == "wanna_receive":
            deal.deal_value = will_have_to_give
        deal.rate = rate
        
        deal.save()

        text = f"✅ Предлжение изменения курса свапа <code>#{deal.id}</code> на <b>{rate if rate >= 1 else 1/ rate:.2f}</b> одобрено"
        await c.message.edit_text(text)
        await bot.send_message(deal.owner.id, text, reply_markup=Keyboards.Deals.jump_to_deal(deal))

    if actions[0] == "change_rate":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        await c.message.answer(f"✏️ Введите новое значене курса для свапа <code>#{deal.id}</code> <b>{deal.dir_text()}</b>")
        await AdminInputStates.ChangeDealRate.set()
        await state.update_data(deal=deal)
        await c.answer()

    if actions[0] == "decline_rate":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        rate = float(actions[2])

        text = f"⛔ Предлжение изменения курса свапа <code>#{deal.id}</code> на <b>{rate if rate >= 1 else 1/ rate:.2f}</b> отклонено"
        await c.message.edit_text(text)
        await bot.send_message(deal.owner.id, text, reply_markup=Keyboards.Deals.jump_to_deal(deal))
        
    # endregion
        
    # region deals
    if actions[0] == "deals_with_status":
        status = actions[1]
        verbose_status = BOT_TEXTS.verbose[status]
        deals = Deal.objects.raw({"status": status})
        await state.update_data(deals_status=status)

        await c.message.edit_text(f"💎 Ниже список свапов со статусом {verbose_status}", reply_markup=Keyboards.Admin.deals(deals))
        
    if actions[0] == "see_deal":
        try:
            deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        except Deal.DoesNotExist as e:
            await c.answer(f"❌ Свап #{actions[1]} не найден", show_alert=True)
            return
        
        deal.owner = TgUser.objects.get({"_id": deal.owner.id})
        await c.message.edit_text(f"💠 Свап <code>#{deal.id}</code>\n\n"
                                  f"🙂 Пользователь: <a href='tg://user?id={deal.owner.id}'>{deal.owner.username}</a>\n"
                                  f"🚦 Статус: <code>{BOT_TEXTS.verbose[deal.status]}</code>\n"
                                  f"💱 Направление: <code>{deal.dir_text(remove_currency_type=True)}</code>\n"
                                  f"💱 Обмен: {deal.dir_text(with_values=True, tag='b')}\n"
                                  f"💱 Курс: <code>{deal.get_rate_text()}</code>\n"
                                  f"📝 Дополнительная информация: <b> {deal.additional_info} </b>\n"
                                  f"📅 Дата создания: <code>{str(deal.created_at)[:-7]}</code>\n", 
                                  reply_markup=Keyboards.Admin.see_deal(deal))
    if actions[0] == "finish_deal":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})

        deal.status = Deal.DealStatuses.FINISHED.value
        deal.save()

        await c.answer("🏁 Свап завершён!")
        await c.message.edit_reply_markup(Keyboards.back(f"|admin:deals_with_status:{stateData.get('deals_status', deal.status)}"))

        await bot.send_message(deal.owner.id, f"🏁 Свап <code>#{deal.id}</code> завершён!")

        cc: Currency = Currency.objects.get({"_id": deal.source_currency.id})
        cc.pool_balance += deal.deal_value
        cc.save()
        
        tc: Currency = Currency.objects.get({"_id": deal.target_currency.id})
        tc.pool_balance -= deal.deal_value * deal.rate
        tc.save()
        
        # Cash Flow
        deal_owner: TgUser = TgUser.objects.get({"_id": deal.owner.id})
        cash_flow = CashFlow(
            id=get_max_id_doc(CashFlow) + 1,
            user=deal.owner,
            type=CashFlow.CashFlowType.SWAP.name,
            source_currency=deal.source_currency,
            source_amount=deal.deal_value,
            target_currency=deal.target_currency,
            target_amount=deal.deal_value * deal.rate,
            additional_data="По курсу:",
            additional_amount=deal.rate if deal.rate > 1 else 1/deal.rate,
            created_at=datetime.datetime.now(),
        ) 
        cash_flow.save()
        deal_owner.cash_flow.append(cash_flow)
        deal_owner.save()
        
        # Change balance
        # deal_owner: TgUser = TgUser.objects.get({"_id": deal.owner.id})
        # if str(deal.target_currency.id) not in deal_owner.balances:
        #     deal_owner.balances[str(deal.target_currency.id)] = 0
        #     deal_owner.save()
            
        # deal_owner.balances[str(deal.target_currency.id)] += deal.deal_value * deal.rate
        # deal_owner.save()
        

        SheetsSyncer.sync_deals()
        SheetsSyncer.sync_users_cash_flow(deal_owner.id)


    if actions[0] == "cancel_deal":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})

        deal.status = Deal.DealStatuses.CANCELLED.value
        deal.save()
        
        deal_owner = TgUser.objects.get({"_id": deal.owner.id})
        deal_owner.balances[str(deal.source_currency.id)] += deal.deal_value
        deal_owner.save()

        await c.answer("⛔ Свап отменён!")
        await c.message.edit_reply_markup(Keyboards.back(f"|admin:deals_with_status:{stateData.get('deals_status', deal.status)}"))

        await bot.send_message(deal.owner.id, f"⛔ Свап <code>#{deal.id}</code> отменён!")
        
    if actions[0] == "send_deal_receipt":
        
        try:
            deal = Deal.objects.get({"_id": int(actions[1])})
        except Deal.DoesNotExist:
            await c.answer(f"Не могу найти свап #{actions[1]}")
            return
        
        await c.message.edit_text("🧾 Приложите чек для отправки", reply_markup=Keyboards.back('|main'))
        await AdminInputStates.SendReceipt.set()
        await state.update_data(deal=deal)
    
    #endregion        

    # region users
    if actions[0] == "accept_refill" and user.is_admin:
        await c.message.edit_reply_markup(None)
        await c.message.edit_text(c.message.text + "\n\n💜 Одобрена")
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        refill_amount = float(actions[2])
        currency: Currency = Currency.objects.get({"symbol": actions[3]})

        if str(currency.id) not in x_user.balances:
            x_user.balances[str(currency.id)] = 0
        x_user.balances[str(currency.id)] += refill_amount
        
        x_user.save()
        
        # Cash Flow
        cash_flow = CashFlow(
            id=get_max_id_doc(CashFlow) + 1,
            user=x_user,
            type=CashFlow.CashFlowType.REFILL_BALANCE.name,
            target_currency=currency,
            target_amount=x_user.balances[str(currency.id)],
            additional_data="Пополнил на:",
            additional_amount=refill_amount,
            created_at=datetime.datetime.now(),
        ) 
        cash_flow.save()
        x_user.cash_flow.append(cash_flow)
        x_user.save()
        
        await bot.send_message(x_user.id, f"💜 Ваша заявка на пополнение <code>{refill_amount} {currency.symbol}</code> одобрена!")
        
        SheetsSyncer.sync_users_cash_flow(x_user.id)

    if actions[0] == "discard_refill" and user.is_admin:
        await c.message.edit_reply_markup(None)
        await c.message.edit_text(c.message.text + "\n\n🛑 Отклонена")
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        refill_amount = float(actions[2])
        currency: Currency = Currency.objects.get({"symbol": actions[3]})

        await bot.send_message(x_user.id, f"🛑 Ваша заявка на пополнение <code>{refill_amount} {currency.symbol}</code> отклонена!")

    # endregion

@dp.callback_query_handler(lambda c: c.data.startswith('|currency_pool'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    
    
    if actions[0] == "main":
        if state:
            await state.finish()
        currency: Currency = Currency.objects.get({"_id": int(actions[1])})
        await c.message.edit_text(f"💎 Валюта <code>{currency.symbol}</code>\n", reply_markup=Keyboards.Admin.Currencies.currency_actions(currency))
        
    if actions[0] == "buy":
        currency: Currency = Currency.objects.get({"_id": int(actions[1])})
        await c.message.edit_text(f"✏️ Укажите количество валюты которую вы купили:", reply_markup=Keyboards.back('|currency_pool:main:{}'))
        
        await AdminInputStates.BuyCurrencyTargetAmount.set()
        await state.update_data(target_currency=currency)
        # See other in buying_currency.py


@dp.message_handler(content_types=[ContentType.TEXT], state=AdminInputStates.ChangeRate)
async def _(m: Message, state: FSMContext = None):
    # Get currency
    stateData = await state.get_data()
    currency: Currency = stateData['currency']
    
    try:
        rate = float(m.text.replace(',','.'))
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    
    currency.rub_rate = rate
    currency.save()
    
    await state.finish()
    
    await m.answer("✅ Готово")
    MDB.Settings.update_one({"id": "Constants"}, {"$set": dict(LAST_RATES_UPDATE=datetime.datetime.now())}) 
    currencies: List[Currency] = Currency.objects.raw({"is_available": True})
    await m.answer("💎 Выберите валюту чтобы установить её курс\n\nТекущие курсы:\n" + get_rates_text(), 
                                reply_markup=Keyboards.Admin.choose_target_currency_change_rate(currencies))
    
    
@dp.message_handler(content_types=[ContentType.TEXT], state=AdminInputStates.ChangeDealRate)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    # Get deal
    stateData = await state.get_data()
    deal: Deal = stateData['deal']

    try:
        rate = float(m.text.replace(',','.'))
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    should_have_to_receive = deal.deal_value * deal.rate
    will_have_to_give = should_have_to_receive / rate
    # If user wants to receive
    if deal.dir == "wanna_receive":
        deal.deal_value = will_have_to_give
    deal.rate = rate
    deal.save()

    await m.answer(f"💱 Курс свапа <code>#{deal.id}</code> изменён на {deal.get_rate_text()}")
    await bot.send_message(deal.owner.id, f"💱 Курс свапа <code>#{deal.id}</code> изменён на {deal.get_rate_text()}", reply_markup=Keyboards.Deals.jump_to_deal(deal))
    await state.finish()


@dp.message_handler(content_types=[ContentType.PHOTO], state=AdminInputStates.SendReceipt)
async def _(m: Message, state: FSMContext = None):
    # Get deal
    stateData = await state.get_data()
    deal: Deal = stateData['deal']
     # Get the photo file ID
    file_id = m.photo[-1].file_id
    
    # Download the photo
    photo = await bot.get_file(file_id)
    counter = 1
    filename = f"{deal.id}.jpg"
    while os.path.exists(os.path.join('receipts', filename)):
        # Increment the counter and generate a new filename
        counter += 1
        filename = f"{deal.id}_{counter}.jpg"
    photo_path = os.path.join('receipts', filename)
    await photo.download(photo_path)
    
    # Send the photo to deal owner user
    try:
        await bot.send_photo(deal.owner.id, file_id, caption=f"✨ Ваш чек по свапу <code>#{deal.id}</code>")
        await m.answer(f"📤 Чек свапу  <code>{deal.id}</code> отправлен <a href='tg://user?id={deal.owner.id}'>пользователю</a>")
    except Exception as e:
        await m.answer(f"❌ Не удалось отправить чек пользователю из-за ошибки <code>{str(e)}</code>")
        
    await state.finish()
    
    
# Чит-коды
@dp.message_handler(Text("переключи"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    if user:
        user.is_admin = not user.is_admin
        user.save()
        await m.answer(f"Статус админа: <code>{user.is_admin}</code>")
        
        
@dp.message_handler(Text("переключи2"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    if user:
        user.invited_by = user if user.invited_by == 6069303965 else TgUser.objects.get({"_id": 6069303965})
        user.save()
        await m.answer(f"Приглашён пользователем: <code>{user.invited_by.id}</code>")