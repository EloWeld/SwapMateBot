from etc.texts import BOT_TEXTS
from models.tg_user import TgUser
from typing import List, Union
from aiogram.types import \
    ReplyKeyboardMarkup as Keyboard, \
    KeyboardButton as Button, \
    InlineKeyboardMarkup as IKeyboard, \
    InlineKeyboardButton as IButton
    
class Keyboards:
    def start_menu(user: TgUser):
        k = IKeyboard()
        if user.isAdmin:
            k.row(IButton(BOT_TEXTS.AdminMenuBtn, callback_data="|admin:main"))
        k.row(IButton(BOT_TEXTS.ActualRates, callback_data="|convertor:actual_price"))
        k.row(IButton(BOT_TEXTS.DealCalc, callback_data="|convertor:deal_calc"))
        k.row(IButton(BOT_TEXTS.DealsHistory, callback_data="|convertor:deals_history"))
        
        return k