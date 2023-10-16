# type: ignore

import asyncio
from datetime import datetime
from pprint import pformat

from discord.ext.commands import Context
from polars import DataFrame
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base

from senor_bot.config import settings

Base = declarative_base()
engine = create_async_engine(settings.database.url, echo=True, pool_recycle=3600)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer)
    author_nick = Column(String)
    mentions_id = Column(Integer)
    guild_id = Column(Integer)
    message_id = Column(Integer)
    timestamp = Column(DateTime)
    text = Column(String)
    answer = Column(String)
    has_answer = Column(Boolean)
    num_replies = Column(Integer)

    def __init__(self, ctx: Context, question: str):
        assert ctx.mentions is not None and len(ctx.mentions) == 1
        self.author_id = ctx.author.id
        self.author_nick = ctx.author.nick
        self.mentions_id = ctx.mentions[0].id
        self.mentions_nick = ctx.mentions[0].nick
        self.message_id = ctx.id
        self.guild_id = ctx.guild.id
        self.timestamp = datetime.now()
        self.text = question
        self.num_replies = 0

    def __repr__(self):
        return pformat(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author_id": self.author_id,
            "author_nick": self.author_nick,
            "mentions_id": self.mentions_id,
            "mentions_nick": self.mentions_nick,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "text": self.text,
            "answer": self.answer,
            "has_answer": self.has_answer,
            "num_replies": self.num_replies,
        }


async def write_question(question: Question) -> None:
    async with async_session() as session:
        async with session.begin():
            session.add(question)
            await session.commit()


async def read_guild(ctx: Context) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(Question.guild_id == ctx.guild.id)
        result = await session.execute(stmt)
        data = [question.to_dict() for question in result.scalars().all()]
        return DataFrame(data)


async def read_author(ctx: Context) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(
            Question.guild_id == ctx.guild.id and Question.author_id == ctx.author.id
        )
        result = await session.execute(stmt)
        data = [question.to_dict() for question in result.scalars().all()]
        return DataFrame(data)


async def read_mentions(ctx: Context) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(
            Question.guild_id == ctx.guild.id and Question.mentions_id == ctx.author.id
        )
        result = await session.execute(stmt)
        data = [question.to_dict() for question in result.scalars().all()]
        return DataFrame(data)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(async_main())
