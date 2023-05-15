from etc.texts import BOT_TEXTS
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from typing import List, Union
from aiogram.types import \
    ReplyKeyboardMarkup as Keyboard, \
    KeyboardButton as Button, \
    InlineKeyboardMarkup as IKeyboard, \
    InlineKeyboardButton as IButton
    
class Keyboards:
    
    class Admin:
        def dealsTypes(deals: List[Deal]):
            a_delas_count = len([x for x in deals if x.status == "ACTIVE"])
            c_delas_count = len([x for x in deals if x.status == "CANCELLED"])
            f_delas_count = len([x for x in deals if x.status == "FINISHED"])
            k = IKeyboard()
            k.row(IButton(f"Активные ({a_delas_count})", callback_data=f"|admin:deals_with_status:{'ACTIVE'}"))
            k.row(IButton(f"Отменённые ({c_delas_count})", callback_data=f"|admin:deals_with_status:{'FINISHED'}"))
            k.row(IButton(f"Завершённые ({f_delas_count})", callback_data=f"|admin:deals_with_status:{'CANCELLED'}"))
            
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|admin:main"))
            
            return k
        
        def deals(deals: List[Deal]):
            k = IKeyboard()
            for deal in deals:
                k.row(IButton(f"Сделка от {str(deal.created_at)[:-5]}", callback_data=f"|admin:see_deal:{deal.id}"))
            return k
            
    # Calc class
    class Calc:
        def main(selected_from=None, selected_to=None):
            k = IKeyboard()
            currencies: List[Currency] = Currency.objects.raw({"is_available": True})
            for currency in currencies:
                k.row()
                k.insert(IButton(f"{currency.symbol}" if selected_from != currency.symbol else f"✅ {currency.symbol}", callback_data=f"|convertor:sel_from:{currency.symbol}"))
                k.insert(IButton(f"{currency.symbol}" if selected_to != currency.symbol else f"✅ {currency.symbol}", callback_data=f"|convertor:sel_to:{currency.symbol}"))
            
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|main"))
            
            return k
            
    def start_menu(user: TgUser):
        k = IKeyboard()
        if user.isAdmin:
            k.row(IButton(BOT_TEXTS.AdminMenuBtn, callback_data="|admin:main"))
        k.row(IButton(BOT_TEXTS.ActualRates, callback_data="|convertor:actual_price"))
        k.row(IButton(BOT_TEXTS.DealCalc, callback_data="|convertor:deal_calc"))
        k.row(IButton(BOT_TEXTS.DealsHistory, callback_data="|convertor:deals_history"))
        
        
        return k
    
    def admin_menu(user: TgUser):
        k = IKeyboard()
        if user.isAdmin:
            k.row(IButton(BOT_TEXTS.SetExchangeRates, callback_data="|admin:setup_exchange_rates"))
            k.row(IButton(BOT_TEXTS.MyCurrencies, callback_data="|admin:my_currencies"))
            k.row(IButton(BOT_TEXTS.MyDeals, callback_data="|admin:my_deals"))
            k.row(IButton(BOT_TEXTS.MyRates, callback_data="|admin:my_rates"))
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|main"))
        return k