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
def get_calc_text(sel_from, sel_to, sel_from_type, sel_to_type):
    tl = "1️⃣ Выберите то, что отдаёте в левой колонке"
    tr = "2️⃣ Выберите то, что получаете в правой колонке"
    
    if sel_from:
        tl = f"1️⃣ Отдаёте: <code>{sel_from.symbol}</code>"
        if sel_from_type:
            tl += f" <code>({sel_from_type})</code>"
    if sel_to:
        tr = f"1️⃣ Получаете: <code>{sel_to.symbol}</code>"
        if sel_to_type:
            tr += f" <code>({sel_to_type})</code>"
        
    
    return tl + "\n\n" + tr

@dp.callback_query_handler(lambda c: c.data.startswith('|deal_calc'), state="*")
async def _(c: CallbackQuery, state: FSMContext = None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()

    if actions[0] in ["sel_from", "sel_to"]:
        selected = Currency.objects.get({"symbol": actions[1]})
        ctype = actions[-1] if len(actions) == 3 else None
        await state.set_state("deal_direction")
        if actions[0] == "sel_from":
            await state.update_data(sel_from=selected, sel_from_type=ctype)
        elif actions[0] == "sel_to":
            await state.update_data(sel_to=selected, sel_to_type=ctype)

        stateData = await state.get_data()
        wdata = stateData.get('sel_from', None), stateData.get('sel_to', None), stateData.get('sel_from_type', None), stateData.get('sel_to_type', None)
        await c.message.edit_text(get_calc_text(*wdata), reply_markup=Keyboards.Calc.main(*wdata))

    if actions[0] == "cancel_deal":
        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        await c.message.edit_text(f"❌ Сделка <b>{selFrom.symbol}</b> ➡️ <b>{selTo.symbol}</b> отменена", reply_markup=Keyboards.back('|main'))
        await state.finish()
 
    if actions[0] == "start_deal":
        selFrom: Currency = stateData.get('sel_from')
        await c.message.edit_text(f"📈 Введите объём средств для обмена в <b>{selFrom.symbol}</b>", reply_markup=Keyboards.back('|convertor:deal_calc'))
        await state.set_state("deal_calc_value")
        
    if actions[0] == "can_start_that_deal":
        await c.answer("⛔ В данном направлении конвертировать нельзя, так как выбрана одинаковая валюта", show_alert=True)

    if actions[0] == "send_deal":

        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        deal_value: float = stateData.get('deal_value')
        maxIDDeal: Deal = get_max_id_doc(Deal, {"created_at": {"$lt": find_next_month(datetime.datetime.now()),
                                                                  "$gt": find_month_start(datetime.datetime.now())}})
        maxIDDealExtID = maxIDDeal.external_id + 1 if maxIDDeal and hasattr(maxIDDeal, 'external_id') else 0
        d = Deal(random.randint(0, 999999999),
                 external_id=maxIDDealExtID,
                 deal_value=deal_value,
                 owner_id=user.id,
                 currency_symbol_from=selFrom.symbol,
                 currency_symbol_to=selTo.symbol,
                 currency_type_from=stateData.get('sel_from_type', None),
                 currency_type_to=stateData.get('sel_to_type', None),
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
    selFromType: Currency = stateData.get('sel_from_type', '')
    selToType: Currency = stateData.get('sel_to_type', '')

    await state.update_data(deal_value=deal_value)

    await m.answer("⭐ Заявка на обмен готова! Подтвердите нажатием кнопки\n\n"
                   f"<b>{selFrom.symbol} {selFromType}</b> ➡️ <b>{selTo.symbol} {selToType}</b>\n"
                   f"Объём: <b>{deal_value}</b>\n", reply_markup=Keyboards.Calc.dealRequestDone())
