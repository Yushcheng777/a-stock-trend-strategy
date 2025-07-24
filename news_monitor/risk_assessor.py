#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
风险评估模块

综合评估新闻政策对市场的风险影响：
1. 多维度风险评分
2. 风险级别判定
3. 风险预警机制
4. 历史风险事件对比
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from dataclasses import dataclass


@dataclass
class RiskEvent:
    """风险事件数据类"""
    event_id: str
    title: str
    content: str
    source: str
    publish_time: datetime
    risk_score: float
    risk_level: str
    risk_factors: Dict[str, float]
    impact_areas: List[str]
    time_sensitivity: str
    

class RiskAssessor:
    """风险评估器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化风险评估器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 风险权重配置
        self.risk_weights = self._initialize_risk_weights()
        
        # 历史风险事件数据库（实际应用中应该从数据库加载）
        self.historical_events = []
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'risk_threshold_high': 0.7,      # 高风险阈值
            'risk_threshold_medium': 0.4,    # 中风险阈值
            'time_decay_factor': 0.1,        # 时间衰减因子
            'volatility_weight': 0.3,        # 波动性权重
            'impact_weight': 0.4,            # 影响力权重
            'sentiment_weight': 0.3,         # 情感权重
            'enable_historical_comparison': True,
            'max_historical_days': 365,      # 历史对比最大天数
        }
    
    def _initialize_risk_weights(self) -> Dict[str, Dict[str, float]]:
        """初始化风险因子权重"""
        return {
            'policy_risk': {
                'monetary_policy': 0.9,      # 货币政策风险权重最高
                'fiscal_policy': 0.8,
                'regulatory_policy': 0.7,
                'trade_policy': 0.85
            },
            'market_risk': {
                'systemic_risk': 1.0,        # 系统性风险权重最高
                'liquidity_risk': 0.8,
                'credit_risk': 0.7,
                'operational_risk': 0.6
            },
            'industry_risk': {
                'finance': 0.9,              # 金融行业风险影响大
                'real_estate': 0.85,
                'technology': 0.7,
                'manufacturing': 0.6,
                'consumption': 0.5
            },
            'external_risk': {
                'geopolitical': 0.9,         # 地缘政治风险
                'trade_war': 0.85,
                'natural_disaster': 0.6,
                'pandemic': 0.95
            }
        }
    
    def assess_news_risk(self, 
                        news_item: Dict[str, Any],
                        sentiment_result: Dict[str, Any] = None,
                        keyword_result: Dict[str, Any] = None,
                        policy_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        评估单条新闻的风险
        
        Args:
            news_item: 新闻条目
            sentiment_result: 情感分析结果
            keyword_result: 关键词匹配结果
            policy_context: 政策上下文信息
            
        Returns:
            风险评估结果
        """
        # 提取基础信息
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        source = news_item.get('source', '')
        publish_time = news_item.get('publish_time', datetime.now().isoformat())
        
        if isinstance(publish_time, str):
            publish_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
        
        # 计算各维度风险得分
        risk_factors = {}
        
        # 1. 情感风险得分
        if sentiment_result:
            risk_factors['sentiment_risk'] = self._calculate_sentiment_risk(sentiment_result)
        else:
            risk_factors['sentiment_risk'] = 0.0
        
        # 2. 关键词风险得分
        if keyword_result:
            risk_factors['keyword_risk'] = self._calculate_keyword_risk(keyword_result)
        else:
            risk_factors['keyword_risk'] = 0.0
        
        # 3. 政策风险得分
        if policy_context:
            risk_factors['policy_risk'] = self._calculate_policy_risk(policy_context)
        else:
            risk_factors['policy_risk'] = 0.0
        
        # 4. 来源权威性风险调整
        risk_factors['source_credibility'] = self._calculate_source_risk(source)
        
        # 5. 时效性风险
        risk_factors['time_sensitivity'] = self._calculate_time_sensitivity_risk(
            publish_time, news_item.get('time_sensitivity', 'long_term')
        )
        
        # 6. 市场影响范围
        risk_factors['market_impact'] = self._calculate_market_impact_risk(
            news_item, keyword_result
        )
        
        # 计算综合风险得分
        comprehensive_risk_score = self._calculate_comprehensive_risk_score(risk_factors)
        
        # 确定风险级别
        risk_level = self._determine_risk_level(comprehensive_risk_score)
        
        # 识别主要风险因子
        main_risk_factors = self._identify_main_risk_factors(risk_factors)
        
        # 影响的具体领域
        impact_areas = self._identify_impact_areas(keyword_result, sentiment_result)
        
        # 时间敏感性
        time_sensitivity = self._assess_time_sensitivity(publish_time, content)
        
        # 风险建议
        risk_recommendation = self._generate_risk_recommendation(
            comprehensive_risk_score, risk_level, main_risk_factors
        )
        
        return {
            'risk_score': round(comprehensive_risk_score, 3),
            'risk_level': risk_level,
            'risk_factors': {k: round(v, 3) for k, v in risk_factors.items()},
            'main_risk_factors': main_risk_factors,
            'impact_areas': impact_areas,
            'time_sensitivity': time_sensitivity,
            'risk_recommendation': risk_recommendation,
            'assessment_time': datetime.now().isoformat(),
            'confidence_score': self._calculate_confidence_score(risk_factors)
        }
    
    def _calculate_sentiment_risk(self, sentiment_result: Dict[str, Any]) -> float:
        """计算情感风险得分"""
        sentiment_label = sentiment_result.get('sentiment_label', 'neutral')
        sentiment_intensity = sentiment_result.get('sentiment_intensity', 0)
        
        if sentiment_label == 'negative':
            return min(sentiment_intensity * 1.5, 1.0)  # 负面情感风险更高
        elif sentiment_label == 'positive':
            return max(0, sentiment_intensity * 0.3)    # 正面情感可能的风险
        else:
            return 0.1  # 中性情感的基础风险
    
    def _calculate_keyword_risk(self, keyword_result: Dict[str, Any]) -> float:
        """计算关键词风险得分"""
        risk_score = 0.0
        
        # 政策风险
        policy_impact = keyword_result.get('policy_impact', {})
        risk_score += policy_impact.get('impact_score', 0) * 0.4
        
        # 风险信号
        risk_signals = keyword_result.get('risk_signals', {})
        risk_score += risk_signals.get('risk_score', 0) * 0.6
        
        return min(risk_score, 1.0)
    
    def _calculate_policy_risk(self, policy_context: Dict[str, Any]) -> float:
        """计算政策上下文风险"""
        if not policy_context:
            return 0.0
        
        # 是否为敏感期
        is_sensitive = policy_context.get('is_sensitive', False)
        sensitivity_base = 0.3 if is_sensitive else 0.0
        
        # 即将到来的重要事件
        high_importance_events = policy_context.get('high_importance_events', [])
        event_risk = min(len(high_importance_events) * 0.1, 0.4)
        
        return min(sensitivity_base + event_risk, 1.0)
    
    def _calculate_source_risk(self, source: str) -> float:
        """计算来源风险权重"""
        # 官方来源风险权重更高（影响更大）
        official_sources = ['pbc_official', 'csrc_official', 'ndrc_official']
        high_credibility = ['xinhua', 'people_daily', 'china_securities']
        
        if source in official_sources:
            return 0.9  # 官方来源权威性高，影响大
        elif source in high_credibility:
            return 0.7
        else:
            return 0.5  # 一般来源
    
    def _calculate_time_sensitivity_risk(self, publish_time: datetime, time_sensitivity: str) -> float:
        """计算时效性风险"""
        # 计算新闻发布时间距现在的时间
        time_diff = datetime.now() - publish_time
        hours_diff = time_diff.total_seconds() / 3600
        
        # 时间衰减
        time_decay = np.exp(-hours_diff * self.config['time_decay_factor'])
        
        # 时效性权重
        sensitivity_weights = {
            'immediate': 1.0,
            'short_term': 0.7,
            'long_term': 0.3
        }
        
        sensitivity_weight = sensitivity_weights.get(time_sensitivity, 0.5)
        
        return time_decay * sensitivity_weight
    
    def _calculate_market_impact_risk(self, news_item: Dict, keyword_result: Dict = None) -> float:
        """计算市场影响范围风险"""
        base_impact = 0.2
        
        if keyword_result:
            # 行业相关性
            industry_relevance = keyword_result.get('industry_relevance', {})
            industry_count = len(industry_relevance)
            industry_impact = min(industry_count * 0.1, 0.4)
            
            # 市场情绪强度
            market_sentiment = keyword_result.get('market_sentiment', {})
            sentiment_intensity = abs(market_sentiment.get('sentiment_score', 0))
            
            return min(base_impact + industry_impact + sentiment_intensity * 0.3, 1.0)
        
        return base_impact
    
    def _calculate_comprehensive_risk_score(self, risk_factors: Dict[str, float]) -> float:
        """计算综合风险得分"""
        # 权重配置
        weights = {
            'sentiment_risk': self.config['sentiment_weight'],
            'keyword_risk': 0.25,
            'policy_risk': 0.15,
            'source_credibility': 0.1,
            'time_sensitivity': 0.1,
            'market_impact': self.config['impact_weight']
        }
        
        # 加权计算
        weighted_score = 0.0
        total_weight = 0.0
        
        for factor, score in risk_factors.items():
            weight = weights.get(factor, 0.05)
            weighted_score += score * weight
            total_weight += weight
        
        # 归一化
        if total_weight > 0:
            normalized_score = weighted_score / total_weight
        else:
            normalized_score = 0.0
        
        return min(normalized_score, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """确定风险级别"""
        if risk_score >= self.config['risk_threshold_high']:
            return 'high'
        elif risk_score >= self.config['risk_threshold_medium']:
            return 'medium'
        else:
            return 'low'
    
    def _identify_main_risk_factors(self, risk_factors: Dict[str, float]) -> List[str]:
        """识别主要风险因子"""
        # 按得分排序，返回前3个主要风险因子
        sorted_factors = sorted(
            risk_factors.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        main_factors = []
        for factor, score in sorted_factors[:3]:
            if score > 0.3:  # 只包含显著的风险因子
                main_factors.append(factor)
        
        return main_factors
    
    def _identify_impact_areas(self, keyword_result: Dict = None, sentiment_result: Dict = None) -> List[str]:
        """识别影响领域"""
        impact_areas = set()
        
        if keyword_result:
            # 从关键词结果中提取影响领域
            industry_relevance = keyword_result.get('industry_relevance', {})
            impact_areas.update(industry_relevance.keys())
            
            # 从政策影响中提取
            policy_impact = keyword_result.get('policy_impact', {})
            policy_details = policy_impact.get('policy_details', {})
            impact_areas.update(policy_details.keys())
        
        if sentiment_result:
            # 从情感分析中提取相关行业
            related_industries = sentiment_result.get('related_industries', [])
            impact_areas.update(related_industries)
        
        return list(impact_areas)
    
    def _assess_time_sensitivity(self, publish_time: datetime, content: str) -> str:
        """评估时间敏感性"""
        # 简单的时间敏感性判断
        time_diff = datetime.now() - publish_time
        hours_diff = time_diff.total_seconds() / 3600
        
        # 检查内容中的紧急词汇
        urgent_keywords = ['紧急', '立即', '马上', '当日', '盘中', '临时']
        urgent_count = sum(1 for keyword in urgent_keywords if keyword in content)
        
        if urgent_count > 0 or hours_diff < 2:
            return 'immediate'
        elif hours_diff < 24:
            return 'short_term'
        else:
            return 'long_term'
    
    def _generate_risk_recommendation(self, risk_score: float, risk_level: str, main_factors: List[str]) -> Dict[str, Any]:
        """生成风险建议"""
        recommendations = {
            'position_action': 'hold',  # hold, reduce, close
            'monitoring_level': 'normal',  # normal, enhanced, intensive
            'specific_actions': [],
            'reasoning': ''
        }
        
        if risk_level == 'high':
            recommendations['position_action'] = 'reduce'
            recommendations['monitoring_level'] = 'intensive'
            recommendations['specific_actions'] = [
                '立即减仓50%',
                '暂停新开仓',
                '加强市场监控',
                '准备止损措施'
            ]
            recommendations['reasoning'] = f'高风险事件，风险得分{risk_score:.2f}，主要风险因子：{", ".join(main_factors)}'
            
        elif risk_level == 'medium':
            recommendations['position_action'] = 'reduce'
            recommendations['monitoring_level'] = 'enhanced'
            recommendations['specific_actions'] = [
                '适当减仓20-30%',
                '谨慎开新仓',
                '密切关注后续发展'
            ]
            recommendations['reasoning'] = f'中等风险，建议谨慎操作，主要关注：{", ".join(main_factors)}'
            
        else:
            recommendations['position_action'] = 'hold'
            recommendations['monitoring_level'] = 'normal'
            recommendations['specific_actions'] = [
                '正常交易',
                '保持关注'
            ]
            recommendations['reasoning'] = '风险可控，可正常交易'
        
        return recommendations
    
    def _calculate_confidence_score(self, risk_factors: Dict[str, float]) -> float:
        """计算评估置信度"""
        # 基于风险因子的数量和分布计算置信度
        non_zero_factors = [v for v in risk_factors.values() if v > 0.1]
        
        if len(non_zero_factors) >= 3:
            # 多个维度都有信号，置信度高
            confidence = 0.8 + min(len(non_zero_factors) * 0.05, 0.2)
        elif len(non_zero_factors) >= 2:
            confidence = 0.6
        else:
            confidence = 0.4
        
        return min(confidence, 1.0)
    
    def batch_assess_risk(self, news_list: List[Dict[str, Any]], 
                         analysis_results: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        批量评估新闻风险
        
        Args:
            news_list: 新闻列表
            analysis_results: 对应的分析结果列表
            
        Returns:
            风险评估结果列表
        """
        risk_assessments = []
        
        for i, news_item in enumerate(news_list):
            # 获取对应的分析结果
            if analysis_results and i < len(analysis_results):
                analysis = analysis_results[i]
                sentiment_result = analysis.get('sentiment')
                keyword_result = analysis.get('keyword_analysis')
            else:
                sentiment_result = None
                keyword_result = None
            
            # 评估风险
            risk_assessment = self.assess_news_risk(
                news_item,
                sentiment_result,
                keyword_result
            )
            
            risk_assessments.append(risk_assessment)
        
        return risk_assessments
    
    def generate_risk_summary(self, risk_assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成风险评估摘要
        
        Args:
            risk_assessments: 风险评估结果列表
            
        Returns:
            风险摘要
        """
        if not risk_assessments:
            return {'error': '无风险评估数据'}
        
        # 统计各风险级别数量
        risk_levels = [r['risk_level'] for r in risk_assessments]
        level_counts = {
            'high': risk_levels.count('high'),
            'medium': risk_levels.count('medium'),
            'low': risk_levels.count('low')
        }
        
        # 计算平均风险得分
        risk_scores = [r['risk_score'] for r in risk_assessments]
        avg_risk_score = np.mean(risk_scores)
        
        # 识别最高风险事件
        highest_risk = max(risk_assessments, key=lambda x: x['risk_score'])
        
        # 主要风险因子统计
        all_factors = []
        for assessment in risk_assessments:
            all_factors.extend(assessment.get('main_risk_factors', []))
        
        factor_counts = {}
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        # 总体风险建议
        if level_counts['high'] > 0:
            overall_recommendation = 'high_risk_reduce_position'
        elif level_counts['medium'] > level_counts['low']:
            overall_recommendation = 'medium_risk_cautious'
        else:
            overall_recommendation = 'low_risk_normal'
        
        return {
            'summary_stats': {
                'total_assessments': len(risk_assessments),
                'risk_level_distribution': level_counts,
                'average_risk_score': round(avg_risk_score, 3),
                'highest_risk_score': highest_risk['risk_score']
            },
            'highest_risk_event': {
                'risk_score': highest_risk['risk_score'],
                'risk_level': highest_risk['risk_level'],
                'main_factors': highest_risk['main_risk_factors']
            },
            'main_risk_factors': dict(sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'overall_recommendation': overall_recommendation,
            'generated_at': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    assessor = RiskAssessor()
    
    # 测试新闻
    test_news = {
        'title': '央行紧急降准应对流动性危机',
        'content': '面对市场流动性紧张，央行决定立即降准1个百分点，释放资金应对系统性风险。',
        'source': 'pbc_official',
        'publish_time': datetime.now().isoformat()
    }
    
    # 模拟分析结果
    sentiment_result = {
        'sentiment_label': 'negative',
        'sentiment_intensity': 0.8,
        'related_industries': ['finance', 'real_estate']
    }
    
    keyword_result = {
        'policy_impact': {'impact_score': 0.9},
        'risk_signals': {'risk_score': 0.7},
        'industry_relevance': {'finance': {'count': 3}},
        'market_sentiment': {'sentiment_score': -0.6}
    }
    
    # 风险评估
    risk_result = assessor.assess_news_risk(test_news, sentiment_result, keyword_result)
    
    print("=== 风险评估结果 ===")
    print(f"风险得分: {risk_result['risk_score']}")
    print(f"风险级别: {risk_result['risk_level']}")
    print(f"主要风险因子: {risk_result['main_risk_factors']}")
    print(f"建议操作: {risk_result['risk_recommendation']['position_action']}")
    print(f"置信度: {risk_result['confidence_score']:.2f}")