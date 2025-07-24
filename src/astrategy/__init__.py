"""
A股趋势策略系统 (A-Share Trend Strategy System)

一个专门为中国A股市场设计的趋势跟踪策略系统，基于三角移动平均线、ADX确认和突破入场机制。
考虑了A股市场的特殊交易规则和市场特点。

主要功能:
- 三角移动平均线策略核心
- ADX趋势确认
- A股特色风险控制 (T+1, 涨跌停板等)
- 完整的回测框架
- 数据接口支持 (akshare, tushare)
"""

__version__ = "1.0.0"
__author__ = "A-Stock Strategy Team"

from .core.strategy import AStockTrendStrategy
from .core.engine import StrategyEngine
from .indicators.triangular_ma import TriangularMA
from .indicators.adx import ADXIndicator
from .risk.manager import RiskManager

__all__ = [
    "AStockTrendStrategy",
    "StrategyEngine", 
    "TriangularMA",
    "ADXIndicator",
    "RiskManager",
]