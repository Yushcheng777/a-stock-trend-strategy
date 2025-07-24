#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
关键词匹配模块

提供多层级关键词监控功能：
1. 政策类关键词：货币政策、财政政策、监管政策
2. 行业关键词：房地产、科技、金融等
3. 风险关键词：地缘政治、贸易摩擦、系统性风险
"""

import re
import logging
from typing import Dict, List, Set, Any, Tuple
from datetime import datetime
import yaml


class KeywordMatcher:
    """关键词匹配器"""
    
    def __init__(self, config_file: str = None):
        """
        初始化关键词匹配器
        
        Args:
            config_file: 关键词配置文件路径
        """
        self.logger = logging.getLogger(__name__)
        
        # 加载关键词库
        if config_file:
            self.keyword_library = self._load_keywords_from_file(config_file)
        else:
            self.keyword_library = self._get_default_keywords()
            
        # 编译正则表达式以提高性能
        self.compiled_patterns = self._compile_patterns()
        
    def _get_default_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """获取默认关键词库"""
        return {
            'policy': {
                'monetary_policy': [
                    '货币政策', '降准', '降息', '加息', '流动性', '存款准备金率',
                    'MLF', '逆回购', '央行', '人民银行', '基准利率', '市场利率',
                    '货币供应量', 'M1', 'M2', '社会融资规模'
                ],
                'fiscal_policy': [
                    '财政政策', '减税', '降费', '基建', '消费刺激', '财政支出',
                    '预算', '赤字', '地方债', '专项债', '财政部', '国债',
                    '税收', '增值税', '企业所得税', '个人所得税'
                ],
                'regulatory_policy': [
                    '监管', '注册制', '退市', '规范发展', '证监会', '银保监会',
                    '金融监管', '资本市场', '上市公司', '信息披露', '内幕交易',
                    '市场操纵', '违法违规', '行政处罚'
                ]
            },
            'industry': {
                'real_estate': [
                    '房地产', '地产', '房价', '限购', '限贷', '房住不炒',
                    '土地市场', '商品房', '保障房', '房企', '房贷', '按揭',
                    '房地产税', '土地财政', '城镇化'
                ],
                'technology': [
                    '人工智能', 'AI', '芯片', '半导体', '5G', '6G', '云计算',
                    '大数据', '物联网', '区块链', '数字经济', '新基建',
                    '科技创新', '研发', '专利', '知识产权'
                ],
                'finance': [
                    '银行', '保险', '证券', '券商', '基金', '信托', 'P2P',
                    '金融科技', 'fintech', '数字货币', '移动支付', '资管',
                    '风控', '不良贷款', '资本充足率'
                ],
                'new_energy': [
                    '新能源', '电动车', '新能源汽车', '光伏', '风电', '水电',
                    '核电', '储能', '锂电池', '充电桩', '氢能', '碳中和',
                    '碳达峰', '绿色发展'
                ],
                'healthcare': [
                    '医药', '生物医药', '疫苗', '药品', '医疗器械', '医院',
                    '健康', '医保', '带量采购', 'CRO', '创新药', '仿制药'
                ],
                'consumption': [
                    '消费', '零售', '电商', '食品饮料', '服装', '家电',
                    '餐饮', '旅游', '酒店', '消费升级', '下沉市场', '直播带货'
                ]
            },
            'risk': {
                'geopolitical': [
                    '地缘政治', '国际关系', '贸易战', '贸易摩擦', '制裁',
                    '关税', '脱钩', '供应链', '国际制裁', '军事冲突'
                ],
                'systemic_risk': [
                    '系统性风险', '金融危机', '流动性危机', '债务危机',
                    '银行危机', '市场崩盘', '恐慌性抛售', '踩踏', '连锁反应'
                ],
                'market_risk': [
                    '暴跌', '跌停', '熔断', '大跌', '闪崩', '黑天鹅',
                    '灰犀牛', '尾部风险', '波动率', 'VIX', '恐慌指数'
                ],
                'corporate_risk': [
                    '财务造假', '退市', 'ST', '*ST', '债务违约', '资金链',
                    '破产', '重组', '停牌', '复牌', '业绩变脸', '商誉减值'
                ]
            },
            'market_sentiment': {
                'bullish': [
                    '利好', '看多', '买入', '推荐', '上调', '增持',
                    '超买', '突破', '创新高', '强势', '涨停', '大涨'
                ],
                'bearish': [
                    '利空', '看空', '卖出', '下调', '减持', '抛售',
                    '超卖', '跌破', '创新低', '弱势', '跌停', '大跌'
                ]
            }
        }
    
    def _load_keywords_from_file(self, config_file: str) -> Dict:
        """从YAML文件加载关键词库"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"加载关键词文件失败: {e}")
            return self._get_default_keywords()
    
    def _compile_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        """编译正则表达式模式以提高匹配性能"""
        compiled_patterns = {}
        
        for category, subcategories in self.keyword_library.items():
            compiled_patterns[category] = {}
            for subcategory, keywords in subcategories.items():
                # 创建正则表达式模式，使用单词边界
                pattern = '|'.join(re.escape(keyword) for keyword in keywords)
                compiled_patterns[category][subcategory] = re.compile(
                    f'({pattern})', 
                    re.IGNORECASE
                )
                
        return compiled_patterns
    
    def match_keywords(self, text: str, categories: List[str] = None) -> Dict[str, Any]:
        """
        匹配关键词
        
        Args:
            text: 待匹配的文本
            categories: 指定匹配的类别，如果为None则匹配所有类别
            
        Returns:
            匹配结果字典
        """
        if categories is None:
            categories = list(self.keyword_library.keys())
            
        matches = {}
        total_matches = 0
        
        for category in categories:
            if category not in self.compiled_patterns:
                continue
                
            matches[category] = {}
            
            for subcategory, pattern in self.compiled_patterns[category].items():
                found_matches = pattern.findall(text)
                
                if found_matches:
                    matches[category][subcategory] = {
                        'matches': found_matches,
                        'count': len(found_matches),
                        'unique_matches': list(set(found_matches))
                    }
                    total_matches += len(found_matches)
        
        return {
            'matches': matches,
            'total_matches': total_matches,
            'match_time': datetime.now().isoformat(),
            'text_length': len(text)
        }
    
    def calculate_category_scores(self, match_result: Dict[str, Any]) -> Dict[str, float]:
        """
        计算各类别的匹配得分
        
        Args:
            match_result: 关键词匹配结果
            
        Returns:
            各类别得分字典
        """
        scores = {}
        text_length = match_result.get('text_length', 1)
        
        for category, subcategories in match_result['matches'].items():
            category_score = 0
            category_matches = 0
            
            for subcategory, data in subcategories.items():
                category_matches += data['count']
            
            # 计算类别得分（匹配次数 / 文本长度）
            category_score = category_matches / text_length * 1000  # 乘以1000便于观察
            scores[category] = round(category_score, 4)
            
        return scores
    
    def assess_policy_impact(self, text: str) -> Dict[str, Any]:
        """
        评估政策影响
        
        Args:
            text: 新闻文本
            
        Returns:
            政策影响评估结果
        """
        policy_matches = self.match_keywords(text, ['policy'])
        
        # 政策影响权重
        policy_weights = {
            'monetary_policy': 0.4,   # 货币政策影响最大
            'fiscal_policy': 0.35,    # 财政政策次之
            'regulatory_policy': 0.25  # 监管政策
        }
        
        impact_score = 0
        policy_details = {}
        
        if 'policy' in policy_matches['matches']:
            for subcategory, data in policy_matches['matches']['policy'].items():
                weight = policy_weights.get(subcategory, 0.1)
                subcategory_score = data['count'] * weight
                impact_score += subcategory_score
                
                policy_details[subcategory] = {
                    'matches': data['unique_matches'],
                    'count': data['count'],
                    'weight': weight,
                    'score': subcategory_score
                }
        
        # 确定影响级别
        if impact_score >= 1.5:
            impact_level = 'high'
        elif impact_score >= 0.8:
            impact_level = 'medium'
        else:
            impact_level = 'low'
            
        return {
            'impact_score': round(impact_score, 3),
            'impact_level': impact_level,
            'policy_details': policy_details,
            'total_policy_matches': policy_matches['total_matches']
        }
    
    def detect_risk_signals(self, text: str) -> Dict[str, Any]:
        """
        检测风险信号
        
        Args:
            text: 新闻文本
            
        Returns:
            风险信号检测结果
        """
        risk_matches = self.match_keywords(text, ['risk'])
        
        # 风险权重
        risk_weights = {
            'systemic_risk': 1.0,      # 系统性风险权重最高
            'geopolitical': 0.8,       # 地缘政治风险
            'market_risk': 0.6,        # 市场风险
            'corporate_risk': 0.4      # 企业风险
        }
        
        risk_score = 0
        risk_details = {}
        risk_types = []
        
        if 'risk' in risk_matches['matches']:
            for subcategory, data in risk_matches['matches']['risk'].items():
                weight = risk_weights.get(subcategory, 0.2)
                subcategory_score = data['count'] * weight
                risk_score += subcategory_score
                
                if data['count'] > 0:
                    risk_types.append(subcategory)
                
                risk_details[subcategory] = {
                    'matches': data['unique_matches'],
                    'count': data['count'],
                    'weight': weight,
                    'score': subcategory_score
                }
        
        # 确定风险级别
        if risk_score >= 2.0:
            risk_level = 'high'
        elif risk_score >= 1.0:
            risk_level = 'medium'
        elif risk_score >= 0.3:
            risk_level = 'low'
        else:
            risk_level = 'minimal'
            
        return {
            'risk_score': round(risk_score, 3),
            'risk_level': risk_level,
            'risk_types': risk_types,
            'risk_details': risk_details,
            'total_risk_matches': risk_matches['total_matches']
        }
    
    def analyze_market_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析市场情绪
        
        Args:
            text: 新闻文本
            
        Returns:
            市场情绪分析结果
        """
        sentiment_matches = self.match_keywords(text, ['market_sentiment'])
        
        bullish_count = 0
        bearish_count = 0
        
        if 'market_sentiment' in sentiment_matches['matches']:
            bullish_count = sentiment_matches['matches']['market_sentiment'].get(
                'bullish', {}
            ).get('count', 0)
            bearish_count = sentiment_matches['matches']['market_sentiment'].get(
                'bearish', {}
            ).get('count', 0)
        
        # 计算情绪得分 (-1 到 1)
        total_sentiment = bullish_count + bearish_count
        if total_sentiment > 0:
            sentiment_score = (bullish_count - bearish_count) / total_sentiment
        else:
            sentiment_score = 0
            
        # 确定情绪类别
        if sentiment_score > 0.3:
            sentiment_label = 'bullish'
        elif sentiment_score < -0.3:
            sentiment_label = 'bearish'
        else:
            sentiment_label = 'neutral'
            
        return {
            'sentiment_score': round(sentiment_score, 3),
            'sentiment_label': sentiment_label,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'total_sentiment_matches': total_sentiment
        }
    
    def comprehensive_analysis(self, text: str, title: str = "") -> Dict[str, Any]:
        """
        综合关键词分析
        
        Args:
            text: 新闻正文
            title: 新闻标题
            
        Returns:
            综合分析结果
        """
        combined_text = title + " " + text
        
        # 完整匹配
        all_matches = self.match_keywords(combined_text)
        
        # 分类别分析
        policy_impact = self.assess_policy_impact(combined_text)
        risk_signals = self.detect_risk_signals(combined_text)
        market_sentiment = self.analyze_market_sentiment(combined_text)
        
        # 行业相关性分析
        industry_matches = self.match_keywords(combined_text, ['industry'])
        industry_relevance = {}
        
        if 'industry' in industry_matches['matches']:
            for industry, data in industry_matches['matches']['industry'].items():
                if data['count'] > 0:
                    industry_relevance[industry] = {
                        'matches': data['unique_matches'],
                        'count': data['count'],
                        'relevance_score': data['count'] / len(combined_text) * 1000
                    }
        
        # 计算综合重要性得分
        importance_score = (
            policy_impact['impact_score'] * 0.4 +
            risk_signals['risk_score'] * 0.4 +
            abs(market_sentiment['sentiment_score']) * 0.2
        )
        
        return {
            'all_matches': all_matches,
            'policy_impact': policy_impact,
            'risk_signals': risk_signals,
            'market_sentiment': market_sentiment,
            'industry_relevance': industry_relevance,
            'importance_score': round(importance_score, 3),
            'analysis_time': datetime.now().isoformat()
        }
    
    def add_custom_keywords(self, category: str, subcategory: str, keywords: List[str]):
        """
        添加自定义关键词
        
        Args:
            category: 类别
            subcategory: 子类别
            keywords: 关键词列表
        """
        if category not in self.keyword_library:
            self.keyword_library[category] = {}
            
        if subcategory not in self.keyword_library[category]:
            self.keyword_library[category][subcategory] = []
            
        # 添加新关键词
        existing_keywords = set(self.keyword_library[category][subcategory])
        new_keywords = [kw for kw in keywords if kw not in existing_keywords]
        
        self.keyword_library[category][subcategory].extend(new_keywords)
        
        # 重新编译正则表达式
        pattern = '|'.join(
            re.escape(keyword) 
            for keyword in self.keyword_library[category][subcategory]
        )
        
        if category not in self.compiled_patterns:
            self.compiled_patterns[category] = {}
            
        self.compiled_patterns[category][subcategory] = re.compile(
            f'({pattern})', 
            re.IGNORECASE
        )
        
        self.logger.info(f"添加了 {len(new_keywords)} 个新关键词到 {category}.{subcategory}")


if __name__ == "__main__":
    # 测试代码
    matcher = KeywordMatcher()
    
    # 测试文本
    test_text = """
    央行今日发布公告，决定降准0.5个百分点，释放长期资金约1万亿元。
    此次降准是为了保持银行体系流动性合理充裕，支持实体经济发展。
    市场分析师认为，这一政策对房地产、基建等行业形成利好，
    但也需要关注通胀风险和资产泡沫的可能性。
    """
    
    result = matcher.comprehensive_analysis(test_text)
    
    print("=== 关键词匹配分析结果 ===")
    print(f"政策影响得分: {result['policy_impact']['impact_score']}")
    print(f"政策影响级别: {result['policy_impact']['impact_level']}")
    print(f"风险得分: {result['risk_signals']['risk_score']}")
    print(f"风险级别: {result['risk_signals']['risk_level']}")
    print(f"市场情绪: {result['market_sentiment']['sentiment_label']}")
    print(f"综合重要性得分: {result['importance_score']}")
    
    if result['industry_relevance']:
        print("\n相关行业:")
        for industry, data in result['industry_relevance'].items():
            print(f"  {industry}: {data['matches']} (得分: {data['relevance_score']:.2f})")