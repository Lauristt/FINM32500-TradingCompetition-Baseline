
# The backtester framework will call Strategy.generate_signals(tick) for every bar/tick.

from abc import ABC, abstractmethod
from collections import deque
from typing import List

from models import MarketDataPoint

class Strategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    Strategies must implement the generate_signals method.
    """

    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        """
        Receives one MarketDataPoint (tick) and returns a list of signals.
        Signals must be either "BUY" or "SELL".
        """
        pass


class MAC(Strategy):
    """
    Moving Average Crossover Strategy (Example implementation).
    Generates signals based on the cross of short and long moving averages.
    """

    def __init__(self, short_window: int = 5, long_window: int = 20):
        self._short_window = short_window
        self._long_window = long_window
        self._short_prices = deque(maxlen=short_window)
        self._long_prices = deque(maxlen=long_window)
        self._last_signal = None

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        self._short_prices.append(tick.price)
        self._long_prices.append(tick.price)

        if len(self._short_prices) < self._short_window or len(self._long_prices) < self._long_window:
            return []

        signals = []
        short_ma = sum(self._short_prices) / len(self._short_prices)
        long_ma = sum(self._long_prices) / len(self._long_prices)

        if short_ma > long_ma and self._last_signal != "BUY":
            signals.append("BUY")
            self._last_signal = "BUY"
        elif short_ma < long_ma and self._last_signal != "SELL":
            signals.append("SELL")
            self._last_signal = "SELL"

        return signals


class Momentum(Strategy):
    """
    Momentum Strategy (Example implementation).
    Generates signals based on price change over a lookback window.
    """

    def __init__(self, window: int = 10):
        self._window = window
        self._prices = deque(maxlen=window)
        self._last_signal = None

    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        self._prices.append(tick.price)
        if len(self._prices) < self._window:
            return []

        momentum = tick.price - self._prices[0]
        signals = []

        if momentum > 0 and self._last_signal != "BUY":
            signals.append("BUY")
            self._last_signal = "BUY"
        elif momentum < 0 and self._last_signal != "SELL":
            signals.append("SELL")
            self._last_signal = "SELL"

        return signals