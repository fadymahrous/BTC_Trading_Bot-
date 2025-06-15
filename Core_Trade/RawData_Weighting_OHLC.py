import pandas as pd
from os import path
from Helper.Database_Engine import DatabaseEngine
from scipy.stats import linregress
import numpy as np

class RawData_Weighting_OHLC:
    def __init__(self,trade_history:pd=None):
        if trade_history is None:
            raise ValueError("There is no Data passed, this is an empty dataset")
        self.trade_history=trade_history

    def generate_clean_data(self):
        def compute_slope_and_residual(df, column, window):
            slopes = np.full(len(df), np.nan)
            residuals = np.full(len(df), np.nan)
            
            y_series = df[column].values
            x = np.arange(window)
            
            for i in range(window - 1, len(df)):
                y = y_series[i - window + 1:i + 1]
                slope, intercept, _, _, _ = linregress(x, y)
                y_pred = slope * x + intercept
                residual_max = np.max(np.abs(y - y_pred))

                slopes[i] = slope
                residuals[i] = residual_max

            return slopes, residuals

        # Calculate gains
        self.trade_history['gain'] = self.trade_history['close'] - self.trade_history['open']
        self.trade_history['gain_last_5interval'] = (self.trade_history['gain'].rolling(window=2, min_periods=1).sum())

        # MACD and Signal Line calculation
        ema_12 = self.trade_history['close'].ewm(span=12, adjust=False).mean()
        ema_26 = self.trade_history['close'].ewm(span=26, adjust=False).mean()
        self.trade_history['MACD'] = ema_12 - ema_26
        self.trade_history['Signal'] = self.trade_history['MACD'].ewm(span=9, adjust=False).mean()
        self.trade_history['MACD_Position'] = self.trade_history['MACD'] - self.trade_history['Signal']

        # Calculate Key Levels
        self.trade_history['Max_Close_5'] = self.trade_history['close'].shift(1).rolling(window=5).max()
        self.trade_history['Min_Close_5'] = self.trade_history['close'].shift(1).rolling(window=5).min()
        self.trade_history['Scaled_Close_5'] = (self.trade_history['close']-self.trade_history['Min_Close_5'])/(self.trade_history['Max_Close_5']-self.trade_history['Min_Close_5'])

        self.trade_history['Max_Close_10'] = self.trade_history['close'].shift(1).rolling(window=10).max()
        self.trade_history['Min_Close_10'] = self.trade_history['close'].shift(1).rolling(window=10).min()
        self.trade_history['Scaled_Close_10'] = (self.trade_history['close']-self.trade_history['Min_Close_10'])/(self.trade_history['Max_Close_10']-self.trade_history['Min_Close_10'])

        self.trade_history['Max_Close_15'] = self.trade_history['close'].shift(1).rolling(window=15).max()
        self.trade_history['Min_Close_15'] = self.trade_history['close'].shift(1).rolling(window=15).min()
        self.trade_history['Scaled_Close_15'] = (self.trade_history['close']-self.trade_history['Min_Close_15'])/(self.trade_history['Max_Close_15']-self.trade_history['Min_Close_15'])
    
        self.trade_history['Max_Close_30'] = self.trade_history['close'].shift(1).rolling(window=30).max()
        self.trade_history['Min_Close_30'] = self.trade_history['close'].shift(1).rolling(window=30).min()
        self.trade_history['Scaled_Close_30'] = (self.trade_history['close']-self.trade_history['Min_Close_30'])/(self.trade_history['Max_Close_30']-self.trade_history['Min_Close_30'])

        self.trade_history['Max_Close_50'] = self.trade_history['close'].shift(1).rolling(window=50).max()
        self.trade_history['Min_Close_50'] = self.trade_history['close'].shift(1).rolling(window=50).min()
        self.trade_history['Scaled_Close_50'] = (self.trade_history['close']-self.trade_history['Min_Close_50'])/(self.trade_history['Max_Close_50']-self.trade_history['Min_Close_50'])

        self.trade_history['Max_Close_60'] = self.trade_history['close'].shift(1).rolling(window=60).max()
        self.trade_history['Min_Close_60'] = self.trade_history['close'].shift(1).rolling(window=60).min()
        self.trade_history['Scaled_Close_60'] = (self.trade_history['close']-self.trade_history['Min_Close_60'])/(self.trade_history['Max_Close_60']-self.trade_history['Min_Close_60'])


        self.trade_history['middle_value'] = abs(self.trade_history['close'] - self.trade_history['open'])/2 + self.trade_history[['close', 'open']].min(axis=1)
        self.trade_history['slope_5'], self.trade_history['Width_slope_5'] = compute_slope_and_residual(self.trade_history, 'middle_value', 5)
        self.trade_history['slope_10'], self.trade_history['Width_slope_10'] = compute_slope_and_residual(self.trade_history, 'middle_value', 10)
        self.trade_history['slope_15'], self.trade_history['Width_slope_15'] = compute_slope_and_residual(self.trade_history, 'middle_value', 15)
        self.trade_history['slope_30'], self.trade_history['Width_slope_30'] = compute_slope_and_residual(self.trade_history, 'middle_value', 30)
        self.trade_history['slope_50'], self.trade_history['Width_slope_50'] = compute_slope_and_residual(self.trade_history, 'middle_value', 50)
        self.trade_history['slope_100'], self.trade_history['Width_slope_100'] = compute_slope_and_residual(self.trade_history, 'middle_value', 100)
        self.trade_history['slope_200'], self.trade_history['Width_slope_200'] = compute_slope_and_residual(self.trade_history, 'middle_value', 200)



        def classify_candle(row):
            body = abs(row['close'] - row['open'])
            upper_wick = row['high'] - max(row['close'], row['open'])
            lower_wick = min(row['close'], row['open']) - row['low']

            # Avoid divide by zero
            if body == 0:
                return None

            #if lower_wick >= 2 * body and lower_wick/5 > upper_wick:
            if lower_wick >= 2 * body and lower_wick>upper_wick:
                return 'HangedMan' if row.Scaled_Close_5>0.9 and row.slope_5>10 else 'Hammer'
            #elif upper_wick >= 2 * body and upper_wick/5 >lower_wick:
            elif upper_wick >= 2 * body and lower_wick<upper_wick:
                return 'ShootingStar' if row.Scaled_Close_5>0.9 and row.slope_5>10 else 'InvertedHammer'
            else:
                return None

        self.trade_history['candle_figure'] = self.trade_history.apply(classify_candle, axis=1)

        # Volume Momentum Direction based on candle body only, ignoring candles wicks
        is_red = self.trade_history['close'] < self.trade_history['open']   # red  = True
        body         = (self.trade_history['close'] - self.trade_history['open']).abs()
        candle_range = self.trade_history['high'] - self.trade_history['low']
        candle_range = candle_range.replace(0, 1e-6)                        # avoid div-by-zero
        raw_momentum = (body / candle_range) * self.trade_history['volume']
        self.trade_history['volume_momentum'] = np.where(is_red, -raw_momentum, raw_momentum)

        # Create Avalanche Exit in case a shooting star or hanging man is observed at the peak
        mask = self.trade_history['candle_figure'].isin(['ShootingStar', 'HangedMan']).astype(int)
        self.trade_history['avalanch'] = (
            mask.rolling(window=3, min_periods=1).sum() > 0
        ).astype(int)

        # Create Bloodbath flag whihc happens at great loss time
        mask = (self.trade_history['volume_momentum'] < -30).astype(int)
        self.trade_history['Bloodbath'] = (
            mask.rolling(window=4, min_periods=1).max()
            .fillna(0)  # ensure no NaNs at beginning
            .astype(int)
        )

        self.trade_history = self.trade_history.drop(columns=['MACD','Signal','Max_Close_5','Min_Close_5','Max_Close_10','Min_Close_10','Max_Close_15','Min_Close_15','Max_Close_30','Min_Close_30','Max_Close_50','Min_Close_50','middle_value','Width_slope_5','Width_slope_10','Width_slope_15','Width_slope_30','Width_slope_50'])
        return self.trade_history
        #self.trade_history.to_csv('Data\\Binance_Bitcoin_minute_clean.csv', index=False)
       

if __name__ == "__main__":
    cleaner = RawData_Weighting_OHLC()
    cleaner.generate_clean_data()
