from typing import List
from models.buying_currency import BuyingCurrency
from models.cash_flow import CashFlow
from models.deal import Deal
from models.etc import Currency
from models.tg_user import TgUser
from services.sheets_api import GoogleSheetsService
import pymongo


class SheetsSyncer:

    @staticmethod
    def sync_users_cash_flow(owner_user: TgUser):
        
        spsheet = GoogleSheetsService.spreadsheet()
        sheet_index = TgUser.objects.raw({"is_admin": True}).count() * 3 
        
        
        members: List[TgUser] = TgUser.objects.raw({"is_member": True})
        for member in members:
            GoogleSheetsService.clear_sheet(sheet_index, spsheet)
            
            rows = [CashFlow.get_row_headers()]
            for cf in member.cash_flow:
                rows.append(cf.as_row())
            
            GoogleSheetsService.row_style("bold|highlight", sheet_index, spsheet)
            GoogleSheetsService.add_data_to_sheet(rows, sheet_index, spsheet)
            GoogleSheetsService.update_sheet_title(
            sheet_index, "П " + member.real_name, spsheet)
            sheet_index += 1
            
        
    @staticmethod
    def sync_currencies(owner_user: TgUser):
        currencies: List[Currency] = Currency.objects.raw({"admin": owner_user.id})
        owner_order = list(TgUser.objects.raw({"is_admin": True}).order_by(
            [('created_at', pymongo.ASCENDING)])).index(owner_user)

        spsheet = GoogleSheetsService.spreadsheet()

        sheet_index = 0 + owner_order * 3

        GoogleSheetsService.clear_sheet(sheet_index, spsheet)

        rows = [Currency.get_row_headers()]
        for currency in currencies:
            rows.append(currency.as_row())

        GoogleSheetsService.row_style("bold|highlight", sheet_index, spsheet)
        GoogleSheetsService.add_data_to_sheet(rows, sheet_index, spsheet)
        GoogleSheetsService.update_sheet_title(
            sheet_index, owner_user.real_name + " (Валюты)", spsheet)

    @staticmethod
    def sync_currency_purchases(owner_user: TgUser):
        purchases: List[BuyingCurrency] = BuyingCurrency.objects.raw(
            {"owner": owner_user.id})
        owner_order = list(TgUser.objects.raw({"is_admin": True}).order_by(
            [('created_at', pymongo.ASCENDING)])).index(owner_user)

        spsheet = GoogleSheetsService.spreadsheet()

        sheet_index = 1 + owner_order * 3

        GoogleSheetsService.clear_sheet(sheet_index, spsheet)

        rows = [Deal.get_row_headers()]
        for purchase in purchases:
            rows.append(purchase.as_row())

        GoogleSheetsService.row_style("bold|highlight", sheet_index, spsheet)
        GoogleSheetsService.add_data_to_sheet(rows, sheet_index, spsheet)
        GoogleSheetsService.update_sheet_title(
            sheet_index, owner_user.real_name + " (Покупки)", spsheet)

    @staticmethod
    def sync_deals(owner_user: TgUser):
        deals: List[Deal] = Deal.objects.raw({"admin": owner_user.id})
        owner_order = list(TgUser.objects.raw({"is_admin": True}).order_by(
            [('created_at', pymongo.ASCENDING)])).index(owner_user)

        spsheet = GoogleSheetsService.spreadsheet()

        sheet_index = 2 + owner_order * 3

        GoogleSheetsService.clear_sheet(sheet_index, spsheet)

        rows = [Deal.get_row_headers()]
        for deal in deals:
            rows.append(deal.as_row())

        GoogleSheetsService.row_style("bold|highlight", sheet_index, spsheet)
        GoogleSheetsService.add_data_to_sheet(rows, sheet_index, spsheet)
        GoogleSheetsService.update_sheet_title(
            sheet_index, owner_user.real_name + " (Свапы)", spsheet)
