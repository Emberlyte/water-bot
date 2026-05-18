import datetime
import logging
import os
import aiosqlite
import counter
from aiogram import types
from aiogram.filters import CommandObject
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

DB_NAME = os.getenv("DB_NAME")


async def check_date(user_id, db: aiosqlite.Connection):
    today = datetime.date.today().isoformat()

    try:
        async with db.execute(
            "SELECT last_reset FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if row and row[0] != today:
                await db.execute(
                    "UPDATE users SET poured_water = 0, last_reset = ? WHERE user_id = ?",
                    (today, user_id),
                )
                await db.commit()
            logging.info(f"Проверка даты выполнена для пользователя {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при проверке даты: {e}")
        return


async def check_goal_water(
    message: types.Message, user_id: int, db: aiosqlite.Connection
):
    try:
        async with db.execute(
            "SELECT poured_water, goal FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if row is None:
                return

            water = row[0]
            goal = row[1]

            if water >= goal:
                await message.answer(
                    "Поздравляю! Вы достигли своей цели по потреблению воды! 🎉"
                )
            else:
                remaining = goal - water
                await message.answer(
                    f"Вы выпили {water} мл из {goal} мл. Осталось еще {remaining} мл."
                )

    except Exception as e:
        logging.error(f"Ошибка при проверке воды: {e}")
        await message.answer("Произошла ошибка при проверке данных.")


async def add_user_in_db(message: types.Message, db: aiosqlite.Connection):
    try:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (message.from_user.id,),
        )
        await db.commit()
        logging.info(
            f"Пользователь {message.from_user.id} добавлен в базу данных"
        )
    except Exception as e:
        logging.error(f"Ошибка при добавлении пользователя: {e}")
        return


async def add_water_intake(
    message: types.Message,
    command: CommandObject,
    db: aiosqlite.Connection,
    water_ml: int,
):
    try:
        await check_date(message.from_user.id, db)

        await db.execute(
            "UPDATE users SET poured_water = poured_water + ?, poured_water_alltime = poured_water_alltime + ? WHERE user_id = ?",
            (
                water_ml,
                water_ml,
                message.from_user.id,
            ),
        )
        await db.commit()
        logging.info(f"Вода добавлена для пользователя {message.from_user.id}")

        async with db.execute(
            "SELECT poured_water, goal FROM users WHERE user_id = ?",
            (message.from_user.id,),
        ) as cursor:
            row = await cursor.fetchone()

            if row:
                row[0]
                row[1]
            else:
                pass
        await check_goal_water(message, message.from_user.id, db)
    except Exception as e:
        logging.error(f"Ошибка при добавлении воды: {e}")
        return


async def add_kg_intake(
    message: types.Message,
    command: CommandObject,
    db: aiosqlite.Connection,
    kg_answer: int,
):
    try:
        await check_date(message.from_user.id, db)

        await db.execute(
            "UPDATE users SET kg = ? WHERE user_id = ?",
            (kg_answer, message.from_user.id),
        )
        await db.commit()
        logging.info(f"Вес добавлен для пользователя {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении веса: {e}")
        return


async def add_goal_intake(
    message: types.Message,
    command: CommandObject,
    db: aiosqlite.Connection,
    goal_answer: int,
):
    try:
        await check_date(message.from_user.id, db)

        await db.execute(
            "UPDATE users SET goal = ? WHERE user_id = ?",
            (goal_answer, message.from_user.id),
        )
        await db.commit()
        logging.info(f"Цель добавлена для пользователя {message.from_user.id}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении цели: {e}")
        return


async def check_stats_intake(message: types.Message, db: aiosqlite.Connection):
    try:
        await check_date(message.from_user.id, db)
        async with db.execute(
            "SELECT poured_water, poured_water_alltime, kg, goal FROM users WHERE user_id = ?",
            (message.from_user.id,),
        ) as cursor:
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

        logging.info(
            f"Статистика получена для пользователя {message.from_user.id}"
        )
        return poured_water, goal, liter, weight
    except Exception as e:
        logging.error(f"Ошибка при проверке статистики: {e}")
        return None
