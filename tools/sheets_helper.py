"""
Shared helper for connecting to Google Sheets.
Loads credentials from GOOGLE_CREDENTIALS_JSON env var (cloud)
or credentials.json file (local).
"""

import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
HEADERS = ['Subscription Name', 'Amount', 'Frequency', 'Start Date', 'Next Renewal Date']


def get_sheet():
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds_file = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)

    client = gspread.authorize(creds)
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    return client.open_by_key(sheet_id).sheet1


def ensure_headers(sheet):
    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        sheet.insert_row(HEADERS, 1)
