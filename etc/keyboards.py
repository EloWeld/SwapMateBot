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
                k.row(IButton(f"Сделка от {str(deal.created_at)[:-7]}", callback_data=f"|convertor:see_deal:{deal.id}"))
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|admin:main"))
            return k
        
        def choose_currency_to_change_rate(currencies: List[Currency]):
            k = IKeyboard()
            for currency in currencies:
                k.row(IButton(f"{currency.symbol}", callback_data=f"|admin:set_new_exchange_rate:{currency.id}"))
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|admin:main"))
            return k
        
        class Currencies:
            def all_pool_currencies(currencies: List[Currency]):
                k = IKeyboard()
                for currency in currencies:
                    k.row(IButton(currency.symbol, callback_data=f"|currency_pool:main:{currency.id}"))
                k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|admin:main"))
                return k
            
            def currency_actions(currency: Currency):
                k = IKeyboard()
                k.row(IButton(f"Купить {currency.symbol}", callback_data=f"|currency_pool:buy:{currency.id}"))
                k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|admin:my_currencies"))
                return k
            
            def choose_currency_to_buy_from(currencies: List[Currency]):
                k = IKeyboard()
                for currency in currencies:
                    k.row(IButton(f"За {currency.symbol}", callback_data=f"|buy_currecny:choose_source:{currency.id}"))
                k.row(IButton(BOT_TEXTS.Cancel, callback_data=f"|admin:my_currencies"))
                return k
                
                
                
            
    # Calc class
    class Calc:
        def main(selected_from=None, selected_to=None, selected_from_type=None, selected_to_type=None,):
            k = IKeyboard()
            currencies: List[Currency] = Currency.objects.raw({"is_available": True})
            for currency in currencies:
                if currency.types == []:
                    k.row()
                    f = selected_from.symbol if selected_from else None
                    t = selected_to.symbol if selected_to else None
                    k.insert(IButton(f"{currency.symbol}" if f != currency.symbol else f"✅ {currency.symbol}", callback_data=f"|deal_calc:sel_from:{currency.symbol}"))
                    k.insert(IButton(f"{currency.symbol}" if t != currency.symbol else f"✅ {currency.symbol}", callback_data=f"|deal_calc:sel_to:{currency.symbol}"))
                else:
                    for ctype in currency.types:
                        k.row()
                        f = selected_from.symbol+selected_from_type if selected_from and selected_from_type else None
                        t = selected_to.symbol+selected_to_type if selected_to and selected_to_type else None
                        k.insert(IButton(f"{currency.symbol} ({ctype})" if f != currency.symbol+ctype else f"✅ {currency.symbol} ({ctype})", callback_data=f"|deal_calc:sel_from:{currency.symbol}:{ctype}"))
                        k.insert(IButton(f"{currency.symbol} ({ctype})" if t != currency.symbol+ctype else f"✅ {currency.symbol} ({ctype})", callback_data=f"|deal_calc:sel_to:{currency.symbol}:{ctype}"))
                    
                
            if selected_from and selected_to and selected_from != selected_to:
                k.row(IButton(BOT_TEXTS.Continue, callback_data=f"|deal_calc:start_deal"))
            if selected_from and selected_to and selected_from_type and selected_to_type and selected_from == selected_to:
                k.row(IButton("⛔", callback_data=f"|deal_calc:can_start_that_deal"))
                
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|main"))
            
            return k
                
        def dealRequestDone():
            k = IKeyboard()
            k.insert(IButton(BOT_TEXTS.Cancel, callback_data="|deal_calc:cancel_deal"))
            k.insert(IButton(BOT_TEXTS.SendDeal, callback_data="|deal_calc:send_deal"))
            return k
        
    class Deals:
        def user_deals_history(deals: List[Deal]):
            k = IKeyboard()
            for deal in deals:
                k.row(IButton(f"{deal.external_id} | {deal.currency_symbol_from} > {deal.currency_symbol_to}", 
                              callback_data=f"|convertor:see_deal:{deal.id}"))
            k.row(IButton(BOT_TEXTS.BackButton, callback_data="|main"))
            return k
        
        def deal_info(user: TgUser, deal: Deal):
            k = IKeyboard()
            if user.is_admin:
                k.row(IButton(BOT_TEXTS.SendReceipt, callback_data=f"|admin:send_deal_receipt:{deal.id}"))
                k.row()
                k.insert(IButton(BOT_TEXTS.Finish, callback_data=f"|admin:finish_deal:{deal.id}"))
                k.insert(IButton(BOT_TEXTS.Cancel, callback_data=f"|admin:cancel_deal:{deal.id}"))
            k.row(IButton(BOT_TEXTS.BackButton, callback_data="|convertor:deals_history"))
            return k
            
            
    def start_menu(user: TgUser):
        k = IKeyboard()
        if user.is_admin:
            k.row(IButton(BOT_TEXTS.AdminMenuBtn, callback_data="|admin:main"))
        k.row(IButton(BOT_TEXTS.ActualRates, callback_data="|convertor:actual_rates"))
        k.row(IButton(BOT_TEXTS.DealCalc, callback_data="|convertor:deal_calc"))
        k.row(IButton(BOT_TEXTS.DealsHistory, callback_data="|convertor:deals_history"))
        
        return k
    
    def admin_menu(user: TgUser):
        k = IKeyboard()
        if user.is_admin:
            k.row(IButton(BOT_TEXTS.SetExchangeRates, callback_data="|admin:setup_exchange_rates"))
            k.row(IButton(BOT_TEXTS.MyCurrencies, callback_data="|admin:my_currencies"))
            k.row(IButton(BOT_TEXTS.MyDeals, callback_data="|admin:my_deals"))
            k.row(IButton(BOT_TEXTS.MyRates, callback_data="|admin:my_rates"))
            k.row(IButton(BOT_TEXTS.BackButton, callback_data=f"|main"))
        return k
    
    def actual_rates():
        k = IKeyboard()
        k.row(IButton(BOT_TEXTS.FoundCheaper, callback_data="|convertor:found_cheaper"))
        k.row(IButton(BOT_TEXTS.BackButton, callback_data="|main"))
        
        return k
    
    def back(path: str):
        k = IKeyboard()
        k.row(IButton(BOT_TEXTS.BackButton, callback_data=path))
        return k
    