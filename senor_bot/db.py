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
engine = create_async_engine(settings.database.url, echo=False, pool_recycle=3600)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Question(Base):
    __tablename__ = "questions"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer)
    author_id = Column(Integer)
    mentions_id = Column(Integer)
    message_id = Column(Integer)
    timestamp = Column(DateTime)
    text = Column(String)
    answer = Column(String)
    has_answer = Column(Boolean)
    num_replies = Column(Integer)

    timer_start: datetime

    def __init__(self, ctx: Context, question: str):
        assert ctx.mentions is not None and len(ctx.mentions) == 1
        self.author_id = ctx.author.id
        self.mentions_id = ctx.mentions[0].id
        self.message_id = ctx.id
        self.guild_id = ctx.guild.id
        self.timestamp = datetime.now()
        self.text = question
        self.answer = None
        self.has_answer = False
        self.num_replies = 0
        self.timer_start = None

    def __repr__(self):
        return pformat(self.to_dict())

    @property
    def replies(self):
        pass

    @replies.getter
    def replies(self) -> int:
        return self.num_replies

    @replies.setter
    def replies(self, value: int) -> None:
        if self.num_replies == 0 and value > 0:
            self.timer_start = datetime.now()
        self.num_replies = value

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author_id": self.author_id,
            "mentions_id": self.mentions_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "text": self.text,
            "answer": self.answer,
            "has_answer": self.has_answer,
            "num_replies": self.num_replies,
        }


async def write_question(question: Question) -> None:
    try:
        async with async_session() as session:
            async with session.begin():
                session.add(question)
                await session.commit()
        logging.info(f"Question written to database: {question}")
    except Exception as e:
        logger.error(f"Error writing question to database: {e}")


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
