# Trading Strategy Backtester

A Python backtester that tests whether classic trading strategies can outperform a basic buy-and-hold approach, on any stock, ETF or crypto ticker, with realistic trading costs and proper risk metrics.

## Overview

This project started as a test of a single 20/50-day simple moving-average strategy on Apple (AAPL) stock. It now supports six strategies, any ticker on Yahoo Finance, fees and slippage, and a full set of performance metrics, so strategies can be compared fairly against an appropriate benchmark.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python backtester.py                          # 20/50 SMA crossover on AAPL since 2020
python backtester.py TSLA -s all              # compare every strategy on TSLA
python backtester.py MSFT -s sma -p fast=10 -p slow=30 --start 2018-01-01
python backtester.py BTC-USD -s momentum --fractional --fee 0.1 --slippage 0.1
python backtester.py SPY -s rsi --json --no-plot   # machine-readable output
python backtester.py X --csv prices.csv       # offline data (Date, Open, Close columns)
```

| Option | Default | Description |
|---|---|---|
| `ticker` | `AAPL` | Any Yahoo Finance symbol |
| `-s, --strategy` | `sma` | `sma`, `ema`, `rsi`, `bollinger`, `momentum`, `buyhold` or `all` |
| `-p, --param` | | Strategy parameter, repeatable (see below) |
| `--start` / `--end` | `2020-01-01` / today | Backtest period |
| `--cash` | `10000` | Starting cash |
| `--fee` | `0.05` | Fee per trade, in % |
| `--slippage` | `0.05` | Slippage per trade, in % |
| `--fractional` | | Allow fractional shares (needed for crypto or high-priced stocks) |
| `--risk-free` | `0` | Annual risk-free rate in %, used for Sharpe/Sortino |
| `--json` | | Print results as JSON |
| `--no-plot` / `--save-plot FILE` | | Skip the chart window / save the chart to a file |

## Strategies

| Name | Idea | Parameters (defaults) |
|---|---|---|
| `sma` | Hold while the fast SMA is above the slow SMA | `fast=20`, `slow=50` |
| `ema` | Same, with exponential moving averages | `fast=12`, `slow=26` |
| `rsi` | Buy when oversold, sell when overbought | `period=14`, `oversold=30`, `overbought=70` |
| `bollinger` | Buy below the lower band, sell back above the middle | `window=20`, `num_std=2` |
| `momentum` | Hold while price is above its level `lookback` days ago | `lookback=126` |
| `buyhold` | Always invested (benchmark, always included) | |

### How the original SMA strategy works

The strategy uses two simple moving averages:

* **20-day SMA**: represents the shorter-term price trend.
* **50-day SMA**: represents the longer-term price trend.

1. If the 20-day SMA is above the 50-day SMA, the strategy buys as many whole shares as possible using the available cash.
2. If the 20-day SMA falls below the 50-day SMA, the strategy sells its holdings and moves into cash.
3. Portfolio value is calculated throughout the backtest using the current stock price, cash balance and number of shares held.

Adding a strategy means writing one function in `strategies.py` that returns a 1/0 position for each day and registering it in `STRATEGIES`.

## Results

AAPL, 2 January 2020 to 31 December 2025, starting with **$10,000**, 0.05% fees and 0.05% slippage (`python backtester.py AAPL -s all --end 2026-01-01`):

| Metric | SMA | EMA | RSI | Bollinger | Momentum | Buy & Hold |
|---|--:|--:|--:|--:|--:|--:|
| Final Value | $20,131 | $18,444 | $17,623 | $15,114 | $19,687 | **$37,946** |
| Total Return | 101.3% | 84.4% | 76.2% | 51.1% | 96.9% | **279.5%** |
| CAGR | 12.4% | 10.7% | 9.9% | 7.1% | 12.0% | **24.9%** |
| Sharpe | 0.65 | 0.60 | 0.53 | 0.44 | 0.56 | **0.86** |
| Max Drawdown | -28.4% | -33.4% | -30.0% | **-25.8%** | -40.1% | -33.3% |
| Time in Market | 62% | 63% | 36% | 19% | 75% | 100% |

### Interpretation

Every strategy made a positive return, but all of them significantly underperformed simply buying and holding AAPL over the same period. Most did reduce volatility and drawdowns a little, but not by enough to make up for the time spent out of a strongly rising stock, which is why buy-and-hold also has the best risk-adjusted return (Sharpe).

This demonstrates why a backtesting strategy should be compared against an appropriate benchmark rather than judged solely on whether it makes a profit.

> The first version of this project reported a 116.05% strategy return against 363.72% for buy-and-hold. The numbers above differ because the backtester now uses split- and dividend-adjusted prices, starts on the first day of the period with indicators already warmed up, trades at the next day's open, and includes trading costs.

## Metrics

Final value, total return, CAGR, annualised volatility, Sharpe, Sortino, max drawdown, Calmar, number of trades, win rate and time in market.

## How the simulation works

- Signals are calculated from each day's close, and trades execute at the **next day's open**, so the backtest never uses information it wouldn't have had yet (no look-ahead bias).
- Whole shares by default (`--fractional` allows partial shares). Fees and slippage are charged on every buy and sell.
- Prices are split- and dividend-adjusted. About 400 extra days of history are downloaded before the start date so indicators are ready on day one.

## Technologies Used

* Python
* pandas
* NumPy
* Matplotlib
* yfinance
* pytest

## Tests

```bash
pytest
```

## Disclaimer

For education and research only. Backtests don't account for every real-world factor, and past performance does not guarantee future results. Not financial advice.
