"""
ADX (Average Directional Movement Index) 指标

专门为A股市场优化的ADX趋势强度确认指标。
"""

import numpy as np
import pandas as pd
from typing import Tuple


class ADXIndicator:
    """ADX趋势强度指标 - A股市场优化版本"""
    
    def __init__(self, period: int = 14, threshold: float = 25.0, strong_trend: float = 40.0):
        """
        初始化ADX指标
        
        Args:
            period: 计算周期，A股建议14-21
            threshold: ADX阈值，高于此值认为有趋势
            strong_trend: 强趋势阈值，高于此值认为是强趋势
        """
        self.period = period
        self.threshold = threshold
        self.strong_trend = strong_trend
    
    def calculate_directional_movement(self, high: pd.Series, low: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        计算方向性移动 (Directional Movement)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            
        Returns:
            (dm_plus, dm_minus): 正向和负向方向性移动
        """
        # 计算价格变动
        high_diff = high.diff()
        low_diff = -low.diff()
        
        # 正向方向性移动 (+DM)
        dm_plus = pd.Series(0.0, index=high.index)
        dm_plus[(high_diff > low_diff) & (high_diff > 0)] = high_diff
        
        # 负向方向性移动 (-DM)
        dm_minus = pd.Series(0.0, index=low.index)
        dm_minus[(low_diff > high_diff) & (low_diff > 0)] = low_diff
        
        return dm_plus, dm_minus
    
    def calculate_true_range(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        计算真实波动幅度 (True Range)
        
        Args:
            high: 最高价序列
            low: 最低价序列  
            close: 收盘价序列
            
        Returns:
            真实波动幅度序列
        """
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range
    
    def wilder_smoothing(self, data: pd.Series, period: int) -> pd.Series:
        """
        Wilder平滑法 (专用于ADX计算)
        
        Args:
            data: 待平滑的数据序列
            period: 平滑周期
            
        Returns:
            平滑后的序列
        """
        alpha = 1.0 / period
        return data.ewm(alpha=alpha, adjust=False).mean()
    
    def calculate(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
        """
        计算完整的ADX指标
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            
        Returns:
            包含ADX, +DI, -DI的DataFrame
        """
        # 计算方向性移动
        dm_plus, dm_minus = self.calculate_directional_movement(high, low)
        
        # 计算真实波动幅度
        true_range = self.calculate_true_range(high, low, close)
        
        # 平滑方向性移动和真实波动幅度
        dm_plus_smooth = self.wilder_smoothing(dm_plus, self.period)
        dm_minus_smooth = self.wilder_smoothing(dm_minus, self.period)
        tr_smooth = self.wilder_smoothing(true_range, self.period)
        
        # 计算方向性指标 (Directional Indicators)
        di_plus = 100 * dm_plus_smooth / tr_smooth.replace(0, np.nan)
        di_minus = 100 * dm_minus_smooth / tr_smooth.replace(0, np.nan)
        
        # 计算方向性移动指数 (Directional Movement Index)
        di_sum = di_plus + di_minus
        dx = 100 * abs(di_plus - di_minus) / di_sum.replace(0, np.nan)
        
        # 计算ADX (对DX进行Wilder平滑)
        adx = self.wilder_smoothing(dx, self.period)
        
        # 确保值在合理范围内
        di_plus = di_plus.clip(0, 100)
        di_minus = di_minus.clip(0, 100)
        dx = dx.clip(0, 100)
        adx = adx.clip(0, 100)
        
        # 返回结果
        result = pd.DataFrame({
            'ADX': adx,
            'DI_plus': di_plus,
            'DI_minus': di_minus,
            'DX': dx
        }, index=close.index)
        
        return result
    
    def generate_trend_signals(self, adx_data: pd.DataFrame) -> pd.DataFrame:
        """
        生成趋势确认信号
        
        Args:
            adx_data: ADX计算结果
            
        Returns:
            包含趋势信号的DataFrame
        """
        signals = adx_data.copy()
        
        # 趋势强度分类
        signals['trend_strength'] = pd.cut(
            signals['ADX'],
            bins=[0, self.threshold, self.strong_trend, 100],
            labels=['无趋势', '弱趋势', '强趋势'],
            include_lowest=True
        )
        
        # 趋势方向
        signals['trend_direction'] = np.where(
            signals['DI_plus'] > signals['DI_minus'], 1, -1
        )
        
        # DI交叉信号
        di_cross_up = (signals['DI_plus'] > signals['DI_minus']) & \
                      (signals['DI_plus'].shift(1) <= signals['DI_minus'].shift(1))
        di_cross_down = (signals['DI_plus'] < signals['DI_minus']) & \
                        (signals['DI_plus'].shift(1) >= signals['DI_minus'].shift(1))
        
        signals['DI_cross'] = 0
        signals.loc[di_cross_up, 'DI_cross'] = 1
        signals.loc[di_cross_down, 'DI_cross'] = -1
        
        # 综合信号 (需要ADX确认)
        signals['confirmed_signal'] = 0
        
        # 买入确认：DI+上穿DI-且ADX>阈值
        buy_confirm = di_cross_up & (signals['ADX'] > self.threshold)
        signals.loc[buy_confirm, 'confirmed_signal'] = 1
        
        # 卖出确认：DI-上穿DI+且ADX>阈值
        sell_confirm = di_cross_down & (signals['ADX'] > self.threshold)
        signals.loc[sell_confirm, 'confirmed_signal'] = -1
        
        return signals
    
    def analyze_trend_quality(self, adx_data: pd.DataFrame, price: pd.Series) -> pd.DataFrame:
        """
        分析趋势质量 (A股特色分析)
        
        Args:
            adx_data: ADX计算结果
            price: 价格数据
            
        Returns:
            趋势质量分析结果
        """
        analysis = adx_data.copy()
        analysis['price'] = price
        
        # ADX斜率 (趋势加速/减速)
        analysis['ADX_slope'] = analysis['ADX'].diff()
        analysis['ADX_acceleration'] = analysis['ADX_slope'].diff()
        
        # DI差值 (方向性强度)
        analysis['DI_diff'] = abs(analysis['DI_plus'] - analysis['DI_minus'])
        
        # 趋势持续性评分
        analysis['trend_persistence'] = 0
        
        # 计算趋势持续天数
        trend_dir = analysis['trend_direction']
        trend_changes = (trend_dir != trend_dir.shift(1)).cumsum()
        trend_persistence = trend_changes.groupby(trend_changes).cumcount() + 1
        analysis['trend_duration'] = trend_persistence
        
        # 质量评分 (0-100)
        quality_score = 0
        
        # ADX强度评分 (40%)
        adx_score = np.clip(analysis['ADX'] / 50 * 40, 0, 40)
        
        # DI差值评分 (30%)
        di_score = np.clip(analysis['DI_diff'] / 50 * 30, 0, 30)
        
        # 趋势持续性评分 (20%)
        persistence_score = np.clip(analysis['trend_duration'] / 10 * 20, 0, 20)
        
        # ADX斜率评分 (10%)
        slope_score = np.where(
            analysis['ADX_slope'] > 0, 10, 
            np.where(analysis['ADX_slope'] < -2, -5, 0)
        )
        
        analysis['quality_score'] = adx_score + di_score + persistence_score + slope_score
        
        return analysis
    
    def get_a_share_optimized_params(self, market_condition: str = "normal") -> dict:
        """
        获取A股市场优化参数
        
        Args:
            market_condition: 市场状态 ("bull", "bear", "normal", "volatile")
            
        Returns:
            优化参数字典
        """
        if market_condition == "bull":
            # 牛市：降低阈值，捕捉更多机会
            return {
                "period": 12,
                "threshold": 20.0,
                "strong_trend": 35.0
            }
        elif market_condition == "bear":
            # 熊市：提高阈值，避免假突破
            return {
                "period": 16,
                "threshold": 30.0,
                "strong_trend": 45.0
            }
        elif market_condition == "volatile":
            # 震荡市：使用更长周期，减少噪音
            return {
                "period": 21,
                "threshold": 35.0,
                "strong_trend": 50.0
            }
        else:
            # 正常市况：默认参数
            return {
                "period": 14,
                "threshold": 25.0,
                "strong_trend": 40.0
            }
    
    def detect_trend_reversal(self, adx_data: pd.DataFrame, lookback: int = 5) -> pd.Series:
        """
        检测趋势反转信号 (A股特色功能)
        
        Args:
            adx_data: ADX计算结果
            lookback: 回望周期
            
        Returns:
            反转信号序列
        """
        reversal_signals = pd.Series(0, index=adx_data.index)
        
        # ADX下降且DI交叉
        adx_declining = adx_data['ADX'] < adx_data['ADX'].shift(1)
        di_cross = adx_data['DI_cross'] != 0
        
        # 强趋势后的反转
        strong_trend_before = adx_data['ADX'].rolling(lookback).max() > self.strong_trend
        current_weak = adx_data['ADX'] < self.threshold
        
        # 反转信号条件
        reversal_condition = (
            (adx_declining & di_cross) |  # ADX下降且DI交叉
            (strong_trend_before & current_weak)  # 强趋势后变弱
        )
        
        reversal_signals[reversal_condition] = adx_data['trend_direction'][reversal_condition] * -1
        
        return reversal_signals