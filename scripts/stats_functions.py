import random

import polars as pl
from faker import Faker
from polars import DataFrame, col

from senor_bot.db import Question

fake = Faker()

data = list()
for _ in range(50):
    author_id = fake.random_int(min=int(1e18), max=int(2e18))
    author_nick = fake.name()
    mentions_id = fake.random_int(min=int(1e18), max=int(2e18))
    mentions_nick = fake.name()
    num_ids = random.randint(1, 5)

    for _ in range(num_ids):
        question = dict(
            author_id=author_id,
            author_nick=author_nick,
            mentions_id=mentions_id,
            mentions_nick=mentions_nick,
            guild_id=fake.random_int(min=int(1e18), max=int(2e18)),
            message_id=fake.random_int(min=int(1e18), max=int(2e18)),
            timestamp=fake.date_time_between(start_date="-15m", end_date="now"),
            text=fake.text(),
            answer=fake.text(),
            has_answer=bool(fake.random_int(min=0, max=1)),
            num_replies=fake.random_int(min=1, max=10),
        )

        data.append(question)

df = DataFrame(data)


def rank_guild_stats(df: DataFrame):
    def format_nick(
        nick: str,
    ) -> str:
        if len(nick) > 25:
            return nick[0:22] + "..."
        else:
            return nick.ljust(25)

    df = (
        df.groupby(col(["author_id", "author_nick"]))
        .agg(
            pl.count().alias("num_questions"),
            (col("num_replies").sum() / pl.count()).alias("avg_replies"),
            (col("has_answer").sum() / pl.count()).alias("answer_rate"),
        )
        .sort([col("avg_replies"), -col("answer_rate"), -col("num_questions")])
        .with_row_count(offset=1)
        .select(
            col("row_nr").alias("rank"),
            col("author_nick").apply(format_nick).alias("member"),
            col("num_questions").alias("num_questions"),
            col("avg_replies").round(0).cast(pl.Int64).alias("avg_replies"),
            col("answer_rate").apply(lambda x: f"{x:.1%}").alias("pct_answered"),
        )
    )

    return df


def get_user_stats(df: DataFrame) -> DataFrame:
    df = rank_guild_stats(df)
    return df.filter(col("rank") == 23)


print(get_user_stats(df))
