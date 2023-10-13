# type: ignore

import asyncio
from datetime import datetime
from pprint import pformat

from discord import Message
from discord.ext.commands import Context
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
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
        self.timestamp = datetime.now()
        self.text = question

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


async def write_question(self, question: Question) -> None:
    async with async_session() as session:
        async with session.begin():
            session.add(question)
            await session.commit()


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(async_main())
