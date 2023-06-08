import datetime
import traceback
from typing import List

import loguru
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc, res
from handlers.admin import send_currencies
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher import FSMContext
from models.buying_currency import BuyingCurrency
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from services.sheets_syncer import SheetsSyncer
   

@dp.message_handler(content_types=[ContentType.TEXT], state=AdminInputStates.BuyCurrencyAmounts)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    try:
        source_amount, target_amount = map(float, res(m.text).split())
        await state.update_data(source_amount=source_amount, target_amount=target_amount)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    # Получаем сохраненные данные из состояния
    stateData = await state.get_data()
    
    # Вычисляем курс свапа
    exchange_rate = 1/ (target_amount / source_amount)

    # Обновляем валюту в бд
    stateData['target_currency'].pool_balance += target_amount
    stateData['target_currency'].save()
    
    await state.finish()
    
    await m.answer(f"💱 Вы совершили свап <code>{stateData['source_amount']}</code> <code>{stateData['source_currency'].symbol}</code> ➡️ <code>{stateData['target_amount']}</code> <code>{stateData['target_currency'].symbol}</code>\n\n"
                   f"Курс 1 {stateData['target_currency'].symbol} = {exchange_rate} {stateData['source_currency'].symbol}")
    
    
    bc = BuyingCurrency(id=get_max_id_doc(BuyingCurrency) + 1,
                    owner=user.id,
                   source_currency=stateData['source_currency'],
                   source_amount=source_amount,
                   target_currency=stateData['target_currency'],
                   target_amount=target_amount,
                   created_at=datetime.datetime.now(),
                   exchange_rate=exchange_rate
                   )
    bc.save()
    
    await send_currencies(m, user)

    # Update sheets
    SheetsSyncer.sync_currency_purchases()
    SheetsSyncer.sync_currencies()
    