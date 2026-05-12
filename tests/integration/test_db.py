import pytest
import aiosqlite
import pytest_asyncio
from main import check_date

@pytest_asyncio.fixture
async def db():
    async with aiosqlite.connect(":memory:") as db:
        await db.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                poured_water INTEGER DEFAULT 0,
                poured_water_alltime INTEGER DEFAULT 0,
                kg INTEGER DEFAULT 60,
                goal INTEGER DEFAULT 2000,
                last_reset DATE DEFAULT (CURRENT_DATE)
            )""")
        await db.commit()
        yield db

@pytest.mark.asyncio
class TestUserDatabase:
    async def test_init_user(self, db):
        user_id = 123
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        async with db.execute("SELECT kg, goal FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            assert row[0] == 60
            assert row[1] == 2000

    async def test_add_water_logic(self, db):
        user_id = 123
        water_to_add = 500
        await db.execute("INSERT INTO users (user_id, poured_water) VALUES (?, ?)", (user_id, 100))
        await db.execute(
            "UPDATE users SET poured_water = poured_water + ? WHERE user_id = ?",
            (water_to_add, user_id)
        )
        await db.commit()
        async with db.execute("SELECT poured_water FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            assert row[0] == 600

    async def test_check_date_reset(self, db):
        user_id = 456
        await db.execute(
            "INSERT INTO users (user_id, poured_water, last_reset) VALUES (?, ?, ?)",
            (user_id, 1500, "2000-01-01")
        )
        await db.commit()
        await check_date(user_id, db)
        async with db.execute("SELECT poured_water FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            assert row[0] == 0