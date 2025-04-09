import asyncio
from aiosqlite import connect, Row
import logging

from config import TOKEN
from handlers import router
from db import init_db

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message



bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main() -> None:
    await init_db()
    async with connect("database.db") as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE is_admin = 1")
        admin_exists = await cursor.fetchone()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Прекращение работы...")