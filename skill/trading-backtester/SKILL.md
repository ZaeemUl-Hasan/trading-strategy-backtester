---
name: trading-backtester
description: Backtests trading strategies (SMA/EMA crossover, RSI, Bollinger Bands, momentum) on any stock, ETF or crypto ticker and compares them against buy-and-hold, with fees, slippage and risk metrics like Sharpe ratio and max drawdown. Use when the user asks to backtest a trading strategy, compare strategies, or check whether a strategy beats buy-and-hold on a ticker such as AAPL, SPY or BTC-USD.
argument-hint: "[ticker] [strategy] [start date]"
---

# Trading Strategy Backtester

Runs a daily, long-only backtest on historical prices from Yahoo Finance and reports performance against a buy-and-hold benchmark.

All paths below are relative to this skill's directory.

## Steps

1. **Check dependencies.** Run `python3 -c "import pandas, numpy, matplotlib, yfinance"`. If it fails, tell the user which packages are missing and, with their OK, run `python3 -m pip install -r scripts/requirements.txt`.

2. **Work out the inputs** from the user's request. Use these defaults for anything they don't say, and mention the defaults you used:
   - ticker: `AAPL` (Yahoo Finance symbols, e.g. `MSFT`, `SPY`, `BTC-USD`, `VOD.L`)
   - strategy: `all` if they want a comparison or don't name one, otherwise one of `sma`, `ema`, `rsi`, `bollinger`, `momentum`, `buyhold`
   - start `2020-01-01`, end today, cash `10000`, fee `0.05`%, slippage `0.05`%

3. **Run the backtest** with JSON output:

   ```bash
   python3 scripts/backtester.py <TICKER> -s <STRATEGY> --start <YYYY-MM-DD> --json --no-plot
   ```

   **For crypto (e.g. `BTC-USD`) or any asset priced above the starting cash, always add `--fractional`**, otherwise no shares can be bought. If stderr shows "buy signal(s) skipped", rerun with `--fractional`.

   Optional flags: `--end YYYY-MM-DD`, `--cash 5000`, `--fee 0.1`, `--slippage 0.1`, `--risk-free 4` (annual %, for Sharpe/Sortino), and strategy parameters with repeated `-p key=value`.

   If the user wants a chart, add `--save-plot <ticker>_backtest.png` (saved in the current directory), then tell them where it is.

4. **Explain the results** (see below).

## Strategy parameters

| Strategy | What it does | Parameters (defaults) |
|---|---|---|
| `sma` | Hold while the fast SMA is above the slow SMA | `fast=20`, `slow=50` |
| `ema` | Same with exponential moving averages | `fast=12`, `slow=26` |
| `rsi` | Buy when RSI < oversold, sell when RSI > overbought | `period=14`, `oversold=30`, `overbought=70` |
| `bollinger` | Buy below the lower band, sell back above the middle band | `window=20`, `num_std=2` |
| `momentum` | Hold while price is above its level `lookback` days ago | `lookback=126` |
| `buyhold` | Always invested (benchmark, always included automatically) | none |

Example: `python3 scripts/backtester.py MSFT -s sma -p fast=10 -p slow=30 --json --no-plot`

## Output

The JSON contains `ticker`, `period`, `initial_cash`, `fee_pct`, `slippage_pct`, `params` and a `results` object keyed by strategy name. Each result has: `Final Value ($)`, `Total Return (%)`, `CAGR (%)`, `Volatility (%)`, `Sharpe`, `Sortino`, `Max Drawdown (%)`, `Calmar`, `Trades`, `Win Rate (%)` and `Time in Market (%)`.

## Explaining the results

- Show a compact table: Total Return, CAGR, Sharpe, Max Drawdown and Time in Market for each strategy.
- **Always compare against buy-and-hold.** Say plainly whether each strategy beat it on return and on risk-adjusted return (Sharpe), and whether it reduced drawdown.
- Name the best strategy by Sharpe ratio as well as by total return if they differ.
- Note any caveats that apply: a single ticker and period, default parameters, and that strongly rising markets tend to favour buy-and-hold.
- If the user asks you to tune parameters to find the "best" ones, warn that picking parameters by past performance overfits and rarely holds up out of sample.
- End with: "Backtests are simulations on past data and don't guarantee future results. This is not financial advice."

## How the simulation works

- Signals use each day's close, and trades execute at the next day's open (no look-ahead bias).
- Whole shares by default (`--fractional` allows partial shares), long-only, all-in or all-out. Fees and slippage apply to every buy and sell.
- Prices are split- and dividend-adjusted. About 400 days of extra history are loaded so indicators are ready on the start date.

## Errors

- `No data found for '<ticker>'`: the symbol is wrong or has no data for those dates. Suggest the correct Yahoo Finance symbol (e.g. `BRK-B`, `BTC-USD`, `.L` for London listings).
- `Not enough data in the chosen date range`: ask for a longer period.
- Network errors from Yahoo Finance: retry once, then tell the user the data source is unavailable. If they have their own price data, it can be loaded with `--csv file.csv` (columns `Date`, `Open`, `Close`).
