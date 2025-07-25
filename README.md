# A-Share Trend Strategy

An advanced dual moving average trading strategy optimized for A-share markets, featuring comprehensive technical indicators and robust risk management.

## Features

### Technical Indicators
- **Moving Averages**: 8-day fast and 21-day slow periods
- **RSI**: 14-day period with 70/30 overbought/oversold thresholds
- **MACD**: Histogram crossover confirmation (12/26/9 periods)
- **Bollinger Bands**: 20-day MA ± 2 standard deviations
- **ADX**: 14-day period for trend strength analysis
- **Volume Analysis**: On-Balance Volume (OBV), VWAP deviation, volume spike detection (>1.5× average)

### Risk Management
- **Fixed Stop Loss**: 8% from entry price
- **ATR Trailing Stop**: 3× ATR dynamic trailing stop
- **Time Stop**: Automatic exit after 20 trading days
- **Position Sizing**: Pyramid entries (up to 3 positions), maximum 30% capital per stock

### Strategy Logic
The strategy generates buy signals when:
- Fast MA crosses above slow MA
- ADX indicates strong trend (>25)
- RSI is not overbought (<70)
- MACD histogram is bullish or crossing up
- Volume spike confirmation

Exit conditions include:
- Technical sell signals (MA cross down, RSI overbought, BB breakdown)
- Risk management stops (fixed, ATR trailing, time-based)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Yushcheng777/a-stock-trend-strategy.git
cd a-stock-trend-strategy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.optimized_strategy import DualMAOptimizedStrategy, create_realistic_sample_data

# Create sample data
sample_data = create_realistic_sample_data()

# Initialize strategy with A-share optimized parameters
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

print(f"Total Trades: {results['total_trades']}")
print(f"Total Return: {results['total_return']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
```

### Running the Example

```bash
python src/optimized_strategy.py
```

### Jupyter Notebook Demo

For a comprehensive demonstration with visualizations:

```bash
jupyter notebook examples/strategy_demo.ipynb
```

## Project Structure

```
a-stock-trend-strategy/
├── src/
│   ├── __init__.py
│   └── optimized_strategy.py      # Main strategy implementation
├── tests/
│   ├── __init__.py
│   └── test_optimized_strategy.py # Unit tests
├── examples/
│   └── strategy_demo.ipynb        # Jupyter notebook demo
├── requirements.txt               # Dependencies
├── README.md                      # This file
└── .gitignore                     # Git ignore rules
```

## API Reference

### DualMAOptimizedStrategy Class

#### Constructor Parameters

- `fast_ma_period` (int): Fast moving average period (default: 8)
- `slow_ma_period` (int): Slow moving average period (default: 21)
- `adx_period` (int): ADX calculation period (default: 14)
- `rsi_period` (int): RSI calculation period (default: 14)
- `rsi_overbought` (float): RSI overbought threshold (default: 70.0)
- `rsi_oversold` (float): RSI oversold threshold (default: 30.0)
- `bb_period` (int): Bollinger Bands period (default: 20)
- `bb_std` (float): Bollinger Bands standard deviation multiplier (default: 2.0)
- `volume_spike_multiplier` (float): Volume spike detection multiplier (default: 1.5)
- `stop_loss_pct` (float): Fixed stop loss percentage (default: 0.08)
- `atr_period` (int): ATR calculation period (default: 14)
- `atr_multiplier` (float): ATR trailing stop multiplier (default: 3.0)
- `time_stop_days` (int): Maximum holding period in days (default: 20)
- `max_positions` (int): Maximum pyramid positions (default: 3)
- `max_capital_per_stock` (float): Maximum capital allocation per stock (default: 0.30)

#### Key Methods

- `calculate_all_indicators(data)`: Calculate all technical indicators
- `generate_signals(data)`: Generate buy/sell signals
- `backtest_strategy(data)`: Run complete backtest
- `calculate_stop_levels(data, entry_price, entry_date)`: Calculate risk management stops
- `should_exit_position(data, entry_price, entry_date)`: Determine exit conditions

## Data Format

The strategy expects OHLCV data in pandas DataFrame format:

```python
data = pd.DataFrame({
    'open': [...],    # Opening prices
    'high': [...],    # High prices
    'low': [...],     # Low prices
    'close': [...],   # Closing prices
    'volume': [...]   # Trading volume
}, index=pd.DatetimeIndex([...]))  # Date index
```

## Testing

Run the unit tests to verify functionality:

```bash
python tests/test_optimized_strategy.py
```

The test suite includes 17 comprehensive test cases covering:
- Indicator calculations
- Signal generation
- Risk management
- Backtest functionality
- Parameter validation

## Performance Considerations

- The strategy uses multiple technical indicators which require sufficient historical data
- Minimum recommended data length: 50+ trading days
- For production use, consider:
  - Transaction costs and slippage
  - Market impact for large positions
  - Sector diversification controls
  - Real-time data feeds

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. It is not intended as investment advice. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

## Acknowledgments

- Technical analysis concepts based on established market indicators
- Risk management principles adapted for A-share market characteristics
- Strategy framework designed for institutional-grade backtesting