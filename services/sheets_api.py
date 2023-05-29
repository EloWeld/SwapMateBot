import datetime
import time
from typing import Union
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from loader import Consts


class GoogleSheetsService:
    json_keyfile_path = 'google-creds.json'
    spreadsheet_id = Consts.SPREADSHEET_ID
    credentials = None
    client: Union[None, gspread.Client] = None

    @staticmethod
    def authenticate():
        GoogleSheetsService.credentials = ServiceAccountCredentials.from_json_keyfile_name(GoogleSheetsService.json_keyfile_path, ['https://www.googleapis.com/auth/spreadsheets'])
        GoogleSheetsService.client = gspread.authorize(GoogleSheetsService.credentials)

    @staticmethod
    def format_datetime(date: datetime.datetime):
        return date.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def add_data_to_sheet(row_data, sheet_index=0):
        if not GoogleSheetsService.client:
            GoogleSheetsService.authenticate()

        spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)
        sheet = None
        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)
        
        sheet = spreadsheet.get_worksheet(sheet_index)

        sheet.append_row(row_data)
        return True
    
    @staticmethod
    def achieve_sheet(spreadsheet, sheet_index=0):
        worksheets = spreadsheet.worksheets()
        if sheet_index >= len(worksheets):
            for i in range(len(worksheets), sheet_index+1):
                spreadsheet.add_worksheet(title=f"Лист {i+1}", rows="10000", cols="100", index=i)
                time.sleep(2)
    
    @staticmethod
    def clear_sheet(sheet_index=0):
        if not GoogleSheetsService.client:
            GoogleSheetsService.authenticate()

        spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)

        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)

        worksheets = spreadsheet.worksheets()
        if sheet_index < len(worksheets):
            sheet = worksheets[sheet_index]
            sheet.clear()
            return True
        else:
            return False