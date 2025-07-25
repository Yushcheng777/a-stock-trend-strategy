"""
End-to-end tests for parallel_backtest.py
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parallel_backtest import (
    run_single_backtest,
    generate_parameter_grid,
    run_parallel_backtest,
    fetch_stock_data,
    analyze_results
)


class TestParallelBacktest:
    """Test class for parallel backtesting functionality."""

    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data for testing."""
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
    def sample_strategy_params(self):
        """Sample strategy parameters for testing."""
        return {
            'sma_short': 10,
            'sma_long': 30,
            'rsi_period': 14,
            'rsi_oversold': 30.0,
            'rsi_overbought': 70.0
        }

    def test_generate_parameter_grid(self):
        """Test parameter grid generation."""
        param_grid = generate_parameter_grid()

        # Should generate multiple parameter combinations
        assert len(param_grid) > 0

        # Each combination should be a dictionary with required keys
        required_keys = ['sma_short', 'sma_long', 'rsi_period', 'rsi_oversold', 'rsi_overbought']
        for params in param_grid:
            assert isinstance(params, dict)
            for key in required_keys:
                assert key in params

            # Ensure short SMA is less than long SMA
            assert params['sma_short'] < params['sma_long']

            # Ensure RSI thresholds make sense
            assert params['rsi_oversold'] < params['rsi_overbought']
            assert 0 <= params['rsi_oversold'] <= 50
            assert 50 <= params['rsi_overbought'] <= 100

    @patch('parallel_backtest.fetch_stock_data')
    def test_run_single_backtest_success(self, mock_fetch, sample_stock_data, sample_strategy_params):
        """Test successful single backtest execution."""
        # Mock the data fetching
        mock_fetch.return_value = sample_stock_data

        # Prepare test parameters
        params = ('AAPL', sample_strategy_params, '2023-01-01', '2023-12-31')

        # Run single backtest
        result = run_single_backtest(params)

        # Check result structure
        expected_keys = [
            'ticker', 'start_date', 'end_date', 'total_return',
            'total_trades', 'win_rate', 'final_capital'
        ]
        for key in expected_keys:
            assert key in result

        # Check strategy parameters are included
        for key, value in sample_strategy_params.items():
            assert result[key] == value

        # Check data types and ranges
        assert isinstance(result['total_return'], (int, float))
        assert isinstance(result['total_trades'], (int, np.integer))
        assert isinstance(result['win_rate'], (int, float))
        assert isinstance(result['final_capital'], (int, float))
        assert result['ticker'] == 'AAPL'
        assert 0 <= result['win_rate'] <= 1
        assert result['total_trades'] >= 0

    @patch('parallel_backtest.fetch_stock_data')
    def test_run_single_backtest_no_data(self, mock_fetch, sample_strategy_params):
        """Test single backtest with no data available."""
        # Mock empty data
        mock_fetch.return_value = pd.DataFrame()

        params = ('INVALID', sample_strategy_params, '2023-01-01', '2023-12-31')
        result = run_single_backtest(params)

        # Should handle gracefully and return error
        assert 'error' in result
        assert result['ticker'] == 'INVALID'
        assert result['error'] == 'No data available'

    @patch('parallel_backtest.fetch_stock_data')
    def test_run_single_backtest_exception(self, mock_fetch, sample_strategy_params):
        """Test single backtest with exception during execution."""
        # Mock exception during data fetch
        mock_fetch.side_effect = Exception("Network error")

        params = ('AAPL', sample_strategy_params, '2023-01-01', '2023-12-31')
        result = run_single_backtest(params)

        # Should handle exception gracefully
        assert 'error' in result
        assert result['ticker'] == 'AAPL'
        assert 'Network error' in result['error']

    @patch('parallel_backtest.fetch_stock_data')
    def test_run_parallel_backtest(self, mock_fetch, sample_stock_data):
        """Test parallel backtest execution with mocked data."""
        # Mock the data fetching to return our sample data
        mock_fetch.return_value = sample_stock_data

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            # Run parallel backtest with limited parameters for faster testing
            with patch('parallel_backtest.generate_parameter_grid') as mock_grid:
                # Use just 2 parameter combinations for faster testing
                mock_grid.return_value = [
                    {'sma_short': 10, 'sma_long': 30, 'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70},
                    {'sma_short': 5, 'sma_long': 20, 'rsi_period': 10, 'rsi_oversold': 25, 'rsi_overbought': 75}
                ]

                result_df = run_parallel_backtest(
                    tickers=['AAPL', 'MSFT'],
                    start_date='2023-01-01',
                    end_date='2023-12-31',
                    max_workers=2,
                    output_file=output_file
                )

            # Check that results DataFrame is created
            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) == 4  # 2 tickers × 2 parameter combinations

            # Check required columns exist
            required_columns = [
                'ticker', 'total_return', 'total_trades', 'win_rate', 'final_capital',
                'sma_short', 'sma_long', 'rsi_period', 'rsi_oversold', 'rsi_overbought'
            ]
            for col in required_columns:
                assert col in result_df.columns

            # Check that output file was created
            assert os.path.exists(output_file)

            # Read the saved file and verify it matches
            saved_df = pd.read_csv(output_file)
            assert len(saved_df) == len(result_df)

        finally:
            # Clean up temporary file
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_analyze_results(self, capsys):
        """Test results analysis functionality."""
        # Create sample results DataFrame
        results_data = {
            'ticker': ['AAPL', 'AAPL', 'MSFT', 'MSFT'],
            'total_return': [0.15, 0.10, 0.20, -0.05],
            'win_rate': [0.6, 0.5, 0.7, 0.4],
            'total_trades': [10, 8, 12, 6],
            'sma_short': [10, 5, 10, 5],
            'sma_long': [30, 20, 30, 20],
            'rsi_period': [14, 10, 14, 10],
            'rsi_oversold': [30, 25, 30, 25],
            'rsi_overbought': [70, 75, 70, 75]
        }
        df_results = pd.DataFrame(results_data)

        # Analyze results
        analyze_results(df_results)

        # Capture output
        captured = capsys.readouterr()

        # Check that analysis output contains expected information
        assert "BACKTEST ANALYSIS" in captured.out
        assert "Successful backtests: 4" in captured.out
        assert "Average return:" in captured.out
        assert "Best return:" in captured.out
        assert "Top 5 Parameter Combinations:" in captured.out

    def test_analyze_results_with_errors(self, capsys):
        """Test results analysis with some failed backtests."""
        # Create results with some errors
        results_data = {
            'ticker': ['AAPL', 'INVALID', 'MSFT'],
            'total_return': [0.15, np.nan, 0.10],
            'win_rate': [0.6, np.nan, 0.5],
            'total_trades': [10, np.nan, 8],
            'error': [np.nan, 'No data available', np.nan]
        }
        df_results = pd.DataFrame(results_data)

        analyze_results(df_results)
        captured = capsys.readouterr()

        # Should handle errors gracefully
        assert "Successful backtests: 2" in captured.out
        assert "Failed backtests: 1" in captured.out

    def test_analyze_results_empty(self, capsys):
        """Test results analysis with no successful backtests."""
        # Create DataFrame with only failed results
        results_data = {
            'ticker': ['INVALID1', 'INVALID2'],
            'total_return': [np.nan, np.nan],
            'error': ['No data', 'Network error']
        }
        df_results = pd.DataFrame(results_data)

        analyze_results(df_results)
        captured = capsys.readouterr()

        assert "No successful backtests to analyze." in captured.out

    @patch('yfinance.Ticker')
    def test_fetch_stock_data_success(self, mock_ticker):
        """Test successful stock data fetching."""
        # Mock yfinance Ticker
        mock_stock = MagicMock()
        mock_ticker.return_value = mock_stock

        # Create sample data
        sample_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101],
            'Close': [100.5, 101.5, 102.5],
            'Volume': [100000, 110000, 120000]
        })
        mock_stock.history.return_value = sample_data

        # Test data fetching
        result = fetch_stock_data('AAPL', '2023-01-01', '2023-12-31')

        # Verify the call and result
        mock_ticker.assert_called_once_with('AAPL')
        mock_stock.history.assert_called_once_with(start='2023-01-01', end='2023-12-31')
        pd.testing.assert_frame_equal(result, sample_data)

    @patch('yfinance.Ticker')
    def test_fetch_stock_data_exception(self, mock_ticker):
        """Test stock data fetching with exception."""
        # Mock exception
        mock_ticker.side_effect = Exception("API error")

        result = fetch_stock_data('INVALID', '2023-01-01', '2023-12-31')

        # Should return empty DataFrame on error
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_integration_with_small_dataset(self):
        """Integration test with a small, controlled dataset."""
        # This test runs the actual code path without mocking
        # but with minimal data to ensure everything works together

        # Create a simple test case that should work
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = pd.Series(range(100, 150), index=dates)  # Simple uptrend

        test_data = pd.DataFrame({
            'Open': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': [100000] * 50
        })

        # Test parameters
        test_params = {
            'sma_short': 5,
            'sma_long': 10,
            'rsi_period': 7,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }

        # Mock fetch_stock_data for this test
        with patch('parallel_backtest.fetch_stock_data') as mock_fetch:
            mock_fetch.return_value = test_data

            # Test single backtest
            params = ('TEST', test_params, '2023-01-01', '2023-12-31')
            result = run_single_backtest(params)

            # Should complete successfully
            assert 'error' not in result
            assert result['ticker'] == 'TEST'
            assert isinstance(result['total_return'], (int, float))
            assert isinstance(result['final_capital'], (int, float))
