import asyncio
import aiohttp
import logging
import discord

logger = logging.getLogger("Poller")

class DarkStatPoller:
    def __init__(self, api_url, bot, db):
        self.api_url = api_url
        self.bot = bot
        self.db = db
        self.last_data = {} # Cache for diffing: {base_id: base_data}

    async def fetch_data(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.api_url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API Error: Status {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Fetch failed: {e}")
                return None

    async def process_data(self, current_data):
        """
        Compare current_data with self.last_data to find changes.
        """
        if not current_data or not isinstance(current_data, list):
            return

        # Map current data by name or ID
        current_map = {item.get('name', 'Unknown'): item for item in current_data}
        
        # If this is the first run, just populate cache and return
        if not self.last_data:
            self.last_data = current_map
            logger.info("Initial data loaded. Ready to track changes.")
            return

        # Check for changes
        for name, data in current_map.items():
            old_data = self.last_data.get(name)
            
            if old_data:
                # Check Health Drop (Ensure 'health' matches the actual API key)
                current_health = data.get('health', 0)
                old_health = old_data.get('health', 0)

                if current_health < old_health:
                    diff = old_health - current_health
                    # Threshold: Only alert if drop is significant (e.g. > 5%)
                    if diff > 5: 
                        await self.trigger_alert(name, old_health, current_health)
            
        # Update cache
        self.last_data = current_map

    async def trigger_alert(self, base_name, old_h, new_h):
        logger.info(f"ALERT: {base_name} dropped health {old_h} -> {new_h}")
        
        embed = discord.Embed(
            title="⚠️ Base Under Attack / Decaying",
            description=f"**{base_name}** health has dropped!",
            color=discord.Color.red()
        )
        embed.add_field(name="Previous Health", value=f"{old_h}%", inline=True)
        embed.add_field(name="Current Health", value=f"{new_h}%", inline=True)
        embed.set_footer(text="MoonBot POB Tracker")

        await self.bot.send_global_alert(message_content="", embed=embed)

    async def start(self, stop_event):
        logger.info("Poller started.")
        while not stop_event.is_set():
            data = await self.fetch_data()
            if data:
                await self.process_data(data)
            
            # Wait for 60 seconds before next poll
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=60.0)
            except asyncio.TimeoutError:
                continue