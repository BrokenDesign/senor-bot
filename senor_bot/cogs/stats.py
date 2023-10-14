# type: ignore

from datetime import datetime, timedelta
from enum import Enum

from discord.ext.commands import Context, command

from senor_bot import db
from senor_bot.config import settings
from senor_bot.db import Question


class Stats:
    @command.slash_command(name="me", description="get user stats")
    async def get_user_stats(self, ctx: Context) -> list[Question]:
        if ctx.guild is None:
            return ctx.respond("Command only available in server")
        else:
            author = await db.read_author(
                guild_id=ctx.guild.id, author_id=ctx.author.id
            )
            mentioned = await db.read_author(
                guild_id=ctx.guild.id, author_id=ctx.author.id
            )
