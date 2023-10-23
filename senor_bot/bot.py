# type: ignore

import asyncio
import os

from discord import Intents
from discord.ext import commands
from discord.ext.commands import Context
from loguru import logger

from senor_bot import db
from senor_bot.config import settings

for i in range(5):
    logger.add(f"logs/file{i}.log", rotation="10 MB")

intents = Intents(**settings.bot.intents)
bot = commands.Bot(command_prefix=settings.bot.prefix, intents=intents)

if not os.path.exists("data.db"):
    print("Initializing database...")
    asyncio.run(db.async_main())

# for cog in settings.bot.cogs:
#     print(f"Loading {cog} cog...")
#     bot.load_extension(f"cogs.{cog}")

bot.load_extension("cogs.misc")


@bot.event
async def on_ready():
    print(f"{bot.user.name} ready and raring to go")


print("Logging in...")
bot.run(settings.tokens.bot)
