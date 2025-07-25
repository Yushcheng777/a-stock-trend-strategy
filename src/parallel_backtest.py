"""
Parallel Grid-Search Backtesting for A-Stock Trend Strategy
"""
import pandas as pd
import yfinance as yf
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import argparse
from typing import List, Dict, Tuple, Any
import time

from strategy import EnhancedAStockTrendStrategy


def fetch_stock_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch stock data using yfinance.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with OHLCV data
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=end_date)
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


def run_single_backtest(params: Tuple[str, Dict[str, Any], str, str]) -> Dict[str, Any]:
    """
    Run a single backtest with given parameters.

    Args:
        params: Tuple containing (ticker, strategy_params, start_date, end_date)

    Returns:
        Dictionary with backtest results
    """
    ticker, strategy_params, start_date, end_date = params

    try:
        # Fetch data
        data = fetch_stock_data(ticker, start_date, end_date)
        if data.empty:
            return {
                'ticker': ticker,
                'error': 'No data available',
                **strategy_params
            }

        # Run backtest
        strategy = EnhancedAStockTrendStrategy(**strategy_params)
        results = strategy.backtest(data)

        # Return results with metadata
        return {
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'total_return': results['total_return'],
            'total_trades': results['total_trades'],
            'win_rate': results['win_rate'],
            'final_capital': results['final_capital'],
            **strategy_params
        }

    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            **strategy_params
        }


def generate_parameter_grid() -> List[Dict[str, Any]]:
    """
    Generate parameter combinations for grid search.

    Returns:
        List of parameter dictionaries
    """
    sma_short_values = [5, 10, 15, 20]
    sma_long_values = [20, 30, 40, 50]
    rsi_period_values = [10, 14, 20]
    rsi_oversold_values = [20, 30, 40]
    rsi_overbought_values = [60, 70, 80]

    param_combinations = []

    for sma_short, sma_long, rsi_period, rsi_oversold, rsi_overbought in product(
            sma_short_values, sma_long_values, rsi_period_values,
            rsi_oversold_values, rsi_overbought_values
    ):
        # Ensure short SMA is less than long SMA
        if sma_short < sma_long:
            param_combinations.append({
                'sma_short': sma_short,
                'sma_long': sma_long,
                'rsi_period': rsi_period,
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought
            })

    return param_combinations


def run_parallel_backtest(tickers: List[str],
                          start_date: str,
                          end_date: str,
                          max_workers: int = 4,
                          output_file: str = 'backtest_results.csv') -> pd.DataFrame:
    """
    Run parallel grid-search backtests across multiple tickers and parameters.

    Args:
        tickers: List of stock ticker symbols
        start_date: Start date for backtesting
        end_date: End date for backtesting
        max_workers: Maximum number of parallel workers
        output_file: Output CSV file path

    Returns:
        DataFrame with all backtest results
    """
    print(f"Starting parallel backtest with {max_workers} workers...")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Date range: {start_date} to {end_date}")

    # Generate parameter grid
    param_grid = generate_parameter_grid()
    print(f"Generated {len(param_grid)} parameter combinations")

    # Create task list
    tasks = []
    for ticker in tickers:
        for params in param_grid:
            tasks.append((ticker, params, start_date, end_date))

    print(f"Total tasks: {len(tasks)}")

    # Run parallel backtests
    results = []
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(run_single_backtest, task): task
            for task in tasks
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                results.append(result)
                completed += 1

                if completed % 50 == 0:
                    elapsed = time.time() - start_time
                    print(f"Completed {completed}/{len(tasks)} tasks ({elapsed:.1f}s)")

            except Exception as e:
                task = future_to_task[future]
                print(f"Task failed: {task[0]} - {e}")

    elapsed = time.time() - start_time
    print(f"Completed all {len(results)} backtests in {elapsed:.1f}s")

    # Convert to DataFrame and save
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

    return df_results


def analyze_results(df: pd.DataFrame) -> None:
    """
    Analyze and display backtest results.

    Args:
        df: DataFrame with backtest results
    """
    print("\n=== BACKTEST ANALYSIS ===")

    if df.empty:
        print("No backtest results to analyze.")
        return

    # Check if total_return column exists
    if 'total_return' not in df.columns:
        print("Results contain only error cases - no successful backtests to analyze.")
        print(f"Total attempts: {len(df)}")
        if 'error' in df.columns:
            error_counts = df['error'].value_counts()
            print("Error breakdown:")
            for error, count in error_counts.items():
                print(f"  {error}: {count}")
        return

    # Filter out error cases
    df_clean = df[~df['total_return'].isna()]

    if df_clean.empty:
        print("No successful backtests to analyze.")
        print(f"Total failed backtests: {len(df)}")
        if 'error' in df.columns:
            error_counts = df['error'].value_counts()
            print("Error breakdown:")
            for error, count in error_counts.items():
                print(f"  {error}: {count}")
        return

    print(f"Successful backtests: {len(df_clean)}")
    print(f"Failed backtests: {len(df) - len(df_clean)}")

    # Overall statistics
    print("\\nOverall Performance:")
    print(f"Average return: {df_clean['total_return'].mean():.4f}")
    print(f"Best return: {df_clean['total_return'].max():.4f}")
    print(f"Worst return: {df_clean['total_return'].min():.4f}")
    print(f"Average win rate: {df_clean['win_rate'].mean():.4f}")

    # Best performing combinations
    print("\\nTop 5 Parameter Combinations:")
    if len(df_clean) > 0:
        # Only show columns that exist
        available_columns = ['ticker', 'total_return', 'win_rate', 'total_trades']
        strategy_columns = ['sma_short', 'sma_long', 'rsi_period', 'rsi_oversold', 'rsi_overbought']
        display_columns = available_columns + [col for col in strategy_columns if col in df_clean.columns]

        top_params = df_clean.nlargest(5, 'total_return')[display_columns]
        print(top_params.to_string(index=False))
    else:
        print("No data to display.")


def main():
    """Main entry point for parallel backtesting."""
    parser = argparse.ArgumentParser(description='Run parallel grid-search backtests')
    parser.add_argument('--tickers', nargs='+', default=['AAPL', 'MSFT', 'GOOGL'],
                        help='Stock tickers to backtest')
    parser.add_argument('--start-date', default='2022-01-01',
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2023-12-31',
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of parallel workers')
    parser.add_argument('--output', default='backtest_results.csv',
                        help='Output CSV file')

    args = parser.parse_args()

    # Run parallel backtest
    results_df = run_parallel_backtest(
        tickers=args.tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        max_workers=args.workers,
        output_file=args.output
    )

    # Analyze results
    analyze_results(results_df)


if __name__ == '__main__':
    main()