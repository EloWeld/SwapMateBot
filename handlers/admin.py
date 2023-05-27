import os
from typing import List
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_rates_text
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher.filters import ContentTypeFilter
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from aiogram.dispatcher.filters import Text

async def send_currencies(message: Message, is_edit = False):
    currencies: List[Currency] = Currency.objects.raw({"is_available": True})
    c_text = ""
    for currency in currencies:
        c_text += f"{currency.symbol} | {currency.pool_balance} | {currency.rub_rate} ₽\n"
        
    func = message.edit_text if is_edit else message.answer
    await func("💎 Список ваших валют\n"+c_text, reply_markup=Keyboards.Admin.Currencies.all_pool_currencies(currencies))

@dp.callback_query_handler(lambda c: c.data.startswith('|admin'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    
    
    if actions[0] == "main":
        if state:
            await state.finish()
        await c.message.edit_text("Админ меню", reply_markup=Keyboards.admin_menu(user))
        return
    
    if actions[0] == "setup_exchange_rates":
        currencies: List[Currency] = Currency.objects.raw({"is_available": True})
        await c.message.edit_text("💎 Выберите валюту чтобы установить её курс\n\nТекущие курсы:\n" + get_rates_text(), 
                                  reply_markup=Keyboards.Admin.choose_currency_to_change_rate(currencies))
    
    if actions[0] == "set_new_exchange_rate":
        currency: Currency = Currency.objects.get({"_id": int(actions[1])})
        await AdminInputStates.ChangeRate.set()
        await state.update_data(currency=currency)
        await c.message.edit_text(f"✏️ Установите новый курс валюты {currency.symbol}")
    
    if actions[0] == "my_currencies":
        await send_currencies(c.message, True)
    
    if actions[0] == "my_deals":
        deals = Deal.objects.all()
        await c.message.edit_text("💎 Выберите тип сделок", reply_markup=Keyboards.Admin.dealsTypes(deals))
        
    if actions[0] == "deals_with_status":
        status = actions[1]
        verbose_status = {'CANCELLED': 'Отменённая', 'ACTIVE': 'Активная', 'FINISHED': 'Завершённая'}[status]
        deals = Deal.objects.raw({"status": status})
        await c.message.edit_text(f"💎 Ниже список сделок со статусом {verbose_status}", reply_markup=Keyboards.Admin.deals(deals))
        
    
    if actions[0] == "finish_deal":
        deals = Deal.objects.all()
        await c.message.edit_text("В разработке", reply_markup=Keyboards.back('|main'))
    if actions[0] == "cancel_deal":
        deals = Deal.objects.all()
        await c.message.edit_text("В разработке", reply_markup=Keyboards.back('|main'))
        
    if actions[0] == "send_deal_receipt":
        
        try:
            deal = Deal.objects.get({"_id": int(actions[1])})
        except Deal.DoesNotExist:
            await c.answer(f"Не могу найти сделку #{actions[1]}")
            return
        
        await c.message.edit_text("🧾 Приложите чек для отправки", reply_markup=Keyboards.back('|main'))
        await AdminInputStates.SendReceipt.set()
        await state.update_data(deal=deal)
        


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
    currencies: List[Currency] = Currency.objects.raw({"is_available": True})
    await m.answer("💎 Выберите валюту чтобы установить её курс\n\nТекущие курсы:\n" + get_rates_text(), 
                                reply_markup=Keyboards.Admin.choose_currency_to_change_rate(currencies))
    
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
        await bot.send_photo(deal.owner_id, file_id, caption=f"✨ Ваш чек по сделке <code>#{deal.id}</code>")
        await m.answer(f"📤 Чек сделке  <code>{deal.id}</code> отправлен <a href='tg://user?id={deal.owner_id}'>пользователю</a>")
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