from etc.keyboards import Keyboards
from loader import dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.etc import Currency
from models.tg_user import TgUser

@dp.callback_query_handler(lambda c: c.data.startswith('|convertor'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    
    
    if actions[0] == "deals_history":
        await c.answer("🕸️ Ваша история сделок пуста", show_alert=True)
    if actions[0] == "actual_price":
        await c.answer("🧠 В разработке", show_alert=True)
    if actions[0] == "deal_calc":
        await c.message.edit_text("1️⃣Выберите валюту которую хотите ОБМЕНЯТЬ в левой колонке\n\n2️⃣Выберите валюту которую хотите ПОЛУЧИТЬ в правой колонке", reply_markup=Keyboards.Calc.main())
        
    if actions[0] in ["sel_from", "sel_to"]:
        selected = Currency.objects.get({"symbol": actions[1]})
        await state.set_state("MakeDeal")
        if actions[0] == "sel_from":
            await state.update_data(sel_from=selected)
        elif actions[0] == "sel_to":
            await state.update_data(sel_to=selected)
         
        stateData = await state.get_data()   
        await c.message.edit_reply_markup(Keyboards.Calc.main(stateData.get('sel_from', None), stateData.get('sel_to', None)))