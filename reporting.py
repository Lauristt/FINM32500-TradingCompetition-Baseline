# reporting.py

import numpy as np
from typing import Dict, Any

try:
    # Ensure these imports match your module structure
    from data_loader import MarketDataPoint
    # Note: ExecutionEngine, MAC, Momentum are not strictly needed for the reporter
    # but kept for compatibility with your initial file structure.
    from engine import MatchingEngine
    from Strategies import MAC, Momentum
except ModuleNotFoundError as e:
    # This warning helps debug if dependencies are missing
    print(
        f"Fatal! Source Broken. Please implement module 'models' or  'data_loader' or 'Strategies' or 'engine'. Error! {e}. ")


class PerformanceReporter:
    def __init__(self, backtest_results: Dict[str, Any]):
        self.equity_curve = backtest_results.get("equity_curve", [])
        if not self.equity_curve or len(self.equity_curve) < 2:
            raise ValueError("Equity curve is empty or insufficient for analysis. Cannot generate report.")

        self.timestamps, self.equity_values = zip(*self.equity_curve)
        self.metrics = {}

    def calculate_metrics(self) -> Dict[str, str]:
        equity_array = np.array(self.equity_values)

        # 1. Total Return
        total_return = (equity_array[-1] / equity_array[0]) - 1

        # 2. Series of periodic returns
        # Returns based on tick-to-tick changes
        returns = (equity_array[1:] / equity_array[:-1]) - 1

        # 3. Sharpe Ratio (Per-Tick)
        # Handle the case where the standard deviation is zero (no volatility)
        if np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns)
        else:
            sharpe_ratio = np.inf

        # 4. Maximum Drawdown
        peak = equity_array[0]
        max_drawdown = 0
        for equity in equity_array:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        self.metrics = {
            "Total Return": f"{total_return:.2%}",
            "Sharpe Ratio (Per-Tick)": f"{sharpe_ratio:.3f}" if np.isfinite(sharpe_ratio) else "inf",
            "Maximum Drawdown": f"{max_drawdown:.2%}",
        }
        return self.metrics

    def _generate_ascii_plot(self, width: int = 80, height: int = 20) -> str:
        """Generates an ASCII art representation of the equity curve."""
        equity = self.equity_values
        min_val, max_val = min(equity), max(equity)

        if max_val == min_val:
            return "Equity curve is flat. No plot generated."

        y_range = max_val - min_val
        # Scale Y values to the plot height
        scaled_y = [int(((val - min_val) / y_range) * (height - 1)) for val in equity]

        # Scale X values to the plot width
        x_indices = np.linspace(0, len(equity) - 1, width, dtype=int)
        plot_data = [scaled_y[i] for i in x_indices]

        # Create the plot canvas
        plot = [[' ' for _ in range(width)] for _ in range(height)]

        # Draw the data points on the canvas
        for i, y in enumerate(plot_data):
            plot[height - 1 - y][i] = '*'

        # Assemble the plot with Y-axis labels
        output = []
        y_label_max = f"{max_val:,.2f} -"
        y_label_min = f"{min_val:,.2f} -"

        output.append(y_label_max + "".join(plot[0]))
        for r in range(1, height - 1):
            line = " " * len(y_label_max) + "".join(plot[r])
            output.append(line)
        output.append(y_label_min + "".join(plot[height - 1]))

        return "\n".join(output)

    def generate_report(self, filename: str = "performance.md"):
        """Generates and saves the full performance report to a Markdown file."""
        self.calculate_metrics()

        narrative = (
            "### Performance Analysis\n\n"
            "This report summarizes the performance of the trading strategy based on the backtest results.\n\n"
            f"- The strategy yielded a **total return of {self.metrics['Total Return']}** over the backtest period.\n"
            f"- The **Sharpe Ratio is {self.metrics['Sharpe Ratio (Per-Tick)']}**. This value represents the risk-adjusted return on a per-tick basis and is not annualized. A higher value generally indicates better performance for the amount of risk taken.\n"
            f"- The portfolio experienced a **maximum drawdown of {self.metrics['Maximum Drawdown']}**. This is the largest peak-to-trough decline in the portfolio's value, indicating the potential downside risk during an unfavorable period."
        )

        table = (
            "### Summary Metrics\n\n"
            "| Metric                   | Value            |\n"
            "|--------------------------|------------------|\n"
            f"| Total Return             | {self.metrics['Total Return']}       |\n"
            f"| Sharpe Ratio (Per-Tick)  | {self.metrics['Sharpe Ratio (Per-Tick)']}        |\n"
            f"| Maximum Drawdown         | {self.metrics['Maximum Drawdown']}   |"
        )

        plot_title = "\n### Equity Curve\n"
        ascii_plot = self._generate_ascii_plot()

        report_content = f"# Backtest Performance Report\n\n{narrative}\n\n{table}\n\n{plot_title}\n```\n{ascii_plot}\n```"

        with open(filename, 'w') as f:
            f.write(report_content)
        print(f"Performance report saved to {filename}")