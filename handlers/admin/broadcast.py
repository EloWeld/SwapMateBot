import datetime
import os
from typing import List

import loguru
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc, get_rates_text
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher.filters import ContentTypeFilter
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from aiogram.dispatcher.filters import Text
from models.cash_flow import CashFlow
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, UserDeactivated


from services.sheets_api import GoogleSheetsService
from services.sheets_syncer import SheetsSyncer


def broadcast_results_text(success, failed, deleted, all, spentTime):
    text = f"🥂 Сообщение было разослано! ({success}/{all})\n" \
            f"👍 Отправлено: <b>{success}</b>\n" \
            f"👎 Не отправлено: <b>{failed}</b>\n" \
            f"🗑️ Удалено пользователей: <b>{deleted}</b>\n" \
            f"🕐 Время выполнения рассылки: <b>{round(spentTime)} сек</b>\n"
    return text

@dp.callback_query_handler(lambda c: c.data.startswith('|admin_broadcast:'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "go":
        if state:
            await state.finish()
        await c.message.edit_text("💭 Введите сообщение для рассылки и приложите всё что нужно:\n(Текст, фото, видео, GIF, документ)", reply_markup=Keyboards.back("|admin:main"))
        await AdminInputStates.BroadcastData.set()
        return
    
    if actions[0] == "cancel":
        await c.message.answer("😐 Рассылка отменена")
        await c.message.answer(BOT_TEXTS.MainMenuText, reply_markup=Keyboards.start_menu(user))
        await c.message.delete()
        await state.finish()
        return
    
    if actions[0] == "confirm":
        msg = await c.message.answer("♻️ Рассылаю...")
        bKeyboard = Keyboards.generate_from_text(stateData["broadcast_links"])
        bData = stateData['broadcast_data']
        success, failed, deleted, timeStart = 0, 0, 0, datetime.datetime.now()
        users = TgUser.objects.raw({"is_member": True})
        all = users.count()
        for user in users:
            # Try to send broadcast message
            try:
                await bot.copy_message(user.id, from_chat_id=bData['chat_id'],
                                        message_id=bData['message_id'],
                                        reply_markup=bKeyboard)
                success += 1
            except Exception as e:
                # If failed - check if bot blocked or user not found and remove him from database
                if e in [BotBlocked, ChatNotFound, UserDeactivated] or "Chat not found" in str(e) \
                        or "blocked " in str(e) \
                        or "deactivated" in str(e):
                    deleted += 1
                loguru.logger.error(f"[ BROADCAST ]: Can't send broadcast to {user.id}|{e}")
                failed += 1
        # Send message about broadcast finished
        spentTime = round((datetime.datetime.now() - timeStart).seconds)
        await msg.answer(broadcast_results_text(success, failed, deleted, all, spentTime))
        # Close state
        await state.finish()
    
    
@dp.message_handler(state=AdminInputStates.BroadcastData, content_types=ContentType.ANY)
async def _(m: Message, state: FSMContext, user: TgUser = None):
    if user.is_admin:
        data = dict(message_id=m.message_id, chat_id=m.chat.id)
        await state.update_data(broadcast_data=data)
        await m.answer("Прикрепите ссылки в виде кнопок\n" \
                    "[Текст+Ссылка]\n" \
                    "<code>Пример</code>\n" \
                    "[ILoveGoogle + https://google.com]\n\n" \
                    "Чтобы добавить несколько кнопок в один ряд — пишите ссылки рядом с предыдущими, " \
                    "не более трех. Формат:\n" \
                    "[Первый текст + первая ссылка][Второй текст + вторая ссылка]\n\n" \
                    "Чтобы добавить несколько кнопок в строчку, пишите новые ссылки с новой строки. Формат:\n" \
                    "[Первый текст + первая ссылка]\n[Второй текст + вторая ссылка]")
        await AdminInputStates.BroadcastLinks.set()
        

@dp.message_handler(state=AdminInputStates.BroadcastLinks, content_types=ContentType.ANY)
async def _(m: Message, state: FSMContext, user: TgUser = None):
    if user.is_admin:
        broadcast_data = (await state.get_data())['broadcast_data']

        kb = Keyboards.generate_from_text(m.text)
        if not kb:
            await m.answer("⛔ Форматирование ссылок нераспознано!")
        # Preview message
        await m.answer("Будет разослано сообщение ниже")
        await bot.copy_message(user.id, from_chat_id=broadcast_data['chat_id'],
                               message_id=broadcast_data['message_id'],
                               reply_markup=kb)
        # Confirm and change state
        await m.answer("Подтвердить рассылку?", reply_markup=Keyboards.Admin.confirm_broadcast())
        await state.update_data(broadcast_links=m.text)
