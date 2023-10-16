# type: ignore

import tempfile
from enum import Enum, auto

import polars as pl
from discord import Color, Embed, File, Member, User
from discord.ext.commands import Context, command
from PIL import Image, ImageDraw, ImageFont
from polars import DataFrame

from senor_bot import db


class StatsType(Enum):
    SINGLE = auto()
    MULTIPLE = auto()


class Stats:
    async def text_to_image(text, image_size=(580, 240)):
        font_size = 12
        font_path = "CascadiaMono.ttf"
        background_color = "#2a2e36"
        text_color = "white"

        image = Image.new("RGB", image_size, background_color)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, font_size)
        draw.text((5, 0), text, font=font, fill=text_color)

        return image

    async def process_guild_stats(df: DataFrame) -> DataFrame:
        def format_nick(nick: str) -> str:
            if len(nick) > 25:
                return nick[0:22] + "..."
            else:
                return nick.ljust(25)

        return (
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

    async def get_stats_image(self, df: DataFrame, type: StatsType) -> Image:
        if type == StatsType.MULTIPLE:
            size = (580, 240)
        elif type == StatsType.SINGLE:
            size = (580, 112)
        else:
            raise ValueError("Unhandled value of StatsType")
        return await self.text_to_image(str(df), size)

    async def respond_with_image(self, ctx: Context, image: Image) -> None:
        with tempfile.NamedTemporaryFile(prefix="stats.", suffix=".png") as temp:
            embed = Embed(color=Color.dark_red)
            image.save(temp, format="PNG")
            file = File(temp.name, filename="stats.png")
            embed.set_image(url="attachment://stats.png")
            ctx.respond(embed=embed, file=file)

    @command.slash_command(name="top", description="output the top/bottom users")
    async def get_guild_stats(self, ctx: Context):
        if ctx.guild is None:
            return ctx.respond("Command only available in server")
        else:
            df = await db.read_guild(ctx)
            df = await self.process_guild_stats(df)
            image = self.get_stats_image(df, StatsType.MULTIPLE)
            self.respond_with_image(ctx, image)

    @command.slash_command(name="user", description="get user stats")
    async def get_user_stats(self, ctx: Context, user: User | Member):
        if ctx.guild is None:
            return ctx.respond("Command only available in server")
        else:
            df = await db.read_guild(ctx)
            df = await self.process_guild_stats(df)
            df = df.filter(
                pl.col()
            )  # TODO I need to have their ID's on there to filter or pass it in to the stats function
            image = self.get_stats_image(df, StatsType.MULTIPLE)
            self.respond_with_image(ctx, image)
