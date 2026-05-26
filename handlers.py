import logging

from aiogram import Router, types
from dotenv import load_dotenv
from aiogram.filters import Command, CommandObject, CommandStart

import database

logging.basicConfig(level=logging.INFO)

load_dotenv()

router = Router()

@router.message(CommandStart())
async def start_command(message: types.Message, db):
    try:
        await database.add_user_in_db(message, db)
    except Exception as e:
        logging.error(f"ошибка при стартовой команде: {e}")
        return

    await message.answer(
            f"👋 **Привет, {message.from_user.full_name}!**\n\n"
            "Я помогу тебе следить за водным балансом. 💧\n\n"
            "**С чего начать?**\n"
            "1️⃣ Установи свой вес: `/kg 75`\n"
            "2️⃣ Установи цель (если стандартная не подходит): `/goal 2000`\n"
            "3️⃣ Добавляй выпитую воду: `/add 250`"
        )

@router.message(Command("add"))
async def water_command(message: types.Message, command: CommandObject, db):

    if command.args is None or not command.args.isdigit():
        await message.answer(
            "⚠️ **Не указано количество!**\n"
            "Напишите, сколько мл вы выпили.\n"
            "Пример: `/add 300`"
        )
        return
    try:
        water_ml = int(command.args)
    except ValueError:
        await message.answer("Ошибка: аргумент должен быть целым числом.")
        return

    await database.add_water_intake(message, command, db, water_ml)
    await message.answer(f"Зафиксировано: +{water_ml} мл воды! 🚰")


@router.message(Command("kg"))
async def kg_command(message: types.Message, command: CommandObject, db):

    if command.args is None or not command.args.isdigit():
        await message.answer("⚖️ **Укажите ваш вес в килограммах.**\n" "Пример: `/kg 70`")
        return

    try:
        kg = int(command.args)
    except ValueError:
        await message.answer("Ошибка: аргумент должен быть целым числом.")
        return

    await database.add_kg_intake(message, command, db, kg)
    await message.answer(f"Ваш вес обновлен: {kg} кг ⚖️")

@router.message(Command("goal"))
async def goal_command(message: types.Message, command: CommandObject, db):

    if command.args is None:
        await message.answer(
            "Ошибка: введите вашу цель по воде в мл после команды. Пример: /goal 2000"
        )
        return

    try:
        goal = int(command.args)
    except ValueError:
        await message.answer("Ошибка: аргумент должен быть целым числом.")
        return

    await database.add_goal_intake(message, command, db, goal)
    await message.answer(f"Ваша цель обновлена: {goal} мл 🎯")

@router.message(Command("stats"))
async def stats_command(message: types.Message, db):
    stats = await database.check_stats_intake(message, db)

    if stats is None:
        await message.answer("Произошла ошибка при получении статистики. Попробуйте позже.")
        return

    poured_water, goal, liter, weight = stats

    await message.answer(
        f"📊 Статистика:\n"
        f"💧 Выпито сегодня: {poured_water} / {goal} мл\n"
        f"🌍 Всего выпито: {liter} л\n"
        f"⚖️ Вес: {weight} кг"
    )




