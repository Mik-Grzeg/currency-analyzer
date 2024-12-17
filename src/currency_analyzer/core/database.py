import sqlite3
import polars as pl
from typing import List, Optional
from currency_analyzer.core.exceptions import DatabaseError, MissingDataError
from datetime import date

from currency_analyzer.core.types import ExchangeRate, ExchangeRateChange
from currency_analyzer.logger import get_logger


logger = get_logger(__name__)


class RateRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

        self.apply_migrations()

    def apply_migrations(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rates (
                        currency_code TEXT,
                        rate REAL,
                        date TEXT,
                        source TEXT,
                        PRIMARY KEY (currency_code, date, source)
                    )
                    """
                )
                logger.debug("Created `rates` table in {} database", self.db_path)

                conn.commit()
            except sqlite3.Error as e:
                logger.error(
                    "Error while creating `rates` table in {} database: {}",
                    self.db_path,
                    e,
                )
                raise DatabaseError(f"Error while creating `rates` table: {e}")

    def insert_exchange_rates(self, rates: List["ExchangeRate"]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO rates VALUES (?, ?, ?, ?)
                    """,
                    [rate.to_tuple() for rate in rates],
                )
                logger.debug(
                    "Inserted {} rates to `rates` table in {} database",
                    len(rates),
                    self.db_path,
                )
                conn.commit()
            except sqlite3.Error as e:
                logger.error(
                    "Error while creating inserting rates to `rates` table in {} database: {}",
                    self.db_path,
                    e,
                )
                raise DatabaseError(f"Error while inserting rates data: {e}")

    def get_exchange_rates(
        self,
        start_date: date,
        end_date: date,
        currency_code: Optional[str],
        source: str,
    ) -> List["ExchangeRate"]:
        with sqlite3.connect(self.db_path) as conn:
            try:
                if currency_code:
                    query_result = pl.read_database(
                        query="SELECT currency_code, rate, date, source FROM rates WHERE currency_code = ? AND date BETWEEN ? AND ? AND source = ?",
                        connection=conn,
                        execute_options={
                            "parameters": [
                                currency_code,
                                start_date.isoformat(),
                                end_date.isoformat(),
                                source,
                            ]
                        },
                    )
                else:
                    query_result = pl.read_database(
                        query="SELECT currency_code, rate, date, source FROM rates WHERE date BETWEEN ? AND ? AND source = ?",
                        connection=conn,
                        execute_options={
                            "parameters": [
                                start_date.isoformat(),
                                end_date.isoformat(),
                                source,
                            ]
                        },
                    )

                if query_result.is_empty():
                    logger.error(
                        "No data found for the specified date range or currency"
                    )
                    raise MissingDataError(
                        "No data found for the specified date range or currency"
                    )

                df = query_result.with_columns(
                    pl.col("date").str.strptime(pl.Date, format="%Y-%m-%d"),
                )

                # create a dataframe with all dates in the range
                dates_df = pl.DataFrame(
                    {"date": pl.date_range(start_date, end_date, "1d", eager=True)}
                )
                currencies = df.get_column("currency_code").unique()
                complete_df = (
                    dates_df.join(
                        pl.DataFrame({"currency_code": currencies}), how="cross"
                    )
                    .join(df, on=["currency_code", "date"], how="left")
                    .with_columns(pl.col("source").fill_null(source))
                    .sort(["currency_code", "date"])
                )

                return [
                    ExchangeRate(
                        currency_code=row["currency_code"],
                        rate=row.get("rate", None),
                        date=row["date"].isoformat(),
                        source=row["source"],
                    )
                    for row in complete_df.iter_rows(named=True)
                ]
            except sqlite3.Error as e:
                logger.error(
                    "Error while fetching exchange_rates from `rates` table from {} database: {}",
                    self.db_path,
                    e,
                )
                raise DatabaseError(f"Error while fetching exchange rates: {e}")

    def get_exchange_rate_changes(
        self,
        start_date: date,
        end_date: date,
        currency_code: Optional[str | int],
        source: str,
    ) -> List["ExchangeRateChange"]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()

            # filter by currency code if provided
            currency_code_filter = None
            if currency_code is not None:
                currency_code_filter = "currency_code = ?"
            else:
                currency_code_filter = "1 = ?"
                currency_code = 1

            try:
                cursor.execute(
                    f"""
                    WITH daily_changes AS (
                        SELECT
                            currency_code,
                            source,
                            date,
                            rate,
                            -- get the previous day rate for the same currency and source
                            LAG(rate) OVER (PARTITION BY currency_code ORDER BY date) as prev_rate,

                            -- calculate the daily percentage change in rate with the following formula:
                            -- daily_change = (rate_today - rate_yesterday) / rate_yesterday * 100
                            ((rate - LAG(rate) OVER (PARTITION BY currency_code ORDER BY date))
                            / LAG(rate) OVER (PARTITION BY currency_code ORDER BY date) * 100) as daily_change,

                            -- get the first value of rate for the currency 
                            FIRST_VALUE(rate) OVER (PARTITION BY currency_code ORDER BY date) as start_rate,

                            -- get the last value of rate for the currency 
                            LAST_VALUE(rate) OVER (
                                PARTITION BY currency_code
                                ORDER BY date
                                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                            ) as end_rate
                        FROM rates
                        WHERE {currency_code_filter} AND date between ? AND ? AND source = ?
                    )
                    SELECT
                        currency_code,
                        source,
                        -- calculate the minimum rate in the date range
                        MIN(rate) as min_rate,

                        -- calculate the maximum rate in the date range
                        MAX(rate) as max_rate,

                        -- calculate the average rate in the date range
                        ROUND(AVG(rate), 4) as avg_rate,

                        -- calculate the total percentage change in rate
                        ROUND(((MAX(rate) - MIN(rate)) / MIN(rate) * 100), 2) as total_change_percent,

                        -- calculate the average daily percentage change
                        ROUND(AVG(daily_change), 2) as avg_daily_change,

                        -- get start_rate
                        MIN(start_rate) as start_rate,

                        -- get end_rate
                        MAX(end_rate) as end_rate,

                        -- calculate the percentage change from start to end rate
                        ROUND(((MAX(end_rate) - MIN(start_rate)) / MIN(start_rate) * 100), 2) as start_to_end_change_percent
                    FROM daily_changes
                    GROUP BY currency_code
                    ORDER BY start_to_end_change_percent DESC;
                    """,
                    (currency_code, start_date_str, end_date_str, source),
                )

                return [
                    ExchangeRateChange(
                        **dict(row),
                        start_date=start_date,
                        end_date=end_date,
                    )
                    for row in cursor.fetchall()
                ]
            except sqlite3.Error as e:
                logger.error(
                    "Error while fetching exchange_rate_changes from `rates` table from {} database: {}",
                    self.db_path,
                    e,
                )
                raise DatabaseError(f"Error while fetching exchange rate changes: {e}")
