import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
API_URL_BASES_GOODS = os.getenv("API_URL_BASES_GOODS")
API_URL_BASES_STATS = os.getenv("API_URL_BASES_STATS")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

print("API_URL_BASES_GOODS:", API_URL_BASES_GOODS)
print("API_URL_BASES_STATS:", API_URL_BASES_STATS)
bot = commands.Bot(command_prefix='?', intents=intents)

goods = {}
health = {}
swear_words = ['shit', 'fat']

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if any(swear_word in message.content.lower() for swear_word in swear_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please watch your language.")
    await bot.process_commands(message)

@bot.command()
async def healthtracker(ctx):
    await ctx.send(f"Test")   


bot.run(token, log_handler=handler, log_level=logging.DEBUG)