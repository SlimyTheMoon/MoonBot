import discord
from discord.ext import commands, tasks
import logging
import aiohttp
from dotenv import load_dotenv
import os
import ssl
from urllib.parse import urlparse

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
API_URL_BASES_GOODS = os.getenv("API_URL_BASES_GOODS")
API_URL_BASES_STATS = os.getenv("API_URL_BASES_STATS")
# TLS / scheme enforcement and options
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() not in ("0", "false", "no")
ALLOW_INSECURE_HTTP = os.getenv("ALLOW_INSECURE_HTTP", "false").lower() in ("1", "true", "yes")
SSL_CA_PATH = os.getenv("SSL_CA_PATH")  # optional path to a CA bundle

# If configured URL is not HTTPS and insecure HTTP is not explicitly allowed,
# disable the updater to avoid sending credentials/data over plaintext.
GOODS_UPDATER_DISABLED = False
if API_URL_BASES_GOODS:
    parsed_url = urlparse(API_URL_BASES_GOODS)
    if parsed_url.scheme and parsed_url.scheme.lower() != "https":
        if ALLOW_INSECURE_HTTP:
            logging.warning("API_URL_BASES_GOODS uses non-HTTPS scheme (%s) but ALLOW_INSECURE_HTTP is enabled", parsed_url.scheme)
        else:
            logging.error("API_URL_BASES_GOODS must use https:// — found '%s'. goods_updater will be disabled.", API_URL_BASES_GOODS)
            GOODS_UPDATER_DISABLED = True

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Helper: build an aiohttp connector according to TLS settings
def _create_connector():
    if not VERIFY_SSL:
        logging.warning("VERIFY_SSL is false — TLS certificate verification is disabled")
        return aiohttp.TCPConnector(ssl=False)
    if SSL_CA_PATH:
        try:
            ctx = ssl.create_default_context(cafile=SSL_CA_PATH)
            return aiohttp.TCPConnector(ssl=ctx)
        except Exception:
            logging.exception("Failed to create SSL context from SSL_CA_PATH=%s — falling back to system CAs", SSL_CA_PATH)
            return aiohttp.TCPConnector()
    return aiohttp.TCPConnector()  # default system verification
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

print("API_URL_BASES_GOODS:", API_URL_BASES_GOODS)
print("API_URL_BASES_STATS:", API_URL_BASES_STATS)
bot = commands.Bot(command_prefix='?', intents=intents)

goods = {}
health = {}
swear_words = ['shit', 'fat']


# HTTP session used by the periodic goods updater
_http_session = None

def _ensure_http_session():
    """Create a shared aiohttp.ClientSession with TLS settings applied."""
    global _http_session
    if _http_session is None:
        connector = _create_connector()
        _http_session = aiohttp.ClientSession(connector=connector)
    return _http_session


async def _fetch_goods_once(session):
    """Fetch JSON from API_URL_BASES_GOODS and update module-level `goods`.
    Failures are logged and do not raise — the loop should continue."""
    if not API_URL_BASES_GOODS:
        logging.warning("API_URL_BASES_GOODS not set")
        return
    try:
        async with session.get(API_URL_BASES_GOODS, timeout=10) as resp:
            if resp.status != 200:
                logging.warning("goods fetch returned %s", resp.status)
                return
            data = await resp.json()
    except Exception:
        logging.exception("Failed to fetch goods from %s", API_URL_BASES_GOODS)
        return

    # update goods atomically
    global goods
    if isinstance(data, dict):
        goods.clear()
        goods.update(data)
    else:
        goods = data
    logging.info("Updated goods (items=%s)", len(goods) if isinstance(goods, dict) else 1)


@tasks.loop(seconds=60)
async def goods_updater():
    if GOODS_UPDATER_DISABLED:
        logging.debug("goods_updater is disabled (non-HTTPS endpoint without ALLOW_INSECURE_HTTP)")
        return
    session = _ensure_http_session()
    await _fetch_goods_once(session)


@bot.event
async def on_ready():
    """Start the goods updater and ensure an aiohttp session exists."""
    if GOODS_UPDATER_DISABLED:
        logging.warning("goods_updater not started because API_URL_BASES_GOODS is not HTTPS and ALLOW_INSECURE_HTTP is false")
        return
    _ensure_http_session()
    if not goods_updater.is_running():
        goods_updater.start()
    logging.info("goods_updater started and running")


@bot.event
async def on_disconnect():
    """Attempt to close the shared aiohttp session on disconnect."""
    global _http_session
    if _http_session:
        try:
            await _http_session.close()
        except Exception:
            logging.exception("Error closing aiohttp session")
        _http_session = None


@bot.command(name="goods_debug")
async def goods_debug(ctx):
    """Debug command: show number of goods and a small sample."""
    if isinstance(goods, dict):
        sample_keys = list(goods.keys())[:5]
        sample = {k: goods[k] for k in sample_keys}
        await ctx.send(f"goods: {len(goods)} items\nsample: {sample}")
    else:
        await ctx.send(f"goods: {repr(goods)}")


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