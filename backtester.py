#!/usr/bin/env python3
import argparse
import json
import sys

import pandas as pd
import matplotlib.pyplot as plt

from metrics import calculate_metrics
from strategies import STRATEGIES

# Extra history downloaded before the start date so indicators like the
# 50-day SMA are already "warmed up" on the first day of the backtest
WARMUP_DAYS = 400


def load_data(ticker, start, end, csv_path=None):
    """Load daily OHLC data from Yahoo Finance, or from a CSV with Date/Open/Close columns."""
    if csv_path:
        data = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
    else:
        import yfinance as yf
        warmup_start = pd.Timestamp(start) - pd.Timedelta(days=WARMUP_DAYS)
        data = yf.download(ticker, start=warmup_start, end=end, auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError(f"No data found for '{ticker}'. Check the ticker symbol and dates.")
        # Remove multi-level columns
        data.columns = data.columns.get_level_values(0)

    if 'Open' not in data.columns:
        data['Open'] = data['Close']
    return data.sort_index()


def run_backtest(data, positions, start, initial_cash=10000, fee=0.0, slippage=0.0, fractional=False):
    """
    Simulate trading from 'start' onwards, in whole shares unless 'fractional'
    is set (needed for crypto or very high-priced stocks).

    positions: Series of 1 (hold) / 0 (cash) decided at each day's close.
    The trade happens at the NEXT day's open, so we never trade on
    information we wouldn't have had yet.
    fee, slippage: fractions of trade value, e.g. 0.001 = 0.1%.
    """
    signal = positions.shift(1).fillna(0)
    window = data[data.index >= pd.Timestamp(start)]
    if len(window) < 2:
        raise ValueError("Not enough data in the chosen date range.")

    cash = initial_cash
    shares = 0
    trades = []
    values = []
    days_invested = 0
    missed_buys = 0

    for day in window.index:
        open_price = window.loc[day, 'Open']
        close_price = window.loc[day, 'Close']

        if signal[day] == 1 and shares == 0:
            # Buy: slippage makes us pay a bit more than the quoted price
            buy_price = open_price * (1 + slippage)
            bought_shares = cash / (buy_price * (1 + fee))
            if not fractional:
                bought_shares = int(bought_shares)
            if bought_shares == 0:
                missed_buys += 1
            else:
                cost = bought_shares * buy_price
                cash -= cost * (1 + fee)
                shares = bought_shares
                trades.append({'entry_date': day, 'entry_price': buy_price,
                               'cost': cost * (1 + fee), 'exit_date': None,
                               'exit_price': None, 'pnl': None})

        elif signal[day] == 0 and shares > 0:
            # Sell: slippage means we receive a bit less
            sell_price = open_price * (1 - slippage)
            proceeds = shares * sell_price * (1 - fee)
            cash += proceeds
            trades[-1].update({'exit_date': day, 'exit_price': sell_price,
                               'pnl': proceeds - trades[-1]['cost']})
            shares = 0

        if shares > 0:
            days_invested += 1

        #Calculate portfolio value
        values.append(cash + shares * close_price)

    if missed_buys:
        print(f"Warning: {missed_buys} buy signal(s) skipped because cash was below one share's price. "
              "Use --fractional for crypto or high-priced stocks.", file=sys.stderr)

    # Mark any still-open trade to market so it counts in the win rate
    if shares > 0:
        trades[-1]['pnl'] = shares * window['Close'].iloc[-1] - trades[-1]['cost']

    equity = pd.Series(values, index=window.index)
    exposure = days_invested / len(window)
    return equity, trades, exposure


def parse_params(param_list):
    """Turn ['fast=10', 'slow=30'] into {'fast': 10, 'slow': 30}."""
    params = {}
    for item in param_list or []:
        key, value = item.split('=', 1)
        number = float(value)
        params[key] = int(number) if number.is_integer() else number
    return params


def plot_results(ticker, data, results, main_strategy):
    fig, (ax_equity, ax_drawdown, ax_price) = plt.subplots(
        3, 1, figsize=(11, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1.5, 2]})

    for name, result in results.items():
        equity = result['equity']
        width = 2 if name == main_strategy else 1
        ax_equity.plot(equity, label=name, linewidth=width)
        ax_drawdown.plot((equity / equity.cummax() - 1) * 100, label=name, linewidth=width)

    ax_equity.set_title(f'{ticker}: Portfolio Value Over Time')
    ax_equity.set_ylabel('Portfolio Value ($)')
    ax_equity.legend()
    ax_drawdown.set_title('Drawdown')
    ax_drawdown.set_ylabel('Drawdown (%)')

    # Price chart with the main strategy's buys and sells marked
    window = results[main_strategy]['equity'].index
    ax_price.plot(data.loc[window, 'Close'], color='grey', label='Close')
    trades = results[main_strategy]['trades']
    ax_price.scatter([t['entry_date'] for t in trades], [t['entry_price'] for t in trades],
                     marker='^', color='green', label='Buy', zorder=3)
    closed = [t for t in trades if t['exit_date'] is not None]
    ax_price.scatter([t['exit_date'] for t in closed], [t['exit_price'] for t in closed],
                     marker='v', color='red', label='Sell', zorder=3)
    ax_price.set_title(f'{main_strategy} trades')
    ax_price.set_ylabel('Price ($)')
    ax_price.legend()

    fig.tight_layout()
    return fig


