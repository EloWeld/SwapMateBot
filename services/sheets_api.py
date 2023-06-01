import datetime
import time
from typing import List, Union
import gspread
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
    def add_data_to_sheet(rows, sheet_index=0, spreadsheet=None):
        if not spreadsheet:
            spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)
            
        sheet = None
        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)
        
        sheet = spreadsheet.get_worksheet(sheet_index)

        sheet.append_rows(rows)
        return True
    
    @staticmethod
    def achieve_sheet(spreadsheet, sheet_index=0):
        worksheets =  spreadsheet.worksheets()
        if sheet_index >= len(worksheets):
            for i in range(len(worksheets), sheet_index+1):
                spreadsheet.add_worksheet(title=f"Лист {i+1}", rows="10000", cols="100", index=i)
                time.sleep(1)
    
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
    def row_style(style, sheet_index=0, spreadsheet=None):
        if not spreadsheet:
            spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)
            
        sheet = None
        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)
        
        sheet = spreadsheet.get_worksheet(sheet_index)
    
        range_name = f'A{1}:{chr(64+25)}{1}'

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
    def update_sheet_title(sheet_index=0, new_title='', spreadsheet=None):
        if not spreadsheet:
            spreadsheet = GoogleSheetsService.client.open_by_key(GoogleSheetsService.spreadsheet_id)
        
        GoogleSheetsService.achieve_sheet(spreadsheet, sheet_index)

        worksheets = spreadsheet.worksheets()
        if sheet_index < len(worksheets):
            sheet = worksheets[sheet_index]
            try:
                sheet.update_title(new_title)
            except Exception as e:
                loguru.logger.error(f"Cant change sheet name: {new_title}, {e}")
            return True
        else:
            return False
        
    @staticmethod
    def spreadsheet():
        return GoogleSheetsService.client.open_by_key(Consts.SPREADSHEET_ID)
    
GoogleSheetsService.authenticate()