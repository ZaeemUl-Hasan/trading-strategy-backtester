# Trading Strategy Backtester

A Python-based backtesting project that evaluates a simple moving-average trading strategy using historical Apple (AAPL) stock data.

## Overview

This project tests whether a simple moving-average strategy can outperform a basic buy-and-hold approach.

Historical AAPL price data from January 2020 to January 2026 is downloaded using `yfinance`. The strategy then calculates 20-day and 50-day simple moving averages and uses their relationship to determine whether to hold shares or cash.

## How the Strategy Works

The strategy uses two simple moving averages:

* **20-day SMA** — represents the shorter-term price trend.
* **50-day SMA** — represents the longer-term price trend.

The strategy follows these rules:

1. If the 20-day SMA is above the 50-day SMA, the strategy buys as many whole AAPL shares as possible using the available cash.
2. If the 20-day SMA falls below the 50-day SMA, the strategy sells its AAPL holdings and moves into cash.
3. Portfolio value is calculated throughout the backtest using the current stock price, cash balance and number of shares held.

The backtest starts after the first 50 trading days so that the 50-day moving average is available.

## Results

The strategy was tested using an initial investment of **$10,000**.

| Metric               |      Result |
| -------------------- | ----------: |
| Initial Capital      |  $10,000.00 |
| Strategy Final Value |  $21,604.91 |
| Strategy Return      | **116.05%** |
| Buy & Hold Return    | **363.72%** |

### Interpretation

Although the moving-average strategy generated a positive return of **116.05%**, it significantly underperformed simply buying and holding AAPL over the same period, which generated a **363.72%** return.

This demonstrates why a backtesting strategy should be compared against an appropriate benchmark rather than judged solely on whether it makes a profit.

## Technologies Used

* Python
* pandas
* Matplotlib
* yfinance

## Future Improvements

I plan to improve the backtester by adding transaction costs and slippage, testing the strategy across multiple stocks and time periods, and incorporating additional performance metrics such as maximum drawdown and the Sharpe ratio.
