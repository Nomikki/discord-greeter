#bot.py
import asyncio
import os
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GREETING_CHANNEL = int(os.getenv('GREETING_CHANNEL'))
MEDIA_CHANNEL = int(os.getenv('MEDIA_CHANNEL'))

TIMEOUT = eval(os.getenv('TIMEOUT'))

description = '''igorTheLoggerBot'''

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!',
                      case_insensitive=True,
                      help_command=None,
                      intents = intents)

#Event
@bot.event
async def on_member_join(member):
    print("somebody joined")

    print(">>>>")
    print(member)
    print(">>>>")

    channel = await bot.fetch_channel(GREETING_CHANNEL)
    embed=discord.Embed(title="Päivöö!",description=f"{member.mention} hyppäsi servulle")
    await channel.send(embed=embed)
    await channel.send(f'{member.mention}, ohai! Mistäs tulet ja miten päädyit tänne? Bottina potkin sellaiset pois jotka ei vastaile. Aikaa 2 tuntia ^^')

    user = await bot.user(member)
    print(">>>>")
    print(user)
    print(">>>>")

    def check(m):
        return  bot.user.mention in m.content and m.channel == channel and member == m.author
        
    try:
        msg = await bot.wait_for('message', check=check, timeout=TIMEOUT)
    except asyncio.TimeoutError:
        await channel.send('👎')
        await member.kick(reason="Ei vastausta botille. :(")
        await channel.send(f'{member} potkittiin, koska ei vastaillut botille.')
    else:
        await channel.send('👍')

@bot.event
async def on_message(message):
    formats = ['jpg', 'png', 'gif', 'svg', 'mp4', 'm4v', 'mov', 'webm', 'mp3', 'ogg', 'wav', '3gp', 'flac', 'jpeg']
    attachments = [f for f in message.attachments if f.filename.split('.')[-1].lower() in formats]
    
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, message.content)
    urls_has_extension = 0

    if message.channel.id == MEDIA_CHANNEL:
        for url in urls:
            if urls:
                url_parts = url.split('.')
                if len(url_parts) > 1:
                    file_extension = url_parts[-1].lower()
                    
                    if file_extension in formats:
                        urls_has_extension = 1
        
    
        if urls and urls_has_extension > 0:
            return
        elif not attachments:
            await message.delete()

@bot.event
async def on_ready():
    print('Logged in as {0} / {1}'.format(bot.user.name, bot.user.id))
    print('-----')
    
    #print(TIMEOUT)
    #channel = bot.get_channel(GREETING_CHANNEL)
    #await channel.send("Elossa! ^_^")

bot.run(TOKEN)
