import pytest
from typing import Union
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from services.sheets_api import GoogleSheetsService

@pytest.fixture(scope="function")
def setup_google_sheets_service():
    json_keyfile_path = 'google-creds.json'
    spreadsheet_id = '1eud4AwOBH8CAYAMqA0dvKfPxBoF6LU6HEIVO-A6r6_s'
    GoogleSheetsService.json_keyfile_path = json_keyfile_path
    GoogleSheetsService.spreadsheet_id = spreadsheet_id
    return GoogleSheetsService

def test_authenticate(setup_google_sheets_service, mocker):
    setup_google_sheets_service.authenticate()
    assert setup_google_sheets_service.client is not None

def test_add_data_to_sheet(setup_google_sheets_service: GoogleSheetsService, mocker):
    row_data = ['test1', 'test2']
    sheet_index = 6
    result = setup_google_sheets_service.add_row_to_sheet(row_data, sheet_index)
    assert result == True
