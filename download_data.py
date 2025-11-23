# download_data.py

# We need DataLoader which handles the yfinance logic
from data_loader import DataLoader
import pandas as pd
from datetime import datetime
from typing import List

SYMBOL = "AAPL"
DATA_FILE = "market_data.csv"
PERIOD = '7d'  # 7 days of historical data
INTERVAL = '1m'  # 1-minute bars (intraday data)


def execute_download():
    """
    Executes the data download, cleaning, and CSV saving process
    as required by Part 1, Step 1.
    """
    print(f"--- Starting Data Download for {SYMBOL} ---")
    print(f"Period: {PERIOD}, Interval: {INTERVAL}")

    try:
        # Call the static method in your DataLoader class
        df = DataLoader.get_yfinance_data(
            ticker=SYMBOL,
            period=PERIOD,
            interval=INTERVAL,
            filename=DATA_FILE
        )

        if not df.empty:
            print("\n✅ Download Successful.")
            print(f"Data saved to {DATA_FILE}")
            print(f"Total Ticks/Bars: {len(df)}")
            print(f"Columns: {list(df.columns)}")
        else:
            print("\n⚠️ Download Failed: DataFrame is empty. Check the ticker symbol or period.")

    except Exception as e:
        print(f"\n❌ An error occurred during download: {e}")
        print("Please ensure 'yfinance' is installed and your internet connection is active.")


if __name__ == "__main__":
    execute_download()