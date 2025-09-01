import asyncpg
from app.config import POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT

class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(100),
                    full_name VARCHAR(200),
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    async def add_user(self, user_id, username, full_name):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, full_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name
            ''', user_id, username, full_name)

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch('SELECT user_id FROM users')

# Глобальный экземпляр базы данных
db = Database()