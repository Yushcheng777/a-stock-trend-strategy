"""
简单的集成测试脚本
"""

import sys
import os
import numpy as np
import pandas as pd

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from astrategy.indicators.triangular_ma import TriangularMA
from astrategy.indicators.adx import ADXIndicator
from astrategy.risk.manager import RiskManager
from astrategy.utils.config import load_config

def test_triangular_ma():
    """测试三角移动平均线"""
    print("🧪 测试三角移动平均线...")
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0, 1, 100))
    test_data = pd.Series(prices, index=dates)
    
    # 测试TMA
    tma = TriangularMA(fast_period=5, slow_period=20, smoothing=3)
    fast_tma, slow_tma = tma.calculate(test_data)
    signals = tma.generate_signals(fast_tma, slow_tma)
    
    assert len(fast_tma) == len(test_data)
    assert len(slow_tma) == len(test_data)
    assert len(signals) == len(test_data)
    
    # 检查信号
    unique_signals = signals.dropna().unique()
    assert all(s in [-1, 0, 1] for s in unique_signals)
    
    print("   ✅ 三角移动平均线测试通过")

def test_adx():
    """测试ADX指标"""
    print("🧪 测试ADX指标...")
    
    # 创建测试OHLC数据
    np.random.seed(42)
    n_days = 100
    dates = pd.date_range('2023-01-01', periods=n_days, freq='D')
    
    close_prices = 100 + np.cumsum(np.random.normal(0, 1, n_days))
    high_prices = close_prices + np.random.uniform(0, 2, n_days)
    low_prices = close_prices - np.random.uniform(0, 2, n_days)
    
    high_series = pd.Series(high_prices, index=dates)
    low_series = pd.Series(low_prices, index=dates)
    close_series = pd.Series(close_prices, index=dates)
    
    # 测试ADX
    adx = ADXIndicator(period=14, threshold=25, strong_trend=40)
    adx_data = adx.calculate(high_series, low_series, close_series)
    
    expected_columns = ['ADX', 'DI_plus', 'DI_minus', 'DX']
    for col in expected_columns:
        assert col in adx_data.columns
    
    # 检查ADX值范围
    adx_values = adx_data['ADX'].dropna()
    assert (adx_values >= 0).all()
    assert (adx_values <= 100).all()
    
    print("   ✅ ADX指标测试通过")

def test_risk_manager():
    """测试风险管理器"""
    print("🧪 测试风险管理器...")
    
    config = load_config()
    risk_manager = RiskManager(config)
    
    # 测试T+1约束
    from datetime import datetime
    today = datetime.now()
    yesterday = today.replace(day=today.day-1)
    
    # 测试涨跌停检测
    price_limit_result = risk_manager.check_price_limit(
        '000001', 11.0, 10.0, 'normal'
    )
    
    assert 'is_limit_up' in price_limit_result
    assert 'is_limit_down' in price_limit_result
    assert 'price_change_ratio' in price_limit_result
    
    # 检查变动幅度计算
    assert abs(price_limit_result['price_change_ratio'] - 0.1) < 0.001
    
    print("   ✅ 风险管理器测试通过")

def test_config():
    """测试配置管理"""
    print("🧪 测试配置管理...")
    
    config = load_config()
    
    # 检查关键配置项
    assert 'market' in config
    assert 'strategy' in config
    assert 'risk' in config
    assert 'backtest' in config
    
    # 检查策略参数
    strategy_config = config['strategy']
    assert 'triangular_ma' in strategy_config
    assert 'adx' in strategy_config
    
    print("   ✅ 配置管理测试通过")

def main():
    """运行所有测试"""
    print("🚀 运行A股趋势策略系统组件测试")
    print("=" * 50)
    
    try:
        test_config()
        test_triangular_ma()
        test_adx()
        test_risk_manager()
        
        print("\n🎉 所有测试通过!")
        print("✅ 系统组件工作正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)