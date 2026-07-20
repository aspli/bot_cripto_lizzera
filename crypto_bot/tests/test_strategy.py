import pytest
import pandas as pd
import numpy as np
from app.strategies.trend_following import TrendFollowingStrategy

@pytest.fixture
def sample_data():
    # Create 250 rows of dummy data
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=250, freq="1h")

    # Simulate an uptrend to trigger buy
    close_prices = np.linspace(100, 200, 250) + np.random.normal(0, 2, 250)

    df = pd.DataFrame({
        "timestamp": dates,
        "open": close_prices - 1,
        "high": close_prices + 2,
        "low": close_prices - 2,
        "close": close_prices,
        "volume": np.random.randint(100, 1000, 250)
    })
    return df

def test_trend_following_strategy_signals(sample_data):
    strategy = TrendFollowingStrategy()
    df_signals = strategy.generate_signals(sample_data)

    assert "signal" in df_signals.columns
    assert "EMA_20" in df_signals.columns
    assert "EMA_50" in df_signals.columns
    assert "EMA_200" in df_signals.columns
    assert "RSI" in df_signals.columns

    # Check that signals contain 1, 0, or -1
    unique_signals = df_signals['signal'].unique()
    for sig in unique_signals:
        assert sig in [1, 0, -1]

def test_trend_following_strategy_not_enough_data():
    df = pd.DataFrame({"close": [1, 2, 3]})
    strategy = TrendFollowingStrategy()
    df_signals = strategy.generate_signals(df)
    assert all(df_signals['signal'] == 0)
