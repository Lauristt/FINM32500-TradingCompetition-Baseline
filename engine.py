import heapq
import random
import time
from collections import deque
from typing import List, Dict, Tuple, Any, Optional
import logging
from datetime import datetime
from models import Order, OrderStatus, LimitOrder, OrderError, ExecutionError, MarketDataPoint

logger = logging.getLogger("backtest")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


# --- Gateway (Part 2, Step 3: Logging) ---
class Gateway:
    """Handles logging all order and execution events for audit."""

    def __init__(self, log_filename="trade_audit.csv"):
        self.log_filename = log_filename
        with open(self.log_filename, 'w') as f:
            f.write("timestamp,order_id,symbol,side,quantity,price,status,reason\n")

    def log_order(self, order: Order):
        """Writes order event to the audit file."""
        # Use order.status.name for clean string representation
        with open(self.log_filename, 'a') as f:
            f.write(
                f"{time.time()},{order.order_id},{order.symbol},{order.side},{order.quantity},{order.price},{order.status.name},{order.reason}\n")

    def log_message(self, message: str):
        """Writes a simple system message."""
        logger.info(f"[GATEWAY] {message}")


# --- Order Book (Part 2, Step 2: Heaps) ---
class OrderBook:
    """Manages limit orders using heaps for price-time priority."""

    def __init__(self):
        # Bids: Max heap (stores -price for max-heap behavior)
        self.bids: List[Tuple[float, float, Order]] = []
        # Asks: Min heap (stores +price)
        self.asks: List[Tuple[float, float, Order]] = []
        # Note: The backtester uses the MatchingEngine for execution, not the OrderBook match method.

    def add_order(self, order: Order):
        """Adds an order to the book, primarily for future complex matching logic or inspection."""
        price_key = -order.price if order.side == 'BUY' else order.price
        timestamp_key = time.time()

        limit_order = (price_key, timestamp_key, order)  # Tuple structure for heap

        if order.side == 'BUY':
            heapq.heappush(self.bids, limit_order)
        else:
            heapq.heappush(self.asks, limit_order)

    def check_match(self) -> bool:
        """Checks if the best bid and best ask cross."""
        if not self.bids or not self.asks:
            return False

        best_bid_price = -self.bids[0][0]  # Undo negation
        best_ask_price = self.asks[0][0]

        return best_bid_price >= best_ask_price


#Order Manager (Part 2, Step 3: Risk Checks) ---
class OrderManager:
    """Validates orders against risk limits and capital sufficiency."""

    def __init__(self, initial_capital: float, max_orders_per_minute: int = 50):
        self.capital = initial_capital
        self.orders_timestamps = deque()
        self.MAX_ORDERS_PER_MIN = max_orders_per_minute
        # Tracks current position quantity, updated by the Portfolio class
        self.positions: Dict[str, float] = {}
        self.MAX_POSITION = 500  # Example: Max 500 shares long or short

    def validate_order(self, order: Order) -> bool:
        """Checks order quantity, capital sufficiency, rate limits, and position limits."""
        # 1. Basic Quantity/Price Check
        try:
            order.validate()
        except OrderError as e:
            order.mark_rejected(str(e))
            return False

        # 2. Capital Sufficiency Check (Simple check for immediate BUY cost)
        if order.side == 'BUY':
            cost = order.quantity * order.price
            if cost > self.capital:
                order.mark_rejected("Insufficient capital.")
                return False

        # 3. Rate Limit Check (Orders per minute)
        now = time.time()
        # Remove orders older than 60s
        while self.orders_timestamps and self.orders_timestamps[0] < now - 60:
            self.orders_timestamps.popleft()

        if len(self.orders_timestamps) >= self.MAX_ORDERS_PER_MIN:
            order.mark_rejected("Rate limit exceeded.")
            return False

        # 4. Position Limit Check
        current_pos = self.positions.get(order.symbol, 0.0)

        if order.side == 'BUY' and (current_pos + order.quantity) > self.MAX_POSITION:
            order.mark_rejected(f"Position limit ({self.MAX_POSITION}) exceeded.")
            return False

        if order.side == 'SELL' and (current_pos - order.quantity) < -self.MAX_POSITION:
            order.mark_rejected(f"Short position limit (-{self.MAX_POSITION}) exceeded.")
            return False

        # Pass: Record the order timestamp and return True
        self.orders_timestamps.append(now)
        return True


#Matching Engine Simulator (Part 2, Step 4: Simulation) ---
class MatchingEngine:
    """Simulates probabilistic order fills, partial fills, cancellations, and failures."""

    def __init__(self, slippage_factor: float = 0.0001):
        self.slippage_factor = slippage_factor

    def simulate_execution(self, order: Order) -> Tuple[float, int]:
        """Returns: (fill_price, filled_quantity)"""
        # 1. Simulate occasional failures (Requirement: 2% chance)
        if random.random() < 0.02:
            raise ExecutionError("Simulated execution failure (2% chance)")

        # 2. Determine Fill Type
        fill_probability = 0.95
        partial_probability = 0.04
        filled_qty = 0

        if random.random() < fill_probability:
            # Full Fill
            filled_qty = order.quantity
        elif random.random() < partial_probability:
            # Partial Fill
            filled_qty = random.randint(1, order.quantity - 1)
        else:
            # Canceled/No liquidity
            order.mark_rejected("Canceled/No liquidity.")
            return (0.0, 0)

        # 3. Simulate Slippage
        slippage = random.gauss(0, self.slippage_factor)
        fill_price = order.price * (1 + slippage)

        if filled_qty > 0:
            order.mark_filled(filled_qty, fill_price)

        return (round(fill_price, 2), filled_qty)


# --- Portfolio Accountant (Part 3: Performance Tracking) ---
class Portfolio:
    """Handles cash, positions, and trade accounting."""

    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.positions: Dict[str, Dict[str, float]] = {}  # symbol -> {"quantity": Q, "avg_price": P}
        self.trades: List[Tuple[datetime, float]] = []  # Stores (timestamp, equity) for reporting
        self.om: Optional[OrderManager] = None  # Placeholder for circular dependency

    def update_from_fill(self, order: Order, fill_price: float, filled_qty: int):
        """Updates cash and position based on a successful fill."""
        symbol = order.symbol
        pos = self.positions.get(symbol, {"quantity": 0.0, "avg_price": 0.0})

        # Accounting for Cash and Quantity
        cost = filled_qty * fill_price
        self.cash += cost if order.side == "SELL" else -cost

        current_qty = pos["quantity"]
        new_qty = current_qty + filled_qty if order.side == "BUY" else current_qty - filled_qty

        # Update Average Price (Simplified weighted average, maintains price when reducing size)
        if new_qty * current_qty >= 0 and new_qty != 0:
            new_total_cost = (pos["avg_price"] * current_qty) + (fill_price * filled_qty)
            pos["avg_price"] = new_total_cost / new_qty
        elif new_qty == 0:
            pos["avg_price"] = 0.0

        pos["quantity"] = new_qty
        self.positions[symbol] = pos

        # CRITICAL: Update OrderManager's position record for real-time risk checks
        if self.om:
            self.om.positions[symbol] = new_qty

    def compute_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculates total equity (Cash + Positions marked to market)."""
        total_value = self.cash
        for sym, pos in self.positions.items():
            # Use current tick price if available, otherwise use cost basis (avg_price)
            price = current_prices.get(sym, pos["avg_price"])
            total_value += pos["quantity"] * price
        return total_value