# type: ignore

import asyncio
import random

from box import Box
from faker import Faker

from senor_bot import db


async def async_main():
    fake = Faker()
    for _ in range(50):
        author_id = fake.random_int(min=int(1e18), max=int(2e18))
        author_nick = fake.name()
        mentions_id = fake.random_int(min=int(1e18), max=int(2e18))
        mentions_nick = fake.name()
        num_ids = random.randint(1, 5)

        for _ in range(num_ids):
            ctx = Box(
                author=Box(display_name=author_nick, id=author_id),
                mentions=[Box(display_name=mentions_nick, id=mentions_id)],
                guild=Box(id=1161158101676855367),
                id=fake.random_int(min=int(1e18), max=int(2e18)),
            )
            question = db.Question(ctx, fake.text())

            has_answer = bool(fake.random_int(min=0, max=1))
            if has_answer == 1:
                question.answer = fake.text()
                question.has_answer = True

            question.num_replies = fake.random_int(min=1, max=10)

            await db.write_question(question)


if __name__ == "__main__":
    asyncio.run(db.async_main())
    asyncio.run(async_main())
