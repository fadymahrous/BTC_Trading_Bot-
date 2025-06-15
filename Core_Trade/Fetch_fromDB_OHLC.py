import pandas as pd
from os import path
from Helper.Database_Engine import DatabaseEngine
from scipy.stats import linregress
import numpy as np
import re

class Fetch_fromDB_OHLC:
    def __init__(self,schema:str='trade'):
        self.schema=schema

        # Create engine to connect to AWS-hosted PostgreSQL DB
        db_engine = DatabaseEngine()
        self.engine = db_engine.create_postgres_engine()

    def get_OHLC_fromDB(self,symbol:str=None,interval:str=None,since_hour:int=None):
        if symbol is None:
            raise ValueError("the symbol must be provided like 'BTC/USDT'.")
        crypto_stock_type=re.sub(r'[^A-Za-z0-9]', '', symbol).lower()
        if interval is None:
            raise ValueError("the interval must be provided like '5m'.")
        self.table_name="trade_{segment}_ohlc".format(segment=crypto_stock_type+interval)
        if since_hour is None:
            raise ValueError("Yuo must provide Integer value, you need the data for how many hours back")
        self.since_hour=since_hour

        # Fetch last 4 hours of OHLC data from trade_btcusdt_ohlc table in 'trade' schema
        try:
            query = f"""
                SELECT * FROM {self.schema}.{self.table_name}
                WHERE date >= NOW() - INTERVAL '{self.since_hour} HOURS'
                ORDER BY date ASC;
            """
            self.trade_history = pd.read_sql(query, self.engine)
            if self.trade_history.empty:
                return None
            else:
                return self.trade_history
        except Exception as e:
            raise RuntimeError(f"Failed to fetch recent OHLC data: {e}")