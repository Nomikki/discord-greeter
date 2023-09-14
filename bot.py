import asyncio
import mimetypes
import os
from urllib.parse import urlparse
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re
import json
import logging
import yaml

# Configure logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(filename='output.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.NOTSET)

logging.info("Running greeter-bot")
logger = logging.getLogger('greeter-bot')



# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

dev = False
if dev:
    GREETING_CHANNEL = int(os.getenv('GREETING_CHANNEL_DEV'))
    MEDIA_CHANNEL = int(os.getenv('MEDIA_CHANNEL_DEV'))
else:
    GREETING_CHANNEL = int(os.getenv('GREETING_CHANNEL'))
    MEDIA_CHANNEL = int(os.getenv('MEDIA_CHANNEL'))

GREETING_TIMEOUT_HOURS = int(os.getenv('GREETING_TIMEOUT_HOURS') or 2)
GREETING_TIMEOUT = GREETING_TIMEOUT_HOURS * 60 * 60
RULES_FILE = 'rules.yaml'

ALLOWED_URLS_RULES = re.compile(r"(.*)")
ALLOWED_MIMETYPES_RULES = re.compile(r"(.*)")

# Load messages from JSON file
with open('messages.json') as f:
    messages = json.load(f)

LANGUAGE = 'fi'  # Change this based on user preferences or server settings

# Initialize the bot with a command prefix and description
description = '''igorTheLoggerBot'''
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', case_insensitive=True, help_command=None, intents=intents)

def reload_rules_if_changed(file):
    global rules_stamp
    global rules
    global ALLOWED_MIMETYPES_RULES
    global ALLOWED_URLS_RULES

    current_stamp = os.stat(file).st_mtime
    
    if rules_stamp != current_stamp:
        with open(RULES_FILE, "r") as f:
            try:
                rules = yaml.safe_load(f)
                logging.info("Reloaded rules")
            except yaml.YAMLError as exc:
                logging.exception(exc)

        rules_stamp = current_stamp
        ALLOWED_URLS_RULES = re.compile(fr"({'|'.join(rules['allowed_urls'])})")
        ALLOWED_MIMETYPES_RULES = re.compile(fr"({'|'.join(rules['allowed_mimetypes'])})")

def is_url_allowed(url):
    allowed_url, _ = ALLOWED_URLS_RULES.findall(url)
    if allowed_url:
        logging.info(f"URL is allowed, for: {url}")
        return True
    else:
        logging.warning(f"URL not allowed for: {url}")
        return False

def is_mimetype_allowed(url):
    u = urlparse(url)
    mimetype, _ = mimetypes.guess_type(u.path)
    if mimetype:
        allowed = ALLOWED_MIMETYPES_RULES.match(mimetype)
        if allowed:
            logging.info(f"Mimetype is allowed ('{mimetype}'), for: {url}")
            return True
        else:
            logging.warning(f"Mimetype is not allowed ('{mimetype}'), in: {url}")
            return False
    else:
        logging.warning(f"Mimetype not found for: {url}")
        return False

rules_stamp = ''
rules = reload_rules_if_changed(RULES_FILE)
    
@bot.event
async def on_member_join(member):
    "This event is triggered when a new member joins the server."
    try:
        channel = await bot.fetch_channel(GREETING_CHANNEL)
        embed = discord.Embed(title=messages[LANGUAGE]['GREETING_TITLE'], description=messages[LANGUAGE]["GREETING_MESSAGE"].format(member_mention=member.mention))
        await channel.send(embed=embed)
        await channel.send(messages[LANGUAGE]['GREETING_PROMPT'].format(member_mention=member.mention, greeting_hours=GREETING_TIMEOUT_HOURS))

        def check(m):
            return bot.user.mention in m.content and m.channel == channel and member == m.author

        try:
            msg = await bot.wait_for('message', check=check, timeout=GREETING_TIMEOUT)
        except asyncio.TimeoutError:
            await channel.send(messages[LANGUAGE]["TIMEOUT_MESSAGE"])
            await member.kick(reason=messages[LANGUAGE]["KICK_REASON"])
            await channel.send(messages[LANGUAGE]['KICK_MESSAGE'].format(member_name=member.name))
        else:
            logging.info(f"Message: {msg}")
            await channel.send(messages[LANGUAGE]["SUCCESS_MESSAGE"])
    except Exception as e:
        logging.exception(f"Error in on_member_join, {e}")


@bot.event
async def on_message(message):
    "This event is triggered when a message is sent in the server."
    try:
        if message.channel.id == MEDIA_CHANNEL:
            reload_rules_if_changed(RULES_FILE)
            attachments = [f for f in message.attachments if is_mimetype_allowed(f.url)]
            url_pattern = r'https?://\S+'
            urls = [url for url in re.findall(url_pattern, message.content) if is_url_allowed(url) or is_mimetype_allowed(url)]
            if not (attachments or urls):
                await message.delete()
    except Exception as e:
        logging.exception(f"Error in on_message, {e}")

@bot.event
async def on_ready():
    "This event is triggered when the bot successfully connects to the server."
    try:
        logging.info(f'Logged in as {bot.user.name} / {bot.user.id}')
        logging.info(f'GREETING_CHANNEL: {GREETING_CHANNEL}')
        logging.info(f'MEDIA_CHANNEL: {MEDIA_CHANNEL}')
    except Exception as e:
        logging.exception(f"Error in on_ready, {e}")

# Run the bot with the specified token
bot.run(TOKEN)
