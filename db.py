from aiosqlite import connect, Row
import hashlib
from datetime import datetime


async def init_db():
    # Инициализация БД
    async with connect("database.db") as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_admin INTEGER DEFAULT 0,
                full_name TEXT,
                city TEXT,
                balance INTEGER DEFAULT 0,
                signup_date TEXT,
                amount_tasks INTEGER DEFAULT 0,
                task_check INTEGER DEFAULT 0
            )
        """)
        # Таблица заданий
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT UNIQUE,
                category TEXT,
                description TEXT,
                price INTEGER,
                geo TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        # Таблица активных заданий
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                status TEXT DEFAULT 'active',
                accepted_at TEXT,
                completed_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(task_id) REFERENCES tasks(external_id)
            )
        ''')

        # Индексы для ускорения поиска
        await db.execute('CREATE INDEX IF NOT EXISTS idx_external_id ON tasks(external_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')

        await db.commit()


class Database:
    def __init__(self, db_file):
        self.db_file = db_file

    async def user_exists(self, user_id):
        async with connect(self.db_file) as db:
            cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            result = await cursor.fetchone()
            return result is not None

    async def add_user(self, user_id, full_name):
        async with connect(self.db_file) as db:
            await db.execute("INSERT INTO users (user_id, full_name, signup_date) VALUES (?, ?, ?)",
                            (user_id, full_name, datetime.now().strftime("%d.%m.%Y")))
            await db.commit()
    
    async def set_city(self, user_id, city):
        #Установка города пользователя
        async with connect(self.db_file) as db:
            await db.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id,))
            await db.commit()