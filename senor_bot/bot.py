# type: ignore

from discord import Intents
from discord.ext import commands

from senor_bot.config import settings

intents = Intents(**settings.bot.intents)
bot = commands.Bot(command_prefix=settings.bot.prefix, intents=intents)


@bot.event
async def on_ready():
    print(f"Now logged in as {bot.user}")


for cog in settings.bot.cogs:
    print(f"here - {cog}")
    bot.load_extension(f"cogs.{cog}")


@bot.slash_command()
async def ping(ctx: commands.Context):
    await ctx.respond("pong")


bot.run(settings.tokens.bot)
