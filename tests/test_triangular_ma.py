"""
测试三角移动平均线指标
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from astrategy.indicators.triangular_ma import TriangularMA


class TestTriangularMA:
    """三角移动平均线测试"""
    
    def setup_method(self):
        """测试设置"""
        self.tma = TriangularMA(fast_period=5, slow_period=20, smoothing=3)
        
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, 100))
        self.test_data = pd.Series(prices, index=dates)
    
    def test_single_tma_calculation(self):
        """测试单个三角移动平均线计算"""
        result = self.tma.calculate_single_tma(self.test_data, 10)
        
        # 检查结果不为空
        assert result is not None
        assert len(result) == len(self.test_data)
        
        # 检查前几个值为NaN (由于计算窗口)
        assert pd.isna(result.iloc[0])
        
        # 检查后面的值不为NaN
        assert not pd.isna(result.iloc[-1])
    
    def test_fast_slow_calculation(self):
        """测试快慢线计算"""
        fast_tma, slow_tma = self.tma.calculate(self.test_data)
        
        # 检查返回结果
        assert fast_tma is not None
        assert slow_tma is not None
        assert len(fast_tma) == len(self.test_data)
        assert len(slow_tma) == len(self.test_data)
        
        # 快线应该比慢线更敏感（变化更快）
        fast_std = fast_tma.dropna().std()
        slow_std = slow_tma.dropna().std()
        assert fast_std >= slow_std  # 快线波动应该更大
    
    def test_signal_generation(self):
        """测试信号生成"""
        fast_tma, slow_tma = self.tma.calculate(self.test_data)
        signals = self.tma.generate_signals(fast_tma, slow_tma)
        
        # 检查信号格式
        assert signals is not None
        assert len(signals) == len(self.test_data)
        
        # 信号应该只包含 -1, 0, 1
        unique_signals = signals.dropna().unique()
        assert all(s in [-1, 0, 1] for s in unique_signals)
        
        # 应该有一些交叉信号
        signal_count = (signals != 0).sum()
        assert signal_count > 0
    
    def test_trend_strength_analysis(self):
        """测试趋势强度分析"""
        fast_tma, slow_tma = self.tma.calculate(self.test_data)
        analysis = self.tma.analyze_strength(fast_tma, slow_tma, self.test_data)
        
        # 检查分析结果结构
        expected_columns = [
            'price', 'fast_tma', 'slow_tma', 'price_vs_fast', 
            'price_vs_slow', 'ma_divergence', 'fast_trend', 
            'slow_trend', 'trend_consistency', 'trend_strength'
        ]
        
        for col in expected_columns:
            assert col in analysis.columns
        
        # 检查趋势强度范围
        trend_strength = analysis['trend_strength'].dropna()
        assert (trend_strength >= 0).all()
        assert (trend_strength <= 100).all()
    
    def test_a_share_optimized_params(self):
        """测试A股优化参数"""
        # 测试不同波动率环境的参数
        low_vol_params = self.tma.get_a_share_optimized_params("low")
        normal_params = self.tma.get_a_share_optimized_params("normal")
        high_vol_params = self.tma.get_a_share_optimized_params("high")
        
        # 检查参数结构
        for params in [low_vol_params, normal_params, high_vol_params]:
            assert 'fast_period' in params
            assert 'slow_period' in params
            assert 'smoothing' in params
        
        # 检查参数逻辑
        assert low_vol_params['fast_period'] < normal_params['fast_period']
        assert normal_params['fast_period'] < high_vol_params['fast_period']
    
    def test_signal_quality_validation(self):
        """测试信号质量验证"""
        fast_tma, slow_tma = self.tma.calculate(self.test_data)
        signals = self.tma.generate_signals(fast_tma, slow_tma)
        
        # 创建成交量数据
        volume = pd.Series(np.random.uniform(1000000, 5000000, len(self.test_data)), 
                          index=self.test_data.index)
        
        quality_result = self.tma.validate_signal_quality(signals, self.test_data, volume)
        
        # 检查质量验证结果
        assert 'signal' in quality_result.columns
        assert 'price' in quality_result.columns
        assert 'quality_score' in quality_result.columns
        
        # 质量分数应该在合理范围内
        quality_scores = quality_result['quality_score']
        non_zero_scores = quality_scores[quality_scores > 0]
        if len(non_zero_scores) > 0:
            assert (non_zero_scores >= 0).all()
            assert (non_zero_scores <= 100).all()


if __name__ == "__main__":
    # 简单运行测试
    test_tma = TestTriangularMA()
    test_tma.setup_method()
    
    print("运行三角移动平均线测试...")
    
    try:
        test_tma.test_single_tma_calculation()
        print("✅ 单个TMA计算测试通过")
        
        test_tma.test_fast_slow_calculation()
        print("✅ 快慢线计算测试通过")
        
        test_tma.test_signal_generation()
        print("✅ 信号生成测试通过")
        
        test_tma.test_trend_strength_analysis()
        print("✅ 趋势强度分析测试通过")
        
        test_tma.test_a_share_optimized_params()
        print("✅ A股优化参数测试通过")
        
        test_tma.test_signal_quality_validation()
        print("✅ 信号质量验证测试通过")
        
        print("\n🎉 所有测试通过!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()