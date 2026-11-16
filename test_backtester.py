import numpy as np
import pandas as pd
import pytest

from backtester import run_backtest, parse_params
from metrics import calculate_metrics, max_drawdown
from strategies import STRATEGIES


def make_data(prices):
    index = pd.bdate_range('2021-01-01', periods=len(prices))
    return pd.DataFrame({'Open': prices, 'Close': prices}, index=index)


def test_buy_and_hold_matches_price_change():
    data = make_data([100.0] * 5 + [200.0] * 5)
    positions = STRATEGIES['buyhold'](data)
    equity, trades, _ = run_backtest(data, positions, data.index[0], initial_cash=1000)
    # Signal acts next day: buys 10 shares at 100 on day 2, worth 2000 at the end
    assert equity.iloc[-1] == pytest.approx(2000)
    assert len(trades) == 1


def test_trades_happen_on_next_day_open():
    data = make_data([10.0, 10.0, 10.0, 10.0])
    data['Open'] = [10.0, 20.0, 20.0, 20.0]
    positions = pd.Series([1, 1, 1, 1], index=data.index)
    _, trades, _ = run_backtest(data, positions, data.index[0], initial_cash=100)
    assert trades[0]['entry_date'] == data.index[1]
    assert trades[0]['entry_price'] == 20.0


def test_fees_and_slippage_reduce_returns():
    data = make_data(list(np.linspace(100, 150, 60)))
    positions = STRATEGIES['buyhold'](data)
    free, _, _ = run_backtest(data, positions, data.index[0])
    costly, _, _ = run_backtest(data, positions, data.index[0], fee=0.01, slippage=0.01)
    assert costly.iloc[-1] < free.iloc[-1]


def test_fractional_shares_when_price_exceeds_cash():
    data = make_data([50000.0, 50000.0, 60000.0])
    positions = STRATEGIES['buyhold'](data)
    whole, _, _ = run_backtest(data, positions, data.index[0], initial_cash=10000)
    fractional, _, _ = run_backtest(data, positions, data.index[0], initial_cash=10000, fractional=True)
    assert whole.iloc[-1] == 10000
    assert fractional.iloc[-1] == pytest.approx(12000)


def test_round_trip_pnl_and_win_rate():
    data = make_data([100.0, 100.0, 110.0, 110.0])
    positions = pd.Series([1, 0, 0, 0], index=data.index)
    equity, trades, exposure = run_backtest(data, positions, data.index[0], initial_cash=1000)
    # Buy at 100 on day 2, sell at 110 on day 3
    assert trades[0]['pnl'] == pytest.approx(100)
    metrics = calculate_metrics(equity, trades, exposure, 1000)
    assert metrics['Win Rate (%)'] == 100


def test_max_drawdown():
    equity = pd.Series([100, 120, 60, 90])
    assert max_drawdown(equity) == pytest.approx(-50)


@pytest.mark.parametrize('name', list(STRATEGIES))
def test_strategies_return_valid_positions(name):
    rng = np.random.default_rng(0)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 300)))
    positions = STRATEGIES[name](make_data(prices))
    assert len(positions) == 300
    assert set(positions.unique()) <= {0, 1}


def test_parse_params():
    assert parse_params(['fast=10', 'std=1.5']) == {'fast': 10, 'std': 1.5}
