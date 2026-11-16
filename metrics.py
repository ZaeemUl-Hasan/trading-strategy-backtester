import numpy as np
import pandas as pd

TRADING_DAYS = 252


def periods_per_year(dates):
    """Price bars per year: ~252 for stocks, ~365 for crypto, which trades every day."""
    if isinstance(dates, pd.DatetimeIndex) and len(dates) > 1:
        span_years = (dates[-1] - dates[0]).days / 365.25
        if span_years > 0:
            return (len(dates) - 1) / span_years
    return TRADING_DAYS


def max_drawdown(equity):
    """Largest peak-to-trough fall, as a negative percentage."""
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1
    return drawdown.min() * 100


def calculate_metrics(equity, trades, exposure, initial_cash, risk_free_rate=0.0):
    """Summarise an equity curve (a Series of daily portfolio values)."""
    per_year = periods_per_year(equity.index)
    # Start the curve from the initial cash so day one's move is counted
    equity = pd.concat([pd.Series([initial_cash]), equity.reset_index(drop=True)])
    daily_returns = equity.pct_change().dropna()
    years = len(daily_returns) / per_year

    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
    cagr = ((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else 0.0
    volatility = daily_returns.std() * np.sqrt(per_year) * 100

    # Sharpe: return per unit of total risk. Sortino: per unit of downside risk only.
    excess = daily_returns - risk_free_rate / per_year
    sharpe = excess.mean() / daily_returns.std() * np.sqrt(per_year) if daily_returns.std() > 0 else 0.0
    downside = daily_returns[daily_returns < 0].std()
    sortino = excess.mean() / downside * np.sqrt(per_year) if downside > 0 else 0.0

    mdd = max_drawdown(equity)
    calmar = cagr / abs(mdd) if mdd < 0 else 0.0

    # Open trades count using their value on the last day
    wins = [t for t in trades if t['pnl'] > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0

    return {
        'Final Value ($)': equity.iloc[-1],
        'Total Return (%)': total_return,
        'CAGR (%)': cagr,
        'Volatility (%)': volatility,
        'Sharpe': sharpe,
        'Sortino': sortino,
        'Max Drawdown (%)': mdd,
        'Calmar': calmar,
        'Trades': len(trades),
        'Win Rate (%)': win_rate,
        'Time in Market (%)': exposure * 100,
    }
