# type: ignore

import asyncio
import datetime
import re
from datetime import datetime
from pprint import pformat

import discord
import openai
from discord import Message
from discord.ext import commands
from discord.ext.commands import Bot, Context
from icecream import ic

from senor_bot.config import settings
from senor_bot.db import Question, write_question


class Questions(commands.Cog):
    bot: commands.Bot
    muted: bool
    open_questions: list[Question]
    whitelist: dict[int, int]

    emotes = {
        "point": "\u261D",
        "question": "\u2754",
        "check": "\u2705",
        "cross": "\u274C",
        "zipped": "\U0001F910",
        "unzipped": "\U0001F62E",
    }

    def __init__(self, bot: Bot, **kwargs):
        openai.api_key = settings.tokens.gpt
        self.bot = bot
        self.muted = False
        self.open_questions = []
        self.whitelist = {
            config.guild: config.channel for config in settings.bot.whitelist
        }

    async def ignore_message(self, ctx: Context) -> bool:
        return ic(
            ctx.author.id == self.bot.user.id
            or ctx.guild.id not in self.whitelist
            or ctx.channel.id != self.whitelist[ctx.guild.id]
        )

    @commands.Cog.listener()
    async def on_message(self, ctx: Context):
        if self.muted:
            self.open_questions.clear()
            return

        if "whos your daddy?" in ctx.content.lower().strip().replace("'", ""):
            await ctx.channel.send(
                "<@!180505942872424448>'s yo daddy, and don't forget it."
            )
            return

        if await self.ignore_message(ctx):
            return
        await self.check_open_questions(ctx)
        if await self.has_question(ctx):
            await self.add_questions(ctx)

    async def has_question(self, ctx: Context) -> bool:
        return (
            ctx.mentions is not None and len(ctx.mentions) == 1 and "?" in ctx.content
        )

    async def strip_mentions(self, text: str) -> str:
        return re.sub(f"<.+>", "", text)

    async def parse_questions(self, text: str) -> list[str]:
        text = await self.strip_mentions(text)
        words = "([\w\,\-']+\s?)+"
        quote = '"[^"]*"\s?'
        terminators = "[\?\.\:\;\!]"
        pattern = (
            f"(?P<text>({words})({quote})?({words})?)+(?P<terminator>{terminators}+|$)"
        )
        return [
            match.group("text").lower().strip() + "?"
            for match in re.finditer(pattern, text)
            if match.group("text").strip() != ""
            and match.group("terminator").strip() == "?"
        ]

    async def add_questions(self, ctx: Context) -> None:
        questions = await self.parse_questions(ctx.content)
        if questions == []:
            return
        else:
            await ctx.add_reaction(self.emotes["point"])
            for question in questions:
                self.open_questions.append(Question(ctx, question))

    async def is_answered(self, ctx: Context, question: Question) -> bool:
        prompt = f"Can '{ctx.content}' be considered an answer to the question '{question.text}'"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=1,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip().lower() == "yes"

    # TODO: add time constraint to remove unanswered questions
    async def check_open_questions(self, ctx: Context) -> None:
        for question in self.open_questions:
            if ctx.guild.id != question.guild_id:
                continue
            elif ctx.author.id != question.mentions_id:
                continue
            elif (
                not ctx.reference
                or ctx.reference.message_id != question.message_id
                and ctx.reference.message_id
                not in [question.message_id for question in self.open_questions]
            ):
                await ctx.add_reaction(self.emotes["question"])
                question.replies += 1
                continue
            else:
                try:
                    has_answer = await self.is_answered(ctx, question)

                except Exception as err:
                    await ctx.send("error: openai error, clearing open questions")
                    self.open_questions.clear()
                    print(err)

                if not has_answer:
                    await ctx.add_reaction(self.emotes["cross"])
                    question.replies += 1
                    continue
                else:
                    await ctx.add_reaction(self.emotes["check"])
                    question.replies += 1
                    question.answer = ctx.content
                    question.has_answer = True
                    await write_question(question)
                    self.open_questions.remove(question)

    @commands.slash_command(
        name="mute", description="toggles checking of questions on/off"
    )
    async def mute(self, ctx: Context):
        self.muted = not self.muted
        if self.muted:
            await ctx.respond(self.emotes["zipped"])
        else:
            await ctx.respond(self.emotes["unzipped"])

    @commands.slash_command(name="list", description="lists open questions")
    async def send_open_questions(self, ctx: Context):
        embed = discord.Embed()
        embed.title = "Open Questions"
        embed.color = 10038562
        if len(self.open_questions) == 0:
            embed.description = "There are currently no open questions"
            await ctx.respond(embed=embed)
            return

        if len(self.open_questions) > 25:
            embed.description = (
                "NOTE: there are currently > 25 open questions and output has been truncated"
                "The following questions are currently waiting for answers\n_ _"
            )
            await ctx.respond(embed=embed)
        else:
            for i, question in enumerate(self.open_questions):
                author = await self.bot.fetch_user(question.author_id)
                assert author is not None
                embed.add_field(
                    name=f"Question #{i+1}",
                    value=f"<@!{question.mentions_id}> {question.text}",
                    inline=False,
                )
            await ctx.respond(embed=embed)

    @commands.slash_command(
        name="remove", description="removes question from list of open questions by #"
    )
    async def remove_open_question(self, ctx: Context, number: int):
        if ctx.author.id != settings.bot.owner.id:
            await ctx.respond("Insufficient permission: Owner required")

        elif len(self.open_questions) == 0:
            await ctx.respond("Error: No open questions")

        elif number not in range(1, len(self.open_questions) + 1):
            await ctx.respond(
                f"Invalid index: expected value in 1..{len(self.open_questions)}."
            )
        else:
            question = self.open_questions.pop(number - 1)
            await ctx.respond(f"Removed question:\n```{pformat(question.to_dict())}```")

    @commands.slash_command(
        name="close", description="closes an open question as answered"
    )
    async def close_open_question(self, ctx: Context, n: int, answer: str):
        if ctx.author.id != settings.bot.owner.id:
            await ctx.respond("Insufficient permission: Owner required")

        elif len(self.open_questions) == 0:
            await ctx.respond("Error: No open questions")

        elif number not in range(1, len(self.open_questions) + 1):
            await ctx.respond(
                f"Invalid index: expected value in 1..{len(self.open_questions)}."
            )

        elif answer is None or answer.strip() == "":
            await ctx.respond(f"Error: must supply answer text")

        else:
            question = self.open_questions.pop(number - 1)
            question.has_answer = True
            question.answer = answer
            await write_question(question)
            await ctx.respond(f"Closed question:\n```{pformat(question.to_dict())}```")

    @commands.slash_command(name="clear", description="clears *all* open questions")
    async def clear_open_questions(self, ctx: Context):
        if ctx.author.id != settings.bot.owner.id:
            await ctx.respond("Insufficient permission: Owner required")
        self.open_questions.clear()
        await self.send_open_questions(ctx)


def setup(bot: commands.Bot):
    bot.add_cog(Questions(bot))
