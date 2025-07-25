"""
Unit tests for the DualMAOptimizedStrategy class
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from optimized_strategy import DualMAOptimizedStrategy


class TestDualMAOptimizedStrategy(unittest.TestCase):
    """Test cases for DualMAOptimizedStrategy class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.strategy = DualMAOptimizedStrategy(
            fast_ma_period=8,
            slow_ma_period=21,
            adx_period=14,
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            stop_loss_pct=0.08,
            time_stop_days=20
        )
        
        # Create sample test data
        self.sample_data = self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2023-01-01', end='2023-03-31', freq='D')
        np.random.seed(42)  # For reproducible tests
        
        n_days = len(dates)
        base_price = 100
        
        # Generate price movements
        returns = np.random.normal(0, 0.02, n_days)
        prices = base_price * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
            'close': prices,
            'volume': np.random.randint(10000, 100000, n_days)
        }, index=dates)
        
        # Ensure proper OHLC relationships
        data['high'] = np.maximum(data['high'], data[['open', 'close']].max(axis=1))
        data['low'] = np.minimum(data['low'], data[['open', 'close']].min(axis=1))
        
        return data
    
    def test_initialization(self):
        """Test strategy initialization with parameters."""
        self.assertEqual(self.strategy.fast_ma_period, 8)
        self.assertEqual(self.strategy.slow_ma_period, 21)
        self.assertEqual(self.strategy.adx_period, 14)
        self.assertEqual(self.strategy.rsi_overbought, 70)
        self.assertEqual(self.strategy.rsi_oversold, 30)
        self.assertEqual(self.strategy.stop_loss_pct, 0.08)
        self.assertEqual(self.strategy.time_stop_days, 20)
    
    def test_moving_averages_calculation(self):
        """Test moving averages calculation."""
        result = self.strategy.calculate_moving_averages(self.sample_data)
        
        # Check that MA columns are added
        self.assertIn('ma_fast', result.columns)
        self.assertIn('ma_slow', result.columns)
        
        # Check that fast MA has fewer NaN values than slow MA
        fast_na_count = result['ma_fast'].isna().sum()
        slow_na_count = result['ma_slow'].isna().sum()
        self.assertLess(fast_na_count, slow_na_count)
        
        # Check that MAs are calculated correctly for valid data
        valid_data = result.dropna()
        if len(valid_data) > 0:
            # Fast MA should be more reactive (generally closer to current price)
            self.assertTrue(all(isinstance(x, (int, float)) for x in valid_data['ma_fast']))
            self.assertTrue(all(isinstance(x, (int, float)) for x in valid_data['ma_slow']))
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        result = self.strategy.calculate_rsi(self.sample_data)
        
        # Check that RSI column is added
        self.assertIn('rsi', result.columns)
        
        # Check RSI is within valid range (0-100)
        valid_rsi = result['rsi'].dropna()
        if len(valid_rsi) > 0:
            self.assertTrue(all(0 <= x <= 100 for x in valid_rsi))
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        result = self.strategy.calculate_macd(self.sample_data)
        
        # Check that MACD columns are added
        self.assertIn('macd_line', result.columns)
        self.assertIn('macd_signal', result.columns)
        self.assertIn('macd_histogram', result.columns)
        
        # Check histogram calculation
        valid_data = result.dropna()
        if len(valid_data) > 0:
            for _, row in valid_data.iterrows():
                expected_histogram = row['macd_line'] - row['macd_signal']
                self.assertAlmostEqual(row['macd_histogram'], expected_histogram, places=10)
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation."""
        result = self.strategy.calculate_bollinger_bands(self.sample_data)
        
        # Check that BB columns are added
        self.assertIn('bb_upper', result.columns)
        self.assertIn('bb_middle', result.columns)
        self.assertIn('bb_lower', result.columns)
        
        # Check that upper > middle > lower
        valid_data = result.dropna()
        if len(valid_data) > 0:
            for _, row in valid_data.iterrows():
                self.assertGreater(row['bb_upper'], row['bb_middle'])
                self.assertGreater(row['bb_middle'], row['bb_lower'])
    
    def test_obv_calculation(self):
        """Test On-Balance Volume calculation."""
        result = self.strategy.calculate_obv(self.sample_data)
        
        # Check that OBV column is added
        self.assertIn('obv', result.columns)
        
        # Check that OBV is calculated (should have no NaN values)
        self.assertEqual(result['obv'].isna().sum(), 0)
        
        # First value should equal first volume
        self.assertEqual(result['obv'].iloc[0], result['volume'].iloc[0])
    
    def test_vwap_calculation(self):
        """Test VWAP calculation."""
        result = self.strategy.calculate_vwap(self.sample_data)
        
        # Check that VWAP columns are added
        self.assertIn('vwap', result.columns)
        self.assertIn('vwap_deviation', result.columns)
        
        # Check that VWAP deviation is calculated correctly
        valid_data = result.dropna()
        if len(valid_data) > 0:
            for _, row in valid_data.iterrows():
                expected_deviation = (row['close'] - row['vwap']) / row['vwap']
                self.assertAlmostEqual(row['vwap_deviation'], expected_deviation, places=10)
    
    def test_atr_calculation(self):
        """Test ATR calculation."""
        result = self.strategy.calculate_atr(self.sample_data)
        
        # Check that ATR column is added
        self.assertIn('atr', result.columns)
        
        # Check that ATR values are positive
        valid_atr = result['atr'].dropna()
        if len(valid_atr) > 0:
            self.assertTrue(all(x > 0 for x in valid_atr))
    
    def test_adx_calculation(self):
        """Test ADX calculation."""
        result = self.strategy.calculate_atr(self.sample_data)  # ATR needed for ADX
        result = self.strategy.calculate_adx(result)
        
        # Check that ADX columns are added
        self.assertIn('adx', result.columns)
        self.assertIn('plus_di', result.columns)
        self.assertIn('minus_di', result.columns)
        
        # Check that ADX is between 0 and 100
        valid_adx = result['adx'].dropna()
        if len(valid_adx) > 0:
            self.assertTrue(all(0 <= x <= 100 for x in valid_adx))
    
    def test_volume_anomaly_detection(self):
        """Test volume anomaly detection."""
        result = self.strategy.detect_volume_anomaly(self.sample_data)
        
        # Check that volume columns are added
        self.assertIn('volume_avg', result.columns)
        self.assertIn('volume_spike', result.columns)
        
        # Check that volume_spike is boolean
        valid_spikes = result['volume_spike'].dropna()
        if len(valid_spikes) > 0:
            self.assertTrue(all(isinstance(x, (bool, np.bool_)) for x in valid_spikes))
    
    def test_all_indicators_calculation(self):
        """Test that all indicators are calculated together."""
        result = self.strategy.calculate_all_indicators(self.sample_data)
        
        # Check that all expected columns are present
        expected_columns = [
            'ma_fast', 'ma_slow', 'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower', 'obv', 'vwap', 'vwap_deviation',
            'atr', 'adx', 'plus_di', 'minus_di', 'volume_avg', 'volume_spike'
        ]
        
        for col in expected_columns:
            self.assertIn(col, result.columns)
    
    def test_signal_generation(self):
        """Test buy/sell signal generation."""
        data_with_indicators = self.strategy.calculate_all_indicators(self.sample_data)
        result = self.strategy.generate_signals(data_with_indicators)
        
        # Check that signal columns are added
        self.assertIn('buy_signal', result.columns)
        self.assertIn('sell_signal', result.columns)
        
        # Check that signals are boolean where not NaN
        valid_buy = result['buy_signal'].dropna()
        valid_sell = result['sell_signal'].dropna()
        
        if len(valid_buy) > 0:
            self.assertTrue(all(isinstance(x, (bool, np.bool_)) for x in valid_buy))
        if len(valid_sell) > 0:
            self.assertTrue(all(isinstance(x, (bool, np.bool_)) for x in valid_sell))
    
    def test_stop_levels_calculation(self):
        """Test stop loss levels calculation."""
        data_with_indicators = self.strategy.calculate_all_indicators(self.sample_data)
        
        if len(data_with_indicators) > 20:  # Ensure we have enough data
            entry_price = 100.0
            entry_date = data_with_indicators.index[10]
            
            stop_levels = self.strategy.calculate_stop_levels(
                data_with_indicators, entry_price, entry_date
            )
            
            # Check that all expected keys are present
            expected_keys = ['fixed_stop', 'atr_stop', 'time_stop_triggered', 'days_held', 'current_price']
            for key in expected_keys:
                self.assertIn(key, stop_levels)
            
            # Check that fixed stop is below entry price
            self.assertLess(stop_levels['fixed_stop'], entry_price)
            
            # Check that days_held is non-negative integer
            self.assertGreaterEqual(stop_levels['days_held'], 0)
            self.assertIsInstance(stop_levels['days_held'], int)
    
    def test_exit_position_logic(self):
        """Test position exit logic."""
        data_with_indicators = self.strategy.calculate_all_indicators(self.sample_data)
        
        if len(data_with_indicators) > 20:
            entry_price = 100.0
            entry_date = data_with_indicators.index[10]
            
            should_exit, reason = self.strategy.should_exit_position(
                data_with_indicators, entry_price, entry_date
            )
            
            # Check that function returns boolean and string
            self.assertIsInstance(should_exit, bool)
            self.assertIsInstance(reason, str)
            self.assertGreater(len(reason), 0)  # Reason should not be empty
    
    def test_backtest_strategy(self):
        """Test the complete backtest functionality."""
        results = self.strategy.backtest_strategy(self.sample_data)
        
        # Check that all expected keys are present in results
        expected_keys = [
            'positions', 'total_trades', 'total_return', 'win_rate', 
            'avg_return', 'max_return', 'min_return', 'data_with_indicators'
        ]
        
        for key in expected_keys:
            self.assertIn(key, results)
        
        # Check data types
        self.assertIsInstance(results['positions'], list)
        self.assertIsInstance(results['total_trades'], int)
        self.assertIsInstance(results['total_return'], (int, float))
        self.assertIsInstance(results['win_rate'], (int, float))
        self.assertIsInstance(results['data_with_indicators'], pd.DataFrame)
        
        # Check that win rate is between 0 and 1
        self.assertGreaterEqual(results['win_rate'], 0)
        self.assertLessEqual(results['win_rate'], 1)
        
        # Check that total_trades matches positions length
        self.assertEqual(results['total_trades'], len(results['positions']))
    
    def test_position_structure(self):
        """Test that position data structure is correct."""
        results = self.strategy.backtest_strategy(self.sample_data)
        
        if results['positions']:  # If there are any positions
            position = results['positions'][0]
            
            # Check that all expected keys are present
            expected_keys = [
                'entry_date', 'exit_date', 'entry_price', 'exit_price',
                'return', 'exit_reason', 'days_held'
            ]
            
            for key in expected_keys:
                self.assertIn(key, position)
            
            # Check data types
            self.assertIsInstance(position['entry_date'], pd.Timestamp)
            self.assertIsInstance(position['exit_date'], pd.Timestamp)
            self.assertIsInstance(position['entry_price'], (int, float))
            self.assertIsInstance(position['exit_price'], (int, float))
            self.assertIsInstance(position['return'], (int, float))
            self.assertIsInstance(position['exit_reason'], str)
            self.assertIsInstance(position['days_held'], int)
            
            # Check logical constraints
            self.assertLessEqual(position['entry_date'], position['exit_date'])
            self.assertGreaterEqual(position['days_held'], 0)
    
    def test_custom_parameters(self):
        """Test strategy with custom parameters."""
        custom_strategy = DualMAOptimizedStrategy(
            fast_ma_period=5,
            slow_ma_period=15,
            rsi_overbought=80,
            rsi_oversold=20,
            stop_loss_pct=0.05,
            time_stop_days=15
        )
        
        # Check that custom parameters are set
        self.assertEqual(custom_strategy.fast_ma_period, 5)
        self.assertEqual(custom_strategy.slow_ma_period, 15)
        self.assertEqual(custom_strategy.rsi_overbought, 80)
        self.assertEqual(custom_strategy.rsi_oversold, 20)
        self.assertEqual(custom_strategy.stop_loss_pct, 0.05)
        self.assertEqual(custom_strategy.time_stop_days, 15)
        
        # Test that strategy still works with custom parameters
        results = custom_strategy.backtest_strategy(self.sample_data)
        self.assertIsInstance(results, dict)
        self.assertIn('total_trades', results)


if __name__ == '__main__':
    unittest.main()