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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'shit' in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please watch your language.")
    await bot.process_commands(message)

@bot.command()
async def healthtracker(ctx):
    await ctx.send(f"Test")   

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'am i fat?' in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention}, I am sorry buddy, yes you are.")
    await bot.process_commands(message)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)