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
from aiogram.client.default import DefaultBotProperties

import init_db
import counter

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

    bot = Bot(token=bot_token,
              default=DefaultBotProperties(parse_mode='Markdown'))
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

        await message.answer(
            f"👋 **Привет, {message.from_user.full_name}!**\n\n"
            "Я помогу тебе следить за водным балансом. 💧\n\n"
            "**С чего начать?**\n"
            "1️⃣ Установи свой вес: `/kg 75`\n"
            "2️⃣ Установи цель (если стандартная не подходит): `/goal 2000`\n"
            "3️⃣ Добавляй выпитую воду: `/add 250`"
        )

    @dp.message(Command("add"))
    async def add_water(message: types.Message, command:CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer(
                "⚠️ **Не указано количество!**\n"
                "Напишите, сколько мл вы выпили.\n"
                "Пример: `/add 300`"
            )
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

        await message.answer(
            f"✅ **Данные обновлены!**\n"
            f"➕ Добавлено: `{water_ml}` мл\n"
            f"🥤 Сегодня: `{count}` / `{goal}` мл"
        )


    @dp.message(Command("kg"))
    async def kg_command(message: types.Message, command: CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer(
                "⚖️ **Укажите ваш вес в килограммах.**\n"
                "Пример: `/kg 70`"
            )
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

        kg_water_counter = counter.counter_water_goal(kg_answer)

        await message.answer(
            f"⚙️ **Вес сохранен: {kg_answer} кг.**\n"
            f"💧 Рекомендуемая норма для вас: **{kg_water_counter} мл** в день.\n"
            f"Чтобы применить её, используйте: `/goal {kg_water_counter}`"
        )

    @dp.message(Command("goal"))
    async def goal_command(message: types.Message, command: CommandObject):

        if command.args is None or not command.args.isdigit():
            await message.answer(
                "🎯 **Установите дневную цель.**\n"
                "Пример: `/goal 2500` (в миллилитрах)"
            )
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

        await message.answer(
            f"🎯 **Цель установлена: {goal_answer} мл.**\n"
            "Я буду следить за твоими успехами! 🚀"
        )

    @dp.message(Command("stats"))
    async def stats_command(message: types.Message):
        try:
            async with aiosqlite.connect(db_name) as db:
                await check_date(message.from_user.id, db)
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
                        weight = 60
                        goal = 2000

                liter = counter.counter_water_liter(poured_water_all)

                logging.info(f"Статистика пользователя {message.from_user.id} получена")
        except Exception as e:
            logging.error(f"Ошибка при получении статистики: {e}")


        await message.answer(
            f"📊 Статистика:\n"
            f"💧 Выпито сегодня: {poured_water} / {goal} мл\n"
            f"🌍 Всего выпито: {liter} л\n"
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

