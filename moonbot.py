import asyncio
import os
import aiohttp
import sqlite3
import logging
from datetime import datetime
from quart import Quart, render_template, request, redirect, url_for
from discord.ext import commands, tasks
import discord

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN", "")
API_URL = "https://darkstat.dd84ai.com/api/pob_goods"
POLL_INTERVAL = 60  # Seconds
DB_NAME = "moonbot.db"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MoonBot")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table to store configuration (which channel gets alerts)
    c.execute('''CREATE TABLE IF NOT EXISTS config (guild_id INTEGER PRIMARY KEY, channel_id INTEGER)''')
    # Table to store the last known state of POBs to detect changes
    c.execute('''CREATE TABLE IF NOT EXISTS pobs (id TEXT PRIMARY KEY, owner TEXT, health REAL, items TEXT)''')
    conn.commit()
    conn.close()

def get_alert_channel(guild_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT channel_id FROM config WHERE guild_id=?", (guild_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_alert_channel(guild_id, channel_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (guild_id, channel_id) VALUES (?, ?)", (guild_id, channel_id))
    conn.commit()
    conn.close()

# --- WEB SERVER (QUART) ---
app = Quart(__name__)
# We need a reference to the bot instance in the web app
app.bot_instance = None

@app.route('/')
async def index():
    """Main Dashboard: List guilds and allow configuration."""
    if not app.bot_instance or not app.bot_instance.is_ready():
        return "Bot is starting...", 503
    
    guilds_data = []
    for guild in app.bot_instance.guilds:
        current_channel_id = get_alert_channel(guild.id)
        # Get text channels only
        channels = [{"id": c.id, "name": c.name} for c in guild.text_channels]
        
        guilds_data.append({
            "id": guild.id,
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "channels": channels,
            "current_channel_id": current_channel_id
        })
    
    return await render_template('index.html', guilds=guilds_data)

@app.route('/configure', methods=['POST'])
async def configure():
    """Handle form submission from the dashboard."""
    form = await request.form
    guild_id = int(form.get('guild_id'))
    channel_id = int(form.get('channel_id'))
    
    set_alert_channel(guild_id, channel_id)
    return redirect(url_for('index'))

# --- DISCORD BOT ---
class MoonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True  # Needed to list servers
        intents.message_content = True # Needed if reading commands from chat
        super().__init__(command_prefix="/", intents=intents)
        self.http_session = None

    async def setup_hook(self):
        # Initialize DB
        init_db()
        # Start the background task
        self.tracker_task.start()
        # Link bot to web app
        app.bot_instance = self
        # Run Quart app in background
        asyncio.create_task(app.run_task(host='0.0.0.0', port=5000))
        logger.info("Setup complete. Web UI running on port 5000.")

    async def on_ready(self):
        self.http_session = aiohttp.ClientSession()
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def close(self):
        if self.http_session:
            await self.http_session.close()
        await super().close()

    async def check_pob_data(self):
        """Fetch API and compare with DB to find changes."""
        if not self.http_session: return

        try:
            async with self.http_session.get(API_URL) as response:
                if response.status != 200:
                    logger.warning(f"API Error: {response.status}")
                    return
                
                data = await response.json()
                # Assuming data is a list of objects. Adjust parsing based on actual API structure.
                # Example assumed structure: [{'id': '123', 'owner': 'Player1', 'health': 100, 'items': 'Iron'}]
                
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()

                for pob in data:
                    pob_id = str(pob.get('id', 'unknown'))
                    owner = pob.get('owner', 'Unknown')
                    current_health = float(pob.get('health', 0))
                    current_items = str(pob.get('items', ''))

                    # Check previous state
                    c.execute("SELECT health, items FROM pobs WHERE id=?", (pob_id,))
                    row = c.fetchone()

                    if row:
                        last_health, last_items = row
                        
                        # LOGIC: Check for Health Drop
                        if current_health < last_health:
                            await self.broadcast_alert(
                                title="🚨 POB Under Attack!",
                                description=f"Base owned by **{owner}** took damage!\nHealth: {last_health}% -> **{current_health}%**",
                                color=discord.Color.red()
                            )
                        
                        # LOGIC: Check for New Items (Simple string diff)
                        if current_items != last_items and len(current_items) > len(last_items):
                            await self.broadcast_alert(
                                title="📦 New Public Items",
                                description=f"New goods at **{owner}**'s base.\nItems: {current_items}",
                                color=discord.Color.green()
                            )
                    else:
                        # New base discovered
                        logger.info(f"New POB tracked: {pob_id}")

                    # Update DB
                    c.execute("INSERT OR REPLACE INTO pobs (id, owner, health, items) VALUES (?, ?, ?, ?)",
                              (pob_id, owner, current_health, current_items))
                
                conn.commit()
                conn.close()

        except Exception as e:
            logger.error(f"Error in polling loop: {e}")

    async def broadcast_alert(self, title, description, color):
        """Send embed to all configured channels."""
        for guild in self.guilds:
            channel_id = get_alert_channel(guild.id)
            if channel_id:
                channel = self.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now())
                    try:
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        logger.warning(f"Missing permissions in guild {guild.name}")

    @tasks.loop(seconds=POLL_INTERVAL)
    async def tracker_task(self):
        await self.check_pob_data()

    @tracker_task.before_loop
    async def before_tracker(self):
        await self.wait_until_ready()

bot = MoonBot()

# --- SLASH COMMANDS ---
@bot.tree.command(name="set_alert", description="Set the channel for MoonBot alerts")
@discord.app_commands.describe(channel="The channel to send alerts to")
async def set_alert(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need Administrator permissions.", ephemeral=True)
        return

    set_alert_channel(interaction.guild_id, channel.id)
    await interaction.response.send_message(f"✅ Alerts will now be sent to {channel.mention}")

@bot.tree.command(name="check_now", description="Force a manual check of the API")
async def check_now(interaction: discord.Interaction):
    await interaction.response.defer()
    await bot.check_pob_data()
    await interaction.followup.send("✅ Manual check complete.")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable is missing.")
    else:
        bot.run(TOKEN)