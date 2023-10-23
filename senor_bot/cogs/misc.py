# type: ignore

import random

from discord.ext import commands
from discord.ext.commands import Context
from loguru import logger

from senor_bot.checks import bot_manager


class Misc(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot):
        self.bot = bot

    async def who_your_daddy(self, ctx) -> bool:
        return "whos your daddy?" in ctx.content.lower().strip().replace("'", "")

    @commands.Cog.listener()
    async def on_message(self, ctx: Context):
        try:
            if ctx.author == self.bot.user:
                return

            elif await self.who_your_daddy(ctx):
                logger.info(f"Received 'who's your daddy' message from {ctx.author}")
                await ctx.channel.send(
                    "<@!180505942872424448>'s yo daddy, and don't forget it."
                )
                return

            elif self.bot.user.mentioned_in(ctx):
                logger.info(f"Received mention from {ctx.author}")
                with open("phrases.txt", "r") as f:
                    lines = f.readlines()
                    selected_line = random.choice(lines)
                    await ctx.reply(selected_line.strip())
                return
        except Exception as e:
            logger.error(f"Error in on_message: {e}")

    @commands.check(bot_manager)
    @commands.slash_command(name="ping", description="checks bot latency")
    async def ping(self, ctx: commands.Context):
        try:
            await ctx.respond(f"Pong! ```latency = {round(self.bot.latency, 1)}ms```")
        except Exception as e:
            logger.error(f"Error in ping command: {e}")


def setup(bot):
    bot.add_cog(Misc(bot))
