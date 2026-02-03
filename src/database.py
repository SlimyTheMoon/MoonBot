import aiosqlite
import logging

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    async def init(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.create_tables()
        logging.info("Database initialized.")

    async def create_tables(self):
        # Stores which channels want alerts
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                alert_type TEXT DEFAULT 'all',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, channel_id)
            )
        ''')
        await self.conn.commit()

    async def add_subscription(self, guild_id, channel_id):
        try:
            await self.conn.execute(
                "INSERT INTO subscriptions (guild_id, channel_id) VALUES (?, ?)",
                (guild_id, channel_id)
            )
            await self.conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False # Already exists

    async def remove_subscription(self, channel_id):
        await self.conn.execute(
            "DELETE FROM subscriptions WHERE channel_id = ?",
            (channel_id,)
        )
        await self.conn.commit()

    async def get_all_channels(self):
        async with self.conn.execute("SELECT channel_id FROM subscriptions") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def close(self):
        if self.conn:
            await self.conn.close()