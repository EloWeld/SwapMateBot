import asyncio
import datetime
import os
import traceback
from typing import List, Union

import loguru
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc, get_rates_text
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher.filters import ContentTypeFilter, Command
from aiogram.dispatcher import FSMContext
from models.buying_currency import BuyingCurrency
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from aiogram.dispatcher.filters import Text

from services.sheets_syncer import SheetsSyncer


@dp.message_handler(Command("help"), state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    if not user.is_admin:
        return
    
    help_text = ("💠 Помощь:\n"
                 "Кого приглашать в таблицу: <code>swapmatebot@swapmatebot.iam.gserviceaccount.com</code>\n"
                 "<code>/buy T_CURR T_AMOUNT S_CURR S_AMOUNT</code> — покупает валюту(T_CURR) в размере T_AMOUNT за валюту(S_CURR) в размере(S_AMOUNT)\n"
                 "<code>/sheets 1eud4AwOBH8CAYAMqA0dvKfPxBoF6LU6HEIVO-A6r6_s</code> — Устанавливает таблицу для вывода статистики\n")
    await m.answer(help_text)



@dp.message_handler(Command("buy"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    try:
        
        # Обновляем валюту в бд
        target_currency: Currency = Currency.objects.get({"symbol": m.text.split()[1]})
        target_amount: float = float(m.text.split()[2])
        source_currency: Currency = Currency.objects.get({"symbol": m.text.split()[3]})
        source_amount: float = float(m.text.split()[4])
        
        # Вычисляем курс свапа
        exchange_rate = 1/ (target_amount / source_amount)
        
        await state.finish()
        
        await m.answer(f"💱 Вы совершили свап <code>{source_amount}</code> <code>{source_currency.symbol}</code> ➡️ <code>{target_amount}</code> <code>{target_currency.symbol}</code>\n\n"
                    f"Курс 1 {target_currency.symbol} = {exchange_rate} {source_currency.symbol}")
        max_id_doc = get_max_id_doc(BuyingCurrency)
        bc = BuyingCurrency(id=max_id_doc.id + 1 if max_id_doc else 0,
                        owner=user.id,
                    source_currency=source_currency,
                    source_amount=source_amount,
                    target_currency=target_currency,
                    target_amount=target_amount,
                    created_at=datetime.datetime.now(),
                    exchange_rate=exchange_rate
                    )
        bc.save()

        # Обновляем валюту в бд
        target_currency.pool_balance += target_amount
        target_currency.save()
        
        # Update sheets
        SheetsSyncer.sync_currency_purchases(user)
        
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        loguru.logger.error(f"Error while buying currency: {e}; traceback: {traceback.format_exc()}")
        return