import time
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
try:
    from Strategies import MAC, Momentum
    from models import MarketDataPoint
except ImportError as e:
    print(f"Error when importing necessary files! Source Broken. Aborting... Error:{e}")


API_KEY = "PKWKTVGQLFPWSNZV2IY6NFTBW2"
SECRET_KEY = "DjtzrHEVqJ4pMTWPnmvrrnaSNW7B9uKSpmujvC7FuEbt"
BASE_URL = "https://paper-api.alpaca.markets"

SYMBOL = "AAPL"
QTY = 10
TIMEFRAME = "1Min"  # Candle timeframe

class AlpacaTrader:
    def __init__(self):
        print(f"--- Connecting to Alpaca Paper Trading ({BASE_URL}) ---")
        try:
            self.api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
            account = self.api.get_account()
            print(f" Connected! Account Status: {account.status}")
            print(f" Buying Power: ${account.buying_power}")
        except Exception as e:
            print(f" Connection Failed: {e}")
            print("Please check your API_KEY and SECRET_KEY.")
            exit()

        # Initialize Strategy (Using MAC as defined in Part 1/3)
        self.strategy = MAC(short_window=5, long_window=20)
        print(f" Strategy Loaded: MAC (Short=5, Long=20)")

    def get_market_data_point(self) -> MarketDataPoint:
        """Fetches the latest completed bar and converts it to a MarketDataPoint."""
        # Get the last 2 bars. We do this to ensure we get the latest *completed* bar,
        # not the one currently forming.
        bars = self.api.get_bars(SYMBOL, TimeFrame.Minute, limit=2).df

        if bars.empty:
            return None

        # Take the most recent completed bar
        latest_bar = bars.iloc[-1]

        # Construct MarketDataPoint (Adapting to models.py)
        mdp = MarketDataPoint(
            timestamp=latest_bar.name.to_pydatetime(),
            symbol=SYMBOL,
            price=float(latest_bar['close'])
        )
        return mdp

    def warm_up_strategy(self):
        """
        CRITICAL: Fetches historical data to 'warm up' the strategy.
        Strategies like MAC need previous data points (e.g., 20 bars)
        before they can generate valid signals.
        """
        print("\n Warming up strategy (fetching historical data)...")
        # Fetch past 100 minutes of data
        past_bars = self.api.get_bars(SYMBOL, TimeFrame.Minute, limit=100).df

        count = 0
        for timestamp, row in past_bars.iterrows():
            mdp = MarketDataPoint(
                timestamp=timestamp.to_pydatetime(),
                symbol=SYMBOL,
                price=float(row['close'])
            )
            # Feed data to strategy without executing signals
            self.strategy.generate_signals(mdp)
            count += 1

        print(f"Warm-up complete! Loaded {count} historical bars.\n")

    def check_position(self) -> int:
        """Checks the current quantity of the symbol held in the portfolio."""
        try:
            position = self.api.get_position(SYMBOL)
            return int(position.qty)
        except:
            return 0  # Returns 0 if no position exists

    def run(self):
        self.warm_up_strategy()

        print(f" Starting Live Paper Trading Loop for {SYMBOL}... (Press Ctrl+C to stop)")

        while True:
            try:
                # 1. Fetch latest data
                tick = self.get_market_data_point()
                if not tick:
                    print(" No data received, waiting...")
                    time.sleep(10)
                    continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Price: ${tick.price:.2f} ", end="")

                # 2. Generate Signals
                signals = self.strategy.generate_signals(tick)

                # 3. Process Signals
                if not signals:
                    print("| No Signal (Wait)")
                else:
                    signal = signals[-1]  # Get the most recent signal
                    print(f"| Signal Triggered: {signal}!", end=" ")

                    current_qty = self.check_position()

                    if signal == "BUY":
                        print("Submitting BUY order...")
                        self.api.submit_order(
                            symbol=SYMBOL,
                            qty=QTY,
                            side='buy',
                            type='market',
                            time_in_force='gtc'
                        )
                        print(f" BUY Order Submitted: {QTY} shares")

                    elif signal == "SELL":
                        if current_qty > 0:
                            print("Submitting SELL order...")
                            self.api.submit_order(
                                symbol=SYMBOL,
                                qty=min(QTY, current_qty),  # Prevent short selling if qty < 10
                                side='sell',
                                type='market',
                                time_in_force='gtc'
                            )
                            print(f" SELL Order Submitted")
                        else:
                            print(" Cannot SELL (No position held)")

                # 4. Wait for the next minute
                # Sleeping 60 seconds. For a production system, you might want to
                # calculate the exact seconds remaining until the next minute mark.
                time.sleep(60)

            except KeyboardInterrupt:
                print("\n Program stopped by user.")
                break
            except Exception as e:
                print(f"\n Error occurred: {e}")
                time.sleep(10)


if __name__ == "__main__":
    trader = AlpacaTrader()
    trader.run()