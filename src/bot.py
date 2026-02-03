import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger("DiscordClient")

class MoonBot(commands.Bot):
    def __init__(self, db):
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)
        self.db = db

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=discord.Game(name="Watching POBs"))

    async def send_global_alert(self, message_content, embed=None):
        """
        Sends a message to ALL subscribed channels.
        Used by the Poller when a major event happens.
        """
        channels = await self.db.get_all_channels()
        if not channels:
            logger.info("No channels subscribed for alerts.")
            return

        logger.info(f"Broadcasting alert to {len(channels)} channels.")
        
        for channel_id in channels:
            try:
                channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                if channel:
                    await channel.send(content=message_content, embed=embed)
            except discord.Forbidden:
                logger.warning(f"Missing permissions in channel {channel_id}")
            except Exception as e:
                logger.error(f"Failed to send to {channel_id}: {e}")

    async def setup_hook(self):
        # --- Slash Commands Definitions ---
        
        @self.tree.command(name="track_here", description="Start receiving POB alerts in this channel")
        async def track_here(interaction: discord.Interaction):
            # Check permissions
            if not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("You need 'Manage Server' permission to configure me.", ephemeral=True)
                return

            success = await self.db.add_subscription(interaction.guild_id, interaction.channel_id)
            if success:
                await interaction.response.send_message(f"✅ MoonBot will now send POB alerts to {interaction.channel.mention}.")
            else:
                await interaction.response.send_message(f"ℹ️ This channel is already tracking alerts.", ephemeral=True)

        @self.tree.command(name="stop_tracking", description="Stop receiving POB alerts in this channel")
        async def stop_tracking(interaction: discord.Interaction):
            if not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("You need 'Manage Server' permission.", ephemeral=True)
                return

            await self.db.remove_subscription(interaction.channel_id)
            await interaction.response.send_message(f"🚫 Alerts stopped for {interaction.channel.mention}.")

        @self.tree.command(name="check_api", description="Debug command to check DarkStat connection")
        async def check_api(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            # This is a placeholder. Real status checks can be added here.
            await interaction.followup.send("API Check initiated (Check logs for details).")

        # Sync commands with Discord
        await self.tree.sync()
        logger.info("Command tree synced.")