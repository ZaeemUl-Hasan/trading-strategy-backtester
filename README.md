# Trading Strategy Backtester

Backtest classic trading strategies on any stock, ETF or crypto ticker and compare them against buy-and-hold, with realistic trading costs and proper risk metrics.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python backtester.py                          # 20/50 SMA crossover on AAPL since 2020
python backtester.py TSLA -s all              # compare every strategy on TSLA
python backtester.py MSFT -s sma -p fast=10 -p slow=30 --start 2018-01-01
python backtester.py BTC-USD -s momentum --fee 0.1 --slippage 0.1
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

Adding a strategy means writing one function in `strategies.py` that returns a 1/0 position for each day and registering it in `STRATEGIES`.

## Metrics

Final value, total return, CAGR, annualised volatility, Sharpe, Sortino, max drawdown, Calmar, number of trades, win rate and time in market.

## How the simulation works

- Signals are calculated from each day's close, and trades execute at the **next day's open**, so the backtest never uses information it wouldn't have had yet (no look-ahead bias).
- Whole shares only. Fees and slippage are charged on every buy and sell.
- Prices are split- and dividend-adjusted. About 400 extra days of history are downloaded before the start date so indicators are ready on day one.

## Tests

```bash
pytest
```

## Disclaimer

For education and research only. Backtests don't account for every real-world factor, and past performance does not guarantee future results. Not financial advice.
