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

from senor_bot.config import settings
from senor_bot.db import Question, write_question


class Questions(commands.Cog):
    bot: commands.Bot
    open_questions: list[Question]
    whitelist: dict[int, int]

    emotes = {
        "point": "\u261D",
        "question": "\u2753",
        "check": "\u2705",
        "cross": "\u274C",
    }

    def __init__(self, bot: Bot, **kwargs):
        openai.api_key = settings.tokens.gpt
        self.bot = bot
        self.open_questions = []
        self.whitelist = {
            config.guild: config.channel for config in settings.bot.whitelist
        }

    async def ignore_message(self, ctx: Context) -> bool:
        return (
            ctx.author.id == self.bot.user.id
            or ctx.guild.id not in self.whitelist
            or ctx.channel.id != self.whitelist[ctx.guild.id]
        )

    @commands.Cog.listener()
    async def on_message(self, ctx: Context):
        if await self.ignore_message(ctx):
            return
        await self.check_open_questions(ctx)
        if await self.has_question(ctx):
            await self.add_questions(ctx)

    async def has_question(self, ctx: Context) -> bool:
        return (
            ctx.mentions is not None and len(ctx.mentions) == 1 and "?" in ctx.content
        )

    async def add_questions(self, ctx: Context) -> None:
        questions = re.findall(r"\s[A-Za-z\,\s]*\?", ctx.content)
        if questions == []:
            return
        else:
            await ctx.add_reaction(self.emotes["point"])
            questions = [Question(ctx, question) for question in questions]
            self.open_questions.extend(questions)

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
            elif not ctx.reference or ctx.reference.message_id != question.message_id:
                await ctx.add_reaction(self.emotes["question"])
                question.num_replies += 1
                continue
            elif not await self.is_answered(ctx, question):
                await ctx.add_reaction(self.emotes["cross"])
                question.num_replies += 1
                continue
            else:
                await ctx.add_reaction(self.emotes["check"])
                question.num_replies += 1
                question.answer = ctx.content
                await write_question(question)
                self.open_questions.remove(question)

    @commands.slash_command(name="list", description="lists open questions")
    async def send_open_questions(self, ctx):
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
                    name=f"Question #{i+1} - {author.display_name} asked...",
                    value=f"<@!{question.mentions_id}> {question.text}",
                    inline=False,
                )
            await ctx.respond(embed=embed)

    @commands.slash_command(name="remove")
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

    # @discord.slash_command(name="close")
    # async def close_open_question(self, ctx: Context, n: int, answer: str):
    #     if ctx.author.id != settings.bot.owner.id:
    #         ctx.send("Insufficient permission: Owner required")
    #     elif n not in range(len(self.open_questions)):
    #         ctx.send(
    #             f"Invalid index: expected value in 0..{len(self.open_questions)-1}."
    #         )
    #     else:
    #         question = self.open_questions.pop(n)
    #         ctx.send(f"Removed question:\n```{pformat(question.to_dict())}```")


def setup(bot: commands.Bot):
    bot.add_cog(Questions(bot))
