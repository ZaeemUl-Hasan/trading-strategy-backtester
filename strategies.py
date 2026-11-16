import pandas as pd

# Each strategy takes a DataFrame with a 'Close' column and returns a Series
# of target positions for each day: 1 = hold the stock, 0 = hold cash.
# The engine acts on the signal the NEXT day, so strategies never need to
# worry about look-ahead bias themselves.


def sma_crossover(data, fast=20, slow=50):
    """Hold while the fast simple moving average is above the slow one."""
    fast_ma = data['Close'].rolling(window=fast).mean()
    slow_ma = data['Close'].rolling(window=slow).mean()
    return (fast_ma > slow_ma).astype(int)


def ema_crossover(data, fast=12, slow=26):
    """Same idea as the SMA crossover, but exponential averages react faster."""
    fast_ma = data['Close'].ewm(span=fast, adjust=False).mean()
    slow_ma = data['Close'].ewm(span=slow, adjust=False).mean()
    return (fast_ma > slow_ma).astype(int)


def rsi(data, period=14, oversold=30, overbought=70):
    """Buy when RSI drops below 'oversold', sell when it rises above 'overbought'."""
    change = data['Close'].diff()
    gain = change.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = -change.clip(upper=0).ewm(alpha=1 / period, adjust=False).mean()
    rsi_values = 100 - 100 / (1 + gain / loss)

    # Mark entry (1) and exit (0) days, then carry the last decision forward
    position = pd.Series(float('nan'), index=data.index)
    position[rsi_values < oversold] = 1
    position[rsi_values > overbought] = 0
    return position.ffill().fillna(0).astype(int)


def bollinger(data, window=20, num_std=2):
    """Mean reversion: buy below the lower band, sell once price is back above the middle."""
    middle = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    lower = middle - num_std * std

    position = pd.Series(float('nan'), index=data.index)
    position[data['Close'] < lower] = 1
    position[data['Close'] > middle] = 0
    return position.ffill().fillna(0).astype(int)


def momentum(data, lookback=126):
    """Hold while the price is higher than it was 'lookback' days ago (~6 months)."""
    past_return = data['Close'].pct_change(periods=lookback)
    return (past_return > 0).astype(int)


def buy_and_hold(data):
    """Benchmark: always hold the stock."""
    return pd.Series(1, index=data.index)


STRATEGIES = {
    'sma': sma_crossover,
    'ema': ema_crossover,
    'rsi': rsi,
    'bollinger': bollinger,
    'momentum': momentum,
    'buyhold': buy_and_hold,
}
