"""
策略执行引擎

协调策略、数据、风险管理等组件，提供统一的策略执行接口。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import yaml
import os

from .strategy import AStockTrendStrategy
from ..data.providers import DataProvider
from ..risk.manager import RiskManager
from ..utils.config import ConfigManager


class StrategyEngine:
    """策略执行引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化策略引擎
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # 初始化组件
        self.strategy = AStockTrendStrategy(self.config)
        self.data_provider = DataProvider(self.config)
        self.risk_manager = RiskManager(self.config)
        
        # 运行状态
        self.is_running = False
        self.current_time = None
        self.universe = []  # 股票池
        self.market_data = {}  # 市场数据缓存
        
        # 交易记录
        self.trade_history = []
        self.portfolio_history = []
        self.performance_metrics = {}
        
        # 日志设置
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        log_config = self.config.get('logging', {})
        
        # 创建日志目录
        log_file = log_config.get('file', 'logs/strategy.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
    
    def initialize(self, start_date: str, end_date: str, universe: List[str]):
        """
        初始化策略引擎
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            universe: 股票池列表
        """
        self.logger.info(f"初始化策略引擎: {start_date} 到 {end_date}")
        self.logger.info(f"股票池大小: {len(universe)}")
        
        self.universe = universe
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        
        # 加载数据
        self.logger.info("开始加载历史数据...")
        self._load_market_data()
        
        # 初始化组合
        initial_capital = self.config.get('backtest', {}).get('initial_capital', 1000000)
        self.portfolio = {
            'cash': initial_capital,
            'total_value': initial_capital,
            'positions': {},
            'daily_returns': []
        }
        
        self.logger.info("策略引擎初始化完成")
    
    def _load_market_data(self):
        """加载市场数据"""
        for symbol in self.universe:
            try:
                self.logger.debug(f"加载 {symbol} 数据...")
                data = self.data_provider.get_stock_data(
                    symbol, 
                    start_date=self.start_date,
                    end_date=self.end_date
                )
                
                if data is not None and len(data) > 0:
                    # 计算技术指标
                    data_with_indicators = self.strategy.calculate_indicators(data)
                    self.market_data[symbol] = data_with_indicators
                    self.logger.debug(f"{symbol} 数据加载完成: {len(data)} 条记录")
                else:
                    self.logger.warning(f"{symbol} 数据加载失败或为空")
                    
            except Exception as e:
                self.logger.error(f"加载 {symbol} 数据时出错: {str(e)}")
        
        self.logger.info(f"成功加载 {len(self.market_data)} 只股票的数据")
    
    def run_backtest(self) -> Dict[str, Any]:
        """
        运行回测
        
        Returns:
            回测结果字典
        """
        self.logger.info("开始回测...")
        self.is_running = True
        
        # 获取交易日历
        trading_days = self._get_trading_days()
        total_days = len(trading_days)
        
        for i, current_date in enumerate(trading_days):
            self.current_time = current_date
            
            # 进度日志
            if i % 50 == 0:
                progress = (i / total_days) * 100
                self.logger.info(f"回测进度: {progress:.1f}% ({current_date.strftime('%Y-%m-%d')})")
            
            # 每日处理
            self._process_trading_day(current_date)
            
            # 记录组合状态
            self._record_portfolio_state(current_date)
        
        self.is_running = False
        
        # 计算性能指标
        self.performance_metrics = self._calculate_performance_metrics()
        
        self.logger.info("回测完成")
        return self._generate_backtest_report()
    
    def _get_trading_days(self) -> pd.DatetimeIndex:
        """获取交易日历"""
        # 简化实现：使用工作日作为交易日
        # 实际应用中应该使用真实的A股交易日历
        all_days = pd.date_range(self.start_date, self.end_date, freq='D')
        trading_days = all_days[all_days.weekday < 5]  # 周一到周五
        return trading_days
    
    def _process_trading_day(self, current_date: datetime):
        """处理单个交易日"""
        daily_signals = {}
        
        # 为每只股票生成信号
        for symbol in self.universe:
            if symbol not in self.market_data:
                continue
                
            # 获取当前数据
            stock_data = self.market_data[symbol]
            current_data_slice = stock_data[stock_data.index <= current_date]
            
            if len(current_data_slice) < 50:  # 需要足够的历史数据
                continue
            
            # 生成交易信号
            signal = self.strategy.generate_signals(
                current_data_slice, symbol, current_date
            )
            
            daily_signals[symbol] = signal
            
            # 执行交易
            self._execute_trade(symbol, signal, current_date)
        
        # 更新投资组合
        self._update_portfolio(current_date)
    
    def _execute_trade(self, symbol: str, signal: Dict[str, Any], trade_date: datetime):
        """执行交易"""
        action = signal['action']
        
        if action == 'hold':
            return
        
        # 获取当前价格
        current_price = self._get_current_price(symbol, trade_date)
        if current_price is None:
            return
        
        # 计算交易数量
        if action == 'buy':
            quantity = self._calculate_buy_quantity(symbol, signal, current_price)
            if quantity > 0:
                self._execute_buy(symbol, quantity, current_price, trade_date, signal)
        
        elif action == 'sell':
            quantity = self._calculate_sell_quantity(symbol, signal)
            if quantity > 0:
                self._execute_sell(symbol, quantity, current_price, trade_date, signal)
    
    def _get_current_price(self, symbol: str, trade_date: datetime) -> Optional[float]:
        """获取当前价格"""
        if symbol not in self.market_data:
            return None
        
        stock_data = self.market_data[symbol]
        current_data = stock_data[stock_data.index <= trade_date]
        
        if len(current_data) == 0:
            return None
        
        return current_data.iloc[-1]['close']
    
    def _calculate_buy_quantity(self, symbol: str, signal: Dict, price: float) -> int:
        """计算买入数量"""
        signal_strength = signal.get('signal_strength', 0.5)
        
        # 使用风险管理器计算仓位
        quantity = self.risk_manager.calculate_position_size(
            symbol, signal_strength, price, self.portfolio['total_value']
        )
        
        # 检查资金是否足够
        required_cash = quantity * price * (1 + self._get_transaction_cost())
        if required_cash > self.portfolio['cash']:
            # 调整数量以适应可用资金
            quantity = int(self.portfolio['cash'] / (price * (1 + self._get_transaction_cost())) / 100) * 100
        
        return quantity
    
    def _calculate_sell_quantity(self, symbol: str, signal: Dict) -> int:
        """计算卖出数量"""
        if symbol not in self.portfolio['positions']:
            return 0
        
        current_position = self.portfolio['positions'][symbol]['quantity']
        
        # 根据信号类型决定卖出数量
        reason = signal.get('reason', '')
        
        if reason in ['stop_loss_triggered', 'take_profit_triggered']:
            # 止损止盈：全部卖出
            return current_position
        elif 'partial' in reason:
            # 部分止盈：卖出一半
            return current_position // 2
        else:
            # 常规卖出信号：全部卖出
            return current_position
    
    def _execute_buy(self, symbol: str, quantity: int, price: float, 
                    trade_date: datetime, signal: Dict):
        """执行买入交易"""
        if quantity <= 0:
            return
        
        # 计算交易成本
        transaction_cost = self._calculate_transaction_cost(quantity * price, 'buy')
        total_cost = quantity * price + transaction_cost
        
        # 检查资金
        if total_cost > self.portfolio['cash']:
            self.logger.warning(f"资金不足，无法买入 {symbol}: 需要 {total_cost:.2f}, 可用 {self.portfolio['cash']:.2f}")
            return
        
        # 更新持仓
        if symbol in self.portfolio['positions']:
            # 加仓
            old_pos = self.portfolio['positions'][symbol]
            new_quantity = old_pos['quantity'] + quantity
            new_avg_price = (old_pos['quantity'] * old_pos['avg_price'] + quantity * price) / new_quantity
            
            self.portfolio['positions'][symbol] = {
                'quantity': new_quantity,
                'avg_price': new_avg_price,
                'entry_date': old_pos['entry_date']
            }
        else:
            # 新建仓位
            self.portfolio['positions'][symbol] = {
                'quantity': quantity,
                'avg_price': price,
                'entry_date': trade_date
            }
        
        # 更新现金
        self.portfolio['cash'] -= total_cost
        
        # 更新风险管理器
        self.risk_manager.update_position(symbol, 'buy', quantity, price, trade_date)
        
        # 记录交易
        trade_record = {
            'date': trade_date,
            'symbol': symbol,
            'action': 'buy',
            'quantity': quantity,
            'price': price,
            'cost': transaction_cost,
            'total_amount': total_cost,
            'signal': signal
        }
        self.trade_history.append(trade_record)
        
        self.logger.info(f"买入: {symbol} {quantity}股 @ {price:.2f} 成本:{transaction_cost:.2f}")
    
    def _execute_sell(self, symbol: str, quantity: int, price: float, 
                     trade_date: datetime, signal: Dict):
        """执行卖出交易"""
        if symbol not in self.portfolio['positions'] or quantity <= 0:
            return
        
        current_position = self.portfolio['positions'][symbol]
        if quantity > current_position['quantity']:
            quantity = current_position['quantity']
        
        # 计算交易成本
        transaction_cost = self._calculate_transaction_cost(quantity * price, 'sell')
        total_proceeds = quantity * price - transaction_cost
        
        # 更新持仓
        remaining_quantity = current_position['quantity'] - quantity
        if remaining_quantity <= 0:
            # 清仓
            del self.portfolio['positions'][symbol]
        else:
            # 减仓
            self.portfolio['positions'][symbol]['quantity'] = remaining_quantity
        
        # 更新现金
        self.portfolio['cash'] += total_proceeds
        
        # 更新风险管理器
        self.risk_manager.update_position(symbol, 'sell', quantity, price, trade_date)
        
        # 计算盈亏
        pnl = (price - current_position['avg_price']) * quantity - transaction_cost
        pnl_ratio = pnl / (current_position['avg_price'] * quantity)
        
        # 记录交易
        trade_record = {
            'date': trade_date,
            'symbol': symbol,
            'action': 'sell',
            'quantity': quantity,
            'price': price,
            'cost': transaction_cost,
            'total_amount': total_proceeds,
            'pnl': pnl,
            'pnl_ratio': pnl_ratio,
            'signal': signal
        }
        self.trade_history.append(trade_record)
        
        self.logger.info(f"卖出: {symbol} {quantity}股 @ {price:.2f} 盈亏:{pnl:.2f}({pnl_ratio:.2%})")
    
    def _get_transaction_cost(self) -> float:
        """获取交易成本率"""
        costs = self.config.get('backtest', {}).get('costs', {})
        commission = costs.get('commission', 0.0003)
        return commission
    
    def _calculate_transaction_cost(self, amount: float, action: str) -> float:
        """计算交易成本"""
        costs = self.config.get('backtest', {}).get('costs', {})
        
        # 佣金
        commission = amount * costs.get('commission', 0.0003)
        commission = max(commission, costs.get('min_commission', 5))  # 最低佣金
        
        # 印花税 (仅卖出时收取)
        stamp_tax = 0
        if action == 'sell':
            stamp_tax = amount * costs.get('stamp_tax', 0.001)
        
        # 过户费
        transfer_fee = amount * costs.get('transfer_fee', 0.00002)
        
        # 滑点
        slippage = amount * costs.get('slippage', {}).get('percentage', 0.001)
        
        return commission + stamp_tax + transfer_fee + slippage
    
    def _update_portfolio(self, current_date: datetime):
        """更新投资组合价值"""
        total_position_value = 0
        
        # 计算持仓市值
        for symbol, position in self.portfolio['positions'].items():
            current_price = self._get_current_price(symbol, current_date)
            if current_price:
                position_value = position['quantity'] * current_price
                total_position_value += position_value
        
        # 更新总价值
        self.portfolio['total_value'] = self.portfolio['cash'] + total_position_value
        
        # 计算当日收益率
        if len(self.portfolio_history) > 0:
            prev_value = self.portfolio_history[-1]['total_value']
            daily_return = (self.portfolio['total_value'] - prev_value) / prev_value
            self.portfolio['daily_returns'].append(daily_return)
    
    def _record_portfolio_state(self, current_date: datetime):
        """记录投资组合状态"""
        portfolio_snapshot = {
            'date': current_date,
            'cash': self.portfolio['cash'],
            'total_value': self.portfolio['total_value'],
            'positions': self.portfolio['positions'].copy(),
            'position_count': len(self.portfolio['positions'])
        }
        self.portfolio_history.append(portfolio_snapshot)
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if len(self.portfolio['daily_returns']) == 0:
            return {}
        
        returns = np.array(self.portfolio['daily_returns'])
        
        # 基础统计
        total_return = (self.portfolio['total_value'] / self.config.get('backtest', {}).get('initial_capital', 1000000)) - 1
        annual_return = np.mean(returns) * 252
        annual_volatility = np.std(returns) * np.sqrt(252)
        
        # 夏普比率
        risk_free_rate = 0.03  # 假设无风险利率3%
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
        
        # 最大回撤
        portfolio_values = [p['total_value'] for p in self.portfolio_history]
        portfolio_series = pd.Series(portfolio_values)
        cumulative_max = portfolio_series.expanding().max()
        drawdowns = (portfolio_series - cumulative_max) / cumulative_max
        max_drawdown = drawdowns.min()
        
        # 胜率和盈亏比
        win_trades = [t for t in self.trade_history if t.get('pnl', 0) > 0]
        loss_trades = [t for t in self.trade_history if t.get('pnl', 0) < 0]
        
        win_rate = len(win_trades) / len([t for t in self.trade_history if 'pnl' in t]) if self.trade_history else 0
        
        avg_win = np.mean([t['pnl'] for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in loss_trades]) if loss_trades else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'total_trades': len(self.trade_history),
            'winning_trades': len(win_trades),
            'losing_trades': len(loss_trades)
        }
    
    def _generate_backtest_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        return {
            'performance_metrics': self.performance_metrics,
            'portfolio_history': self.portfolio_history,
            'trade_history': self.trade_history,
            'final_portfolio': self.portfolio,
            'config': self.config
        }