import datetime
import os
from typing import List, Union
from etc.states import AdminInputStates
from etc.texts import BOT_TEXTS
from etc.utils import get_max_id_doc, get_rates_text
from loader import bot, dp
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.dispatcher.filters import ContentTypeFilter
from aiogram.dispatcher import FSMContext
from models.cash_flow import CashFlow
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from etc.keyboards import Keyboards
from aiogram.dispatcher.filters import Text

from services.sheets_syncer import SheetsSyncer

async def send_slave_user(receiver_user: TgUser, user: TgUser, edit_message: Union[Message, None] = None, reply_markup=None):
    swap_count = Deal.objects.raw({"owner": user.id}).count()
    balances_text = "<code>Нет</code>"
    if user.balances != {}:
        balances_text = "\n" + "\n".join([f"▫️ {Currency.objects.get({'_id': int(currency_id)}).symbol}: <code>{balance:.2f}</code>" for currency_id, balance in user.balances.items()])
    
    main_text = f"💠 Профиль {user.id} @{user.username} {user.fullname} 💠\n\n" \
        f"🙂 Имя: <code>{user.real_name}</code>\n" \
        f"🏘️ Город <code>{user.city.name}</code>\n" \
        f"\n" \
        f"💱 Всего свапов: <code>{swap_count}</code>\n" \
        f"💰 Балансы: {balances_text}\n" \
        f"\n" \
        f"\n" \
        f"🔸 Админ: <code>{BOT_TEXTS.verbose[user.is_admin]}</code>\n" \
        f"🔸 Участник: <code>{BOT_TEXTS.verbose[user.is_member]}</code>\n" \
        f"🔸 Гость: <code>{BOT_TEXTS.verbose[not user.is_member]}</code>\n"
    
    if not edit_message:
        await bot.send_message(receiver_user.id, main_text, reply_markup=Keyboards.Admin.SlaveUsers.open(user) if not reply_markup else reply_markup)
    else:
        await edit_message.edit_text(main_text, reply_markup=Keyboards.Admin.SlaveUsers.open(user) if not reply_markup else reply_markup)

@dp.callback_query_handler(lambda c: c.data.startswith('|admin_slave_users:'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "open":
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        await send_slave_user(user, x_user, edit_message=c.message)
    elif actions[0] == "user_from_deal":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        x_user = deal.owner
        await send_slave_user(user, x_user, edit_message=c.message, reply_markup=Keyboards.Admin.SlaveUsers.open_from_deal(deal, x_user))

    elif actions[0] == "change_balance":
        await c.answer()
        x_user: TgUser = TgUser.objects.get({"_id": int(actions[1])})
        await c.message.answer(f"✏️ Введите валюту и новый баланс пользователя\n\nПример: <code>USDT 50</code>")
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
    currency: Currency = Currency.objects.get({"symbol": m.text.split()[0]})
    
    try:
        old_balance = x_user.balances[str(currency.id)]
        new_balance = float(m.text.split()[1].replace(',','.'))
        x_user.balances[str(currency.id)] = new_balance
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return
    
    x_user.save()
    
    
    # Cash Flow
    cash_flow = CashFlow(
        id=get_max_id_doc(CashFlow) + 1,
        user=x_user,
        type=CashFlow.CashFlowType.BALANCE_EDIT.name,
        source_currency=currency,
        source_amount=old_balance,
        target_currency=currency,
        target_amount=new_balance,
        additional_data="Изменил на:",
        additional_amount=new_balance,
        created_at=datetime.datetime.now()
    ) 
    cash_flow.save()
    x_user.cash_flow.append(cash_flow)
    x_user.save()

    await m.answer("✅ Баланс изменён!")
    await state.finish()
    await send_slave_user(user, x_user)
    
    SheetsSyncer.sync_users_cash_flow(x_user.id)