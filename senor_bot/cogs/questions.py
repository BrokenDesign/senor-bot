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
from senor_bot.db import *


class Questions(commands.Cog):
    bot: commands.Bot
    open_questions: list[Question]
    whitelist: dict[int, int]

    def __init__(self, bot: Bot, **kwargs):
        openai.api_key = settings.tokens.gpt
        self.bot = bot
        self.open_questions = []
        self.whitelist = {
            config.guild: config.channel for config in settings.bot.whitelist
        }

    async def ignore_message(self, ctx: Context) -> bool:
        authors = [question.mentions_id for question in self.open_questions]
        messages = [question.message_id for question in self.open_questions]

        print("***")
        print("Checking if I should ignore...")
        print(
            f"(ctx.author.id == self.bot.user.id ) => {ctx.author.id == self.bot.user.id }"
        )
        print(
            f"(ctx.guild.id not in self.whitelist) => {ctx.guild.id not in self.whitelist}"
        )
        print(
            f"(ctx.channel.id != self.whitelist[ctx.guild.id]) => {ctx.channel.id != self.whitelist[ctx.guild.id]}"
        )

        return (
            ctx.author.id == self.bot.user.id
            or ctx.guild.id not in self.whitelist
            or ctx.channel.id != self.whitelist[ctx.guild.id]
        )

    @commands.Cog.listener()
    async def on_message(self, ctx: Context):
        print("Questions: On message...")
        if await self.ignore_message(ctx):
            return

        await self.check_open_questions(ctx)

        if await self.has_question(ctx):
            await self.add_questions(ctx)

    async def has_question(self, ctx: Context) -> bool:
        print(f"length of mentions {len(ctx.mentions)}")
        return (
            ctx.mentions is not None and len(ctx.mentions) == 1 and "?" in ctx.content
        )

    async def add_questions(self, ctx: Context) -> None:
        questions = re.findall(r"\s[A-Za-z\,\s]*\?", ctx.content)
        if questions == []:
            return
        else:
            questions = [Question(ctx, question) for question in questions]
            self.open_questions.extend(questions)

    async def is_answered(self, ctx: Context, question: Question) -> bool:
        prompt = f"Can '{ctx.content}' be considered a response to the question '{question.text}'"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=1,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip().lower() == "yes"

    # TODO: add time constraint to remove unanswered questions
    async def check_open_questions(self, ctx: Context) -> None:
        for question in self.open_questions:
            if ctx.author.id != question.mentions_id:
                continue
            if ctx.reference and ctx.reference.message_id != question.message_id:
                continue
            if await self.is_answered(question, message):
                question.answer = message.content
                await self.write_question(question)
                self.open_questions.remove(question)

    @commands.slash_command(name="list")
    async def send_open_questions(self, ctx):
        await ctx.respond(f"**Open questions:**```{self.open_questions}```")

    @commands.slash_command(name="remove")
    async def remove_open_question(self, ctx: Context, n: int):
        if ctx.author.id != settings.bot.owner.id:
            await ctx.respond("Insufficient permission: Owner required")
        elif len(self.open_questions) == 0:
            await ctx.respond("Error: No open questions")
        elif n not in range(len(self.open_questions)):
            await ctx.respond(
                f"Invalid index: expected value in 0..{len(self.open_questions)-1}."
            )
        else:
            question = self.open_questions.pop(n)
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
    print("loading questions cog...")
    bot.add_cog(Questions(bot))
