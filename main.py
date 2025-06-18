import time
import json
from os import path
from datetime import datetime, timedelta, timezone
import pandas as pd
from Core_Trade.Fetch_Online_OHLC import FetchTradeMinute
from Core_Trade.Fetch_fromDB_OHLC import Fetch_fromDB_OHLC
from Core_Trade.RawData_Weighting_OHLC import RawData_Weighting_OHLC
from Helper.logger_setup import setup_logger

# Initialize logger
logger = setup_logger('combined_OHLC_trade', 'combined_OHLC_trade.log')

class RealTimeTradeStrategy:
    def __init__(self):
        self.active_trade = False
        self.waiting_for_confirmation = False
        self.session_gain = 0
        self.trade_record = {}
        self.entry_evaluated_this_session = False


    def evaluate_entry(self, row):
        if (
            row.get('candle_figure') in ['Hammer', 'InvertedHammer'] and
            row.get('Bloodbath') == 1 and
            row.get('Scaled_Close_10') < 0.2 and 
            row.get('slope_5') < 0 and
            not self.active_trade
        ):
            self.waiting_for_confirmation = True

        elif (
            self.waiting_for_confirmation and
            row.get('gain') > 230 and
            not self.active_trade
        ):
            self.active_trade = True
            self.session_gain = 0
            self.waiting_for_confirmation = False
            self.trade_record = {
                'start': row.get('date'),
                'entrance_gain':row.get('gain'),
                'volume_momentum': row.get('volume_momentum'),
                'Entrance_MDAC': row.get('MACD_Position'),
                'slope_5': row.get('slope_5'),
                'Scaled_Close_10': row.get('Scaled_Close_10'),
                'close': row.get('close'),
                'entry_type': 'Condition1_atBloodBath'
            }
            self.entry_evaluated_this_session = True
            logger.info(' ===> Enter Trade witth Condition1_atBloodBath.')
        #Condition 2
        elif (
            300 < row.get('volume_momentum') and
            row.get('Bloodbath') == 0 and
            row.get('MACD_Position') > 0 and 
            row.get('avalanch') == 0 and 
            row.get('slope_5') > 0 and
            not self.active_trade
        ):
            self.active_trade = True
            self.session_gain = 0
            self.trade_record = {
                'start': row.get('date'),
                'entrance_gain':row.get('gain'),
                'volume_momentum': row.get('volume_momentum'),
                'Entrance_MDAC': row.get('MACD_Position'),
                'slope_5': row.get('slope_5'),
                'Scaled_Close_10': row.get('Scaled_Close_10'),
                'close': row.get('close'),
                'entry_type': 'Condition2_atVolumeMomentum'
            }
            self.entry_evaluated_this_session = True
            logger.info(' ===> Enter Trade witth Condition2_atVolumeMomentum.')

    def evaluate_exit(self, row):
        if self.entry_evaluated_this_session:
            logger.info("No entry evaluated this session, skipping exit evaluation.")
            self.entry_evaluated_this_session = False
            return
        raw_exit_trigger = row.get('avalanch') == 1 or row.get('gain_last_5interval') < -50

        if self.active_trade and raw_exit_trigger:
            self.session_gain += row.get('gain')
            self.trade_record['end'] = row.get('date')
            self.trade_record['gain'] = self.session_gain
            self.trade_record['exit'] = 'Avalanch' if row.get('avalanch') == 1 else 'MaxLoss'

            # Save trade record
            self.write_trade_to_file(self.trade_record)

            # Reset state
            self.active_trade = False
            self.session_gain = 0
            self.trade_record = {}
            logger.info('Exit Trade ...')

        elif self.active_trade:
            self.session_gain += row.get('gain')

    def write_trade_to_file(self, trade):
        trade['start']=trade['start'].isoformat()
        trade['end']=trade['end'].isoformat()
        with open(path.join('Data','trade_records_Result.json'), 'a') as f:
            f.write(json.dumps(trade) + '\n')


def wait_until_next_interval(interval_minutes=5, offset_seconds=10):
    """Waits until the next interval + offset (e.g., every 5 minutes + 10 seconds)"""
    now_tmp = datetime.now(timezone.utc)
    flooring='{interval}min'.format(interval=interval_minutes)
    now=pd.to_datetime(now_tmp).floor(flooring)
    next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=interval_minutes))
    next_run = next_minute + timedelta(seconds=offset_seconds)
    wait_time = (next_run - now_tmp).total_seconds()
    logger.info(f"Next run scheduled at {next_run} UTC. Waiting {wait_time:.2f} seconds.")
    time.sleep(wait_time)

def main():
    strategy = RealTimeTradeStrategy()
    BTC_fetcher = FetchTradeMinute('binance', 'BTC/USDT')
    db_fetcher = Fetch_fromDB_OHLC(schema='trade')

    while True:
        try:
            logger.info("Starting 30m OHLC fetch and load.")
            BTC_fetcher.fetch_ohlc_and_load_to_db('30m')
            logger.info("OHLC fetch complete.")

            # Run trade logic
            raw_data = db_fetcher.get_OHLC_fromDB(symbol='BTC/USDT', interval='30m', since_hour=10)
            cleaner = RawData_Weighting_OHLC(raw_data)
            ohlc = cleaner.generate_clean_data()

            if not ohlc.empty:
                last_row = ohlc.iloc[-1].to_dict()
                logger.info(f"Evaluating trade logic for {last_row.get('date')}")
                strategy.evaluate_entry(last_row)
                strategy.evaluate_exit(last_row)
            else:
                logger.warning("No OHLC data found to evaluate.")

        except Exception as e:
            logger.exception(f"Error in combined loop: {e}")

        wait_until_next_interval(30, 10)

if __name__ == '__main__':
    main()
