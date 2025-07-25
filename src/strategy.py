"""
Enhanced A-Stock Trend Strategy Implementation
"""
import pandas as pd
from typing import Dict


class EnhancedAStockTrendStrategy:
    """
    Enhanced implementation of the A-Stock Trend Strategy.

    This strategy uses technical indicators to identify trend direction
    and generate buy/sell signals for stock trading.
    """

    def __init__(self,
                 sma_short: int = 10,
                 sma_long: int = 30,
                 rsi_period: int = 14,
                 rsi_oversold: float = 30.0,
                 rsi_overbought: float = 70.0):
        """
        Initialize the strategy with configurable parameters.

        Args:
            sma_short: Period for short-term Simple Moving Average
            sma_long: Period for long-term Simple Moving Average
            rsi_period: Period for RSI calculation
            rsi_oversold: RSI threshold for oversold condition
            rsi_overbought: RSI threshold for overbought condition
        """
        self.sma_short = sma_short
        self.sma_long = sma_long
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for the strategy.

        Args:
            data: DataFrame with OHLCV data, must contain 'Close' column

        Returns:
            DataFrame with original data plus indicator columns
        """
        df = data.copy()

        # Calculate moving averages
        df['SMA_Short'] = self.calculate_sma(df['Close'], self.sma_short)
        df['SMA_Long'] = self.calculate_sma(df['Close'], self.sma_long)

        # Calculate RSI
        df['RSI'] = self.calculate_rsi(df['Close'], self.rsi_period)

        return df

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy rules.

        Args:
            data: DataFrame with OHLCV data and calculated indicators

        Returns:
            DataFrame with signal columns added
        """
        df = self.calculate_indicators(data)

        # Initialize signal columns
        df['Signal'] = 0
        df['Position'] = 0

        # Generate signals
        # Buy signal: Short SMA crosses above Long SMA AND RSI is oversold
        buy_condition = (
            (df['SMA_Short'] > df['SMA_Long']) &
            (df['SMA_Short'].shift(1) <= df['SMA_Long'].shift(1)) &
            (df['RSI'] < self.rsi_oversold)
        )

        # Sell signal: Short SMA crosses below Long SMA OR RSI is overbought
        sell_condition = (
            ((df['SMA_Short'] < df['SMA_Long']) &
             (df['SMA_Short'].shift(1) >= df['SMA_Long'].shift(1))) |
            (df['RSI'] > self.rsi_overbought)
        )

        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1

        # Calculate positions (cumulative signals)
        df['Position'] = df['Signal'].cumsum()
        df['Position'] = df['Position'].clip(lower=0, upper=1)

        return df

    def backtest(self, data: pd.DataFrame, initial_capital: float = 10000.0) -> Dict:
        """
        Perform backtest of the strategy.

        Args:
            data: DataFrame with OHLCV data
            initial_capital: Starting capital for backtest

        Returns:
            Dictionary with backtest results
        """
        df = self.generate_signals(data)

        # Calculate returns
        df['Returns'] = df['Close'].pct_change()
        df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']

        # Calculate cumulative returns
        df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
        df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()

        # Calculate performance metrics
        total_return = df['Cumulative_Strategy_Returns'].iloc[-1] - 1
        total_trades = (df['Signal'] != 0).sum()
        win_rate = ((df['Strategy_Returns'] > 0).sum() /
                   max(1, (df['Strategy_Returns'] != 0).sum())) if total_trades > 0 else 0

        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'final_capital': initial_capital * (1 + total_return),
            'data': df
        }
