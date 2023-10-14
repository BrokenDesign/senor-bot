import asyncio

import polars as pl
from polars import col

from senor_bot import db

guild_id = 1161158101676855367
user_id = 477506746986921992

df = asyncio.run(db.read_involved(guild_id=guild_id, user_id=user_id))

stats = (
    df.filter(col("author_id") == user_id)
    .select(
        col("num_replies").min().alias("min"),
        col("num_replies").max().alias("max"),
        (col("num_replies").sum() / pl.count()).alias("mean"),
    )
    .to_dicts()[0]
)

print(df)
print("")
print(stats)
