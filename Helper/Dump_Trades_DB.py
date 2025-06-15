# to Fetch dataset
import pandas as pd
from os import path
from Helper.Database_Engine import DatabaseEngine
import re

class Dump_Trades_DB:
    def __init__(self, symbol=None):
        if symbol is None:
            raise ValueError("the symbol must be provided like 'BTC/USDT'.")
        self.table_name = re.sub(r'[^A-Za-z0-9]', '', symbol).lower()

        # Create engine to connect to AWS-hosted PostgreSQL DB
        db_engine = DatabaseEngine()
        self.engine = db_engine.create_postgres_engine()

    def dump(self):
        # Dump OHLC data
        try:
            query = f"SELECT * FROM trade.trade_{self.table_name}_ohlc;"
            df_ohlc = pd.read_sql(query, self.engine)
            df_ohlc.to_csv(path.join('Data', f'Dump_{self.table_name}_OHLC.csv'), index=False)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OHLC data: {e}")

        # Dump OrderBook data
        try:
            query = f"SELECT * FROM trade.trade_{self.table_name}_orderbook;"
            df_orderbook = pd.read_sql(query, self.engine)
            df_orderbook.to_csv(path.join('Data', f'Dump_{self.table_name}_Orderbook.csv'), index=False)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OrderBook data: {e}")

    def load(self):
        # Load OHLC CSV into database
        try:
            file_ohlc = path.join('Data', f'Dump_{self.table_name}_OHLC.csv')
            df_ohlc = pd.read_csv(file_ohlc, parse_dates=['date'])
            df_ohlc.to_sql(
                f'trade_{self.table_name}_ohlc',
                self.engine,
                schema='trade',
                if_exists='append',
                index=False
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load OHLC data: {e}")

        # Load OrderBook CSV into database
        try:
            file_orderbook = path.join('Data', f'Dump_{self.table_name}_Orderbook.csv')
            df_orderbook = pd.read_csv(file_orderbook, parse_dates=['date'])
            df_orderbook.to_sql(
                f'trade_{self.table_name}_orderbook',
                self.engine,
                schema='trade',
                if_exists='append',
                index=False
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load OrderBook data: {e}")

if __name__ == "__main__":
    dumper = Dump_Trades_DB('BTC/USDT')
    #dumper.dump()
    #dumper.load()
