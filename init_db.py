import aiosqlite
import os
import logging

from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
logging.basicConfig(level=logging.INFO)

async def init_db():
    async with aiosqlite.connect(str(DB_NAME)) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            poured_water INTEGER DEFAULT 0,
            poured_water_alltime INTEGER DEFAULT 0,
            kg INTEGER DEFAULT 0,
            goal INTEGER DEFAULT 0,
            last_reset DATE DEFAULT (CURRENT_DATE)
            )""")
        await db.commit()
        logging.info(f"💾 База данных '{DB_NAME}' успешно инициализирована.")
