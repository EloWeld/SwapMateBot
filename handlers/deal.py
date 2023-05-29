import datetime
import random
from typing import Dict, Union

from etc.keyboards import Keyboards
from etc.states import DealStates, UserStates
from etc.texts import BOT_TEXTS
from etc.utils import find_month_start, find_next_month, get_max_id_doc
from loader import dp, bot
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
        wdata = stateData.get(
            'sel_from', None), stateData.get(
            'sel_to', None), stateData.get(
            'sel_from_type', None), stateData.get(
            'sel_to_type', None)
        await c.message.edit_text(get_calc_text(*wdata), reply_markup=Keyboards.Calc.main(*wdata))

    if actions[0] == "cancel_deal":
        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        await c.message.edit_text(f"❌ Свап <b>{selFrom.symbol}</b> ➡️ <b>{selTo.symbol}</b> отменён", reply_markup=Keyboards.back('|main'))
        await state.finish()

    if actions[0] == "start_deal":
        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        await c.message.edit_text(f"📈 Введите количество <b>{selFrom.symbol}</b> которые вы хотите свапнуть на <b>{selTo.symbol}</b>", reply_markup=Keyboards.back('|convertor:deal_calc'))
        await DealStates.Value.set()

    if actions[0] == "can_start_that_deal":
        await c.answer("⛔ В данном направлении конвертировать нельзя, так как выбрана одинаковая валюта", show_alert=True)

    if actions[0] == "suggest_rate_cancel":
        await state.finish()
        await c.message.delete()

    if actions[0] == "suggest_rate":
        deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        await c.message.answer(f"💡 Вы можете предложить курс по которому будет продолжена сделка, если за время сделки ситуация сильно поменялась.\n\nДля этого просто напишите желаемый курс\n<b>{deal.dir_text()}</b>",
                               reply_markup=Keyboards.Deals.suggest_rate(deal))
        await UserStates.SuggestRate.set()
        await state.update_data(deal=deal)

    if actions[0] == "add_info":
        await c.answer()
        await c.message.answer("📝 Напишите дополнительную информацию для свапа")
        await UserStates.DealAdditionalInfo.set()


    if actions[0] == "send_deal":

        selFrom: Currency = stateData.get('sel_from')
        selTo: Currency = stateData.get('sel_to')
        deal_value: float = stateData.get('deal_value')
        # Check that admin have amount of currency

        if selTo.pool_balance < deal_value * selTo.rate_with(selFrom):
            await c.answer("😔 К сожалению пока что мы не можем предоставить такой объём валюты для свапа. Попробуйте позднее или свяжитесь с администратором", show_alert=True)
            await state.finish()
            return
        
        # Get admin
        admin: TgUser = TgUser.objects.get({"_id": user.invited_by.id})

        # Create deal
        maxIDDeal = get_max_id_doc(Deal)
        maxExtIDDeal: Deal = get_max_id_doc(Deal, {"created_at": {"$lt": find_next_month(datetime.datetime.now()),
                                                                  "$gt": find_month_start(datetime.datetime.now())}})
        maxExtIDDealID = maxExtIDDeal.external_id + 1 if maxExtIDDeal else 0
        maxIDDealID = maxExtIDDeal.id + 1 if maxIDDeal else 0
        d = Deal(maxIDDealID,
                 admin=admin,
                 profit=0,
                 rate=selTo.rate_with(selFrom),
                 external_id=maxExtIDDealID,
                 deal_value=deal_value,
                 owner=user,
                 currency_from=selFrom,
                 currency_to=selTo,
                 currency_type_from=stateData.get('sel_from_type', None),
                 currency_type_to=stateData.get('sel_to_type', None),
                 additional_info=stateData.get('additional_info', 'Отсутствует'),
                 created_at=datetime.datetime.now())
        d.profit = d.calculate_profit()
        d.save()
        await c.message.edit_text(f"⭐ Заявка на свап <code>#{d.id}</code> отправлена!")
        await c.message.answer(f"Hello!", reply_markup=Keyboards.start_menu(user))
        await state.finish()
        await bot.send_message(user.invited_by.id, f"⭐ Открылась новая заявка на свап <code>#{d.id}</code>!\n\nПримерный профит: <code>{d.profit} {d.currency_from.symbol}</code>", reply_markup=Keyboards.Admin.jump_to_deal(d))



async def answer_deal_preview(m: Message, stateData: Dict):
    selFrom: Currency = stateData.get('sel_from')
    deal_value: float = stateData.get('deal_value')
    selTo: Currency = stateData.get('sel_to')
    selFromType: str = stateData.get('sel_from_type', None)
    selToType: str = stateData.get('sel_to_type', None)
    additional_info: str = stateData.get('additional_info', 'Отсутствует')
    selFromType = '' if selFromType is None else selFromType
    selToType = '' if selToType is None else selToType

    await m.answer("⭐ Заявка на свап готова! Подтвердите нажатием кнопки\n\n❗Не забудьте при необходимости добавить дополнительную информацию\n\n"
                   f"<b>{selFrom.symbol} {selFromType}</b> ➡️ <b>{selTo.symbol} {selToType}</b>\n"
                   f"📤 Отдаёте: <code>{deal_value:.4f}</code> <code>{selFrom.symbol}</code>\n"
                   f"📥 Получаете: <code>{selTo.rate_with(selFrom) * deal_value:.4f}</code> <code>{selTo.symbol}</code>\n"
                   f"💱 Курс: <b> {selFrom.symbol} {selFromType} = {selTo.rate_with(selFrom):.4f} {selTo.symbol} {selToType}</b>\n"
                   f"\n"
                   f"📝 Дополнительная информация: <b> {additional_info} </b>\n", 
                   reply_markup=Keyboards.Calc.deal_request_done())

@dp.message_handler(state=UserStates.DealAdditionalInfo)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    try:
        info = m.text.strip()[:3000]
        await state.update_data(additional_info=info)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    stateData = {} if state is None else await state.get_data()

    await answer_deal_preview(m, stateData)


@dp.message_handler(state=DealStates.Value)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    try:
        deal_value = float(m.text.strip())
        await state.update_data(deal_value=deal_value)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    stateData = {} if state is None else await state.get_data()

    await answer_deal_preview(m, stateData)



@dp.message_handler(state=UserStates.SuggestRate)
async def _(m: Message, state: FSMContext = None, user: TgUser = None):
    try:
        rate = float(m.text.strip())
        await state.update_data(rate=rate)
    except Exception as e:
        await m.answer(BOT_TEXTS.InvalidValue)
        return

    deal: Deal = (await state.get_data())['deal']
    rate: float  = (await state.get_data())['rate']

    
    await state.finish()   
    await bot.send_message(user.invited_by.id, f"💡 Покупатель <a href='tg://user?id={user.id}'>{user.real_name}</a> предложил другой курс по сделке <code>#{deal.id}</code> {deal.dir_text()}", reply_markup=Keyboards.Admin.suggested_rate(deal, rate))
    await m.answer(f"⭐ Вы предложили курс по сделке <code>#{deal.id}</code>\n")

