import datetime
import random
import time
from typing import List, Union
import gspread
from gspread.spreadsheet import Spreadsheet
import loguru
from oauth2client.service_account import ServiceAccountCredentials

from loader import Consts
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


class GoogleSheetsService:
    json_keyfile_path = 'google-creds.json'
    spreadsheet_id = Consts.SPREADSHEET_ID
    credentials = None
    client: Union[None, gspread.Client] = None
    worksheets_len = 0
    cached_spreadsheet = None
    cached_worksheets = None

    @staticmethod
    def authenticate():
        GoogleSheetsService.credentials = ServiceAccountCredentials.from_json_keyfile_name(GoogleSheetsService.json_keyfile_path, ['https://www.googleapis.com/auth/spreadsheets'])
        GoogleSheetsService.client = gspread.authorize(GoogleSheetsService.credentials)

    @staticmethod
    def format_datetime(date: datetime.datetime):
        return date.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def add_row_to_sheet(row_data, sheet_index=0, spreadsheet=None):
        if not spreadsheet:
            spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)
            
        sheet = None
        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)
        
        sheet = spreadsheet.get_worksheet(sheet_index)

        sheet.append_row(row_data)
                        
        return True
    
    @staticmethod
    def add_data_to_sheet(sheet, rows):
        return True
    
    @staticmethod
    def achieve_sheet(spreadsheet: Spreadsheet, sheets, sheet_index=0):
        if sheet_index >= len(sheets):
            for i in range(len(sheets), sheet_index+1):
                try:
                    spreadsheet.add_worksheet(title=f"Лист {i+1}", rows="1000", cols="14", index=i)
                except Exception as e:
                    spreadsheet.add_worksheet(title=str(random.randint(0, 100000)), rows="1000", cols="14", index=i)
                    print(e)
                GoogleSheetsService.worksheets_len += 1
                time.sleep(1)
            sheets = spreadsheet.worksheets()
        sheet = sheets[sheet_index]
        return sheets, sheet
    
    @staticmethod
    def clear_sheet(sheet_index=0, spreadsheet=None):
        if not spreadsheet:
            spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)

        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)

        worksheets = spreadsheet.worksheets()
        if sheet_index < len(worksheets):
            sheet = worksheets[sheet_index]
            sheet.clear()
            return True
        else:
            return False
        
        
    @staticmethod
    def row_style(sheet, style):
        range_name = f'A{1}:{chr(64+25)}{1}'   
        return True

        if 'bold' in style:
            sheet.format(range_name, {'textFormat': {'bold': True}})

        if 'highlight' in style:
            sheet.format(range_name, {
                "backgroundColor": {
                "red": 0.5,
                "green": 0.5,
                "blue": 1.0
                },
                "horizontalAlignment": "CENTER",
                "textFormat": {
                    "fontSize": 11,
                    "bold": True
                },
                "wrapStrategy": "WRAP",
                "verticalAlignment": "MIDDLE",
            })
            
                        
        return True
 
    @staticmethod
    def spreadsheet():
        if GoogleSheetsService.cached_spreadsheet is None:
            GoogleSheetsService.cached_spreadsheet = GoogleSheetsService.client.open_by_key(Consts.SPREADSHEET_ID)
        return GoogleSheetsService.cached_spreadsheet
 
    @staticmethod
    def worksheets(shreadsheet: Spreadsheet):
        if GoogleSheetsService.cached_worksheets is None:
            GoogleSheetsService.cached_worksheets = shreadsheet.worksheets()
        return GoogleSheetsService.cached_worksheets
    
    @staticmethod
    def update_titile(sheet, new_titile):
        try:
            sheet.update_title(new_titile)
        except Exception as e:
            loguru.logger.error(f"Cant change sheet name: {new_titile}, {e}")
    
GoogleSheetsService.authenticate()