"""
高级使用示例 - 调整参数以增加交易活跃度

演示如何调整策略参数来生成更多交易信号。
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from astrategy.core.engine import StrategyEngine
from astrategy.utils.config import load_config


def create_active_config():
    """创建更活跃的策略配置"""
    config = load_config()
    
    # 调整参数以增加交易活跃度
    
    # 1. 使用更敏感的移动平均线参数
    config['strategy']['triangular_ma']['fast_period'] = 3  # 更短的快线
    config['strategy']['triangular_ma']['slow_period'] = 15  # 更短的慢线
    config['strategy']['triangular_ma']['smoothing'] = 2    # 更少的平滑
    
    # 2. 降低ADX阈值
    config['strategy']['adx']['threshold'] = 15  # 降低趋势确认阈值
    config['strategy']['adx']['strong_trend'] = 25  # 降低强趋势阈值
    
    # 3. 调整入场参数
    config['strategy']['entry']['breakout_period'] = 10  # 更短的突破周期
    config['strategy']['entry']['volume_confirm'] = False  # 取消成交量确认
    
    # 4. 放宽风险控制以增加交易
    config['risk']['position']['initial_position'] = 0.3  # 增加初始仓位
    config['risk']['stop_loss']['max_loss'] = 0.12  # 放宽止损
    
    # 5. 降低信号阈值 (这需要在策略代码中体现)
    # 我们将在使用时覆盖这些参数
    
    return config


def run_active_backtest():
    """运行活跃交易回测"""
    print("🚀 A股趋势策略系统 - 高级使用示例 (活跃交易)")
    print("=" * 60)
    
    # 1. 创建活跃配置
    print("📋 加载并调整策略配置...")
    config = create_active_config()
    print("✅ 配置调整完成 - 使用更敏感的参数")
    
    # 2. 创建策略引擎
    print("\n🔧 初始化策略引擎...")
    engine = StrategyEngine()
    engine.config = config  # 使用调整后的配置
    
    # 重新初始化组件
    from astrategy.core.strategy import AStockTrendStrategy
    from astrategy.data.providers import DataProvider
    from astrategy.risk.manager import RiskManager
    
    engine.strategy = AStockTrendStrategy(config)
    engine.data_provider = DataProvider(config)
    engine.risk_manager = RiskManager(config)
    
    # 3. 设置回测参数 - 使用较短期间以减少计算时间
    start_date = "2023-06-01"
    end_date = "2023-12-31"
    universe = [
        '000001',  # 平安银行
        '000002',  # 万科A
        '600000',  # 浦发银行
        '600036'   # 招商银行
    ]
    
    print(f"📊 回测设置:")
    print(f"   期间: {start_date} 至 {end_date}")
    print(f"   股票池: {len(universe)} 只股票")
    print(f"   初始资金: {config.get('backtest', {}).get('initial_capital', 1000000):,} 元")
    print(f"   快线周期: {config['strategy']['triangular_ma']['fast_period']}")
    print(f"   慢线周期: {config['strategy']['triangular_ma']['slow_period']}")
    print(f"   ADX阈值: {config['strategy']['adx']['threshold']}")
    
    # 4. 初始化
    print("\n📥 初始化数据和策略...")
    engine.initialize(start_date, end_date, universe)
    
    # 5. 运行回测
    print("\n🔄 开始回测...")
    results = engine.run_backtest()
    
    # 6. 展示结果
    print("\n" + "=" * 60)
    print("📈 回测结果")
    print("=" * 60)
    
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
    
    # 8. 详细交易记录
    trade_history = results['trade_history']
    if trade_history:
        print(f"\n📋 交易记录 (共{len(trade_history)}笔):")
        print("-" * 60)
        
        # 按日期排序并显示所有交易
        for i, trade in enumerate(trade_history[:20]):  # 最多显示20笔
            action = "买入" if trade['action'] == 'buy' else "卖出"
            pnl_info = ""
            if 'pnl' in trade:
                pnl_info = f" | 盈亏:{trade['pnl']:.2f}({trade.get('pnl_ratio', 0):.2%})"
            
            print(f"{i+1:2d}. {trade['date'].strftime('%m-%d')} {action} {trade['symbol']} "
                  f"{trade['quantity']:4d}股 @ {trade['price']:6.2f}{pnl_info}")
        
        if len(trade_history) > 20:
            print(f"    ... 还有 {len(trade_history) - 20} 笔交易")
    else:
        print("\n⚠️  没有产生交易记录")
        print("可能原因:")
        print("- 信号阈值仍然太严格")
        print("- 模拟数据的趋势性不够强")
        print("- 风险控制过于严格")
        
        print("\n💡 建议:")
        print("- 进一步降低信号阈值")
        print("- 使用真实市场数据")
        print("- 调整风险参数")
    
    # 9. 参数调优建议
    print("\n" + "=" * 60)
    print("🔧 参数调优建议")
    print("=" * 60)
    
    print("当前参数设置:")
    print(f"- 快线周期: {config['strategy']['triangular_ma']['fast_period']}")
    print(f"- 慢线周期: {config['strategy']['triangular_ma']['slow_period']}")
    print(f"- ADX阈值: {config['strategy']['adx']['threshold']}")
    print(f"- 初始仓位: {config['risk']['position']['initial_position']:.1%}")
    
    if metrics.get('total_trades', 0) < 5:
        print("\n🎯 增加交易频率的建议:")
        print("- 进一步降低ADX阈值至10-15")
        print("- 使用更短的移动平均线周期")
        print("- 取消成交量确认要求")
        print("- 降低信号强度阈值")
    
    if metrics.get('total_trades', 0) > 0:
        win_rate = metrics.get('win_rate', 0)
        if win_rate < 0.4:
            print("\n📈 提高胜率的建议:")
            print("- 提高ADX阈值以确保趋势质量")
            print("- 增加额外的确认指标")
            print("- 调整止损位置")
        
        max_dd = abs(metrics.get('max_drawdown', 0))
        if max_dd > 0.15:
            print("\n🛡️ 降低风险的建议:")
            print("- 减小单次建仓比例")
            print("- 收紧止损条件")
            print("- 增加回撤控制机制")
    
    print("\n✅ 高级示例运行完成!")
    return results


def compare_configurations():
    """比较不同配置的效果"""
    print("\n" + "=" * 60)
    print("🔍 配置比较分析")
    print("=" * 60)
    
    # 这里可以实现多组配置的对比测试
    print("💡 可以通过以下方式比较不同配置:")
    print("1. 修改配置文件中的参数")
    print("2. 运行多次回测")
    print("3. 对比关键指标:")
    print("   - 总收益率 vs 最大回撤")
    print("   - 交易频率 vs 胜率")
    print("   - 夏普比率")


if __name__ == "__main__":
    results = run_active_backtest()
    compare_configurations()