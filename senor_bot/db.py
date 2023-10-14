# type: ignore

import asyncio
from datetime import datetime
from pprint import pformat

from discord.ext.commands import Context
from polars import DataFrame
from sqlalchemy import Column, DateTime, Integer, String
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
    mentions_id = Column(Integer)
    guild_id = Column(Integer)
    message_id = Column(Integer)
    timestamp = Column(DateTime)
    text = Column(String)
    answer = Column(String)
    num_replies = Column(Integer)

    def __init__(self, ctx: Context, question: str):
        assert ctx.mentions is not None and len(ctx.mentions) == 1
        self.author_id = ctx.author.id
        self.mentions_id = ctx.mentions[0].id
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
            "mentions_id": self.mentions_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "text": self.text,
            "answer": self.answer,
            "num_replies": self.num_replies,
        }


async def write_question(question: Question) -> None:
    async with async_session() as session:
        async with session.begin():
            session.add(question)
            await session.commit()


async def read_guild(guild_id: int) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(Question.guild_id == guild_id)
        result = await session.execute(stmt)
        data = [question.to_dict() for question in result.scalars().all()]
        return DataFrame(data)


async def read_author(guild_id: int, author_id: int) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(
            Question.guild_id == guild_id and Question.author_id == author_id
        )
        result = await session.execute(stmt)
        data = [question.to_dict() for question in result.scalars().all()]
        return DataFrame(data)


async def read_mentions(guild_id: int, mentions_id: int) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(
            Question.guild_id == guild_id and Question.mentions_id == mentions_id
        )
        result = await session.execute(stmt)
        data = [question.to_dict() for question in result.scalars().all()]
        return DataFrame(data)


async def read_involved(guild_id: int, user_id: int) -> DataFrame:
    async with async_session() as session:
        stmt = select(Question).where(
            Question.guild_id == guild_id
            and (Question.author_id == user_id or Question.mentions_id == user_id)
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
