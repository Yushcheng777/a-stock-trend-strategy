"""
A股风险管理器

专门处理A股市场特有的风险控制需求，包括T+1交易限制、涨跌停板、午间休市等。
"""

import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
import warnings


class RiskManager:
    """A股市场专用风险管理器"""
    
    def __init__(self, config: Dict):
        """
        初始化风险管理器
        
        Args:
            config: 风险管理配置字典
        """
        self.config = config
        self.risk_config = config.get('risk', {})
        self.a_share_config = config.get('a_share_features', {})
        self.market_config = config.get('market', {})
        
        # 持仓信息跟踪
        self.positions = {}  # {symbol: {'quantity': int, 'avg_price': float, 'entry_date': datetime}}
        self.portfolio_value = config.get('backtest', {}).get('initial_capital', 1000000)
        self.max_portfolio_value = self.portfolio_value
        self.daily_returns = []
        
    def check_t_plus_1_constraint(self, symbol: str, trade_date: datetime) -> bool:
        """
        检查T+1交易约束
        
        Args:
            symbol: 股票代码
            trade_date: 交易日期
            
        Returns:
            是否可以卖出 (True=可以卖出, False=不能卖出)
        """
        if not self.market_config.get('rules', {}).get('t_plus_1', True):
            return True  # 如果不是T+1制度，可以随时卖出
            
        if symbol not in self.positions:
            return True  # 没有持仓，不存在约束
            
        position = self.positions[symbol]
        entry_date = position.get('entry_date')
        
        if entry_date is None:
            return True
            
        # T+1: 买入当日不能卖出
        return trade_date.date() > entry_date.date()
    
    def check_price_limit(self, symbol: str, current_price: float, 
                         prev_close: float, board_type: str = "normal") -> Dict[str, bool]:
        """
        检查涨跌停板限制
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            prev_close: 前一交易日收盘价
            board_type: 板块类型 ("normal", "star", "chinext")
            
        Returns:
            涨跌停状态字典
        """
        # 获取涨跌停限制
        if board_type in ["star", "chinext"]:
            limit_ratio = self.market_config.get('rules', {}).get('price_limit_star', 0.20)
        else:
            limit_ratio = self.market_config.get('rules', {}).get('price_limit_normal', 0.10)
        
        # 计算涨跌停价格
        limit_up_price = prev_close * (1 + limit_ratio)
        limit_down_price = prev_close * (1 - limit_ratio)
        
        # 当前价格变动幅度
        price_change_ratio = (current_price - prev_close) / prev_close
        
        # 接近涨跌停的阈值
        approach_threshold = self.a_share_config.get('price_limit', {}).get('limit_approach_threshold', 0.08)
        
        return {
            'is_limit_up': current_price >= limit_up_price,
            'is_limit_down': current_price <= limit_down_price,
            'approaching_limit_up': price_change_ratio > (limit_ratio - approach_threshold),
            'approaching_limit_down': price_change_ratio < -(limit_ratio - approach_threshold),
            'limit_up_price': limit_up_price,
            'limit_down_price': limit_down_price,
            'price_change_ratio': price_change_ratio
        }
    
    def check_trading_time(self, current_time: datetime) -> Dict[str, bool]:
        """
        检查交易时间约束
        
        Args:
            current_time: 当前时间
            
        Returns:
            交易时间状态字典
        """
        trading_hours = self.market_config.get('trading_hours', {})
        
        # 解析交易时间
        morning_start = time.fromisoformat(trading_hours.get('morning_start', '09:30'))
        morning_end = time.fromisoformat(trading_hours.get('morning_end', '11:30'))
        afternoon_start = time.fromisoformat(trading_hours.get('afternoon_start', '13:00'))
        afternoon_end = time.fromisoformat(trading_hours.get('afternoon_end', '15:00'))
        
        current_time_only = current_time.time()
        
        # 判断是否在交易时间内
        in_morning_session = morning_start <= current_time_only <= morning_end
        in_afternoon_session = afternoon_start <= current_time_only <= afternoon_end
        in_trading_hours = in_morning_session or in_afternoon_session
        
        # 午间休市风险控制
        lunch_config = self.a_share_config.get('lunch_break', {})
        # 将time对象转换为datetime来计算时间差
        import datetime as dt
        today = current_time.date()
        morning_end_dt = dt.datetime.combine(today, morning_end)
        before_lunch_time = (morning_end_dt - timedelta(minutes=30)).time()
        before_lunch_break = before_lunch_time <= current_time_only <= morning_end
        
        return {
            'in_trading_hours': in_trading_hours,
            'in_morning_session': in_morning_session,
            'in_afternoon_session': in_afternoon_session,
            'before_lunch_break': before_lunch_break,
            'avoid_new_entry_lunch': lunch_config.get('avoid_new_entry', True) and before_lunch_break,
            'reduce_position_lunch': lunch_config.get('reduce_position_before', True) and before_lunch_break
        }
    
    def calculate_position_size(self, symbol: str, signal_strength: float, 
                               current_price: float, portfolio_value: float) -> int:
        """
        计算仓位大小
        
        Args:
            symbol: 股票代码
            signal_strength: 信号强度 (0-1)
            current_price: 当前价格
            portfolio_value: 当前组合价值
            
        Returns:
            建议股数
        """
        position_config = self.risk_config.get('position', {})
        
        # 基础仓位限制
        max_position = position_config.get('max_position', 0.95)
        initial_position = position_config.get('initial_position', 0.2)
        max_single_stock = position_config.get('max_single_stock', 0.15)
        
        # 根据信号强度调整仓位
        adjusted_position = initial_position * signal_strength
        
        # 限制单只股票最大仓位
        max_value_for_stock = portfolio_value * max_single_stock
        
        # 检查当前持仓
        current_position_value = 0
        if symbol in self.positions:
            current_position_value = self.positions[symbol]['quantity'] * current_price
        
        # 可用于新增仓位的资金
        available_value = max_value_for_stock - current_position_value
        target_value = portfolio_value * adjusted_position
        
        # 取较小值
        final_value = min(available_value, target_value)
        
        if final_value <= 0:
            return 0
            
        # 转换为股数 (A股最小交易单位为100股)
        shares = int(final_value / current_price / 100) * 100
        
        return max(0, shares)
    
    def check_stop_loss(self, symbol: str, current_price: float) -> Dict[str, any]:
        """
        检查止损条件
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            止损检查结果
        """
        if symbol not in self.positions:
            return {'should_stop_loss': False, 'reason': 'no_position'}
        
        position = self.positions[symbol]
        avg_price = position['avg_price']
        quantity = position['quantity']
        
        stop_loss_config = self.risk_config.get('stop_loss', {})
        max_loss = stop_loss_config.get('max_loss', 0.08)
        trailing_stop = stop_loss_config.get('trailing_stop', 0.05)
        
        # 当前盈亏比例
        pnl_ratio = (current_price - avg_price) / avg_price
        
        # 固定止损
        fixed_stop_loss = pnl_ratio <= -max_loss
        
        # 追踪止损 (需要跟踪最高价)
        trailing_stop_loss = False
        if hasattr(position, 'highest_price'):
            highest_price = position.get('highest_price', avg_price)
            trailing_stop_loss = (highest_price - current_price) / highest_price >= trailing_stop
        
        should_stop = fixed_stop_loss or trailing_stop_loss
        
        return {
            'should_stop_loss': should_stop,
            'pnl_ratio': pnl_ratio,
            'fixed_stop_loss': fixed_stop_loss,
            'trailing_stop_loss': trailing_stop_loss,
            'reason': 'fixed_stop' if fixed_stop_loss else ('trailing_stop' if trailing_stop_loss else 'none')
        }
    
    def check_take_profit(self, symbol: str, current_price: float) -> Dict[str, any]:
        """
        检查止盈条件
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            
        Returns:
            止盈检查结果
        """
        if symbol not in self.positions:
            return {'should_take_profit': False, 'reason': 'no_position'}
        
        position = self.positions[symbol]
        avg_price = position['avg_price']
        
        stop_profit_config = self.risk_config.get('stop_profit', {})
        target_profit = stop_profit_config.get('target_profit', 0.20)
        partial_profit = stop_profit_config.get('partial_profit', 0.15)
        
        # 当前盈利比例
        profit_ratio = (current_price - avg_price) / avg_price
        
        # 目标止盈
        target_take_profit = profit_ratio >= target_profit
        
        # 部分止盈
        partial_take_profit = profit_ratio >= partial_profit
        
        return {
            'should_take_profit': target_take_profit,
            'should_partial_profit': partial_take_profit,
            'profit_ratio': profit_ratio,
            'reason': 'target_profit' if target_take_profit else ('partial_profit' if partial_take_profit else 'none')
        }
    
    def check_max_drawdown(self, current_portfolio_value: float) -> Dict[str, any]:
        """
        检查最大回撤
        
        Args:
            current_portfolio_value: 当前组合价值
            
        Returns:
            回撤检查结果
        """
        self.max_portfolio_value = max(self.max_portfolio_value, current_portfolio_value)
        current_drawdown = (self.max_portfolio_value - current_portfolio_value) / self.max_portfolio_value
        
        drawdown_config = self.risk_config.get('drawdown', {})
        max_drawdown = drawdown_config.get('max_drawdown', 0.15)
        reduce_position_dd = drawdown_config.get('reduce_position_dd', 0.10)
        
        return {
            'current_drawdown': current_drawdown,
            'max_drawdown_exceeded': current_drawdown >= max_drawdown,
            'should_reduce_position': current_drawdown >= reduce_position_dd,
            'drawdown_level': 'severe' if current_drawdown >= max_drawdown else 
                            ('moderate' if current_drawdown >= reduce_position_dd else 'normal')
        }
    
    def analyze_gap_risk(self, current_price: float, prev_close: float, 
                        volume: Optional[float] = None) -> Dict[str, any]:
        """
        分析跳空缺口风险
        
        Args:
            current_price: 当前价格
            prev_close: 前收盘价
            volume: 当前成交量 (可选)
            
        Returns:
            缺口风险分析结果
        """
        gap_ratio = (current_price - prev_close) / prev_close
        gap_threshold = self.config.get('strategy', {}).get('entry', {}).get('gap_threshold', 0.03)
        
        # 缺口类型判断
        gap_type = None
        if abs(gap_ratio) >= gap_threshold:
            if gap_ratio > 0:
                gap_type = 'gap_up'
            else:
                gap_type = 'gap_down'
        
        # 缺口风险评估
        risk_level = 'low'
        if abs(gap_ratio) >= 0.05:  # 5%以上缺口
            risk_level = 'high'
        elif abs(gap_ratio) >= 0.03:  # 3-5%缺口
            risk_level = 'medium'
        
        return {
            'gap_ratio': gap_ratio,
            'gap_type': gap_type,
            'risk_level': risk_level,
            'should_avoid_entry': risk_level == 'high',
            'requires_confirmation': risk_level in ['medium', 'high'] and volume is not None
        }
    
    def update_position(self, symbol: str, action: str, quantity: int, 
                       price: float, trade_date: datetime):
        """
        更新持仓信息
        
        Args:
            symbol: 股票代码
            action: 交易动作 ('buy', 'sell')
            quantity: 交易数量
            price: 交易价格
            trade_date: 交易日期
        """
        if action == 'buy':
            if symbol in self.positions:
                # 加仓
                old_pos = self.positions[symbol]
                total_quantity = old_pos['quantity'] + quantity
                total_cost = old_pos['quantity'] * old_pos['avg_price'] + quantity * price
                new_avg_price = total_cost / total_quantity
                
                self.positions[symbol] = {
                    'quantity': total_quantity,
                    'avg_price': new_avg_price,
                    'entry_date': old_pos['entry_date'],  # 保持最初入场日期
                    'last_trade_date': trade_date
                }
            else:
                # 新建仓位
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': price,
                    'entry_date': trade_date,
                    'last_trade_date': trade_date,
                    'highest_price': price
                }
        
        elif action == 'sell':
            if symbol in self.positions:
                old_pos = self.positions[symbol]
                remaining_quantity = old_pos['quantity'] - quantity
                
                if remaining_quantity <= 0:
                    # 清仓
                    del self.positions[symbol]
                else:
                    # 减仓
                    self.positions[symbol]['quantity'] = remaining_quantity
                    self.positions[symbol]['last_trade_date'] = trade_date
    
    def get_portfolio_risk_metrics(self) -> Dict[str, float]:
        """
        获取组合风险指标
        
        Returns:
            组合风险指标字典
        """
        if len(self.daily_returns) < 2:
            return {}
        
        returns = np.array(self.daily_returns)
        
        # 基础统计指标
        annual_return = np.mean(returns) * 252
        annual_volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        cumulative_returns = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdowns = (peak - cumulative_returns) / peak
        max_drawdown = np.max(drawdowns)
        
        # VaR (Value at Risk)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'var_99': var_99,
            'total_trades': len([pos for pos in self.positions.values()]),
            'win_rate': self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """计算胜率 (简化实现)"""
        # 这里需要跟踪已平仓的交易记录
        # 简化实现，返回默认值
        return 0.6