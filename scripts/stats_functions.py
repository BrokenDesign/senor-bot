import datetime
import random

import polars as pl
from faker import Faker
from PIL import Image, ImageDraw, ImageFont
from polars import DataFrame, col

from senor_bot.db import Question

# Create Faker instance
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

        # when(col("author_nick").str.lengths() <= 25)
        # .then(col("author_nick").str.ljust(25))
        # .otherwise((col("author_nick").slice(0, 25-3) + "...").str.ljust(25)).alias("member"),

df = DataFrame(data)


async def rank_guild_stats(df: DataFrame):
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


def text_to_image(text, image_size=(580, 240)):
    margin = 5
    font_size = 12
    font_path = "scripts/CascadiaMono.ttf"
    background_color = "#2a2e36"
    text_color = "white"
    text_arr = text.split("\n")

    text_width = len(text_arr[0]) * font_size
    text_height = len(text_arr) * font_size

    image = Image.new("RGB", image_size, background_color)
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(font_path, font_size)
    text_width = draw.textlength(text_arr[0], font)
    text_height = len(text_arr) * font_size
    text_x = (image_size[0] - text_width) // 2
    text_y = (image_size[1] - text_height) // 2

    # Draw the text on the image
    draw.text((5, 0), text, font=font, fill=text_color)

    return image


def get_user_stats(df: DataFrame) -> DataFrame:
    df = rank_guild_stats(df)
    return df.filter(col("rank") == 23)


print(get_user_stats(df))
