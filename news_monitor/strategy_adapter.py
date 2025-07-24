#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略适配器模块

将新闻政策监控结果与A股趋势策略进行联动：
1. 风险事件响应机制
2. 政策窗口期处理
3. 行业轮动优化
4. 仓位动态调整
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class PositionAction(Enum):
    """仓位操作枚举"""
    HOLD = "hold"                    # 保持现有仓位
    REDUCE_LIGHT = "reduce_light"    # 轻度减仓 (10-20%)
    REDUCE_MEDIUM = "reduce_medium"  # 中度减仓 (30-50%)
    REDUCE_HEAVY = "reduce_heavy"    # 重度减仓 (50-80%)
    CLOSE_ALL = "close_all"          # 全部平仓
    PAUSE_TRADING = "pause_trading"  # 暂停交易
    INCREASE = "increase"            # 增仓


class TradingMode(Enum):
    """交易模式枚举"""
    NORMAL = "normal"                # 正常交易
    CONSERVATIVE = "conservative"    # 保守交易
    AGGRESSIVE = "aggressive"        # 激进交易
    DEFENSIVE = "defensive"          # 防御交易
    SUSPENDED = "suspended"          # 暂停交易


@dataclass
class StrategySignal:
    """策略信号数据类"""
    signal_id: str
    signal_type: str  # 'risk_event', 'policy_window', 'industry_rotation'
    action: PositionAction
    trading_mode: TradingMode
    confidence: float
    reason: str
    target_industries: List[str]
    avoid_industries: List[str]
    position_adjustment: Dict[str, float]  # 行业仓位调整比例
    valid_until: datetime
    metadata: Dict[str, Any]


