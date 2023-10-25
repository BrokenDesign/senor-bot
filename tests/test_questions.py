# type: ignore

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from box import Box
from discord.ext import commands

from senor_bot.cogs.questions import Questions


class TestQuestions:
    def setup_method(self):
        self.bot = commands.Bot(command_prefix="!")
        self.questions = Questions(self.bot)

    @pytest.mark.asyncio
    async def test_has_question(self):
        ctx = AsyncMock()
        ctx.mentions = [MagicMock()]
        ctx.content = "What is the meaning of life?"
        assert await self.questions.has_question(ctx) == True

    @pytest.mark.asyncio
    async def test_has_open_question(self):
        ctx = AsyncMock()
        ctx.author.id = 123
        self.questions.open_questions = [Box({"author_id": 123})]
        assert await self.questions.has_open_question(ctx) == True

    @pytest.mark.asyncio
    async def test_is_possible_answer(self):
        ctx = AsyncMock()
        ctx.author.id = 123
        ctx.reference.message_id = 456
        self.questions.open_questions = [Box({"author_id": 123, "message_id": 456})]
        assert await self.questions.is_possible_answer(ctx) == True

    @pytest.mark.asyncio
    async def test_strip_mentions(self):
        ctx = AsyncMock()
        ctx.author = MagicMock(spec=discord.User)
        ctx.content = "<@123> What is the meaning of life?"
        print(ctx.author.mention)
        assert (
            await self.questions.strip_mentions(ctx) == "What is the meaning of life?"
        )

    @pytest.mark.asyncio
    async def test_parse_questions(self):
        ctx = AsyncMock()
        ctx.content = "What is the meaning of life? Is there a God?"
        assert await self.questions.parse_questions(ctx) == [
            "what is the meaning of life?",
            "is there a god?",
        ]
