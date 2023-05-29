import datetime
import traceback
from typing import List

import loguru
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc
from handlers.admin import send_currencies
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher import FSMContext
from models.buying_currency import BuyingCurrency
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from services.sheets_syncer import SheetsSyncer
   

@dp.message_handler(content_types=[ContentType.TEXT], state=AdminInputStates.BuyCurrencyTargetAmount)
async def _(m: Message, state: FSMContext = None):    
    try:
        amount = float(m.text.replace(',','.'))
        # Сохраняем введенное количество валюты в состояние
        await state.update_data(target_amount=amount)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    
    target_currency = (await state.get_data())['target_currency']
    currencies: List[Currency] = Currency.objects.raw({"is_available": True, "_id": {"$ne": target_currency.id}})
    
    await m.answer("Выберите тип валюты, за которую вы купили:",
                        reply_markup=Keyboards.Admin.Currencies.choose_currency_to_buy_from(currencies))
    await AdminInputStates.BuyCurrencySourceType.set()
    

@dp.callback_query_handler(lambda c: c.data.startswith('|buy_currecny:'), state=AdminInputStates.BuyCurrencySourceType)
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    
    if actions[0] == "choose_source":
        await c.answer()
        choosed_currency_id = int(actions[1])
        choosed_currency: Currency = Currency.objects.get({"_id": choosed_currency_id})
        
        await state.update_data(source_currency=choosed_currency)
        
        await c.message.edit_text(f"✏️ Введите количество <code>{choosed_currency.symbol}</code>, за которую вы купили:")
        await AdminInputStates.BuyCurrencySourceAmount.set()

@dp.message_handler(state=AdminInputStates.BuyCurrencySourceAmount)
async def _(m: Message, state: FSMContext, user: TgUser = None):
    try:
        amount = float(m.text.replace(',','.'))
        # Сохраняем введенное количество валюты в состояние
        await state.update_data(source_amount=amount)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    # Сохраняем введенное количество второй валюты в состояние
    await state.update_data(amount2=amount)

    # Получаем сохраненные данные из состояния
    stateData = await state.get_data()
    
    # Вычисляем курс свапа
    source_amount = float(stateData['source_amount'])
    target_amount = float(stateData['target_amount'])
    exchange_rate = 1/ (target_amount / source_amount)

    # Обновляем валюту в бд
    stateData['target_currency'].pool_balance += target_amount
    stateData['target_currency'].save()
    
    await state.finish()
    
    await m.answer(f"💱 Вы совершили свап <code>{stateData['source_amount']}</code> <code>{stateData['source_currency'].symbol}</code> ➡️ <code>{stateData['target_amount']}</code> <code>{stateData['target_currency'].symbol}</code>\n\n"
                   f"Курс 1 {stateData['target_currency'].symbol} = {exchange_rate} {stateData['source_currency'].symbol}")
    
    
    max_id_doc = get_max_id_doc(BuyingCurrency)
    bc = BuyingCurrency(id=max_id_doc.id+1 if max_id_doc else 0,
                    owner=user.id,
                   source_currency=stateData['source_currency'],
                   source_amount=stateData['source_amount'],
                   target_currency=stateData['target_currency'],
                   target_amount=stateData['target_amount'],
                   created_at=datetime.datetime.now(),
                   exchange_rate=exchange_rate
                   )
    bc.save()
    
    await send_currencies(m)

    # Update sheets
    SheetsSyncer.sync_currency_purchases(user)
    