# models.py

import enum
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import time

class OrderStatus(enum.Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

@dataclass(frozen=True)
class MarketDataPoint:
    timestamp: datetime
    symbol: str
    price: float

@dataclass
class Order:
    symbol: str
    quantity: int
    price: float
    side: str = "BUY"  # "BUY" or "SELL"
    order_type: str = "LIMIT"
    status: OrderStatus = OrderStatus.NEW
    filled_quantity: int = 0
    reason: str = ""
    order_id: str = field(default_factory=lambda: str(time.time()))

    def validate(self):
        if self.quantity <= 0:
            raise OrderError("Order quantity must be strictly positive")
        if self.price <= 0:
            raise OrderError("Order price must be strictly positive")

    def mark_filled(self, filled_qty: int, fill_price: float):
        self.filled_quantity += filled_qty
        self.status = OrderStatus.FILLED if self.filled_quantity == self.quantity else OrderStatus.PENDING

    def mark_failed(self, reason:str="Execution failed"):
        self.status = OrderStatus.FAILED
        self.reason = reason

    def mark_rejected(self, reason:str="Risk check failed"):
        self.status = OrderStatus.REJECTED
        self.reason = reason

@dataclass # Removed order=True to fix TypeError
class LimitOrder:
    # Used for Price-Time priority sorting in the OrderBook
    price_key: float
    timestamp_key: float
    order: Order

    def __lt__(self, other):
        # 1. Price Priority (Higher priority is 'less than' in the heap sense)
        if self.price_key != other.price_key:
            return self.price_key < other.price_key
        # 2. Time Priority (If prices are equal, earlier timestamp is better)
        return self.timestamp_key < other.timestamp_key

class OrderError(Exception):
    """Raised when an invalid order is created."""
    pass

class ExecutionError(Exception):
    """Raised when execution fails (e.g., simulated network error)."""
    pass