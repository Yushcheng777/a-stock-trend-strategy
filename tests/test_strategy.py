"""
Unit tests for EnhancedAStockTrendStrategy
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from strategy import EnhancedAStockTrendStrategy


class TestEnhancedAStockTrendStrategy:
    """Test class for EnhancedAStockTrendStrategy."""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)  # For reproducible tests

        # Generate realistic stock price data
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = base_price * np.cumprod(1 + returns)

        data = pd.DataFrame({
            'Open': prices * (1 + np.random.normal(0, 0.005, 100)),
            'High': prices * (1 + np.abs(np.random.normal(0, 0.01, 100))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, 100))),
            'Close': prices,
            'Volume': np.random.randint(100000, 1000000, 100)
        }, index=dates)

        return data

    @pytest.fixture
    def strategy(self):
        """Create strategy instance with default parameters."""
        return EnhancedAStockTrendStrategy()

    def test_strategy_initialization(self):
        """Test strategy initialization with default and custom parameters."""
        # Test default initialization
        strategy = EnhancedAStockTrendStrategy()
        assert strategy.sma_short == 10
        assert strategy.sma_long == 30
        assert strategy.rsi_period == 14
        assert strategy.rsi_oversold == 30.0
        assert strategy.rsi_overbought == 70.0

        # Test custom initialization
        strategy_custom = EnhancedAStockTrendStrategy(
            sma_short=5, sma_long=20, rsi_period=10,
            rsi_oversold=25.0, rsi_overbought=75.0
        )
        assert strategy_custom.sma_short == 5
        assert strategy_custom.sma_long == 20
        assert strategy_custom.rsi_period == 10
        assert strategy_custom.rsi_oversold == 25.0
        assert strategy_custom.rsi_overbought == 75.0

    def test_calculate_sma(self, strategy, sample_data):
        """Test Simple Moving Average calculation."""
        prices = sample_data['Close']

        # Test short SMA
        sma_short = strategy.calculate_sma(prices, 10)
        assert len(sma_short) == len(prices)
        assert not sma_short.iloc[:9].notna().any()  # First 9 values should be NaN
        assert sma_short.iloc[9:].notna().all()  # Remaining values should not be NaN

        # Test that SMA is actually the mean of the window
        expected_sma_10 = prices.iloc[0:10].mean()
        assert abs(sma_short.iloc[9] - expected_sma_10) < 1e-10

        # Test long SMA
        sma_long = strategy.calculate_sma(prices, 30)
        assert len(sma_long) == len(prices)
        assert not sma_long.iloc[:29].notna().any()  # First 29 values should be NaN
        assert sma_long.iloc[29:].notna().all()  # Remaining values should not be NaN

    def test_calculate_rsi(self, strategy, sample_data):
        """Test RSI calculation."""
        prices = sample_data['Close']

        rsi = strategy.calculate_rsi(prices, 14)
        assert len(rsi) == len(prices)

        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

        # First 13 values should be NaN (period for diff and rolling window)
        assert rsi.iloc[:13].isna().all()
        assert rsi.iloc[13:].notna().all()

        # Test with different period
        rsi_10 = strategy.calculate_rsi(prices, 10)
        assert rsi_10.iloc[:9].isna().all()
        assert rsi_10.iloc[9:].notna().all()

    def test_calculate_indicators(self, strategy, sample_data):
        """Test indicator calculation method."""
        result = strategy.calculate_indicators(sample_data)

        # Check that all original columns are preserved
        for col in sample_data.columns:
            assert col in result.columns

        # Check that new indicator columns are added
        assert 'SMA_Short' in result.columns
        assert 'SMA_Long' in result.columns
        assert 'RSI' in result.columns

        # Check data integrity
        assert len(result) == len(sample_data)
        pd.testing.assert_frame_equal(result[sample_data.columns], sample_data)

    def test_generate_signals(self, strategy, sample_data):
        """Test signal generation."""
        result = strategy.generate_signals(sample_data)

        # Check that signal columns are added
        assert 'Signal' in result.columns
        assert 'Position' in result.columns

        # Check signal values are valid
        assert result['Signal'].isin([-1, 0, 1]).all()

        # Check position values are valid (should be 0 or 1)
        assert result['Position'].isin([0, 1]).all()

        # Position should be cumulative and clipped
        assert (result['Position'] >= 0).all()
        assert (result['Position'] <= 1).all()

    def test_signal_consistency(self, strategy):
        """Test that signals are generated consistently."""
        # Create deterministic test data
        dates = pd.date_range('2023-01-01', periods=50, freq='D')

        # Create trending up data to trigger buy signals
        prices = pd.Series(range(50, 100), index=dates)
        data = pd.DataFrame({
            'Open': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': [100000] * 50
        })

        # Run signal generation multiple times
        result1 = strategy.generate_signals(data)
        result2 = strategy.generate_signals(data)

        # Results should be identical
        pd.testing.assert_series_equal(result1['Signal'], result2['Signal'])
        pd.testing.assert_series_equal(result1['Position'], result2['Position'])

    def test_backtest(self, strategy, sample_data):
        """Test backtest functionality."""
        result = strategy.backtest(sample_data, initial_capital=10000.0)

        # Check return structure
        expected_keys = ['total_return', 'total_trades', 'win_rate', 'final_capital', 'data']
        for key in expected_keys:
            assert key in result

        # Check data types
        assert isinstance(result['total_return'], (int, float))
        assert isinstance(result['total_trades'], (int, np.integer))
        assert isinstance(result['win_rate'], (int, float))
        assert isinstance(result['final_capital'], (int, float))
        assert isinstance(result['data'], pd.DataFrame)

        # Check logical constraints
        assert result['total_trades'] >= 0
        assert 0 <= result['win_rate'] <= 1
        assert result['final_capital'] > 0

        # Check that backtest data contains required columns
        backtest_data = result['data']
        required_columns = ['Returns', 'Strategy_Returns', 'Cumulative_Returns', 'Cumulative_Strategy_Returns']
        for col in required_columns:
            assert col in backtest_data.columns

    def test_different_parameters(self, sample_data):
        """Test strategy with different parameter combinations."""
        params_list = [
            {'sma_short': 5, 'sma_long': 15},
            {'sma_short': 20, 'sma_long': 50},
            {'rsi_period': 10, 'rsi_oversold': 20, 'rsi_overbought': 80}
        ]

        for params in params_list:
            strategy = EnhancedAStockTrendStrategy(**params)
            result = strategy.generate_signals(sample_data)

            # Should always produce valid signals
            assert 'Signal' in result.columns
            assert 'Position' in result.columns
            assert result['Signal'].isin([-1, 0, 1]).all()
            assert result['Position'].isin([0, 1]).all()

    def test_empty_data_handling(self, strategy):
        """Test strategy behavior with empty data."""
        empty_data = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])

        # Should handle empty data gracefully
        result = strategy.calculate_indicators(empty_data)
        assert len(result) == 0
        assert 'SMA_Short' in result.columns
        assert 'SMA_Long' in result.columns
        assert 'RSI' in result.columns

    def test_insufficient_data(self, strategy):
        """Test strategy with insufficient data for indicators."""
        # Create data with only 5 rows (less than default SMA long period)
        short_data = pd.DataFrame({
            'Open': [100, 101, 102, 103, 104],
            'High': [101, 102, 103, 104, 105],
            'Low': [99, 100, 101, 102, 103],
            'Close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'Volume': [100000] * 5
        })

        result = strategy.generate_signals(short_data)

        # Should not crash and should produce output with correct structure
        assert len(result) == 5
        assert 'Signal' in result.columns
        assert 'Position' in result.columns

        # Most indicators will be NaN due to insufficient data
        assert result['SMA_Long'].isna().all()  # 30-period SMA with only 5 data points
