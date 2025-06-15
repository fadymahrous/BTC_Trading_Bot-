import ccxt
import pandas as pd
import logging
from time import time
import re
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from Helper.Database_Engine import DatabaseEngine
from Helper.Create_DatabaseSchema import CreateDatabaseSchema
from Helper.Previous_Interval import Previous_Interval

HEADER = ['date', 'open', 'high', 'low', 'close', 'volume']

class FetchTradeMinute:
    def __init__(self, exchange_name: str = 'binance', symbol: str = 'BTC/USDT'):
        # Initialize logger
        self.logger = logging.getLogger('combined_OHLC_trade')

        # Validate symbol
        if not symbol:
            raise ValueError('Symbol must be provided to fetch OHLC data.')

        self.exchange_name = exchange_name
        self.symbol = symbol
        self.table_name = re.sub(r'[^A-Za-z0-9]', '', self.symbol).lower()

        # Initialize helper classes
        self.previous_interval = Previous_Interval()
        self.exchange = getattr(ccxt, self.exchange_name)()

        # Create database engine and inspector
        engine_builder = DatabaseEngine()
        self.engine = engine_builder.create_postgres_engine()
        self.inspector = inspect(self.engine)

        # Used to create table/partition if needed
        self.schema_creator = CreateDatabaseSchema('trade')

    def _fetch_previous_candle_ohlc(self, interval: str) -> pd.DataFrame:
        # Validate interval against exchange-supported timeframes
        if interval not in self.exchange.timeframes:
            self.logger.error(
                f"Invalid interval: {interval}. Valid intervals: {list(self.exchange.timeframes.keys())}"
            )
            raise ValueError('Invalid interval')

        HEADER = ['date', 'open', 'high', 'low', 'close', 'volume']

        # Get floored timestamp and convert to milliseconds
        since_ts = self.previous_interval.get_previous_floored_timestamp(interval)
        since_ms = int(since_ts.timestamp() * 1000)

        retries = 3
        for attempt in range(retries):
            try:
                # Fetch OHLCV data from the exchange
                candles = self.exchange.fetchOHLCV(self.symbol, timeframe=interval, since=since_ms)
                if not candles:
                    self.logger.warning(f"No OHLCV data returned for {self.symbol} at interval {interval}")
                    if attempt < retries - 1:
                        time.sleep(10)
                    continue
                # Use the first candle and return as DataFrame
                candle = candles[0]
                candle[0] = pd.to_datetime(candle[0], unit='ms')
                df = pd.DataFrame([candle], columns=HEADER)
                return df

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed to fetch OHLCV data: {e}")
                if attempt < retries - 1:
                    time.sleep(10)

        # On final failure, return fallback DataFrame
        self.logger.error(f"All {retries} attempts failed. Returning zeroed fallback candle.")
        fallback_data = [[since_ts, 0, 0, 0, 0, 0]]
        df = pd.DataFrame(fallback_data, columns=HEADER)
        return df


    def fetch_ohlc_and_load_to_db(self, interval: str) -> None:
        if not interval:
            self.logger.error('Interval must be provided.')
            raise ValueError('Interval is None')

        ##Decide the table name
        self.interval = interval
        stock_crypto_type=re.sub(r'[^A-Za-z0-9]', '', self.symbol).lower()
        segment = stock_crypto_type+self.interval
        self.table_name = f"trade_{segment}_ohlc"

        
        df_ohlc = self._fetch_previous_candle_ohlc(self.interval)

        # Check if the target table exists in the database
        try:
            existing_tables = self.inspector.get_table_names(schema='trade')
            if self.table_name not in existing_tables:
                self.logger.info(f"Table {self.table_name} does not exist. Creating Table and Schema if not exist...")
                self.schema_creator.create_tables_ohlc(self.table_name)
        except Exception as e:
            self.logger.error(f"Could not verify wheter table exist or no for Details:: {e}")

        # Load data into the table if it's not empty
        if df_ohlc is not None and not df_ohlc.empty:
            try:
                self.logger.info(f"Inserting {len(df_ohlc)} OHLC records into {self.table_name}...")
                df_ohlc.to_sql(self.table_name, self.engine, schema='trade', if_exists='append', index=False)
            except IntegrityError as e:
                self.logger.error("CheckViolation: likely missing partition. Creating it...")
                self.schema_creator.create_partition(self.table_name, offset=0)
            except Exception as e:
                self.logger.error(f"Unexpected error inserting data: {e}")
                print(type(e))

        else:
            self.logger.error(f"No OHLC data available to insert into {self.table_name}.")

if __name__ == '__main__':
    fetcher = FetchTradeMinute()
    fetcher.fetch_ohlc_and_load_to_db('1m')
    print("Fetch and insert complete.")
