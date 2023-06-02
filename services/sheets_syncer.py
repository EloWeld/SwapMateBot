from typing import List

import loguru
from models.buying_currency import BuyingCurrency
from models.cash_flow import CashFlow
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from services.sheets_api import GoogleSheetsService
import pymongo
from gspread.worksheet import Worksheet

class SheetsSyncer:

    @staticmethod
    def sync_users_cash_flow(user_id=None):
        sheet_index = 3
        
        spreadsheet = GoogleSheetsService.spreadsheet()
        sheets = GoogleSheetsService.worksheets(spreadsheet)
        
        
        members: List[TgUser] = TgUser.objects.raw({"is_member": True})
        for member in members:
            if user_id is not None and member.id != user_id:
                sheet_index += 1
                continue
            sheets, sheet = GoogleSheetsService.achieve_sheet(spreadsheet, sheets, sheet_index)
            sheet.clear()
            
            rows = [CashFlow.get_row_headers()]
            for cf in member.cash_flow:
                if cf:
                    rows.append(cf.as_row())
            rows.append(["Текущие балансы:"])
            for balance_str_currency_key, balance_value in member.balances.items():
                rows.append([Currency.objects.get({"_id": int(balance_str_currency_key)}).symbol, round(balance_value, 2)])
                
            GoogleSheetsService.row_style(sheet, "bold|highlight")
            sheet.append_rows(rows)
            GoogleSheetsService.update_titile(sheet, "П " + member.real_name)
            sheet_index += 1
            
        
    @staticmethod
    def sync_currencies():
        currencies: List[Currency] = Currency.objects.all()

        spreadsheet = GoogleSheetsService.spreadsheet()
        sheets = GoogleSheetsService.worksheets(spreadsheet)
        
        sheet_index = 0

        sheets, sheet = GoogleSheetsService.achieve_sheet(spreadsheet, sheets, sheet_index)
        
        sheet.clear()

        rows = [Currency.get_row_headers()]
        for currency in currencies:
            rows.append(currency.as_row())

        GoogleSheetsService.row_style(sheet, "bold|highlight")
        sheet.append_rows(rows)
        GoogleSheetsService.update_titile(sheet, "Валюты")

    @staticmethod
    def sync_currency_purchases():
        purchases: List[BuyingCurrency] = BuyingCurrency.objects.all()

        spreadsheet = GoogleSheetsService.spreadsheet()
        sheets = GoogleSheetsService.worksheets(spreadsheet)

        sheet_index = 1

        sheets, sheet = GoogleSheetsService.achieve_sheet(spreadsheet, sheets, sheet_index)
        sheet.clear()

        rows = [BuyingCurrency.get_row_headers()]
        for purchase in purchases:
            rows.append(purchase.as_row())

        GoogleSheetsService.row_style(sheet, "bold|highlight")
        sheet.append_rows(rows)
        GoogleSheetsService.update_titile(sheet, "Покупки")

    @staticmethod
    def sync_deals():
        deals: List[Deal] = Deal.objects.all()

        spreadsheet = GoogleSheetsService.spreadsheet()
        sheets = GoogleSheetsService.worksheets(spreadsheet)

        sheet_index = 2

        
        sheets, sheet = GoogleSheetsService.achieve_sheet(spreadsheet, sheets, sheet_index)
        sheet.clear()

        rows = [Deal.get_row_headers()]
        for deal in deals:
            rows.append(deal.as_row())

        GoogleSheetsService.row_style(sheet, "bold|highlight")
        sheet.append_rows(rows)
        GoogleSheetsService.update_titile(sheet, "Свапы")
