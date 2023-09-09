#bot.py
import asyncio
import os
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = int(os.getenv('CHANNEL'))
TIMEOUT = eval(os.getenv('TIMEOUT'))

description = '''Greeter'''

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!',
                      case_insensitive=True,
                      help_command=None,
                      intents = intents)

#Event
@bot.event
async def on_member_join(member):
    print("somebody joined")

    channel = await bot.fetch_channel(CHANNEL)
    embed=discord.Embed(title="Päivöö!",description=f"{member.mention} hyppäsi servulle")
    await channel.send(embed=embed)

    await channel.send(f'{member.mention}, ohai! Mistäs tulet ja miten päädyit tänne? Bottina potkin sellaiset pois jotka ei vastaile. Aikaa 2 tuntia ^^')

    def check(m):
         return bot.user.mention in m.content and m.channel == channel

    try:
        msg = await bot.wait_for('message', timeout=TIMEOUT, check=check)
    except asyncio.TimeoutError:
        await channel.send('👎')
        await member.kick(reason="Ei vastausta botille. :(")
        await channel.send(f'{member} potkittiin, koska ei vastaillut botille.')
    else:
        await channel.send('👍')


@bot.event
async def on_ready():
    print('Logged in as {0} / {1}'.format(bot.user.name, bot.user.id))
    print('-----')
    
    print(TIMEOUT)
    channel = bot.get_channel(CHANNEL)
    await channel.send("Elossa! ^_^")

bot.run(TOKEN)
