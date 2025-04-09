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


class SheetMonitor:
    def __init__(self, sheet_id):
        self.sheet_id = sheet_id
        self.last_hash = None

    async def check_updates(self):
        """Проверяет обновления и возвращает данные, если они изменились."""
        try:
            sheet = client.open_by_key(self.sheet_id).sheet1
            data = sheet.get_all_records()  # Получаем данные в виде списка словарей
            current_hash = hashlib.md5(str(data).encode()).hexdigest()
            
            if self.last_hash and current_hash != self.last_hash:
                self.last_hash = current_hash
                return data  # Возвращаем обновленные данные
                
            self.last_hash = current_hash
            return None  # Если изменений нет, возвращаем None
            
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
            return None

    """Запрос на вывод средств в Google Таблицу"""
    async def add_withdrawal_request(self, data):
        try:
            sheet = client.open_by_key(self.sheet_id).worksheet("Withdraws")
            sheet.append_row(data)
            return True
        except Exception as e:
            print(f"Ошибка при добавлении запроса на вывод: {e}")
            return False

""" Генерим хэш задания """
def generate_task_hash(task_data: dict) -> str:
    hash_string = f"{task_data['num']}_{task_data['Категория']}_{task_data['Описание задания']}_{task_data['Цена (руб.)']}_{task_data['GEO']}"
    return hashlib.md5(hash_string.encode()).hexdigest()


"""Получаем все задания из всех вкладок Google Sheets"""
async def get_tasks_from_sheets():
    try:
        sheet = client.open_by_key(sheet_id)
        tasks = []
        
        worksheets = ["Яндекс Карты", "Google maps", "2GIS", "Flamp"]
        
        for worksheet_name in worksheets:
            try:
                worksheet = sheet.worksheet(worksheet_name)
                records = worksheet.get_all_records()
                
                for record in records:
                    if not record.get('num') or not record.get('Описание задания'):
                        continue  # Пропускаем пустые строки
                        
                    geo = record.get('GEO', 'Все города')
                    if not geo:
                        geo = 'Все города'
                    
                    task = {
                        "task_num": record["num"],
                        "external_id": generate_task_hash(record),
                        "category": worksheet_name,
                        "description": record["Описание задания"],
                        "price": record.get("Цена (руб.)", 0),
                        "geo": geo
                    }
                    tasks.append(task)
                    # print(f"Добавлено задание: {task}")  # Отладочное сообщение
                    
            except Exception as e:
                print(f"Ошибка при обработке вкладки {worksheet_name}: {e}")
                continue
                
        return tasks
        
    except Exception as e:
        print(f"Ошибка при получении заданий из Google Sheets: {e}")
        return None