"""
A股趋势策略新闻监控模块

提供新闻数据采集、情感分析、关键词监控、风险评估等功能，
为A股趋势策略提供风险控制和决策支持。

主要模块:
- news_crawler: 新闻数据爬虫
- sentiment_analyzer: 情感分析
- keyword_matcher: 关键词匹配
- policy_calendar: 政策日历
- risk_assessor: 风险评估
- strategy_adapter: 策略适配器
"""

__version__ = "0.1.0"
__author__ = "Yushcheng777"

from .news_crawler import NewsCrawler
from .sentiment_analyzer import SentimentAnalyzer  
from .keyword_matcher import KeywordMatcher
from .policy_calendar import PolicyCalendar
from .risk_assessor import RiskAssessor
from .strategy_adapter import StrategyAdapter

__all__ = [
    "NewsCrawler",
    "SentimentAnalyzer",
    "KeywordMatcher", 
    "PolicyCalendar",
    "RiskAssessor",
    "StrategyAdapter",
]