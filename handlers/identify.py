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
from models.etc import City, Currency
from models.tg_user import TgUser
import requests

@dp.callback_query_handler(lambda c: c.data.startswith('|identify'), state="*")
async def _(c: CallbackQuery, state: FSMContext=None, user: TgUser = None):
    actions = c.data.split(':')[1:]
    stateData = {} if state is None else await state.get_data()
    
    if actions[0] == "start_identify":
        cities = City.objects.all()
        
        await c.message.edit_text("💠 Выберите свой город", reply_markup=Keyboards.Identify(cities))
    