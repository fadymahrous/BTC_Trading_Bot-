import os
import re
import pandas as pd
from datetime import timedelta
from os import path
from Helper.Database_Engine import DatabaseEngine


class RawData_Weighting_OB:
    def __init__(self, symbol=None):
        if symbol is None:
            raise ValueError("The symbol must be provided, e.g., 'BTC/USDT'.")
        
        self.table_name = re.sub(r'[^A-Za-z0-9]', '', symbol).lower()

        # Create engine to connect to AWS-hosted PostgreSQL DB
        db_engine = DatabaseEngine()
        self.engine = db_engine.create_postgres_engine()

        # Ensure data directory exists
        os.makedirs('Data', exist_ok=True)

    def generate_clean_data(self):
        try:
            query = f"""
                SELECT * FROM trade.trade_{self.table_name}_orderbook
                WHERE date >= NOW() - INTERVAL '34 HOURS'
                ORDER BY date ASC;
            """
            df = pd.read_sql(query, self.engine)
            df.to_csv(path.join('Data', 'OrderBook_forminRaw.csv'), index=False)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch order book data: {e}")

        # Group by timestamp and action (Buy/Sell)
        grouped = df.groupby(['date', 'action'])['btc_amount'].sum().unstack(fill_value=0)

        # Calculate imbalance and push direction
        grouped['imbalance'] = grouped.get('Buy', 0) - grouped.get('Sell', 0)
        grouped['push_direction'] = grouped['imbalance'].apply(
            lambda x: 'Buy Pressure' if x > 0 else ('Sell Pressure' if x < 0 else 'Neutral')
        )

        # Save 5-second grouped data
        result_5s = grouped.reset_index()
        result_5s.to_csv(path.join('Data', 'OrderBook_Grouped_by5sec.csv'), index=False)

        # Group by floored minute and average
        result_5s['date'] = result_5s['date'].dt.floor('min')
        result_min = result_5s.groupby('date')[['Buy', 'Sell']].mean().reset_index()
        result_min['Assumed_OC_volume'] = result_min['Buy'] + result_min['Sell']
        result_min['Assumed_OC_Direction'] = result_min.apply(
            lambda row: 'Bearish' if row['Sell'] > row['Buy'] else (
                        'Bullish' if row['Buy'] > row['Sell'] else 'Neutral'), axis=1)
        result_min['Assumed_OC_Volume_Delta']=result_min['Buy']-result_min['Sell']

        # Save per-minute result
        result_min.to_csv(path.join('Data', 'OrderBook_Grouped_byMin.csv'), index=False)


if __name__ == "__main__":
    symbol = 'BTC/USDT'
    cleaner = RawData_Weighting_OB(symbol)
    cleaner.generate_clean_data()
