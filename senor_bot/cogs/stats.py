import polars as pl
from enum import Enum
from polars import DataFrame
from datetime import datetime, timedelta
from senor_bot.config import settings


class Period(Enum):
    DAY = 1
    WEEK = 7
    MONTH = 30


class Stats:
    def get_asked_by(self, user: str, period: Period) -> DataFrame:
        start_date = (datetime.now() - timedelta(days=period.value)).date()
        query = f"""
            SELECT * 
            FROM messages 
            WHERE user_id = {user} AND timestamp >= '{start_date}'
        """
        return pl.read_database(query, settings.database.path)

    def get_asked_to(self, user: str, period: Period) -> DataFrame:
        start_date = (datetime.now() - timedelta(days=period.value)).date()
        query = f"""
            SELECT * 
            FROM messages 
            WHERE mentioned_id = {user} AND timestamp >= '{start_date}'
        """
        return pl.read_database(query, settings.database.path)

    # def n_message(


# Plotting using Plotly
# fig1 = questions_by_user_df.to_pandas().plot.bar(x='timestamp', y='n_messages', title='Questions by User ID')
# fig2 = questions_mentioning_user_df.to_pandas().plot.bar(x='timestamp', y='n_messages', title='Questions Mentioning User ID')
# fig3 = average_messages_per_day_df.to_pandas().plot.bar(x='date', y='average_messages', title='Average Messages per Day')

# # Show the figures
# fig1.figure.show()
# fig2.figure.show()
# fig3.figure.show()
