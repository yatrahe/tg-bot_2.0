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
                task_num INTEGER,
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

        # Таблица для хранения состояния выполнения заданий по действиям
        await db.execute('''
            CREATE TABLE IF NOT EXISTS task_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_id INTEGER,
                current_step INTEGER DEFAULT 0,
                completed_steps TEXT DEFAULT '[]',
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        ''')
        await db.commit()

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
    
    async def get_user_by_id(self, user_id):
        #Получение данных пользователя по ID
        async with connect(self.db_file) as db:
            db.row_factory = Row
            cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = await cursor.fetchone()
            return user
    
    async def clear_tasks(self):
        """Очищает таблицу заданий"""
        async with connect(self.db_file) as db:
            await db.execute("DELETE FROM tasks")
            await db.commit()
    
    async def add_task(self, task_num, external_id, category, description, price, geo):
        """Добавляет задание в БД"""
        async with connect(self.db_file) as db:
            await db.execute(
                "INSERT INTO tasks (task_num, external_id, category, description, price, geo) VALUES (?, ?, ?, ?, ?, ?)",
                (task_num, external_id, category, description, price, geo)
            )
            await db.commit()
    
    async def get_admin_ids(self):
        """Получает список ID администраторов"""
        async with connect(self.db_file) as db:
            cursor = await db.execute("SELECT user_id FROM users WHERE is_admin = 1")
            admins = await cursor.fetchall()
            return [admin[0] for admin in admins]
    
    """ Для заданий по действиям --------------------------------------------------"""
    async def get_task_by_id(self, task_id):
        async with connect(self.db_file) as db:
            db.row_factory = Row
            cursor = await db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            return await cursor.fetchone()
    
    async def deactivate_task(self, task_id):
        async with connect(self.db_file) as db:
            await db.execute('UPDATE tasks SET is_active = 0 WHERE id = ?', (task_id,))
            await db.commit()
    
    async def delete_task(self, task_id):
        async with connect(self.db_file) as db:
            await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            await db.commit()
    
    async def get_user_task_progress(self, user_id, task_id):
        async with connect(self.db_file) as db:
            db.row_factory = Row
            cursor = await db.execute(
                'SELECT * FROM task_steps WHERE user_id = ? AND task_id = ?',
                (user_id, task_id)
            )
            return await cursor.fetchone()
    
    async def update_task_progress(self, user_id, task_id, current_step, completed_steps):
        async with connect(self.db_file) as db:
            # Проверяем, есть ли уже запись
            progress = await self.get_user_task_progress(user_id, task_id)
            
            if progress:
                await db.execute(
                    'UPDATE task_steps SET current_step = ?, completed_steps = ? WHERE id = ?',
                    (current_step, completed_steps, progress['id'])
                )
            else:
                await db.execute(
                    'INSERT INTO task_steps (user_id, task_id, current_step, completed_steps) VALUES (?, ?, ?, ?)',
                    (user_id, task_id, current_step, completed_steps)
                )
            await db.commit()
    
    async def complete_task_step(self, user_id, task_id, step):
        async with connect(self.db_file) as db:
            progress = await self.get_user_task_progress(user_id, task_id)
            if progress:
                completed_steps = eval(progress['completed_steps'])
                if step not in completed_steps:
                    completed_steps.append(step)
                    await self.update_task_progress(
                        user_id, task_id,
                        progress['current_step'],
                        str(completed_steps)
                    )

    """Получает активное задание по типу"""
    async def get_active_task_by_type(self, task_type):
        async with connect(self.db_file) as db:
            db.row_factory = Row
            cursor = await db.execute(
                'SELECT * FROM tasks WHERE category = ? AND is_active = 1 LIMIT 1',
                (task_type,))
            return await cursor.fetchone()

    """Получает запись о задании пользователя"""
    async def get_user_task_by_task_id(self, task_id):
        async with connect(self.db_file) as db:
            db.row_factory = Row
            cursor = await db.execute(
                'SELECT * FROM user_tasks WHERE task_id = ? LIMIT 1',
                (task_id,))
            return await cursor.fetchone()
    
    """Получает активное задание для пользователя по категории и городу"""
    async def get_active_task_for_user(self, category: str, city: str):
        async with connect(self.db_file) as db:
            db.row_factory = Row
            print(f"Поиск задания: категория={category}, город={city}")  # Отладочное сообщение
            cursor = await db.execute(
                '''SELECT * FROM tasks 
                WHERE category = ? AND is_active = 1 
                AND (geo LIKE ? OR geo LIKE 'Все города%') 
                LIMIT 1''',
                (category, f"%{city}%")
            )
            task = await cursor.fetchone()
            print(f"Найдено задание: {task}")  # Отладочное сообщение
            return task

    """Добавляет запись о взятом задании пользователем"""
    async def add_user_task(self, user_id: int, task_id: int, status: str = 'active'):
        async with connect(self.db_file) as db:
            await db.execute(
                '''INSERT INTO user_tasks 
                (user_id, task_id, status, accepted_at) 
                VALUES (?, ?, ?, ?)''',
                (user_id, task_id, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            await db.commit()

    """Получает активное задание для пользователя по категории и городу"""
    async def get_active_task_for_user(self, category: str, city: str):
        async with connect(self.db_file) as db:
            db.row_factory = Row
            # Ищем сначала для конкретного города, потом для всех городов
            cursor = await db.execute('''
                SELECT * FROM tasks 
                WHERE category = ? AND is_active = 1 
                AND (geo LIKE ? OR geo = 'Все города')
                ORDER BY CASE WHEN geo LIKE ? THEN 0 ELSE 1 END
                LIMIT 1
            ''', (category, f"%{city}%", f"%{city}%"))
            return await cursor.fetchone()