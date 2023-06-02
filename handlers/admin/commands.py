import asyncio
import datetime
import os
import traceback
from typing import List, Union

import loguru
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc, get_rates_text
from loader import MDB, bot, dp
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
                 "Кого приглашать в таблицу: <code>swapmatebot@swapmatebot.iam.gserviceaccount.com</code>\n\n"
                 "<code>/sheets SPREADSHEET_ID</code> — Устанавливает таблицу для вывода статистики\n"
                 "\n"
                 "<code>/buy T_CURR T_AMOUNT S_CURR S_AMOUNT</code> — покупает валюту(T_CURR) в размере T_AMOUNT за (S_AMOUNT) валюты (S_CURR)\n"
                 "<code>/addCurrency СИМВОЛ КРИПТА ДОСУТПНА КУРС_К_РУБ ИМЕЮЩЕЕСЯ_КОЛИЧЕСТВО [ТИПЫ]</code> — Добавляет новую валюту админа\n"
                 "<code>/delCurrency СИМВОЛ</code> — Удаляет валюту админа\n"
                 "\n"
                 "<code>переключи</code> — меняет ваш статус админа \n"
                 "<code>переключи2</code> — меняет админа который вас пригласил \n"
                 "\n"
                 "<code>/setConst KEY VALUE</code> — Назначает значение персональной константы\n"
                 "\n"
                 "Примеры использования:\n"
                 "<code>/buy RUB 79 USD 1 </code>\n\n"
                 "<code>/sheets 1eud4AwOBH8CAYAMqA0dvKfPxBoF6LU6HEIVO-A6r6_s</code>\n\n"
                 "<code>/addCurrency USD NO YES 79.6 100 [Гк;Физ лицо;Юр лицо]</code>\n\n"
                 "<code>/addCurrency USD NO YES 79.6 100 []</code>\n\n"
                 "<code>/delCurrency USD</code>\n\n"
                 "<code>/setConst RefillsChatID -1001968498</code>\n\n"
                 )
    await m.answer(help_text)



@dp.message_handler(Command("setConst"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    try:
        
        # Обновляем валюту в бд
        key = m.text.split()[1]
        value = m.text.split()[2]
        user.personal_data_storage[key] = value
        user.save()
        
        await m.answer("✅ Готово!")
        
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        loguru.logger.error(f"Error while setConst: {e}; traceback: {traceback.format_exc()}")
        return
        

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
        bc = BuyingCurrency(id=get_max_id_doc(BuyingCurrency) + 1,
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
        SheetsSyncer.sync_currency_purchases()
        
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        loguru.logger.error(f"Error while buying currency: {e}; traceback: {traceback.format_exc()}")
        return
    

@dp.message_handler(Command("sheets"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    if user and user.is_admin:
        try:
            sid = m.text.split()[1]
            MDB.Settings .update_one(dict(id="Constants"), {"$set": dict(SPREADSHEET_ID=sid)})
            await m.answer(f"✅ ID Google Sheets изменён на <code>{sid}</code>")
        except Exception as e:
            await m.answer(BOT_TEXTS.InvalidValue)
    

@dp.message_handler(Command("addCurrency"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    if user and user.is_admin:
        try:
            types = m.text.replace(']', '[').split('[')[1].split(';')
            types = types if types != [''] else []
            curr = Currency(
                id=get_max_id_doc(Currency) + 1,
                admin=user,
                symbol = m.text.split()[1],
                is_crypto = m.text.split()[2] == "YES",
                is_available = m.text.split()[3] == "YES",
                rub_rate = float(m.text.split()[4]),
                pool_balance = float(m.text.split()[5]),
                types=types
            )
            curr.save()
            await m.answer(f"✅ Валюта добавлена")
        except Exception as e:
            await m.answer(BOT_TEXTS.InvalidValue)
            loguru.logger.error(f"Can't add currency: {e}: {traceback.format_exc()}")
            

@dp.message_handler(Command("delCurrency"), content_types=[ContentType.TEXT], state="*")
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    if user and user.is_admin:
        symbol = m.text.split()[1]
        curr: Currency = Currency.objects.get({"symbol": symbol})
        curr.delete()
        
        await m.answer(f"✅ Валюта <code>{symbol}</code> удалена!")