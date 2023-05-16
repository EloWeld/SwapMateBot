import datetime
import random
from typing import Union
from etc.keyboards import Keyboards
from etc.texts import BOT_TEXTS
from loader import dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser


@dp.callback_query_handler(lambda c: c.data.startswith('|deal_calc'), state="*")
async def _(c: CallbackQuery, state: FSMContext = None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()

    if actions[0] in ["sel_from", "sel_to"]:
        selected = Currency.objects.get({"symbol": actions[1]})
        await state.set_state("deal_direction")
        if actions[0] == "sel_from":
            await state.update_data(sel_from=selected)
        elif actions[0] == "sel_to":
            await state.update_data(sel_to=selected)

        stateData = await state.get_data()
        await c.message.edit_reply_markup(Keyboards.Calc.main(stateData.get('sel_from', None), stateData.get('sel_to', None)))

    if actions[0] == "cancel_deal":
        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        await c.message.edit_text(f"❌ Сделка <b>{selFrom.symbol}</b>🠖<b>{selTo.symbol}</b> отменена", reply_markup=Keyboards.back('|main'))
        await state.finish()

    if actions[0] == "start_deal":
        selFrom: Currency = stateData.get('sel_from')
        await c.message.edit_text(f"📈 Введите объём средств для обмена в <b>{selFrom.symbol}</b>", reply_markup=Keyboards.back('|convertor:deal_calc'))
        await state.set_state("deal_calc_value")

    if actions[0] == "send_deal":

        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        d = Deal(random.randint(0, 999999999),
                 owner_id=user.id,
                 currency_symbol_from=selFrom.symbol,
                 currency_symbol_to=selTo.symbol,
                 created_at=datetime.datetime.now())
        d.save()
        await c.message.edit_text(f"⭐ Заявка <code>#{d.id}</code> отправлена!")
        await c.message.answer(f"Hello!", reply_markup=Keyboards.start_menu(user))
        await state.finish()


@dp.message_handler(state="deal_calc_value")
async def _(m: Message, state: FSMContext = None):
    try:
        deal_value = float(m.text.strip())
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    stateData = {} if state is None else await state.get_data()

    selFrom: Currency = stateData.get('sel_from')
    selTo: Currency = stateData.get('sel_to')

    await state.update_data(deal_value=deal_value)

    await m.answer("⭐ Заявка на обмен готова! Подтвердите нажатием кнопки\n\n"
                   f"<b>{selFrom.symbol}</b>🠖<b>{selTo.symbol}</b>\n"
                   f"Объём: <b>{deal_value}</b>\n", reply_markup=Keyboards.Calc.dealRequestDone())
