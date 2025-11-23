# End-to-End Trading System  
*FINM 32500 – University of Chicago*  
*Authors: Yuting Li, Xiangchen Liu, Simon Guo, Rajdeep Choudhury*

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Manager](https://img.shields.io/badge/dependency-uv-purple)
![Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

A comprehensive Python-based trading ecosystem designed for **algorithmic strategy development**.  
This project covers the entire lifecycle of a trading strategy: from historical data acquisition and backtesting against a custom matching engine to live paper trading execution via the **Alpaca API**.

---

## 🚀 Features

### **1. Data Pipeline (`Part 1`)**
- **Integration:** Fetches historical intraday data using `yfinance`.
- **Cleaning:** Automatic cleaning, sorting, and formatting of market data.
- **Streaming:** Simulates real-time data feeds using static CSV files.

### **2. Event-Driven Backtester (`Part 2 & 3`)**
- **Custom Engine:** Implements a Limit Order Book (LOB) with price–time priority.
- **Matching Engine:** Simulates fills, partial fills, and random execution failures.
- **Risk Management:** `OrderManager` checks for capital sufficiency and position limits.
- **Reporting:** Generates Markdown performance reports (Sharpe Ratio, Drawdown, Equity Curve) and audit logs.

### **3. Live Paper Trading (`Part 4`)**
- **Alpaca Integration:** Connects to Alpaca Paper Trading API.
- **Strategy Warm-up:** Pre-fetches historical bars to initialize indicators (e.g., Moving Averages).
- **Real-time Execution:** Monitors minute-level bars and submits orders automatically.

---

## 📂 Project Structure

```text
├── strategies.py        # Trading strategies (MAC, Momentum)
├── models.py            # Order and MarketDataPoint dataclasses
├── engine.py            # OrderBook, MatchingEngine, Gateway
├── backtest_runner.py   # Historical backtesting entry point
├── alpaca_runner.py     # Live Paper Trading entry point
├── download_data.py     # yfinance data fetcher
├── data_loader.py       # CSV loader and data streaming
├── reporting.py         # Generates performance_report.md
├── pyproject.toml       # Project configuration and dependencies (uv-managed)
├── uv.lock              # Locked dependencies for reproducibility
└── README.md            # Project documentation
```

---

## 🛠️ Installation & Setup

This project uses **uv** for modern & reproducible dependency management.

### **1. Install `uv` (if not installed)**

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

### **2. Sync Dependencies**

Creates virtual environment + installs all dependencies from `uv.lock`:

```bash
uv sync
```

---

## 🖥️ Usage

---

### **A. Historical Backtesting**

#### **Step 1: Download Data**
Fetch historical data (default: `AAPL`):

```bash
uv run download_data.py
```

#### **Step 2: Run the Backtest**

```bash
uv run backtest_runner.py
```

**Output includes:**

- `performance_report.md` → equity curve + metrics  
- `trade_audit.csv` → audit log of simulated trades  

---

### **B. Live Paper Trading (Alpaca)**

#### **Step 1: Configure Keys**
Open `alpaca_runner.py`:

```python
API_KEY = "PK..."
SECRET_KEY = "..."
```

#### **Step 2: Start the Bot**

```bash
uv run alpaca_runner.py
```

The bot will:

- warm up with historical bars  
- enter a minute-level execution loop  
- trade automatically  

---

## 📊 Sample Output

### **Performance Report**
Included in `performance_report.md`:

- **Total Return:** 0.04%  
- **Sharpe Ratio:** 0.010  
- **Max Drawdown:** 0.07%  
- **ASCII Equity Curve:** visualized equity curve  

---

### **Trade Audit Log**

`trade_audit.csv` example:

```text
timestamp,order_id,symbol,side,status,reason
1763605705.62,1001,AAPL,BUY,FILLED,
1763605705.63,1002,AAPL,SELL,FAILED,Simulated execution failure
```

---

## 📝 License

This project is licensed under the **MIT License**.

© 2025
