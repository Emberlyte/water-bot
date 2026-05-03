import aiosqlite

from aiogram import BaseMiddleware


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db_name: str):
        self.db_name = db_name

    async def __call__(self, handler, event, data):
        async with aiosqlite.connect(self.db_name) as db:
            data["db"] = db
            return await handler(event, data)
