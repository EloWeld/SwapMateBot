from typing import List
from models.buying_currency import BuyingCurrency
from models.deal import Deal
from models.tg_user import TgUser
from services.sheets_api import GoogleSheetsService


class SheetsSyncer:
    @staticmethod
    def sync_currency_purchases(owner_user: TgUser):
        purchases: List[BuyingCurrency] = BuyingCurrency.objects.raw({"owner": owner_user.id})
        
        GoogleSheetsService.clear_sheet(1)
        GoogleSheetsService.add_data_to_sheet(BuyingCurrency.get_row_headers(), 1)
        
        for purchase in purchases:
            GoogleSheetsService.add_data_to_sheet(purchase.as_row(), 1)

    @staticmethod
    def sync_deals(owner_user: TgUser):
        deals: List[Deal] = Deal.objects.raw({"admin": owner_user.id})
        
        GoogleSheetsService.clear_sheet(2)
        GoogleSheetsService.add_data_to_sheet(Deal.get_row_headers(), 2)

        for deal in deals:
            GoogleSheetsService.add_data_to_sheet(deal.as_row(), 2)