import datetime
import random
from typing import List, Union
from etc.keyboards import Keyboards
from etc.states import UserStates
from etc.texts import BOT_TEXTS
from etc.utils import notifyAdmins
from loader import Consts, dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.cash_flow import CashFlow
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from loader import bot
from pymodm.errors import DoesNotExist

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
    if actions[0] == "see_refill":
        try:
            refill: CashFlow = CashFlow.objects.get({"_id": int(actions[1])})
        except DoesNotExist:
            await c.answer("❌ Пополнение не найдено")
            return
        await c.answer()
        await c.message.answer(f"📥 Пополнение\n"
                               f"📅 Дата: <code>{refill.created_at.strftime('%d.%m.%Y %H:%M:%S')}</code>\n"
                               f"💠 Валюта: <code>{refill.target_currency.symbol}</code>\n"
                               f"💸 Количество: <code>{round(refill.additional_amount, 2)}</code>\n", reply_markup=Keyboards.hide())
    if actions[0] == "refill_balance":
        currencies = Currency.objects.raw({"is_available": True})
        await c.message.edit_text(f"⭐ Для пополнения баланса укажите валюту которую вы хотите пополнить.", 
                                  reply_markup=Keyboards.Profile.refill_currency(currencies))
        await UserStates.RefillBalanceCurrency.set()
        
    if actions[0] == "refills_history":
        user_cash_flow: List[CashFlow] = list(CashFlow.objects.raw({"user": user.id}))
        refills = [x for x in user_cash_flow if x.type == "REFILL_BALANCE"]
        refills = sorted(refills, key=lambda x: x.created_at, reverse=True)
        if len(refills) == 0:
            await c.answer("🕸️ История ваших пополнений пуста 🕸️")
        else:
            start = int(actions[1])
            await c.message.edit_text("История пополнений:", reply_markup=Keyboards.Profile.refillsHistory(refills, start=start))
        
    if actions[0] == "refill_balance_currency":
        await state.update_data(refill_currency=Currency.objects.get({"_id": int(actions[1])}))
        await c.message.edit_text(f"⭐ Напишите на сколько вы хотите пополнить. После этого администратору будет отправлена заявка на пополнение", 
                                  reply_markup=Keyboards.back("|profile:main"))
        await UserStates.RefillBalanceAmount.set()
        
@dp.message_handler(state=UserStates.RefillBalanceAmount)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):    
    try:
        refill_amount = float(m.text.strip().replace(',', '.'))
        await state.update_data(refill_amount=refill_amount)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    
    stateData = await state.get_data()
    
    await m.answer("💸📥 Заявка на пополнение отправлена!")
    try:
        await bot.send_message(Consts.RefillsChatID, f"💸📥 Новая заявка на пополнение!"
                           f"\n\nПользователь <a href='tg://user?id={user.id}'>{user.real_name}</a> подал заявку на пополнение\n\n"
                           f"Валюта: <code>{stateData['refill_currency'].symbol}</code>\n"
                           f"Количество: <code>{refill_amount}</code>\n", reply_markup=Keyboards.Admin.refill_user_balance(user, refill_amount, stateData['refill_currency']))
    except Exception as e:
        await notifyAdmins(f"⚠️ Бот не может отправить сообщение в чат для пополнений!!! Измените персональную константу RefillsChatID.\n\nОшибка: {e}")
    await state.finish()