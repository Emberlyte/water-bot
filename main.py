import os
import asyncio
import logging
import aiosqlite

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

import init_db
import handlers
import databasemiddleware

logging.basicConfig(level=logging.INFO)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_NAME = os.getenv("DB_NAME")

if not BOT_TOKEN:
    raise ValueError("телеграмм токен не задан")

if not DB_NAME:
    raise ValueError("название базы данных не задано")


async def main():
  
    await init_db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))

    dp = Dispatcher()

    dp.update.middleware(databasemiddleware.DatabaseMiddleware(DB_NAME))
    dp.include_router(handlers.router)


    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
