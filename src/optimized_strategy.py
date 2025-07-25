"""
Optimized Dual Moving Average Strategy with Advanced Technical Indicators
for A-share Markets
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class DualMAOptimizedStrategy:
    """
    Advanced dual moving average strategy with technical indicators and risk management
    optimized for A-share markets.
    """
    
    def __init__(
        self,
        fast_ma_period: int = 8,
        slow_ma_period: int = 21,
        adx_period: int = 14,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        bb_period: int = 20,
        bb_std: float = 2.0,
        volume_spike_multiplier: float = 1.5,
        volume_avg_period: int = 20,
        stop_loss_pct: float = 0.08,
        atr_period: int = 14,
        atr_multiplier: float = 3.0,
        time_stop_days: int = 20,
        max_positions: int = 3,
        max_capital_per_stock: float = 0.30,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9
    ):
        """
        Initialize the strategy with configurable parameters.
        
        Args:
            fast_ma_period: Fast moving average period (default: 8)
            slow_ma_period: Slow moving average period (default: 21)
            adx_period: ADX calculation period (default: 14)
            rsi_period: RSI calculation period (default: 14)
            rsi_overbought: RSI overbought threshold (default: 70)
            rsi_oversold: RSI oversold threshold (default: 30)
            bb_period: Bollinger Bands period (default: 20)
            bb_std: Bollinger Bands standard deviation multiplier (default: 2.0)
            volume_spike_multiplier: Volume spike detection multiplier (default: 1.5)
            volume_avg_period: Volume average calculation period (default: 20)
            stop_loss_pct: Fixed stop loss percentage (default: 0.08)
            atr_period: ATR calculation period (default: 14)
            atr_multiplier: ATR trailing stop multiplier (default: 3.0)
            time_stop_days: Maximum holding period in days (default: 20)
            max_positions: Maximum pyramid positions (default: 3)
            max_capital_per_stock: Maximum capital allocation per stock (default: 0.30)
            macd_fast: MACD fast EMA period (default: 12)
            macd_slow: MACD slow EMA period (default: 26)
            macd_signal: MACD signal line period (default: 9)
        """
        self.fast_ma_period = fast_ma_period
        self.slow_ma_period = slow_ma_period
        self.adx_period = adx_period
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.volume_spike_multiplier = volume_spike_multiplier
        self.volume_avg_period = volume_avg_period
        self.stop_loss_pct = stop_loss_pct
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.time_stop_days = time_stop_days
        self.max_positions = max_positions
        self.max_capital_per_stock = max_capital_per_stock
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
    
    def calculate_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate fast and slow moving averages."""
        data = data.copy()
        data['ma_fast'] = data['close'].rolling(window=self.fast_ma_period).mean()
        data['ma_slow'] = data['close'].rolling(window=self.slow_ma_period).mean()
        return data
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Relative Strength Index (RSI)."""
        data = data.copy()
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        rs = avg_gain / avg_loss
        data['rsi'] = 100 - (100 / (1 + rs))
        return data
    
    def calculate_macd(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD and histogram."""
        data = data.copy()
        ema_fast = data['close'].ewm(span=self.macd_fast).mean()
        ema_slow = data['close'].ewm(span=self.macd_slow).mean()
        
        data['macd_line'] = ema_fast - ema_slow
        data['macd_signal'] = data['macd_line'].ewm(span=self.macd_signal).mean()
        data['macd_histogram'] = data['macd_line'] - data['macd_signal']
        return data
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        data = data.copy()
        data['bb_middle'] = data['close'].rolling(window=self.bb_period).mean()
        bb_std = data['close'].rolling(window=self.bb_period).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * self.bb_std)
        data['bb_lower'] = data['bb_middle'] - (bb_std * self.bb_std)
        return data
    
    def calculate_obv(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate On-Balance Volume (OBV)."""
        data = data.copy()
        obv = []
        prev_obv = 0
        
        for i in range(len(data)):
            if i == 0:
                obv.append(data['volume'].iloc[i])
            else:
                if data['close'].iloc[i] > data['close'].iloc[i-1]:
                    obv.append(prev_obv + data['volume'].iloc[i])
                elif data['close'].iloc[i] < data['close'].iloc[i-1]:
                    obv.append(prev_obv - data['volume'].iloc[i])
                else:
                    obv.append(prev_obv)
            prev_obv = obv[-1]
        
        data['obv'] = obv
        return data
    
    def calculate_vwap(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Volume Weighted Average Price (VWAP)."""
        data = data.copy()
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        data['vwap'] = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        data['vwap_deviation'] = (data['close'] - data['vwap']) / data['vwap']
        return data
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Average True Range (ATR)."""
        data = data.copy()
        high_low = data['high'] - data['low']
        high_close_prev = np.abs(data['high'] - data['close'].shift(1))
        low_close_prev = np.abs(data['low'] - data['close'].shift(1))
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        data['atr'] = true_range.rolling(window=self.atr_period).mean()
        return data
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Average Directional Index (ADX)."""
        data = data.copy()
        
        # Calculate directional movement
        high_diff = data['high'].diff()
        low_diff = -data['low'].diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        data['plus_dm'] = pd.Series(plus_dm).rolling(window=self.adx_period).mean()
        data['minus_dm'] = pd.Series(minus_dm).rolling(window=self.adx_period).mean()
        
        # Calculate directional indicators
        data['plus_di'] = 100 * data['plus_dm'] / data['atr']
        data['minus_di'] = 100 * data['minus_dm'] / data['atr']
        
        # Calculate ADX
        dx = 100 * np.abs(data['plus_di'] - data['minus_di']) / (data['plus_di'] + data['minus_di'])
        data['adx'] = dx.rolling(window=self.adx_period).mean()
        
        return data
    
    def detect_volume_anomaly(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect volume anomalies (spikes)."""
        data = data.copy()
        data['volume_avg'] = data['volume'].rolling(window=self.volume_avg_period).mean()
        data['volume_spike'] = data['volume'] > (data['volume_avg'] * self.volume_spike_multiplier)
        return data
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        data = self.calculate_moving_averages(data)
        data = self.calculate_rsi(data)
        data = self.calculate_macd(data)
        data = self.calculate_bollinger_bands(data)
        data = self.calculate_obv(data)
        data = self.calculate_vwap(data)
        data = self.calculate_atr(data)
        data = self.calculate_adx(data)
        data = self.detect_volume_anomaly(data)
        return data
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on all indicators."""
        data = data.copy()
        
        # Basic MA crossover
        ma_bullish = data['ma_fast'] > data['ma_slow']
        ma_cross_up = (data['ma_fast'] > data['ma_slow']) & (data['ma_fast'].shift(1) <= data['ma_slow'].shift(1))
        
        # Trend confirmation conditions
        adx_strong = data['adx'] > 25  # Strong trend
        rsi_not_overbought = data['rsi'] < self.rsi_overbought
        rsi_oversold = data['rsi'] < self.rsi_oversold
        macd_bullish = data['macd_histogram'] > 0
        macd_cross_up = (data['macd_histogram'] > 0) & (data['macd_histogram'].shift(1) <= 0)
        bb_breakout = data['close'] > data['bb_upper']
        volume_confirmation = data['volume_spike']
        
        # Buy signal conditions
        buy_signal = (
            ma_cross_up &
            adx_strong &
            rsi_not_overbought &
            (macd_bullish | macd_cross_up) &
            volume_confirmation
        )
        
        # Sell signal conditions
        sell_signal = (
            (data['ma_fast'] < data['ma_slow']) |
            (data['rsi'] > self.rsi_overbought) |
            (data['close'] < data['bb_lower'])
        )
        
        data['buy_signal'] = buy_signal
        data['sell_signal'] = sell_signal
        
        return data
    
    def calculate_stop_levels(self, data: pd.DataFrame, entry_price: float, entry_date: pd.Timestamp) -> Dict:
        """Calculate various stop loss levels."""
        current_data = data[data.index >= entry_date].copy()
        
        if len(current_data) == 0:
            return {}
        
        latest_data = current_data.iloc[-1]
        days_held = len(current_data) - 1
        
        # Fixed stop loss
        fixed_stop = entry_price * (1 - self.stop_loss_pct)
        
        # ATR trailing stop
        if 'atr' in latest_data and not pd.isna(latest_data['atr']):
            atr_stop = latest_data['close'] - (latest_data['atr'] * self.atr_multiplier)
        else:
            atr_stop = fixed_stop
        
        # Time stop
        time_stop_triggered = days_held >= self.time_stop_days
        
        return {
            'fixed_stop': fixed_stop,
            'atr_stop': atr_stop,
            'time_stop_triggered': time_stop_triggered,
            'days_held': days_held,
            'current_price': latest_data['close']
        }
    
    def should_exit_position(self, data: pd.DataFrame, entry_price: float, entry_date: pd.Timestamp) -> Tuple[bool, str]:
        """Determine if position should be exited based on stop conditions."""
        stop_levels = self.calculate_stop_levels(data, entry_price, entry_date)
        
        if not stop_levels:
            return False, "No data available"
        
        current_price = stop_levels['current_price']
        
        # Check fixed stop loss
        if current_price <= stop_levels['fixed_stop']:
            return True, "Fixed stop loss triggered"
        
        # Check ATR trailing stop
        if current_price <= stop_levels['atr_stop']:
            return True, "ATR trailing stop triggered"
        
        # Check time stop
        if stop_levels['time_stop_triggered']:
            return True, "Time stop triggered"
        
        # Check technical sell signals
        latest_signals = self.generate_signals(data.tail(1))
        if not latest_signals.empty and latest_signals['sell_signal'].iloc[-1]:
            return True, "Technical sell signal"
        
        return False, "Hold position"
    
    def backtest_strategy(self, data: pd.DataFrame) -> Dict:
        """
        Simple backtest implementation.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with backtest results
        """
        data_with_indicators = self.calculate_all_indicators(data)
        data_with_signals = self.generate_signals(data_with_indicators)
        
        positions = []
        current_position = None
        
        for i, (date, row) in enumerate(data_with_signals.iterrows()):
            if pd.isna(row['buy_signal']) or pd.isna(row['sell_signal']):
                continue
                
            # Entry logic
            if row['buy_signal'] and current_position is None:
                current_position = {
                    'entry_date': date,
                    'entry_price': row['close'],
                    'entry_index': i
                }
            
            # Exit logic
            if current_position is not None:
                should_exit, exit_reason = self.should_exit_position(
                    data_with_signals.iloc[:i+1], 
                    current_position['entry_price'], 
                    current_position['entry_date']
                )
                
                if should_exit or row['sell_signal']:
                    position_result = {
                        'entry_date': current_position['entry_date'],
                        'exit_date': date,
                        'entry_price': current_position['entry_price'],
                        'exit_price': row['close'],
                        'return': (row['close'] - current_position['entry_price']) / current_position['entry_price'],
                        'exit_reason': exit_reason if should_exit else "Technical sell signal",
                        'days_held': (date - current_position['entry_date']).days
                    }
                    positions.append(position_result)
                    current_position = None
        
        # Calculate summary statistics
        if positions:
            returns = [p['return'] for p in positions]
            total_return = sum(returns)
            win_rate = len([r for r in returns if r > 0]) / len(returns)
            avg_return = total_return / len(returns)
            max_return = max(returns)
            min_return = min(returns)
        else:
            total_return = win_rate = avg_return = max_return = min_return = 0
        
        return {
            'positions': positions,
            'total_trades': len(positions),
            'total_return': total_return,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'max_return': max_return,
            'min_return': min_return,
            'data_with_indicators': data_with_signals
        }


if __name__ == "__main__":
    # Example usage with sample data
    import datetime
    
    # Create sample data for demonstration
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    # Generate sample OHLCV data
    sample_data = pd.DataFrame({
        'date': dates,
        'open': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'high': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5) + np.random.rand(len(dates)) * 2,
        'low': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5) - np.random.rand(len(dates)) * 2,
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        'volume': np.random.randint(10000, 100000, len(dates))
    })
    
    # Ensure high >= low and proper OHLC relationships
    sample_data['high'] = np.maximum(sample_data['high'], sample_data[['open', 'close']].max(axis=1))
    sample_data['low'] = np.minimum(sample_data['low'], sample_data[['open', 'close']].min(axis=1))
    
    sample_data.set_index('date', inplace=True)
    
    # Initialize and run strategy
    strategy = DualMAOptimizedStrategy(
        fast_ma_period=8,
        slow_ma_period=21,
        adx_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
        stop_loss_pct=0.08,
        time_stop_days=20
    )
    
    # Run backtest
    results = strategy.backtest_strategy(sample_data)
    
    print("=== Dual MA Optimized Strategy Backtest Results ===")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    print(f"Average Return per Trade: {results['avg_return']:.2%}")
    print(f"Best Trade: {results['max_return']:.2%}")
    print(f"Worst Trade: {results['min_return']:.2%}")
    
    if results['positions']:
        print("\n=== First 5 Trades ===")
        for i, pos in enumerate(results['positions'][:5]):
            print(f"Trade {i+1}: {pos['entry_date'].strftime('%Y-%m-%d')} to {pos['exit_date'].strftime('%Y-%m-%d')}")
            print(f"  Entry: {pos['entry_price']:.2f}, Exit: {pos['exit_price']:.2f}")
            print(f"  Return: {pos['return']:.2%}, Days: {pos['days_held']}, Reason: {pos['exit_reason']}")