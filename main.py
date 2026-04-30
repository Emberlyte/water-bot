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

    try:
        async with db.execute("SELECT last_reset FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

            if row and row[0] != today:
                await db.execute("UPDATE users SET poured_water = 0, last_reset = ? WHERE user_id = ?", (today, user_id))
                await db.commit()
            logging.info(f"Проверка даты выполнена для пользователя {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при проверке даты: {e}")

async def main():
    await init_db.init_db()

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_command(message: types.Message):
        try:
             async with aiosqlite.connect(db_name) as db:
                await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
                await db.commit()
                logging.info(f"Пользователь {message.from_user.id} добавлен в базу данных")
        except Exception as e:
            logging.error(f"Ошибка при добавлении пользователя в базу данных: {e}")

        await message.answer(f"Привет, {message.from_user.full_name}!")

    @dp.message(Command("add"))
    async def add_water(message: types.Message, command:CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer("Пожалуйста, укажи количество воды в мл. Пример: /add 350")
            return

        water_ml = int(command.args)

        try:
            async with aiosqlite.connect(db_name) as db:
                await check_date(message.from_user.id, db)

                await db.execute("UPDATE users SET poured_water = poured_water + ?, poured_water_alltime = poured_water_alltime + ? WHERE user_id = ?", (water_ml, water_ml, message.from_user.id,))
                await db.commit()
                logging.info(f"Вода добавлена для пользователя {message.from_user.id}")

                async with db.execute("SELECT poured_water, goal FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
                    row = await cursor.fetchone()

                    if row:
                        count = row[0]
                        goal = row[1]
                    else:
                        count = water_ml
                        goal = 2000
        except Exception as e:
            logging.error(f"Ошибка при добавлении воды: {e}")

        await message.answer(f"Вода добавлена. Всего воды: {count} из {goal}")


    @dp.message(Command("kg"))
    async def kg_command(message: types.Message, command: CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer("Пожалуйста, твой вес. Пример: /kg 2000")
            return

        kg_answer = int(command.args)

        try:
            async with aiosqlite.connect(db_name) as db:
                await check_date(message.from_user.id, db)

                await db.execute("UPDATE users SET kg = ? WHERE user_id = ?", (kg_answer, message.from_user.id))
                await db.commit()
                logging.info(f"Вес добавлен для пользователя {message.from_user.id}")
        except Exception as e:
            logging.error(f"Ошибка при добавлении веса: {e}")

        kg_water_counter = kg.counter_water_goal(kg_answer)

        await message.answer(f"Ваша рекомендуемый объем воды: {kg_water_counter}")

    @dp.message(Command("goal"))
    async def goal_command(message: types.Message, command: CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer("Пожалуйста, ваша цель выпитой воды. Пример: /goal 2000")
            return

        goal_answer = int(command.args)

        try:
            async with aiosqlite.connect(db_name) as db:
                await check_date(message.from_user.id, db)

                await db.execute("UPDATE users SET goal = ? WHERE user_id = ?", (goal_answer, message.from_user.id))
                await db.commit()
                logging.info(f"Цель добавлена для пользователя {message.from_user.id}")
        except Exception as e:
            logging.error(f"Ошибка при добавлении цели: {e}")

        await message.answer(f"Ваша цель выпитой воды: {goal_answer}")

    @dp.message(Command("stats"))
    async def stats_command(message: types.Message):
        try:
            async with aiosqlite.connect(db_name) as db:
                async with db.execute("SELECT poured_water, poured_water_alltime, kg, goal FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
                    row = await cursor.fetchone()

                    if row:
                        poured_water = row[0]
                        poured_water_all = row[1]
                        weight = row[2]
                        goal = row[3]
                    else:
                        poured_water = 0
                        poured_water_all = 0
                        weight = 0
                        goal = 2000

                logging.info(f"Статистика пользователя {message.from_user.id} получена")
        except Exception as e:
            logging.error(f"Ошибка при получении статистики: {e}")


        await message.answer(
            f"📊 Статистика:\n"
            f"💧 Выпито сегодня: {poured_water} / {goal} мл\n"
            f"🌍 Всего выпито: {poured_water_all} мл\n"
            f"⚖️ Вес: {weight} кг"
        )

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")

