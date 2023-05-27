import os
from typing import List, Union
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

async def send_slave_user(receiver_user: TgUser, user: TgUser, edit_message: Union[Message, None] = None):
    swap_count = Deal.objects.raw({"owner_id": user.id}).count()
    main_text = f"💠 Профиль {user.id} @{user.username} {user.fullname} 💠\n\n" \
        f"🙂 Имя: <code>{user.real_name}</code>\n" \
        f"🏘️ Город <code>{user.city.name}</code>\n" \
        f"\n" \
        f"💱 Всего свапов: <code>{swap_count}</code>\n" \
        f"💰 Баланс: <code>{user.balance} ₽</code>\n" \
        f"\n" \
        f"\n" \
        f"🔸 Админ: <code>{BOT_TEXTS.verbose[user.is_admin]}</code>\n" \
        f"🔸 Участник: <code>{BOT_TEXTS.verbose[user.is_member]}</code>\n" \
        f"🔸 Гость: <code>{BOT_TEXTS.verbose[not user.is_member]}</code>\n"
    
    if not edit_message:
        await bot.send_message(receiver_user.id, main_text, reply_markup=Keyboards.Admin.SlaveUsers.open(user))
    else:
        await edit_message.edit_text(main_text, reply_markup=Keyboards.Admin.SlaveUsers.open(user))

@dp.callback_query_handler(lambda c: c.data.startswith('|admin_slave_users:'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "open":
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        await send_slave_user(user, x_user, edit_message=c.message)

    elif actions[0] == "change_balance":
        await c.answer()
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        await c.message.answer("✏️ Введите новый баланс пользователя")
        await state.update_data(x_user=x_user)
        await AdminInputStates.ChangeUserBalance.set()

    elif actions[0] == "downgrade":
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        if x_user.is_admin:
            x_user.is_admin = False
            x_user.is_member = True
        else:
            x_user.is_member = False
            x_user.join_request_status = "NO"
        x_user.save()
        await send_slave_user(user, x_user, edit_message=c.message)

    elif actions[0] == "upgrade":
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})

        if x_user.is_member:
            x_user.is_admin = True
        else:
            x_user.is_member = True
            x_user.join_request_status = "ACCEPTED"
        x_user.save()

        await send_slave_user(user, x_user, edit_message=c.message)
    else:

        start = int(actions[0])
        users = TgUser.objects.all()
        if start < 0:
            await c.answer("Вы в начале списка пользователей")
            return
        if start > users.count():
            await c.answer("Вы в конце списка пользователей")
            return
        await c.message.edit_text("👥 Список пользователей бота\n\n🛡️ - админ\n🙂 - пользователь\n👤 - гость", 
                                  reply_markup=Keyboards.Admin.SlaveUsers.list(users, start))


@dp.message_handler(content_types=[ContentType.TEXT], state=AdminInputStates.ChangeUserBalance)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    # Get currency
    stateData = await state.get_data()
    x_user: TgUser = stateData['x_user']
    
    try:
        x_user.balance = float(m.text.replace(',','.'))
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    
    x_user.save()

    await m.answer("✅ Баланс изменён!")
    await state.finish()
    await send_slave_user(user, x_user)