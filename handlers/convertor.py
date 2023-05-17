import datetime
import random
from typing import List, Union
from etc.keyboards import Keyboards
from etc.texts import BOT_TEXTS
from etc.utils import get_rates_text
from loader import dp
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import FSMContext
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
import requests

@dp.callback_query_handler(lambda c: c.data.startswith('|convertor'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "deals_history":
        deals = Deal.objects.raw({"owner_id": user.id})
        if not deals:
            await c.answer("🕸️ Ваша история сделок пуста", show_alert=True)
            return
        
        await c.message.edit_text("📊 Ваша история сделок:", reply_markup=Keyboards.Deals.user_deals_history(deals))
    if actions[0] == "actual_rates":
        
        await c.message.edit_text("⭐ Актуальные курсы валют ниже\n\n"
                                  + get_rates_text(), reply_markup=Keyboards.actual_rates())
        #await c.answer("🧠 В разработке", show_alert=True)
    if actions[0] == "deal_calc":
        
        await c.message.edit_text("1️⃣Выберите валюту которую хотите ОБМЕНЯТЬ в левой колонке\n\n2️⃣Выберите валюту которую хотите ПОЛУЧИТЬ в правой колонке", 
                                  reply_markup=Keyboards.Calc.main(stateData.get('sel_from', None), stateData.get('sel_to', None)))
    if actions[0] == "see_deal":
        try:
            deal: Deal = Deal.objects.get({"_id": int(actions[1])})
        except Deal.DoesNotExist as e:
            await c.answer(f"❌ Сделка #{actions[1]} не найдена", show_alert=True)
            return
        
        await c.message.edit_text(f"💠 Сделка <code>{deal.id}</code>\n\n"
                                  f"🚦 Статус: <code>{deal.status}</code>\n"
                                  f"💱 Направление: <code>{deal.currency_symbol_from}</code>🠖<code>{deal.currency_symbol_to}</code>\n"
                                  f"📅 Дата создания: <code>{str(deal.created_at)[:-7]}</code>\n", 
                                  reply_markup=Keyboards.Deals.deal_info(user, deal))
        
    if actions[0] == "found_cheaper":
        await c.answer("Мне реально вот не важно, дешевле ты нашёл или нет, цены есть цены. Нравится - не нравится, терпи, моя красавица.", show_alert=True)