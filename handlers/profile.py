import datetime
import random
from typing import Union
from etc.keyboards import Keyboards
from etc.texts import BOT_TEXTS
from etc.utils import find_month_start, find_next_month, get_max_id_doc
from loader import dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser


# Text
def get_profile_text(user: TgUser):
    swap_count = Deal.objects.raw({"owner_id": user.id}).count()
    main_text = f"💠 Ваш профиль 💠\n\n" \
        f"🙂 Имя: <code>{user.real_name}</code>\n" \
        f"🏘️ Город <code>{user.city.name}</code>\n" \
        f"\n" \
        f"💱 Всего свапов: <code>{swap_count}</code>\n" \
        f"💰 Баланс: <code>{user.balance} ₽</code>\n"

    return main_text


@dp.callback_query_handler(lambda c: c.data.startswith('|profile'), state="*")
async def _(c: CallbackQuery, state: FSMContext = None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()

    if actions[0] in ["main"]:
        await c.message.edit_text(get_profile_text(user), reply_markup=Keyboards.back("|main"))
