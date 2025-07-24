"""
三角移动平均线指标 (Triangular Moving Average)

专门为A股市场优化的三角移动平均线实现，包含快慢线交叉信号生成。
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional


class TriangularMA:
    """三角移动平均线指标"""
    
    def __init__(self, fast_period: int = 5, slow_period: int = 30, smoothing: int = 3):
        """
        初始化三角移动平均线
        
        Args:
            fast_period: 快线周期，A股建议5-10
            slow_period: 慢线周期，A股建议20-30
            smoothing: 三角平滑系数
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.smoothing = smoothing
        
    def calculate_single_tma(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算单个三角移动平均线
        
        Args:
            data: 价格序列
            period: 移动平均周期
            
        Returns:
            三角移动平均线序列
        """
        # 第一步：计算简单移动平均
        sma1 = data.rolling(window=period).mean()
        
        # 第二步：对第一步结果再次计算移动平均 (三角化)
        triangle_period = (period + 1) // 2
        tma = sma1.rolling(window=triangle_period).mean()
        
        # 第三步：可选的额外平滑
        if self.smoothing > 1:
            tma = tma.rolling(window=self.smoothing).mean()
            
        return tma
    
    def calculate(self, data: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        计算快慢三角移动平均线
        
        Args:
            data: 价格数据 (通常使用收盘价)
            
        Returns:
            (fast_tma, slow_tma): 快线和慢线序列
        """
        fast_tma = self.calculate_single_tma(data, self.fast_period)
        slow_tma = self.calculate_single_tma(data, self.slow_period)
        
        return fast_tma, slow_tma
    
    def generate_signals(self, fast_tma: pd.Series, slow_tma: pd.Series) -> pd.Series:
        """
        生成交叉信号
        
        Args:
            fast_tma: 快线序列
            slow_tma: 慢线序列
            
        Returns:
            信号序列: 1=买入信号, -1=卖出信号, 0=无信号
        """
        signals = pd.Series(0, index=fast_tma.index, dtype=int)
        
        # 计算快慢线的相对位置
        fast_above_slow = (fast_tma > slow_tma).fillna(False)
        fast_above_slow_prev = fast_above_slow.shift(1).fillna(False)
        
        # 寻找交叉点
        cross_up = fast_above_slow & (~fast_above_slow_prev)  # 金叉
        cross_down = (~fast_above_slow) & fast_above_slow_prev  # 死叉
        
        signals[cross_up] = 1   # 买入信号
        signals[cross_down] = -1  # 卖出信号
        
        return signals
    
    def analyze_strength(self, fast_tma: pd.Series, slow_tma: pd.Series, 
                        price: pd.Series) -> pd.DataFrame:
        """
        分析趋势强度
        
        Args:
            fast_tma: 快线序列
            slow_tma: 慢线序列
            price: 当前价格
            
        Returns:
            包含趋势强度分析的DataFrame
        """
        df = pd.DataFrame({
            'price': price,
            'fast_tma': fast_tma,
            'slow_tma': slow_tma
        })
        
        # 计算价格相对于均线的位置
        df['price_vs_fast'] = (df['price'] - df['fast_tma']) / df['fast_tma']
        df['price_vs_slow'] = (df['price'] - df['slow_tma']) / df['slow_tma']
        
        # 计算快慢线的发散度
        df['ma_divergence'] = (df['fast_tma'] - df['slow_tma']) / df['slow_tma']
        
        # 趋势方向
        df['fast_trend'] = np.where(df['fast_tma'] > df['fast_tma'].shift(1), 1, -1)
        df['slow_trend'] = np.where(df['slow_tma'] > df['slow_tma'].shift(1), 1, -1)
        
        # 趋势一致性
        df['trend_consistency'] = df['fast_trend'] == df['slow_trend']
        
        # 趋势强度评分 (0-100)
        df['trend_strength'] = np.clip(
            abs(df['ma_divergence']) * 100 + 
            (df['trend_consistency'].astype(int) * 20) +
            (np.abs(df['price_vs_fast']) * 50), 
            0, 100
        )
        
        return df
    
    def get_a_share_optimized_params(self, volatility_regime: str = "normal") -> dict:
        """
        获取A股市场优化参数
        
        Args:
            volatility_regime: 波动率制度 ("low", "normal", "high")
            
        Returns:
            优化后的参数字典
        """
        if volatility_regime == "low":
            # 低波动环境：使用更敏感的参数
            return {
                "fast_period": 3,
                "slow_period": 20,
                "smoothing": 2
            }
        elif volatility_regime == "high":
            # 高波动环境：使用更稳定的参数
            return {
                "fast_period": 8,
                "slow_period": 40, 
                "smoothing": 5
            }
        else:
            # 正常波动环境：默认参数
            return {
                "fast_period": 5,
                "slow_period": 30,
                "smoothing": 3
            }
    
    def validate_signal_quality(self, signals: pd.Series, price: pd.Series, 
                               volume: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        验证信号质量 (A股特色功能)
        
        Args:
            signals: 交叉信号
            price: 价格数据
            volume: 成交量数据 (可选)
            
        Returns:
            信号质量评估结果
        """
        quality_df = pd.DataFrame(index=signals.index)
        quality_df['signal'] = signals
        quality_df['price'] = price
        
        # 基础质量检查
        signal_points = quality_df[quality_df['signal'] != 0].copy()
        
        if len(signal_points) == 0:
            return quality_df
        
        # 计算信号间隔 (避免过于频繁的信号)
        signal_points['signal_interval'] = signal_points.index.to_series().diff().dt.days
        
        # 价格变化幅度检查
        signal_points['price_change'] = signal_points['price'].pct_change()
        
        # 成交量确认 (如果提供)
        if volume is not None:
            volume_ma = volume.rolling(20).mean()
            signal_points['volume_confirm'] = volume.loc[signal_points.index] > volume_ma.loc[signal_points.index]
        
        # 质量评分
        quality_scores = []
        for idx, row in signal_points.iterrows():
            score = 50  # 基础分
            
            # 信号间隔评分 (避免过于频繁)
            if not pd.isna(row.get('signal_interval', np.nan)):
                if row['signal_interval'] >= 5:  # 至少5天间隔
                    score += 20
                elif row['signal_interval'] >= 3:
                    score += 10
                else:
                    score -= 10
            
            # 价格变化评分
            if not pd.isna(row.get('price_change', np.nan)):
                if abs(row['price_change']) > 0.02:  # 2%以上变化
                    score += 20
                elif abs(row['price_change']) > 0.01:
                    score += 10
            
            # 成交量确认评分
            if volume is not None and 'volume_confirm' in row:
                if row['volume_confirm']:
                    score += 20
                else:
                    score -= 10
            
            quality_scores.append(max(0, min(100, score)))
        
        signal_points['quality_score'] = quality_scores
        
        # 将质量评分映射回原始DataFrame
        quality_df['quality_score'] = 0
        quality_df.loc[signal_points.index, 'quality_score'] = signal_points['quality_score']
        
        return quality_df