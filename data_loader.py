# data_loader.py (Modified)

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List

from models import MarketDataPoint


class DataLoader:
    @staticmethod
    def get_yfinance_data(ticker: str, period: str = '7d', interval: str = '1m',
                          filename: str = "market_data.csv") -> pd.DataFrame:
        """ Downloads data, cleans it, and saves it as CSV. """
        print(f"Downloading {ticker} data from yfinance...")
        df = yf.download(tickers=ticker, period=period, interval=interval)

        df.dropna(inplace=True)

        # 1. Ensure the index is named 'Datetime'
        df.index.name = 'Datetime'

        # 2. CRITICAL FIX: Convert the index (Datetime) into a regular column.
        df = df.reset_index()

        # 3. Sort values by the new 'Datetime' column
        df.sort_values(by='Datetime', inplace=True)

        # 4. Save without writing the automatic Pandas index (index=False)
        df.to_csv(filename, index=False)

        print(f"Data saved to {filename}. 'Datetime' column guaranteed.")
        return df

    @staticmethod
    def stream_data_from_csv(filename: str) -> List[MarketDataPoint]:
        """ Reads cleaned CSV data to simulate a live stream of MarketDataPoints. """
        data_points = []
        try:
            # FIX: Skip the 3 header rows and manually assign column names
            # based on the order shown in the CSV image.
            # Order: Datetime, Price/Close, Price/High, Price/Low, Price/Open, Volume
            df = pd.read_csv(
                filename,
                skiprows=3,  # Skip the first three header rows
                names=['Datetime', 'Price', 'Close', 'High', 'Low', 'Open', 'Volume'],
                index_col='Datetime',
                parse_dates=True
            )

            # Drop the redundant 'Price' column which is created by yfinance's structure
            # df = df.drop(columns=['Price'], errors='ignore')

            for timestamp, row in df.iterrows():
                # We use 'Close' price for simplicity in streaming simulation
                # Note: We must use row['Close'] now, as 'Close' is explicitly named.
                mdp = MarketDataPoint(
                    timestamp=timestamp.to_pydatetime(),
                    symbol=row.get('Symbol', 'AAPL'),
                    price=row['Close']
                )
                data_points.append(mdp)
            return data_points
        except FileNotFoundError:
            print(f"Error: The data file '{filename}' was not found. Please run DataLoader.get_yfinance_data() first.")
            return []