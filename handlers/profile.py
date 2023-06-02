import datetime
import random
from typing import Union
from etc.keyboards import Keyboards
from etc.states import UserStates
from etc.texts import BOT_TEXTS
from loader import Consts, dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from loader import bot

# Text
def get_profile_text(user: TgUser):
    swap_count = Deal.objects.raw({"owner": user.id}).count()
    
    balances_text = "<code>Нет</code>"
    if user.balances != {}:
        balances_text = "\n" + "\n".join([f"▫️ {Currency.objects.get({'_id': int(currency_id)}).symbol}: <code>{balance:.2f}</code>" for currency_id, balance in user.balances.items()])
    
    main_text = f"💠 Ваш профиль 💠\n\n" \
        f"🙂 Имя: <code>{user.real_name}</code>\n" \
        f"🏘️ Город <code>{user.city.name}</code>\n" \
        f"\n" \
        f"💱 Всего свапов: <code>{swap_count}</code>\n" \
        f"💰 Балансы: {balances_text}\n"
    if user.is_admin:
        if user.invited_by == user:
            main_text += "\n👑 Вы админ 👑\n\n"
        else:
            main_text += "\n👑 Вы суб-админ 👑\n\n"

    return main_text


@dp.callback_query_handler(lambda c: c.data.startswith('|profile:'), state="*")
async def _(c: CallbackQuery, state: FSMContext = None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()

    if actions[0] in ["main"]:
        await state.finish()
        await c.message.edit_text(get_profile_text(user), reply_markup=Keyboards.Profile.main(user))
        
    if actions[0] == "refill_balance":
        await c.message.edit_text(f"⭐ Для пополнения баланса напишите валюту которую вы хотите пополнить и количество. После этого администратору будет отправлена заявка на пополнение\n\nПример: <code>USD 50</code>", 
                                  reply_markup=Keyboards.back("|profile:main"))
        await UserStates.RefillBalance.set()
        
@dp.message_handler(state=UserStates.RefillBalance)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    try:
        currency_symbol = m.text.split()[0]
        refill_amount = float(m.text.split()[1])
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    
    
    await state.finish()
    await m.answer("💸📥 Заявка отправлена!")
    try:
        await bot.send_message(Consts.RefillsChatID, f"💸📥 Новая заявка на пополнение!"
                           f"\n\nПользователь <a href='tg://user?id={user.id}'>{user.real_name}</a> подал заявку на пополнение\n\n"
                           f"Валюта: <code>{currency_symbol}</code>\n"
                           f"Количество: <code>{refill_amount}</code>\n", reply_markup=Keyboards.Admin.refill_user_balance(user, refill_amount, currency_symbol))
    except Exception as e:
        await bot.send_message(user.invited_by.id, f"⚠️ Бот не может отправить сообщение в чат для пополнений!!! Измените персональную константу RefillsChatID.\n\nОшибка: {e}")