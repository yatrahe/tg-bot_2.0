import hashlib

import gspread

from google.oauth2.service_account import Credentials


scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)
sheet_id = "1cr3DaZgrekXPad_wmPt4ZcRyhhNkOUijgwmDxA4fQg8"


async def get_sheet_data():
    sheet = client.open_by_key(sheet_id).sheet1
    data = sheet.get_all_records()
    return data