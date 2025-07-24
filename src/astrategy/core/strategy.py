"""
A股三角移动平均趋势策略核心实现

基于原EasyLanguage策略，针对A股市场特点进行优化的趋势跟踪策略。
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

from ..indicators.triangular_ma import TriangularMA
from ..indicators.adx import ADXIndicator
from ..risk.manager import RiskManager


class AStockTrendStrategy:
    """A股三角移动平均趋势策略"""
    
    def __init__(self, config: Dict):
        """
        初始化策略
        
        Args:
            config: 策略配置字典
        """
        self.config = config
        self.strategy_config = config.get('strategy', {})
        self.indicators_config = config.get('indicators', {})
        
        # 初始化技术指标
        tma_config = self.strategy_config.get('triangular_ma', {})
        self.triangular_ma = TriangularMA(
            fast_period=tma_config.get('fast_period', 5),
            slow_period=tma_config.get('slow_period', 30),
            smoothing=tma_config.get('smoothing', 3)
        )
        
        adx_config = self.strategy_config.get('adx', {})
        self.adx_indicator = ADXIndicator(
            period=adx_config.get('period', 14),
            threshold=adx_config.get('threshold', 25),
            strong_trend=adx_config.get('strong_trend', 40)
        )
        
        # 初始化风险管理器
        self.risk_manager = RiskManager(config)
        
        # 策略状态
        self.current_positions = {}
        self.trade_log = []
        self.performance_metrics = {}
        
        # 日志设置
        self.logger = logging.getLogger(__name__)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            data: 包含OHLCV数据的DataFrame
            
        Returns:
            包含所有指标的DataFrame
        """
        result = data.copy()
        
        # 计算三角移动平均线
        fast_tma, slow_tma = self.triangular_ma.calculate(data['close'])
        result['fast_tma'] = fast_tma
        result['slow_tma'] = slow_tma
        
        # 计算ADX指标
        adx_data = self.adx_indicator.calculate(data['high'], data['low'], data['close'])
        result = result.join(adx_data)
        
        # 计算MACD指标
        macd_config = self.indicators_config.get('macd', {})
        result = self._calculate_macd(result, macd_config)
        
        # 计算KDJ指标
        kdj_config = self.indicators_config.get('kdj', {})
        result = self._calculate_kdj(result, kdj_config)
        
        # 计算成交量指标
        volume_config = self.indicators_config.get('volume', {})
        result = self._calculate_volume_indicators(result, volume_config)
        
        return result
    
    def _calculate_macd(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """计算MACD指标"""
        fast_period = config.get('fast_period', 12)
        slow_period = config.get('slow_period', 26)
        signal_period = config.get('signal_period', 9)
        
        # 计算EMA
        ema_fast = data['close'].ewm(span=fast_period).mean()
        ema_slow = data['close'].ewm(span=slow_period).mean()
        
        # MACD线
        data['MACD'] = ema_fast - ema_slow
        
        # 信号线
        data['MACD_signal'] = data['MACD'].ewm(span=signal_period).mean()
        
        # MACD柱状图
        data['MACD_hist'] = data['MACD'] - data['MACD_signal']
        
        return data
    
    def _calculate_kdj(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """计算KDJ指标"""
        k_period = config.get('k_period', 9)
        d_period = config.get('d_period', 3)
        j_period = config.get('j_period', 3)
        
        # 计算RSV
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()
        rsv = (data['close'] - low_min) / (high_max - low_min) * 100
        
        # 计算K值
        data['KDJ_K'] = rsv.ewm(alpha=1/d_period).mean()
        
        # 计算D值
        data['KDJ_D'] = data['KDJ_K'].ewm(alpha=1/d_period).mean()
        
        # 计算J值
        data['KDJ_J'] = 3 * data['KDJ_K'] - 2 * data['KDJ_D']
        
        return data
    
    def _calculate_volume_indicators(self, data: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """计算成交量指标"""
        ma_period = config.get('ma_period', 20)
        
        # 成交量移动平均
        data['volume_ma'] = data['volume'].rolling(window=ma_period).mean()
        
        # 成交量比率
        data['volume_ratio'] = data['volume'] / data['volume_ma']
        
        # 量价关系
        data['price_volume_trend'] = ((data['close'] - data['close'].shift(1)) / 
                                     data['close'].shift(1) * data['volume']).cumsum()
        
        return data
    
    def generate_signals(self, data: pd.DataFrame, symbol: str, current_time: datetime) -> Dict[str, Any]:
        """
        生成交易信号
        
        Args:
            data: 包含所有指标的数据
            symbol: 股票代码
            current_time: 当前时间
            
        Returns:
            信号字典
        """
        if len(data) < 2:
            return {'action': 'hold', 'reason': 'insufficient_data'}
        
        current_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        
        # 基础信号检查
        signals = {
            'tma_signal': self._check_tma_signal(current_row, prev_row),
            'adx_signal': self._check_adx_signal(current_row, prev_row),
            'breakout_signal': self._check_breakout_signal(data),
            'volume_signal': self._check_volume_signal(current_row, prev_row),
            'macd_signal': self._check_macd_signal(current_row, prev_row),
            'kdj_signal': self._check_kdj_signal(current_row, prev_row)
        }
        
        # A股特色风险检查
        risk_checks = self._perform_a_share_risk_checks(
            symbol, current_row, prev_row, current_time
        )
        
        # 综合信号判断
        final_signal = self._combine_signals(signals, risk_checks, symbol, current_row)
        
        return final_signal
    
    def _check_tma_signal(self, current: pd.Series, prev: pd.Series) -> Dict[str, Any]:
        """检查三角移动平均线信号"""
        current_fast = current['fast_tma']
        current_slow = current['slow_tma']
        prev_fast = prev['fast_tma']
        prev_slow = prev['slow_tma']
        
        # 检查交叉
        golden_cross = (current_fast > current_slow) and (prev_fast <= prev_slow)
        death_cross = (current_fast < current_slow) and (prev_fast >= prev_slow)
        
        # 信号强度 (基于均线发散度)
        divergence = abs(current_fast - current_slow) / current_slow
        strength = min(divergence * 10, 1.0)  # 归一化到0-1
        
        if golden_cross:
            return {'signal': 1, 'strength': strength, 'type': 'golden_cross'}
        elif death_cross:
            return {'signal': -1, 'strength': strength, 'type': 'death_cross'}
        else:
            return {'signal': 0, 'strength': 0, 'type': 'no_cross'}
    
    def _check_adx_signal(self, current: pd.Series, prev: pd.Series) -> Dict[str, Any]:
        """检查ADX趋势确认信号"""
        adx = current['ADX']
        di_plus = current['DI_plus']
        di_minus = current['DI_minus']
        
        prev_di_plus = prev['DI_plus']
        prev_di_minus = prev['DI_minus']
        
        # 趋势强度
        trend_strength = 'weak'
        if adx > self.adx_indicator.strong_trend:
            trend_strength = 'strong'
        elif adx > self.adx_indicator.threshold:
            trend_strength = 'moderate'
        
        # DI交叉确认
        di_cross_up = (di_plus > di_minus) and (prev_di_plus <= prev_di_minus)
        di_cross_down = (di_plus < di_minus) and (prev_di_plus >= prev_di_minus)
        
        # 趋势确认信号
        if di_cross_up and adx > self.adx_indicator.threshold:
            return {'signal': 1, 'strength': min(adx/50, 1.0), 'trend_strength': trend_strength}
        elif di_cross_down and adx > self.adx_indicator.threshold:
            return {'signal': -1, 'strength': min(adx/50, 1.0), 'trend_strength': trend_strength}
        else:
            return {'signal': 0, 'strength': min(adx/50, 1.0), 'trend_strength': trend_strength}
    
    def _check_breakout_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查突破信号"""
        entry_config = self.strategy_config.get('entry', {})
        breakout_period = entry_config.get('breakout_period', 20)
        
        if len(data) < breakout_period + 1:
            return {'signal': 0, 'strength': 0, 'type': 'insufficient_data'}
        
        # 最近N日高低点
        recent_data = data.iloc[-(breakout_period+1):-1]  # 排除当前K线
        resistance = recent_data['high'].max()
        support = recent_data['low'].min()
        
        current_price = data.iloc[-1]['close']
        prev_price = data.iloc[-2]['close']
        
        # 突破确认
        upward_breakout = (current_price > resistance) and (prev_price <= resistance)
        downward_breakout = (current_price < support) and (prev_price >= support)
        
        # 突破强度
        if upward_breakout:
            strength = min((current_price - resistance) / resistance * 10, 1.0)
            return {'signal': 1, 'strength': strength, 'type': 'upward_breakout'}
        elif downward_breakout:
            strength = min((support - current_price) / support * 10, 1.0)
            return {'signal': -1, 'strength': strength, 'type': 'downward_breakout'}
        else:
            return {'signal': 0, 'strength': 0, 'type': 'no_breakout'}
    
    def _check_volume_signal(self, current: pd.Series, prev: pd.Series) -> Dict[str, Any]:
        """检查成交量确认信号"""
        entry_config = self.strategy_config.get('entry', {})
        volume_confirm = entry_config.get('volume_confirm', True)
        volume_ratio_threshold = entry_config.get('volume_ratio', 1.5)
        
        if not volume_confirm:
            return {'signal': 0, 'strength': 0.5, 'confirmed': True}
        
        volume_ratio = current.get('volume_ratio', 1.0)
        
        # 放量确认
        volume_surge = volume_ratio >= volume_ratio_threshold
        
        # 缩量警告
        volume_shrink = volume_ratio <= 0.5
        
        if volume_surge:
            return {'signal': 1, 'strength': min(volume_ratio/2, 1.0), 'confirmed': True}
        elif volume_shrink:
            return {'signal': -1, 'strength': 0.3, 'confirmed': False}
        else:
            return {'signal': 0, 'strength': 0.7, 'confirmed': True}
    
    def _check_macd_signal(self, current: pd.Series, prev: pd.Series) -> Dict[str, Any]:
        """检查MACD信号"""
        macd = current.get('MACD', 0)
        macd_signal = current.get('MACD_signal', 0)
        macd_hist = current.get('MACD_hist', 0)
        
        prev_macd = prev.get('MACD', 0)
        prev_signal = prev.get('MACD_signal', 0)
        
        # MACD金叉/死叉
        golden_cross = (macd > macd_signal) and (prev_macd <= prev_signal)
        death_cross = (macd < macd_signal) and (prev_macd >= prev_signal)
        
        # MACD背离检查 (简化)
        macd_strength = min(abs(macd_hist) * 10, 1.0)
        
        if golden_cross and macd > 0:
            return {'signal': 1, 'strength': macd_strength, 'type': 'macd_golden'}
        elif death_cross and macd < 0:
            return {'signal': -1, 'strength': macd_strength, 'type': 'macd_death'}
        else:
            return {'signal': 0, 'strength': macd_strength/2, 'type': 'macd_neutral'}
    
    def _check_kdj_signal(self, current: pd.Series, prev: pd.Series) -> Dict[str, Any]:
        """检查KDJ信号"""
        kdj_config = self.indicators_config.get('kdj', {})
        overbought = kdj_config.get('overbought', 80)
        oversold = kdj_config.get('oversold', 20)
        
        k = current.get('KDJ_K', 50)
        d = current.get('KDJ_D', 50)
        j = current.get('KDJ_J', 50)
        
        # KDJ超买超卖
        is_oversold = k < oversold and d < oversold
        is_overbought = k > overbought and d > overbought
        
        # KDJ金叉死叉
        prev_k = prev.get('KDJ_K', 50)
        prev_d = prev.get('KDJ_D', 50)
        
        kdj_golden = (k > d) and (prev_k <= prev_d) and is_oversold
        kdj_death = (k < d) and (prev_k >= prev_d) and is_overbought
        
        if kdj_golden:
            return {'signal': 1, 'strength': 0.8, 'type': 'kdj_oversold_golden'}
        elif kdj_death:
            return {'signal': -1, 'strength': 0.8, 'type': 'kdj_overbought_death'}
        else:
            return {'signal': 0, 'strength': 0.5, 'type': 'kdj_neutral'}
    
    def _perform_a_share_risk_checks(self, symbol: str, current: pd.Series, 
                                   prev: pd.Series, current_time: datetime) -> Dict[str, Any]:
        """执行A股特色风险检查"""
        risk_checks = {}
        
        # T+1约束检查
        risk_checks['t_plus_1'] = self.risk_manager.check_t_plus_1_constraint(symbol, current_time)
        
        # 涨跌停板检查
        risk_checks['price_limit'] = self.risk_manager.check_price_limit(
            symbol, current['close'], prev['close']
        )
        
        # 交易时间检查
        risk_checks['trading_time'] = self.risk_manager.check_trading_time(current_time)
        
        # 跳空缺口检查
        risk_checks['gap_risk'] = self.risk_manager.analyze_gap_risk(
            current['close'], prev['close'], current.get('volume')
        )
        
        # 止损止盈检查
        risk_checks['stop_loss'] = self.risk_manager.check_stop_loss(symbol, current['close'])
        risk_checks['take_profit'] = self.risk_manager.check_take_profit(symbol, current['close'])
        
        return risk_checks
    
    def _combine_signals(self, signals: Dict, risk_checks: Dict, 
                        symbol: str, current_data: pd.Series) -> Dict[str, Any]:
        """综合所有信号做出最终决策"""
        
        # 计算信号分数
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        # 权重配置 (可配置化)
        weights = {
            'tma_signal': 0.3,      # 主要信号
            'adx_signal': 0.25,     # 趋势确认
            'breakout_signal': 0.2, # 突破确认
            'volume_signal': 0.15,  # 成交量确认
            'macd_signal': 0.07,    # MACD辅助
            'kdj_signal': 0.03      # KDJ辅助
        }
        
        for signal_name, weight in weights.items():
            signal_info = signals.get(signal_name, {})
            signal_value = signal_info.get('signal', 0)
            signal_strength = signal_info.get('strength', 0)
            
            weighted_score = signal_value * signal_strength * weight
            total_weight += weight
            
            if weighted_score > 0:
                buy_score += weighted_score
            elif weighted_score < 0:
                sell_score += abs(weighted_score)
        
        # 归一化分数
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight
        
        # 风险检查过滤
        action = 'hold'
        reason = 'neutral_signal'
        signal_strength = max(buy_score, sell_score)
        
        # 买入信号检查
        if buy_score > sell_score and buy_score > 0.2:  # 降低买入阈值从0.3到0.2
            action = 'buy'
            reason = 'combined_buy_signal'
            
            # 风险检查
            if not risk_checks['trading_time']['in_trading_hours']:
                action = 'hold'
                reason = 'outside_trading_hours'
            elif risk_checks['price_limit']['approaching_limit_up']:
                action = 'hold'
                reason = 'approaching_limit_up'
            elif risk_checks['gap_risk']['should_avoid_entry']:
                action = 'hold'
                reason = 'gap_risk_too_high'
            elif risk_checks['trading_time']['avoid_new_entry_lunch']:
                action = 'hold'
                reason = 'lunch_break_risk'
        
        # 卖出信号检查
        elif sell_score > buy_score and sell_score > 0.2:  # 降低卖出阈值从0.3到0.2
            action = 'sell'
            reason = 'combined_sell_signal'
            
            # 风险检查
            if not risk_checks['t_plus_1']:
                action = 'hold'
                reason = 't_plus_1_constraint'
            elif not risk_checks['trading_time']['in_trading_hours']:
                action = 'hold'
                reason = 'outside_trading_hours'
            elif risk_checks['price_limit']['approaching_limit_down']:
                action = 'hold'
                reason = 'approaching_limit_down'
        
        # 强制止损止盈检查
        if risk_checks['stop_loss']['should_stop_loss']:
            action = 'sell'
            reason = 'stop_loss_triggered'
            signal_strength = 1.0
        elif risk_checks['take_profit']['should_take_profit']:
            action = 'sell'
            reason = 'take_profit_triggered'
            signal_strength = 1.0
        
        return {
            'action': action,
            'reason': reason,
            'signal_strength': signal_strength,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'detailed_signals': signals,
            'risk_checks': risk_checks,
            'timestamp': pd.Timestamp.now()
        }