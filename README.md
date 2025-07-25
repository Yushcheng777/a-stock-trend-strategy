# A-Stock Trend Strategy

A Python-based stock trading strategy implementation with parallel backtesting capabilities. This project implements an Enhanced A-Stock Trend Strategy that uses technical indicators to identify trend direction and generate buy/sell signals for stock trading.

## Features

- **Enhanced A-Stock Trend Strategy**: Technical analysis-based trading strategy using Simple Moving Averages (SMA) and Relative Strength Index (RSI)
- **Parallel Backtesting**: Multi-threaded grid-search backtesting across multiple parameters and stock tickers
- **Comprehensive Testing**: Unit tests and end-to-end tests ensuring code quality and reliability
- **CI/CD Pipeline**: Automated testing and linting with GitHub Actions

## Directory Structure

```
a-stock-trend-strategy/
├── src/
│   ├── strategy.py              # Core strategy implementation
│   └── parallel_backtest.py     # Parallel backtesting engine
├── tests/
│   ├── test_strategy.py         # Unit tests for strategy
│   └── test_parallel_backtest.py # End-to-end backtest tests
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Yushcheng777/a-stock-trend-strategy.git
   cd a-stock-trend-strategy
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation by running tests:**
   ```bash
   pytest tests/ -v
   ```

## Strategy Overview

The Enhanced A-Stock Trend Strategy combines multiple technical indicators:

- **Simple Moving Averages (SMA)**: Short-term and long-term trend identification
- **Relative Strength Index (RSI)**: Momentum oscillator for overbought/oversold conditions

### Signal Generation Rules

- **Buy Signal**: Short SMA crosses above Long SMA AND RSI indicates oversold condition
- **Sell Signal**: Short SMA crosses below Long SMA OR RSI indicates overbought condition

### Configurable Parameters

- `sma_short`: Short-term SMA period (default: 10)
- `sma_long`: Long-term SMA period (default: 30)
- `rsi_period`: RSI calculation period (default: 14)
- `rsi_oversold`: RSI oversold threshold (default: 30.0)
- `rsi_overbought`: RSI overbought threshold (default: 70.0)

## Usage Examples

### Basic Strategy Usage

```python
from src.strategy import EnhancedAStockTrendStrategy
import yfinance as yf

# Fetch stock data
ticker = "AAPL"
data = yf.Ticker(ticker).history(start="2023-01-01", end="2023-12-31")

# Initialize strategy
strategy = EnhancedAStockTrendStrategy(
    sma_short=10, 
    sma_long=30, 
    rsi_period=14
)

# Generate signals
signals = strategy.generate_signals(data)

# Run backtest
results = strategy.backtest(data, initial_capital=10000.0)
print(f"Total Return: {results['total_return']:.2%}")
print(f"Total Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.2%}")
```

### Parallel Backtesting

Run comprehensive grid-search backtests across multiple parameters and tickers:

```bash
cd src/
python parallel_backtest.py --tickers AAPL MSFT GOOGL --start-date 2022-01-01 --end-date 2023-12-31 --workers 4 --output results.csv
```

**Command Line Options:**
- `--tickers`: Space-separated list of stock tickers (default: AAPL MSFT GOOGL)
- `--start-date`: Backtest start date in YYYY-MM-DD format (default: 2022-01-01)
- `--end-date`: Backtest end date in YYYY-MM-DD format (default: 2023-12-31)
- `--workers`: Number of parallel workers (default: 4)
- `--output`: Output CSV filename (default: backtest_results.csv)

### Quick Test Run

For a quick test with limited data:

```bash
cd src/
python parallel_backtest.py --tickers AAPL --start-date 2023-01-01 --end-date 2023-01-31 --workers 1
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Modules

```bash
# Strategy unit tests
pytest tests/test_strategy.py -v

# Parallel backtest end-to-end tests
pytest tests/test_parallel_backtest.py -v
```

### Code Quality

```bash
# Linting with flake8
flake8 src/ tests/ --max-line-length=127 --statistics

# Check test coverage (if coverage is installed)
pytest --cov=src tests/
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Multi-Python Version Testing**: Tests run on Python 3.9, 3.10, 3.11, and 3.12
- **Automated Linting**: Code quality checks with flake8
- **Test Execution**: Comprehensive test suite with pytest
- **Integration Testing**: End-to-end validation of parallel backtesting

The CI pipeline runs on:
- All pushes to the `main` branch
- All pull requests targeting the `main` branch

## Dependencies

Core dependencies include:

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **yfinance**: Financial data retrieval
- **backtrader**: Backtesting framework
- **pytest**: Testing framework
- **flake8**: Code linting
- **matplotlib/seaborn**: Visualization (optional)

See `requirements.txt` for complete dependency list with version constraints.

## Performance Considerations

- **Parallel Processing**: Utilizes Python's `concurrent.futures` for multi-core backtesting
- **Memory Efficiency**: Processes one ticker-parameter combination at a time
- **Scalability**: Grid search scales with available CPU cores

## Output Format

Parallel backtesting generates CSV output with columns:

- `ticker`: Stock ticker symbol
- `total_return`: Strategy total return
- `total_trades`: Number of trades executed
- `win_rate`: Percentage of profitable trades
- `final_capital`: Final portfolio value
- `sma_short`, `sma_long`, `rsi_period`, `rsi_oversold`, `rsi_overbought`: Strategy parameters

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make changes and add tests
4. Run the test suite (`pytest tests/`)
5. Commit changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Create a Pull Request

## License

This project is available under the MIT License. See LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. It is not intended as financial advice. Always do your own research and consider consulting with a qualified financial advisor before making investment decisions.