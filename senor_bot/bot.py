# type: ignore

from discord import Intents
from discord.ext import commands

from senor_bot.config import settings


intents = Intents(**settings.bot.intents)
bot = commands.Bot(command_prefix=settings.bot.prefix, intents=intents)


for cog in settings.bot.cogs:
    print(f"Loading {cog} cog...")
    bot.load_extension(f"cogs.{cog}")


@bot.event
async def on_ready():
    print(f"{bot.user.name} ready and raring to go")


@bot.slash_command()
async def ping(ctx: commands.Context):
    await ctx.respond(f"Pong! {round(bot.latency, 1)}")


bot.run(settings.tokens.bot)
