# backtest_runner.py

import pandas as pd
from datetime import datetime
from typing import List
import time

from data_loader import DataLoader
from Strategies import Strategy, MAC, Momentum  # Import your Strategies
from models import Order, OrderError, ExecutionError
from engine import Gateway, OrderManager, MatchingEngine, Portfolio
from reporting import PerformanceReporter

# Configuration
SYMBOL = "AAPL"
INITIAL_CASH = 100000.0
DEFAULT_QTY = 10
DATA_FILE = "market_data.csv"


def run_backtest_simulation(strategies_list: List[Strategy]):
    """
    Runs the full backtest simulation by streaming data to the system.
    (Part 2, Step 1: Simulates live feed by iterating over historical data)
    """
    print("--- Loading Data and Initializing Components ---")

    # Check if data exists and load the MarketDataPoint objects
    ticks = DataLoader.stream_data_from_csv(DATA_FILE)
    if not ticks:
        print(f"FATAL: Could not load data from {DATA_FILE}. Please run the download script first.")
        return {}

    # Initialize Core Components
    gateway = Gateway()
    order_manager = OrderManager(INITIAL_CASH)
    matching_engine = MatchingEngine()
    portfolio = Portfolio(INITIAL_CASH)

    # Link Portfolio back to OrderManager for position tracking (Circular dependency fix)
    portfolio.om = order_manager

    print(f"--- Starting Backtest Simulation with {len(ticks)} ticks ---")

    # --- Part 3: Simulation Execution Loop ---
    for tick in ticks:
        current_prices = {tick.symbol: tick.price}

        # 1. Strategy Signal Generation
        all_signals = []
        for strat in strategies_list:
            all_signals.extend(strat.generate_signals(tick))

        # 2. Process Signals and Submit Orders
        for direction in all_signals:
            order = None
            try:
                # Create Order object based on signal
                order = Order(symbol=tick.symbol, quantity=DEFAULT_QTY, price=tick.price, side=direction)

                # 3. Order Validation (Order Manager)
                if not order_manager.validate_order(order):
                    gateway.log_order(order)
                    continue  # Order rejected by risk check

                # 4. Order Execution (Matching Engine)
                # Note: For simplicity, the engine simulates execution immediately
                fill_price, filled_qty = matching_engine.simulate_execution(order)

                if filled_qty > 0:
                    # 5. Portfolio Update
                    portfolio.update_from_fill(order, fill_price, filled_qty)

                # 6. Gateway Audit Log
                gateway.log_order(order)

            except ExecutionError as ee:
                if order:
                    order.mark_failed(reason=str(ee))
                    gateway.log_order(order)
            except Exception as e:
                if order:
                    order.mark_failed(reason=f"Unknown Error: {e}")
                    gateway.log_order(order)

        # Record Equity Curve (Part 3: Performance Tracking)
        equity = portfolio.compute_equity(current_prices)
        portfolio.trades.append((tick.timestamp, equity))

        # --- Part 3: Reporting ---
    results = {
        "final_cash": portfolio.cash,
        "portfolio": portfolio.positions,
        # Only pass the list of (timestamp, equity) tuples
        "equity_curve": portfolio.trades
    }

    # Generate the Markdown report
    if results["equity_curve"]:
        reporter = PerformanceReporter(backtest_results=results)
        reporter.generate_report(filename="performance_report.md")

    return results


if __name__ == "__main__":
    # --- Define the strategies you want to test here ---
    # You can add multiple strategies to test simultaneously
    strategies = [
        MAC(short_window=20, long_window=50),
        # Momentum(window=15) # Example: Uncomment to test momentum as well
    ]

    backtest_results = run_backtest_simulation(strategies)

    if backtest_results:
        print("\n--- Final Results Summary ---")
        print(f"Total Ticks Processed: {len(backtest_results['equity_curve'])}")
        print(f"Final Cash: ${backtest_results['final_cash']:,.2f}")
        print("Report saved to performance_report.md and trade_audit.csv")