def main(argv=None):
    parser = argparse.ArgumentParser(description='Backtest trading strategies against buy-and-hold.')
    parser.add_argument('ticker', nargs='?', default='AAPL', help='Ticker symbol, e.g. AAPL, MSFT, BTC-USD')
    parser.add_argument('-s', '--strategy', default='sma',
                        help=f"One of: {', '.join(STRATEGIES)}, or 'all' to compare every strategy")
    parser.add_argument('-p', '--param', action='append',
                        help='Strategy parameter, e.g. -p fast=10 -p slow=30 (can repeat)')
    parser.add_argument('--start', default='2020-01-01', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', default=None, help='Backtest end date (default: today)')
    parser.add_argument('--cash', type=float, default=10000, help='Starting cash (default: 10000)')
    parser.add_argument('--fee', type=float, default=0.05, help='Fee per trade in %% (default: 0.05)')
    parser.add_argument('--slippage', type=float, default=0.05, help='Slippage per trade in %% (default: 0.05)')
    parser.add_argument('--fractional', action='store_true',
                        help='Allow buying fractions of a share (use for crypto or high-priced stocks)')
    parser.add_argument('--risk-free', type=float, default=0.0, help='Annual risk-free rate in %% for Sharpe')
    parser.add_argument('--csv', help='Load prices from a CSV (Date, Open, Close) instead of downloading')
    parser.add_argument('--json', action='store_true', help='Print results as JSON (handy for scripts/agents)')
    parser.add_argument('--no-plot', action='store_true', help="Don't show charts")
    parser.add_argument('--save-plot', help='Save the chart to this file, e.g. results.png')
    args = parser.parse_args(argv)

    if args.strategy != 'all' and args.strategy not in STRATEGIES:
        parser.error(f"Unknown strategy '{args.strategy}'. Choose from: {', '.join(STRATEGIES)}, all")

    try:
        data = load_data(args.ticker, args.start, args.end, args.csv)
    except ValueError as error:
        sys.exit(f"Error: {error}")

    # Always include buy-and-hold so there's a benchmark to compare against
    if args.strategy == 'all':
        names = list(STRATEGIES)
    else:
        names = [args.strategy] if args.strategy == 'buyhold' else [args.strategy, 'buyhold']
    params = parse_params(args.param)

    results = {}
    for name in names:
        strategy_params = params if name == args.strategy else {}
        positions = STRATEGIES[name](data, **strategy_params)
        equity, trades, exposure = run_backtest(
            data, positions, args.start, args.cash, args.fee / 100, args.slippage / 100, args.fractional)
        results[name] = {
            'equity': equity,
            'trades': trades,
            'metrics': calculate_metrics(equity, trades, exposure, args.cash, args.risk_free / 100),
        }

    first_day = next(iter(results.values()))['equity'].index
    period = f"{first_day[0].date()} to {first_day[-1].date()}"

    if args.json:
        output = {'ticker': args.ticker, 'period': period, 'initial_cash': args.cash,
                  'fee_pct': args.fee, 'slippage_pct': args.slippage, 'params': params,
                  'results': {name: {k: round(float(v), 4) for k, v in r['metrics'].items()}
                              for name, r in results.items()}}
        print(json.dumps(output, indent=2))
    else:
        table = pd.DataFrame({name: r['metrics'] for name, r in results.items()})
        print(f"\n{args.ticker}  |  {period}  |  start ${args.cash:,.0f}  |  "
              f"fee {args.fee}%  slippage {args.slippage}%\n")
        print(table.round(2).to_string())
        print("\nPast performance does not guarantee future results. Not financial advice.")

    if not args.no_plot or args.save_plot:
        main_strategy = names[0]
        fig = plot_results(args.ticker, data, results, main_strategy)
        if args.save_plot:
            fig.savefig(args.save_plot, dpi=120)
        if not args.no_plot:
            plt.show()

    return results


if __name__ == '__main__':
    main()
