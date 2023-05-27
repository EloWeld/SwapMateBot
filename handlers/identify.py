import datetime
import random
from typing import List, Union
from etc.keyboards import Keyboards
from etc.states import IdentifyState
from etc.texts import BOT_TEXTS
from etc.utils import get_rates_text
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import City, Currency
from models.tg_user import TgUser
import requests


async def send_join_request(user: TgUser, user_data):
    admins = TgUser.objects.raw({"is_admin": True})
    for admin in admins:
        await bot.send_message(admin.id, f"🔔 Пользователь <a href='tg://user?id={user.id}'>{user.fullname}</a> подал заявку на вступленние!\n\n"
                               f"Указанные данные:\n"
                               f"👤 Имя: <code>{user_data['username']}</code>\n🏘️ Город: <code>{user_data['choosed_city'].name}</code>",
                               reply_markup=Keyboards.Identify.new_request(user))


@dp.callback_query_handler(lambda c: c.data.startswith('|identify'), state="*")
async def _(c: CallbackQuery, state: FSMContext = None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()

    if actions[0] == "start_identify":
        cities = City.objects.all()

        await c.message.edit_text("💠 Выберите свой город", reply_markup=Keyboards.Identify.choose_city(cities))

    if actions[0] == "choose_city":
        await c.answer()
        await c.message.delete_reply_markup()
        choosed_city = City.objects.get({"_id": actions[1]})
        user.city = choosed_city
        user.save()
        await state.update_data(choosed_city=choosed_city)

        await c.message.answer("💠 Введите своё имя", reply_markup=Keyboards.Identify.username(user))
        await IdentifyState.Name.set()

    if user and user.is_admin:
        if actions[0] == "discard_user":
            x_user = TgUser.objects.get({"_id": int(actions[1])})
            x_user.join_request_status = "DISCARDED"
            x_user.save()

            await bot.send_message(x_user.id, f"⛔ Заявка на использование была отклонена.")
            await c.message.delete_reply_markup()
            await c.message.edit_text(c.message.text + '\n\nОтклонена ⛔')
        if actions[0] == "accept_user":
            x_user = TgUser.objects.get({"_id": int(actions[1])})
            x_user.join_request_status = "ACCEPTED"
            x_user.is_member = True
            x_user.invited_by = user.id
            x_user.save()

            await bot.send_message(x_user.id, f"✅ Заявка на использование одобрена. Меню ниже")
            await bot.send_message(x_user.id, f"💠 Главное меню 💠", reply_markup=Keyboards.start_menu(x_user))
            
            await c.message.delete_reply_markup()
            await c.message.edit_text(c.message.text + '\n\nОдобрена 💚')


@dp.message_handler(content_types=[ContentType.TEXT], state=IdentifyState.Name)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    if state:
        real_name = m.text.strip() if 'Использовать \"' not in m.text.strip() else user.fullname
        await state.update_data(username=real_name)
        user_data = await state.get_data()

        user.real_name = real_name
        user.join_request_status = "SENT"
        user.save()

        await send_join_request(user, user_data)
        await m.answer(f"✅ Ваша завяка отправлена на рассмотрение администрации! Ожидайте ответа.\n\n" +
                       f"Указанные данные:\n"
                       f"👤 Имя: <code>{user_data['username']}</code>\n🏘️ Город: <code>{user_data['choosed_city'].name}</code>", reply_markup=ReplyKeyboardRemove())
        await state.finish()
