# type: ignore

from discord import Intents
from discord.ext import commands

from senor_bot.config import settings

# from disputils import BotConfirmation, BotEmbedPaginator, BotMultipleChoice


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


# @bot.command()
# async def paginate(ctx):
#     embeds = [
#         Embed(
#             title="test page 1",
#             description="This is just some test content!",
#             color=0x115599,
#         ),
#         Embed(
#             title="test page 2", description="Nothing interesting here.", color=0x5599FF
#         ),
#         Embed(
#             title="test page 3", description="Why are you still here?", color=0x191638
#         ),
#     ]

#     paginator = BotEmbedPaginator(ctx, embeds)
#     await paginator.run()


bot.run(settings.tokens.bot)