class StrategyAdapter:
    """策略适配器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化策略适配器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 当前策略状态
        self.current_mode = TradingMode.NORMAL
        self.current_position_ratio = 1.0  # 当前仓位比例
        self.active_signals = []  # 活跃信号列表
        
        # 行业权重配置
        self.industry_weights = self._initialize_industry_weights()
        
        # 风险响应规则
        self.risk_response_rules = self._initialize_risk_rules()
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'max_position_reduction': 0.8,      # 最大减仓比例
            'min_position_ratio': 0.2,          # 最小仓位比例
            'signal_decay_hours': 24,           # 信号衰减时间(小时)
            'confidence_threshold': 0.6,        # 信号置信度阈值
            'enable_industry_rotation': True,   # 启用行业轮动
            'enable_policy_window': True,       # 启用政策窗口处理
            'max_simultaneous_signals': 5,      # 最大同时处理信号数
            'position_adjustment_step': 0.1,    # 仓位调整步长
        }
    
    def _initialize_industry_weights(self) -> Dict[str, float]:
        """初始化行业权重"""
        return {
            'finance': 0.25,        # 金融
            'technology': 0.20,     # 科技
            'consumption': 0.15,    # 消费
            'manufacturing': 0.15,  # 制造业
            'real_estate': 0.10,    # 房地产
            'healthcare': 0.10,     # 医药
            'energy': 0.05,         # 能源
        }
    
    def _initialize_risk_rules(self) -> Dict[str, Dict]:
        """初始化风险响应规则"""
        return {
            'high_risk': {
                'position_action': PositionAction.REDUCE_HEAVY,
                'trading_mode': TradingMode.DEFENSIVE,
                'position_reduction': 0.6,
                'signal_priority': 1
            },
            'medium_risk': {
                'position_action': PositionAction.REDUCE_MEDIUM,
                'trading_mode': TradingMode.CONSERVATIVE,
                'position_reduction': 0.3,
                'signal_priority': 2
            },
            'low_risk': {
                'position_action': PositionAction.REDUCE_LIGHT,
                'trading_mode': TradingMode.NORMAL,
                'position_reduction': 0.1,
                'signal_priority': 3
            },
            'policy_sensitive': {
                'position_action': PositionAction.REDUCE_MEDIUM,
                'trading_mode': TradingMode.CONSERVATIVE,
                'position_reduction': 0.4,
                'signal_priority': 2
            }
        }
    
    def process_risk_assessment(self, risk_assessment: Dict[str, Any], 
                              news_item: Dict[str, Any]) -> StrategySignal:
        """
        处理风险评估结果，生成策略信号
        
        Args:
            risk_assessment: 风险评估结果
            news_item: 新闻条目
            
        Returns:
            策略信号
        """
        risk_level = risk_assessment.get('risk_level', 'low')
        risk_score = risk_assessment.get('risk_score', 0.0)
        confidence = risk_assessment.get('confidence_score', 0.5)
        impact_areas = risk_assessment.get('impact_areas', [])
        
        # 获取对应的风险规则
        risk_rule = self.risk_response_rules.get(risk_level, self.risk_response_rules['low_risk'])
        
        # 生成信号ID
        signal_id = f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{risk_level}"
        
        # 计算信号有效期
        valid_hours = self.config['signal_decay_hours']
        if risk_level == 'high':
            valid_hours *= 2  # 高风险信号持续更久
        valid_until = datetime.now() + timedelta(hours=valid_hours)
        
        # 确定需要规避的行业
        avoid_industries = self._identify_risk_industries(impact_areas, risk_assessment)
        
        # 确定目标行业（相对安全的行业）
        target_industries = self._identify_safe_industries(avoid_industries, risk_level)
        
        # 计算仓位调整
        position_adjustment = self._calculate_position_adjustment(
            risk_rule, avoid_industries, target_industries
        )
        
        # 生成策略信号
        signal = StrategySignal(
            signal_id=signal_id,
            signal_type='risk_event',
            action=risk_rule['position_action'],
            trading_mode=risk_rule['trading_mode'],
            confidence=confidence,
            reason=f"风险事件响应: {news_item.get('title', '')[:50]}... (风险级别:{risk_level}, 得分:{risk_score:.2f})",
            target_industries=target_industries,
            avoid_industries=avoid_industries,
            position_adjustment=position_adjustment,
            valid_until=valid_until,
            metadata={
                'risk_assessment': risk_assessment,
                'news_item': news_item,
                'original_risk_level': risk_level,
                'original_risk_score': risk_score
            }
        )
        
        self.logger.info(f"生成风险响应信号: {signal_id}, 动作: {signal.action.value}, 置信度: {confidence:.2f}")
        
        return signal
    
    def process_policy_calendar(self, policy_context: Dict[str, Any]) -> Optional[StrategySignal]:
        """
        处理政策日历信息，生成策略信号
        
        Args:
            policy_context: 政策上下文信息
            
        Returns:
            策略信号或None
        """
        if not self.config['enable_policy_window']:
            return None
        
        is_sensitive = policy_context.get('is_sensitive', False)
        
        if not is_sensitive:
            return None
        
        sensitive_events = policy_context.get('sensitive_events', [])
        recommendation = policy_context.get('recommendation', 'normal_trading')
        
        # 根据建议生成相应的策略信号
        if recommendation == 'reduce_position':
            action = PositionAction.REDUCE_MEDIUM
            trading_mode = TradingMode.CONSERVATIVE
            position_reduction = 0.3
        elif recommendation == 'cautious_trading':
            action = PositionAction.REDUCE_LIGHT
            trading_mode = TradingMode.CONSERVATIVE
            position_reduction = 0.15
        else:
            return None
        
        # 生成信号ID
        signal_id = f"policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_window"
        
        # 计算有效期（直到政策事件结束后）
        max_event_days = 0
        for event_info in sensitive_events:
            event_days = event_info.get('days_diff', 0)
            max_event_days = max(max_event_days, event_days)
        
        valid_until = datetime.now() + timedelta(days=max_event_days + 2)
        
        # 策略信号
        signal = StrategySignal(
            signal_id=signal_id,
            signal_type='policy_window',
            action=action,
            trading_mode=trading_mode,
            confidence=0.7,  # 政策窗口期信号置信度固定为0.7
            reason=f"政策敏感期: 未来{max_event_days}天内有重要政策事件",
            target_industries=[],  # 政策窗口期不特定推荐行业
            avoid_industries=[],   # 政策窗口期不特定规避行业
            position_adjustment={'overall_reduction': position_reduction},
            valid_until=valid_until,
            metadata={
                'policy_context': policy_context,
                'sensitive_events': sensitive_events,
                'recommendation': recommendation
            }
        )
        
        self.logger.info(f"生成政策窗口信号: {signal_id}, 动作: {action.value}")
        
        return signal
    
    def process_industry_analysis(self, keyword_analysis: Dict[str, Any], 
                                sentiment_analysis: Dict[str, Any]) -> Optional[StrategySignal]:
        """
        处理行业分析，生成行业轮动信号
        
        Args:
            keyword_analysis: 关键词分析结果
            sentiment_analysis: 情感分析结果
            
        Returns:
            行业轮动信号或None
        """
        if not self.config['enable_industry_rotation']:
            return None
        
        # 获取行业相关性
        industry_relevance = keyword_analysis.get('industry_relevance', {})
        if not industry_relevance:
            return None
        
        # 获取市场情绪
        market_sentiment = keyword_analysis.get('market_sentiment', {})
        sentiment_label = market_sentiment.get('sentiment_label', 'neutral')
        sentiment_score = market_sentiment.get('sentiment_score', 0)
        
        # 分析政策影响
        policy_impact = keyword_analysis.get('policy_impact', {})
        policy_details = policy_impact.get('policy_details', {})
        
        # 确定受益和受损行业
        target_industries = []
        avoid_industries = []
        
        # 根据政策类型和情感分析确定行业影响
        if sentiment_label == 'positive' and abs(sentiment_score) > 0.3:
            # 正面新闻，相关行业可能受益
            for industry, data in industry_relevance.items():
                if data.get('relevance_score', 0) > 0.5:
                    target_industries.append(industry)
        elif sentiment_label == 'negative' and abs(sentiment_score) > 0.3:
            # 负面新闻，相关行业可能受损
            for industry, data in industry_relevance.items():
                if data.get('relevance_score', 0) > 0.5:
                    avoid_industries.append(industry)
        
        # 特殊政策影响处理
        if 'monetary_policy' in policy_details:
            # 货币政策影响：通常利好地产、基建，利空高估值科技股
            if sentiment_label == 'positive':
                target_industries.extend(['real_estate', 'manufacturing'])
                avoid_industries.extend(['technology'])
        
        if not target_industries and not avoid_industries:
            return None
        
        # 计算置信度
        confidence = min(abs(sentiment_score) + 0.3, 0.9)
        
        # 生成信号
        signal_id = f"industry_{datetime.now().strftime('%Y%m%d_%H%M%S')}_rotation"
        
        # 根据情感强度确定动作
        if abs(sentiment_score) > 0.6:
            action = PositionAction.INCREASE if sentiment_label == 'positive' else PositionAction.REDUCE_MEDIUM
        else:
            action = PositionAction.HOLD
        
        # 计算仓位调整
        position_adjustment = {}
        adjustment_ratio = min(abs(sentiment_score) * 0.5, 0.3)  # 最大调整30%
        
        for industry in target_industries:
            position_adjustment[industry] = adjustment_ratio
        for industry in avoid_industries:
            position_adjustment[industry] = -adjustment_ratio
        
        signal = StrategySignal(
            signal_id=signal_id,
            signal_type='industry_rotation',
            action=action,
            trading_mode=TradingMode.NORMAL,
            confidence=confidence,
            reason=f"行业轮动机会: {sentiment_label}情绪({sentiment_score:.2f}), 相关行业: {', '.join(target_industries + avoid_industries)}",
            target_industries=target_industries,
            avoid_industries=avoid_industries,
            position_adjustment=position_adjustment,
            valid_until=datetime.now() + timedelta(hours=12),  # 行业轮动信号较短期
            metadata={
                'keyword_analysis': keyword_analysis,
                'sentiment_analysis': sentiment_analysis,
                'industry_relevance': industry_relevance
            }
        )
        
        self.logger.info(f"生成行业轮动信号: {signal_id}, 目标行业: {target_industries}, 规避行业: {avoid_industries}")
        
        return signal
    
    def _identify_risk_industries(self, impact_areas: List[str], risk_assessment: Dict) -> List[str]:
        """识别风险行业"""
        risk_industries = []
        
        # 从影响领域直接映射
        risk_industries.extend(impact_areas)
        
        # 从风险因子推导
        main_risk_factors = risk_assessment.get('main_risk_factors', [])
        
        if 'policy_risk' in main_risk_factors:
            # 政策风险通常影响监管严格的行业
            risk_industries.extend(['finance', 'real_estate'])
        
        if 'market_risk' in main_risk_factors:
            # 市场风险影响高beta行业
            risk_industries.extend(['technology', 'finance'])
        
        return list(set(risk_industries))  # 去重
    
    def _identify_safe_industries(self, avoid_industries: List[str], risk_level: str) -> List[str]:
        """识别相对安全的行业"""
        all_industries = list(self.industry_weights.keys())
        safe_industries = [ind for ind in all_industries if ind not in avoid_industries]
        
        # 根据风险级别调整
        if risk_level == 'high':
            # 高风险时优选防御性行业
            defensive_industries = ['consumption', 'healthcare', 'energy']
            safe_industries = [ind for ind in safe_industries if ind in defensive_industries]
        
        return safe_industries[:3]  # 最多返回3个安全行业
    
    def _calculate_position_adjustment(self, risk_rule: Dict, 
                                     avoid_industries: List[str], 
                                     target_industries: List[str]) -> Dict[str, float]:
        """计算仓位调整方案"""
        adjustment = {}
        
        # 整体减仓
        overall_reduction = risk_rule.get('position_reduction', 0)
        if overall_reduction > 0:
            adjustment['overall_reduction'] = overall_reduction
        
        # 行业特定调整
        for industry in avoid_industries:
            # 风险行业额外减仓
            adjustment[industry] = -min(overall_reduction + 0.2, 0.8)
        
        for industry in target_industries:
            # 相对安全行业可适当增加配置
            adjustment[industry] = min(overall_reduction * 0.5, 0.3)
        
        return adjustment
    
    def aggregate_signals(self, signals: List[StrategySignal]) -> Dict[str, Any]:
        """
        聚合多个策略信号
        
        Args:
            signals: 策略信号列表
            
        Returns:
            聚合后的策略建议
        """
        if not signals:
            return {
                'action': PositionAction.HOLD,
                'trading_mode': TradingMode.NORMAL,
                'confidence': 0.0,
                'position_adjustment': {},
                'reasoning': '无有效信号'
            }
        
        # 过滤过期信号
        valid_signals = [s for s in signals if s.valid_until > datetime.now()]
        
        if not valid_signals:
            return {
                'action': PositionAction.HOLD,
                'trading_mode': TradingMode.NORMAL,
                'confidence': 0.0,
                'position_adjustment': {},
                'reasoning': '所有信号已过期'
            }
        
        # 按置信度和优先级排序
        sorted_signals = sorted(
            valid_signals, 
            key=lambda x: (x.confidence, self._get_signal_priority(x)), 
            reverse=True
        )
        
        # 主导信号（置信度最高的信号）
        primary_signal = sorted_signals[0]
        
        # 聚合仓位调整
        aggregated_adjustment = {}
        total_weight = 0
        
        for signal in sorted_signals:
            weight = signal.confidence
            total_weight += weight
            
            for key, value in signal.position_adjustment.items():
                if key not in aggregated_adjustment:
                    aggregated_adjustment[key] = 0
                aggregated_adjustment[key] += value * weight
        
        # 加权平均
        if total_weight > 0:
            for key in aggregated_adjustment:
                aggregated_adjustment[key] /= total_weight
        
        # 确定最终动作
        action_weights = {}
        for signal in sorted_signals:
            action = signal.action
            weight = signal.confidence
            if action not in action_weights:
                action_weights[action] = 0
            action_weights[action] += weight
        
        final_action = max(action_weights.keys(), key=lambda x: action_weights[x])
        
        # 确定交易模式
        mode_weights = {}
        for signal in sorted_signals:
            mode = signal.trading_mode
            weight = signal.confidence
            if mode not in mode_weights:
                mode_weights[mode] = 0
            mode_weights[mode] += weight
        
        final_mode = max(mode_weights.keys(), key=lambda x: mode_weights[x])
        
        # 聚合置信度
        avg_confidence = sum(s.confidence for s in sorted_signals) / len(sorted_signals)
        
        # 生成推理说明
        reasoning_parts = []
        for signal in sorted_signals[:3]:  # 最多显示前3个信号的原因
            reasoning_parts.append(f"{signal.signal_type}: {signal.reason[:100]}")
        
        reasoning = "; ".join(reasoning_parts)
        
        return {
            'action': final_action,
            'trading_mode': final_mode,
            'confidence': round(avg_confidence, 3),
            'position_adjustment': {k: round(v, 3) for k, v in aggregated_adjustment.items()},
            'reasoning': reasoning,
            'signal_count': len(sorted_signals),
            'primary_signal': primary_signal.signal_id,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_signal_priority(self, signal: StrategySignal) -> int:
        """获取信号优先级"""
        priority_map = {
            'risk_event': 1,      # 风险事件优先级最高
            'policy_window': 2,   # 政策窗口次之
            'industry_rotation': 3 # 行业轮动优先级最低
        }
        return priority_map.get(signal.signal_type, 5)
    
    def update_strategy_state(self, aggregated_signal: Dict[str, Any]):
        """
        更新策略状态
        
        Args:
            aggregated_signal: 聚合策略信号
        """
        # 更新交易模式
        self.current_mode = aggregated_signal['trading_mode']
        
        # 更新仓位比例
        position_adjustment = aggregated_signal.get('position_adjustment', {})
        overall_reduction = position_adjustment.get('overall_reduction', 0)
        
        if overall_reduction > 0:
            self.current_position_ratio *= (1 - overall_reduction)
            self.current_position_ratio = max(
                self.current_position_ratio, 
                self.config['min_position_ratio']
            )
        
        self.logger.info(f"策略状态更新: 模式={self.current_mode.value}, 仓位比例={self.current_position_ratio:.2f}")
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """获取当前策略状态"""
        return {
            'current_mode': self.current_mode.value,
            'current_position_ratio': self.current_position_ratio,
            'active_signals_count': len(self.active_signals),
            'industry_weights': self.industry_weights,
            'last_update': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    adapter = StrategyAdapter()
    
    # 模拟风险评估结果
    risk_assessment = {
        'risk_score': 0.8,
        'risk_level': 'high',
        'impact_areas': ['finance', 'real_estate'],
        'confidence_score': 0.7
    }
    
    news_item = {
        'title': '央行紧急调整货币政策应对市场风险',
        'content': '...'
    }
    
    # 生成风险响应信号
    risk_signal = adapter.process_risk_assessment(risk_assessment, news_item)
    
    print("=== 策略适配器测试 ===")
    print(f"信号类型: {risk_signal.signal_type}")
    print(f"建议动作: {risk_signal.action.value}")
    print(f"交易模式: {risk_signal.trading_mode.value}")
    print(f"置信度: {risk_signal.confidence}")
    print(f"规避行业: {risk_signal.avoid_industries}")
    print(f"目标行业: {risk_signal.target_industries}")
    
    # 聚合信号
    aggregated = adapter.aggregate_signals([risk_signal])
    print(f"\n聚合结果:")
    print(f"最终动作: {aggregated['action'].value}")
    print(f"仓位调整: {aggregated['position_adjustment']}")
    print(f"推理: {aggregated['reasoning'][:100]}...")