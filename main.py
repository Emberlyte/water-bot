import datetime
import os
import asyncio
import logging
import aiosqlite

from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandObject
from aiogram import types

import init_db
import kg

logging.basicConfig(level=logging.INFO)

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
db_name = os.getenv("DB_NAME")

if not bot_token:
    raise ValueError("телеграмм токен не задан")

if not db_name:
    raise ValueError("название базы данных не задано")

async def check_date(user_id, db):
    today = datetime.date.today().isoformat()

    async with db.execute("SELECT last_reset FROM users WHERE user_id = ?", (user_id,)) as cursor:
        row = await cursor.fetchone()
        if row and row[0] != today:
            await db.execute("UPDATE users SET poured_water = 0, last_reset = ? WHERE user_id = ?", (today, user_id))
            await db.commit()

async def main():
    await init_db.init_db()

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_command(message: types.Message):
        async with aiosqlite.connect(db_name) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
            await db.commit()

        await message.answer(f"Привет, {message.from_user.full_name}!")

    @dp.message(Command("add"))
    async def add_water(message: types.Message, command:CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer("Пожалуйста, укажи количество воды в мл. Пример: /add 350")
            return

        water_ml = int(command.args)

        async with aiosqlite.connect(db_name) as db:
            await check_date(message.from_user.id, db)

            await db.execute("UPDATE users SET poured_water = poured_water + ? WHERE user_id = ?", (water_ml, message.from_user.id,))
            await db.commit()

            async with db.execute("SELECT poured_water FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
                row = await cursor.fetchone()
                count = row[0]

        await message.answer(f"Вода добавлена. Всего воды: {count}")


    @dp.message(Command("kg"))
    async def kg_command(message: types.Message, command: CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer("Пожалуйста, твой вес. Пример: /kg 2000")
            return

        kg_answer = int(command.args)

        async with aiosqlite.connect(db_name) as db:
            await check_date(message.from_user.id, db)

            await db.execute("UPDATE users SET kg = ? WHERE user_id = ?", (kg_answer, message.from_user.id))
            await db.commit()

        kg_water_counter = kg.counter_water_goal(kg_answer)

        await message.answer(f"Ваша рекомендуемый объем воды: {kg_water_counter}")

    @dp.message(Command("goal"))
    async def goal_command(message: types.Message, command: CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer("Пожалуйста, ваша цель выпитой воды. Пример: /goal 2000")
            return

        goal_answer = int(command.args)

        async with aiosqlite.connect(db_name) as db:
            await check_date(message.from_user.id, db)

            await db.execute("UPDATE users SET goal = ? WHERE user_id = ?", (goal_answer, message.from_user.id))
            await db.commit()

        await message.answer(f"Ваша цель выпитой воды: {goal_answer}")


    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")

