"""
基础使用示例

演示如何使用A股趋势策略系统进行回测。
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from astrategy.core.engine import StrategyEngine
from astrategy.utils.config import load_config


def main():
    """基础使用示例"""
    print("🚀 A股趋势策略系统 - 基础使用示例")
    print("=" * 50)
    
    # 1. 加载配置
    print("📋 加载策略配置...")
    config = load_config()
    print(f"✅ 配置加载完成")
    
    # 2. 创建策略引擎
    print("\n🔧 初始化策略引擎...")
    engine = StrategyEngine()
    
    # 3. 设置回测参数
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    universe = [
        '000001',  # 平安银行
        '000002',  # 万科A
        '600000',  # 浦发银行
        '600036',  # 招商银行
        '600519',  # 贵州茅台
        '002415'   # 海康威视
    ]
    
    print(f"📊 回测设置:")
    print(f"   期间: {start_date} 至 {end_date}")
    print(f"   股票池: {len(universe)} 只股票")
    print(f"   初始资金: {config.get('backtest', {}).get('initial_capital', 1000000):,} 元")
    
    # 4. 初始化
    print("\n📥 初始化数据和策略...")
    engine.initialize(start_date, end_date, universe)
    
    # 5. 运行回测
    print("\n🔄 开始回测...")
    results = engine.run_backtest()
    
    # 6. 展示结果
    print("\n" + "=" * 50)
    print("📈 回测结果")
    print("=" * 50)
    
    metrics = results['performance_metrics']
    
    print(f"总收益率:     {metrics.get('total_return', 0):.2%}")
    print(f"年化收益率:   {metrics.get('annual_return', 0):.2%}")
    print(f"年化波动率:   {metrics.get('annual_volatility', 0):.2%}")
    print(f"夏普比率:     {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"最大回撤:     {metrics.get('max_drawdown', 0):.2%}")
    print(f"胜率:         {metrics.get('win_rate', 0):.2%}")
    print(f"盈亏比:       {metrics.get('profit_loss_ratio', 0):.2f}")
    print(f"总交易次数:   {metrics.get('total_trades', 0)}")
    print(f"盈利交易:     {metrics.get('winning_trades', 0)}")
    print(f"亏损交易:     {metrics.get('losing_trades', 0)}")
    
    # 7. 最终投资组合状态
    final_portfolio = results['final_portfolio']
    print(f"\n最终资金:     {final_portfolio['cash']:,.2f} 元")
    print(f"最终总值:     {final_portfolio['total_value']:,.2f} 元")
    print(f"持仓数量:     {len(final_portfolio['positions'])} 只")
    
    if final_portfolio['positions']:
        print("\n当前持仓:")
        for symbol, pos in final_portfolio['positions'].items():
            print(f"  {symbol}: {pos['quantity']} 股 @ {pos['avg_price']:.2f}")
    
    # 8. 交易记录示例
    trade_history = results['trade_history']
    if trade_history:
        print(f"\n交易记录 (显示最后5笔):")
        for trade in trade_history[-5:]:
            action = "买入" if trade['action'] == 'buy' else "卖出"
            pnl_info = ""
            if 'pnl' in trade:
                pnl_info = f" 盈亏:{trade['pnl']:.2f}({trade.get('pnl_ratio', 0):.2%})"
            
            print(f"  {trade['date'].strftime('%Y-%m-%d')} {action} {trade['symbol']} "
                  f"{trade['quantity']}股 @ {trade['price']:.2f}{pnl_info}")
    
    print("\n✅ 示例运行完成!")
    print("\n💡 提示:")
    print("- 可以修改配置文件调整策略参数")
    print("- 可以更换股票池测试不同组合")
    print("- 实际使用时建议连接真实数据源")


if __name__ == "__main__":
    main()