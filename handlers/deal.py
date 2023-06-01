import datetime
import random
from typing import Dict, Union

from etc.keyboards import Keyboards
from etc.states import DealStates, UserStates
from etc.texts import BOT_TEXTS
from etc.utils import find_month_start, find_next_month, get_max_id_doc
from loader import dp, bot
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser


# Text
def get_calc_text(user, sel_from=None, sel_to=None, sel_from_type=None, sel_to_type=None):
    tl = "1️⃣ ДАЮ"
    tr = "2️⃣ ПОЛУЧАЮ"

    if sel_from:
        tl = f"1️⃣ ДАЮ: <code>{sel_from.symbol}</code>"
        if sel_from_type:
            tl += f" <code>({sel_from_type})</code>"
    if sel_to:
        tr = f"1️⃣ ПОЛУЧАЮ: <code>{sel_to.symbol}</code>"
        if sel_to_type:
            tr += f" <code>({sel_to_type})</code>"

    return tl + "\n\n" + tr


@dp.callback_query_handler(lambda c: c.data.startswith('|deal_calc'), state="*")
async def _(c: CallbackQuery, state: FSMContext = None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()

    if actions[0] == "forbidden_choice":
        await c.answer("🛑 Вы не можете выбрать это нарпавление")

    if actions[0] in ["sel_from", "sel_to"]:
        await c.answer()
        selected = Currency.objects.get({"symbol": actions[1]})
        ctype = actions[-1] if len(actions) == 3 else None
        await state.set_state("deal_direction")
        if actions[0] == "sel_from":
            await state.update_data(sel_from=selected, sel_from_type=ctype)
        elif actions[0] == "sel_to":
            await state.update_data(sel_to=selected, sel_to_type=ctype)

        stateData = await state.get_data()
        wdata = user, stateData.get(
            'sel_from', None), stateData.get(
            'sel_to', None), stateData.get(
            'sel_from_type', None), stateData.get(
            'sel_to_type', None)
        await c.message.edit_text(get_calc_text(*wdata), reply_markup=Keyboards.Calc.main(*wdata))

    if actions[0] == "cancel_deal":
        try:
            selFrom: Currency = stateData.get('sel_from')
            selTo: Currency = stateData.get('sel_to')
            await c.message.edit_text(f"❌ Свап <b>{selFrom.symbol}</b> ➡️ <b>{selTo.symbol}</b> отменён", reply_markup=Keyboards.back('|main'))
            await state.finish()
        except Exception as e:
            await c.message.delete()

    if actions[0] == "start_deal":
        try:
            selFrom: Currency = stateData.get('sel_from')
            selTo: Currency = stateData.get('sel_to')
            await c.message.edit_text(f"📈 Введите количество <b>{selFrom.symbol}</b> которые вы хотите свапнуть на <b>{selTo.symbol}</b>", reply_markup=Keyboards.back('|convertor:deal_calc'))
            await DealStates.Value.set()
        except Exception as e:
            await c.message.delete()

    if actions[0] == "can_start_that_deal":
        await c.answer("⛔ В данном направлении конвертировать нельзя, так как выбрана одинаковая валюта", show_alert=True)

    if actions[0] == "suggest_rate_cancel":
        await state.finish()
        await c.message.delete()

    if actions[0] == "suggest_rate":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        if deal.status != Deal.DealStatuses.ACTIVE.value:
            await c.answer("⚠️ Изменение курса этого свапа уже недоступно", show_alert=True)
            await c.message.edit_reply_markup(Keyboards.Deals.deal_info(user, deal))
            return
        await c.message.answer(f"💡 Вы можете предложить курс по которому будет продолжена свап, если за время свапа ситуация сильно поменялась.\n\nДля этого просто напишите желаемый курс\n<b>{deal.dir_text()}</b>",
                               reply_markup=Keyboards.Deals.suggest_rate(deal))
        await UserStates.SuggestRate.set()
        await state.update_data(deal=deal)

    if actions[0] == "add_info":
        await c.answer()
        await c.message.answer("📝 Напишите дополнительную информацию для свапа")
        await UserStates.DealAdditionalInfo.set()


    if actions[0] == "send_deal":

        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        deal_value: float = stateData.get('deal_value')
        # Check that admin have amount of currency

        # if selTo.pool_balance < deal_value * selTo.rate_with(selFrom):
        #     await c.answer("😔 К сожалению пока что мы не можем предоставить такой объём валюты для свапа. Попробуйте позднее или свяжитесь с администратором", show_alert=True)
        #     await state.finish()
        #     return
        
        # Get admin
        admin: TgUser = TgUser.objects.get({"_id": user.invited_by.id})

        # Create deal
        maxExtIDDealID = get_max_id_doc(Deal, {"created_at": {"$lt": find_next_month(datetime.datetime.now()),
                                                                  "$gt": find_month_start(datetime.datetime.now())}}) + 1
        deal = Deal(get_max_id_doc(Deal) + 1,
                 admin=admin,
                 profit=0,
                 rate=selTo.rate_with(selFrom),
                 external_id=maxExtIDDealID,
                 deal_value=deal_value,
                 owner=user,
                 source_currency=selFrom,
                 target_currency=selTo,
                 currency_type_from=stateData.get('sel_from_type', None),
                 currency_type_to=stateData.get('sel_to_type', None),
                 additional_info=stateData.get('additional_info', 'Отсутствует'),
                 created_at=datetime.datetime.now())
        deal.profit = deal.calculate_profit()
        deal.save()
        
        if str(deal.source_currency.id) not in user.balances:
            user.balances[str(deal.source_currency.id)] = 0
            user.save()
            
        user.balances[str(deal.source_currency.id)] -= deal.deal_value
        user.save()
        
        await c.message.edit_text(f"⭐ Заявка на свап <code>#{deal.id}</code> отправлена!")
        
        await c.message.answer(deal.get_user_text(), reply_markup=Keyboards.Deals.deal_info(user, deal))
        await state.finish()
        await bot.send_message(user.invited_by.id, f"⭐ Открылась новая заявка на свап <code>#{deal.id}</code>!\n\nПримерный профит: <code>{deal.profit} {deal.source_currency.symbol}</code>", reply_markup=Keyboards.Admin.jump_to_deal(deal))
        



async def answer_deal_preview(m: Message, stateData: Dict):
    currency_type_from=stateData.get('sel_from_type', None),
    currency_type_to=stateData.get('sel_to_type', None),
    currency_type_from = '' if currency_type_from is None else currency_type_from
    currency_type_to = '' if currency_type_to is None else currency_type_to
    deal = Deal(
        source_currency=stateData.get('sel_from'),
        target_currency=stateData.get('sel_to'),
        deal_value=stateData.get('deal_value'),
        currency_type_from=stateData.get('sel_from_type', None),
        currency_type_to=stateData.get('sel_to_type', None),
        additional_info=stateData.get('additional_info', 'Отсутствует'),
        rate=stateData.get('sel_to').rate_with(stateData.get('sel_from'))
    )

    await m.answer("⭐ Заявка на свап готова! Подтвердите нажатием кнопки\n\n❗Не забудьте при необходимости добавить дополнительную информацию\n\n"
                   f"<b>{deal.dir_text()}</b>\n"
                   f"📤 Отдаёте: <code>{deal.deal_value:.4f}</code> <code>{deal.source_currency.symbol}</code>\n"
                   f"📥 Получаете: <code>{deal.target_currency.rate_with(deal.source_currency) * deal.deal_value:.4f}</code> <code>{deal.target_currency.symbol}</code>\n"
                   f"💱 Курс: <b>{deal.get_rate_text()}</b>\n"
                   f"\n"
                   f"📝 Дополнительная информация: <b> {deal.additional_info} </b>\n", 
                   reply_markup=Keyboards.Calc.deal_request_done())

@dp.message_handler(state=UserStates.DealAdditionalInfo)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    try:
        info = m.text.strip()[:3000]
        await state.update_data(additional_info=info)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    stateData = {} if state is None else await state.get_data()

    await answer_deal_preview(m, stateData)


@dp.message_handler(state=DealStates.Value)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    try:
        deal_value = float(m.text.strip())
        assert deal_value != 0
        await state.update_data(deal_value=deal_value)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    stateData = {} if state is None else await state.get_data()
    
    if str(stateData['sel_from'].id) not in user.balances:
        await m.answer(f"⚠️ У вас в кошельке нет валюты <code>{stateData['sel_from'].symbol}</code>!", reply_markup=Keyboards.back('|convertor:deal_calc'))
        return 
    
    if user.balances[str(stateData['sel_from'].id)] < deal_value:
        balance = user.balances[str(stateData['sel_from'].id)]
        await m.answer(f"⚠️ Ваш баланс: <code>{balance} {stateData['sel_from'].symbol}</code>. Для такого обмена пополните баланс на <code>{deal_value - balance} {stateData['sel_from'].symbol}</code>!", reply_markup=Keyboards.back('|convertor:deal_calc'))
        return


    await answer_deal_preview(m, stateData)



@dp.message_handler(state=UserStates.SuggestRate)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    try:
        rate = float(m.text.strip())
        await state.update_data(rate=rate)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    deal: Deal = (await state.get_data())['deal']
    rate: float  = (await state.get_data())['rate']

    
    await state.finish()   
    await bot.send_message(user.invited_by.id, f"💡 Покупатель <a href='tg://user?id={user.id}'>{user.real_name}</a> предложил другой курс по свапу <code>#{deal.id}</code> {deal.dir_text()}", reply_markup=Keyboards.Admin.suggested_rate(deal, rate))
    await m.answer(f"⭐ Вы предложили курс по свапу <code>#{deal.id}</code>\n")

