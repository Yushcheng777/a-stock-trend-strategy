#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
情感分析模块

基于中文自然语言处理的新闻情感分析：
1. 情感分类：正面、负面、中性
2. 影响程度评估：高、中、低
3. 相关行业识别
4. 时效性判断
"""

import jieba
import logging
from typing import Dict, List, Any, Tuple
import re
from datetime import datetime
import numpy as np


class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化情感分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 加载情感词典
        self.positive_words = self._load_positive_words()
        self.negative_words = self._load_negative_words()
        self.degree_words = self._load_degree_words()
        self.negation_words = self._load_negation_words()
        
        # 行业关键词字典
        self.industry_keywords = self._load_industry_keywords()
        
        # 影响级别关键词
        self.impact_keywords = self._load_impact_keywords()
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'sentiment_threshold': 0.1,  # 情感强度阈值
            'impact_threshold': 0.3,     # 影响程度阈值
            'use_jieba_userdict': True,  # 是否使用自定义词典
        }
    
    def _load_positive_words(self) -> set:
        """加载正面情感词"""
        # 实际项目中应从文件加载
        positive_words = {
            '利好', '上涨', '增长', '突破', '支持', '促进', '优化', '提升',
            '利多', '涨停', '暴涨', '大涨', '强势', '看好', '推荐', '买入',
            '刺激', '释放', '宽松', '降准', '降息', '减税', '补贴', '扶持'
        }
        return positive_words
    
    def _load_negative_words(self) -> set:
        """加载负面情感词"""
        negative_words = {
            '利空', '下跌', '下滑', '暴跌', '大跌', '跌停', '崩盘', '危机',
            '风险', '警告', '限制', '禁止', '处罚', '调查', '违规', '停牌',
            '紧缩', '加息', '收紧', '监管', '打击', '整顿', '清理', '退市'
        }
        return negative_words
    
    def _load_degree_words(self) -> Dict[str, float]:
        """加载程度副词词典"""
        degree_words = {
            '非常': 2.0, '特别': 2.0, '极其': 2.0, '十分': 1.8,
            '很': 1.5, '比较': 1.2, '相对': 1.1, '略': 0.8,
            '稍': 0.7, '有点': 0.6, '一点': 0.5
        }
        return degree_words
    
    def _load_negation_words(self) -> set:
        """加载否定词"""
        negation_words = {'不', '没', '非', '无', '未', '否', '别', '莫'}
        return negation_words
    
    def _load_industry_keywords(self) -> Dict[str, List[str]]:
        """加载行业关键词字典"""
        industry_keywords = {
            '银行': ['银行', '金融', '存贷款', '利率', '资本充足率'],
            '房地产': ['房地产', '地产', '房价', '土地', '住房', '商品房'],
            '科技': ['科技', '人工智能', 'AI', '芯片', '半导体', '5G', '互联网'],
            '新能源': ['新能源', '电动车', '光伏', '风电', '锂电池', '充电桩'],
            '医药': ['医药', '生物', '疫苗', '药品', '医疗', '健康'],
            '消费': ['消费', '零售', '食品', '饮料', '服装', '家电'],
            '制造业': ['制造', '工业', '机械', '汽车', '钢铁', '化工'],
            '能源': ['石油', '天然气', '煤炭', '电力', '石化']
        }
        return industry_keywords
    
    def _load_impact_keywords(self) -> Dict[str, List[str]]:
        """加载影响级别关键词"""
        impact_keywords = {
            'high': [
                '央行', '降准', '降息', '加息', '货币政策', '财政政策',
                '证监会', '银保监会', '发改委', '重大', '紧急', '立即',
                '系统性风险', '流动性危机', '停牌', '退市', '重组'
            ],
            'medium': [
                '调整', '优化', '规范', '完善', '推进', '支持',
                '业绩', '财报', '分红', '增发', '配股', '股权激励'
            ],
            'low': [
                '一般', '常规', '例行', '正常', '维护', '技术',
                '公告', '提醒', '说明', '澄清'
            ]
        }
        return impact_keywords
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        文本预处理
        
        Args:
            text: 原始文本
            
        Returns:
            分词后的词语列表
        """
        # 清理文本
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 使用jieba分词
        words = list(jieba.cut(text))
        
        # 过滤停用词和短词
        words = [word for word in words if len(word) > 1]
        
        return words
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            
        Returns:
            情感分析结果字典
        """
        words = self.preprocess_text(text)
        
        positive_score = 0
        negative_score = 0
        word_count = len(words)
        
        # 遍历词语计算情感得分
        for i, word in enumerate(words):
            # 检查是否为情感词
            if word in self.positive_words:
                score = 1
            elif word in self.negative_words:
                score = -1
            else:
                continue
            
            # 检查程度副词
            degree_modifier = 1.0
            if i > 0 and words[i-1] in self.degree_words:
                degree_modifier = self.degree_words[words[i-1]]
            
            # 检查否定词
            negation_modifier = 1
            for j in range(max(0, i-3), i):
                if words[j] in self.negation_words:
                    negation_modifier = -1
                    break
            
            # 计算最终得分
            final_score = score * degree_modifier * negation_modifier
            
            if final_score > 0:
                positive_score += final_score
            else:
                negative_score += abs(final_score)
        
        # 归一化得分
        if word_count > 0:
            positive_score /= word_count
            negative_score /= word_count
        
        # 计算净情感得分
        net_sentiment = positive_score - negative_score
        
        # 确定情感类别
        if net_sentiment > self.config['sentiment_threshold']:
            sentiment_label = 'positive'
        elif net_sentiment < -self.config['sentiment_threshold']:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # 计算情感强度
        sentiment_intensity = abs(net_sentiment)
        
        return {
            'sentiment_label': sentiment_label,
            'sentiment_score': net_sentiment,
            'sentiment_intensity': sentiment_intensity,
            'positive_score': positive_score,
            'negative_score': negative_score,
            'word_count': word_count
        }
    
    def assess_impact_level(self, text: str, title: str = "") -> str:
        """
        评估影响程度
        
        Args:
            text: 新闻内容
            title: 新闻标题
            
        Returns:
            影响级别: 'high', 'medium', 'low'
        """
        combined_text = title + " " + text
        words = self.preprocess_text(combined_text)
        
        high_count = sum(1 for word in words if word in self.impact_keywords['high'])
        medium_count = sum(1 for word in words if word in self.impact_keywords['medium'])
        low_count = sum(1 for word in words if word in self.impact_keywords['low'])
        
        total_words = len(words)
        if total_words == 0:
            return 'low'
        
        high_ratio = high_count / total_words
        medium_ratio = medium_count / total_words
        
        if high_ratio > 0.05 or high_count >= 3:  # 高影响关键词占比超过5%或出现3次以上
            return 'high'
        elif medium_ratio > 0.1 or medium_count >= 5:
            return 'medium'
        else:
            return 'low'
    
    def identify_related_industries(self, text: str, title: str = "") -> List[str]:
        """
        识别相关行业
        
        Args:
            text: 新闻内容
            title: 新闻标题
            
        Returns:
            相关行业列表
        """
        combined_text = title + " " + text
        words = self.preprocess_text(combined_text)
        
        related_industries = []
        
        for industry, keywords in self.industry_keywords.items():
            match_count = sum(1 for word in words if word in keywords)
            if match_count > 0:
                related_industries.append({
                    'industry': industry,
                    'relevance_score': match_count / len(words),
                    'match_count': match_count
                })
        
        # 按相关性得分排序
        related_industries.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return [item['industry'] for item in related_industries[:3]]  # 返回最相关的3个行业
    
    def assess_time_sensitivity(self, text: str, title: str = "") -> str:
        """
        评估时效性
        
        Args:
            text: 新闻内容
            title: 新闻标题
            
        Returns:
            时效性: 'immediate', 'short_term', 'long_term'
        """
        combined_text = title + " " + text
        words = self.preprocess_text(combined_text)
        
        immediate_keywords = ['立即', '马上', '紧急', '当日', '即时', '盘中']
        short_term_keywords = ['本周', '本月', '近期', '短期', '临时']
        long_term_keywords = ['长期', '战略', '规划', '未来', '计划']
        
        immediate_count = sum(1 for word in words if word in immediate_keywords)
        short_term_count = sum(1 for word in words if word in short_term_keywords)
        long_term_count = sum(1 for word in words if word in long_term_keywords)
        
        if immediate_count > 0:
            return 'immediate'
        elif short_term_count > long_term_count:
            return 'short_term'
        else:
            return 'long_term'
    
    def analyze_news_comprehensive(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合分析新闻
        
        Args:
            news_item: 新闻条目字典
            
        Returns:
            综合分析结果
        """
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        
        # 情感分析
        sentiment_result = self.analyze_sentiment(title + " " + content)
        
        # 影响程度评估
        impact_level = self.assess_impact_level(content, title)
        
        # 相关行业识别
        related_industries = self.identify_related_industries(content, title)
        
        # 时效性评估
        time_sensitivity = self.assess_time_sensitivity(content, title)
        
        # 综合评分
        risk_score = self._calculate_risk_score(sentiment_result, impact_level, time_sensitivity)
        
        analysis_result = {
            'sentiment': sentiment_result,
            'impact_level': impact_level,
            'related_industries': related_industries,
            'time_sensitivity': time_sensitivity,
            'risk_score': risk_score,
            'analysis_time': datetime.now().isoformat()
        }
        
        return analysis_result
    
    def _calculate_risk_score(self, sentiment_result: Dict, impact_level: str, time_sensitivity: str) -> float:
        """
        计算风险评分
        
        Args:
            sentiment_result: 情感分析结果
            impact_level: 影响级别
            time_sensitivity: 时效性
            
        Returns:
            风险评分 (0-1)
        """
        # 基础风险得分
        base_risk = 0.0
        
        # 情感影响
        if sentiment_result['sentiment_label'] == 'negative':
            base_risk += sentiment_result['sentiment_intensity'] * 0.4
        elif sentiment_result['sentiment_label'] == 'positive':
            base_risk -= sentiment_result['sentiment_intensity'] * 0.2
        
        # 影响级别权重
        impact_weights = {'high': 0.4, 'medium': 0.2, 'low': 0.0}
        base_risk += impact_weights.get(impact_level, 0.0)
        
        # 时效性权重
        time_weights = {'immediate': 0.2, 'short_term': 0.1, 'long_term': 0.0}
        base_risk += time_weights.get(time_sensitivity, 0.0)
        
        # 确保得分在 0-1 范围内
        risk_score = max(0.0, min(1.0, base_risk))
        
        return risk_score


if __name__ == "__main__":
    # 测试代码
    analyzer = SentimentAnalyzer()
    
    # 测试新闻
    test_news = {
        'title': '央行决定降准0.5个百分点 释放长期资金约1万亿元',
        'content': '中国人民银行决定于2024年2月5日下调金融机构存款准备金率0.5个百分点，此次降准将释放长期资金约1万亿元，有利于保持银行体系流动性合理充裕，支持实体经济发展。'
    }
    
    result = analyzer.analyze_news_comprehensive(test_news)
    
    print("=== 新闻情感分析结果 ===")
    print(f"情感标签: {result['sentiment']['sentiment_label']}")
    print(f"情感得分: {result['sentiment']['sentiment_score']:.3f}")
    print(f"影响级别: {result['impact_level']}")
    print(f"相关行业: {result['related_industries']}")
    print(f"时效性: {result['time_sensitivity']}")
    print(f"风险评分: {result['risk_score']:.3f}")