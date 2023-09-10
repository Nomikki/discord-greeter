import asyncio
from mimetypes import MimeTypes
import mimetypes
import os
from urllib.parse import urlparse
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import re
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

# Securely parse the TIMEOUT environment variable
try:
    TIMEOUT = int(eval(os.getenv('TIMEOUT')))
except ValueError:
    logging.exception("Invalid TIMEOUT value. Please ensure it is a valid integer.")
    TIMEOUT = 7200  # default to 2 hours (7200 seconds) if an invalid value is provided

# Load messages from JSON file
with open('messages.json') as f:
    messages = json.load(f)

LANGUAGE = 'fi'  # Change this based on user preferences or server settings

# Initialize the bot with a command prefix and description
description = '''igorTheLoggerBot'''
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', case_insensitive=True, help_command=None, intents=intents)

def is_mimetype_allowed(url):
    u = urlparse(url)
    if re.match(r'.*(youtube.com|youtu.be|soundcloud.com).*', url):
        print(f"URL is allowed, for: {url}")
        return True
    else:
        mimetype, _ = mimetypes.guess_type(u.path)
        if mimetype and mimetype[0]:
            allowed = re.match(r'^(?P<type>audio|image|video)/(?P<subtype>.*)', mimetype)
            if allowed and allowed.group('type'):
                print(f"Mimetype is allowed ('{mimetype}'), for: {url}")
                return True
            else:
                print(f"Mimetype is not allowed ('{mimetype}'), in: {url}")
                return False
        else:
            print(f"Mimetype not found for: {url}")
            return False
    
@bot.event
async def on_member_join(member):
    "This event is triggered when a new member joins the server."
    try:
        channel = await bot.fetch_channel(GREETING_CHANNEL)
        embed = discord.Embed(title=messages[LANGUAGE]['GREETING_MESSAGE'].format(member_mention=member.mention), description=messages[LANGUAGE]["GREETING_MESSAGE"].format(member_mention=member.mention))
        await channel.send(embed=embed)
        await channel.send(messages[LANGUAGE]['GREETING_PROMPT'].format(member_mention=member.mention))

        def check(m):
            return bot.user.mention in m.content and m.channel == channel and member == m.author

        try:
            msg = await bot.wait_for('message', check=check, timeout=TIMEOUT)
        except asyncio.TimeoutError:
            await channel.send(messages[LANGUAGE]["TIMEOUT_MESSAGE"])
            await member.kick(reason=messages[LANGUAGE]["KICK_REASON"])
            await channel.send(messages[LANGUAGE]['KICK_MESSAGE'].format(member_name=member.name))
        else:
            await channel.send(messages[LANGUAGE]["SUCCESS_MESSAGE"])
    except Exception as e:
        logging.exception("Error in on_member_join")


@bot.event
async def on_message(message):
    "This event is triggered when a message is sent in the server."
    try:
        if message.channel.id == MEDIA_CHANNEL:
            attachments = [f for f in message.attachments if is_mimetype_allowed(f.url)]
            url_pattern = r'https?://\S+\.\w+'
            urls = [url for url in re.findall(url_pattern, message.content) if is_mimetype_allowed(url)]
            if not (attachments or urls):
                await message.delete()
    except Exception as e:
        logging.exception("Error in on_message")

@bot.event
async def on_ready():
    "This event is triggered when the bot successfully connects to the server."
    try:
        logging.info(f'Logged in as {bot.user.name} / {bot.user.id}')
        print(GREETING_CHANNEL)
        print(MEDIA_CHANNEL)
    except Exception as e:
        logging.exception("Error in on_ready")

# Run the bot with the specified token
bot.run(TOKEN)