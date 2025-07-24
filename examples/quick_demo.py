#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A股新闻政策监控系统快速演示

展示系统的核心功能和实际使用效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from news_monitor import create_monitor_system
from news_monitor.sentiment_analyzer import SentimentAnalyzer
from news_monitor.keyword_matcher import KeywordMatcher
from news_monitor.policy_calendar import PolicyCalendar
from news_monitor.risk_assessor import RiskAssessor
from news_monitor.strategy_adapter import StrategyAdapter


def quick_demo():
    """快速功能演示"""
    print("🚀 A股新闻政策监控系统快速演示")
    print("=" * 60)
    
    # 1. 模拟重要新闻事件
    sample_news = [
        {
            'title': '央行宣布降准0.5个百分点 释放长期资金约1万亿元',
            'content': '中国人民银行决定于2024年2月5日下调金融机构存款准备金率0.5个百分点，此次降准将释放长期资金约1万亿元，有利于保持银行体系流动性合理充裕，支持实体经济发展。',
            'source': 'pbc_official'
        },
        {
            'title': '证监会发布新规严厉打击财务造假行为',
            'content': '证监会今日发布关于加强上市公司财务信息监管的新规定，对财务造假行为将实施更严厉的处罚措施，涉及资本市场违法违规行为的企业将面临重罚。',
            'source': 'csrc_official'
        },
        {
            'title': '房地产市场调控政策再升级 多城市出台限购新措施',
            'content': '为进一步落实房住不炒的政策要求，多个一二线城市近日出台了更加严格的房地产调控措施，包括提高首付比例、限制购房资格等。',
            'source': 'sina_finance'
        }
    ]
    
    # 2. 创建分析组件
    analyzer = SentimentAnalyzer()
    matcher = KeywordMatcher()
    calendar_mgr = PolicyCalendar()
    assessor = RiskAssessor()
    adapter = StrategyAdapter()
    
    print("\n📊 新闻分析结果:")
    print("-" * 40)
    
    all_signals = []
    
    for i, news in enumerate(sample_news, 1):
        print(f"\n【新闻 {i}】{news['title']}")
        
        # 情感分析
        sentiment_result = analyzer.analyze_news_comprehensive(news)
        print(f"情感: {sentiment_result['sentiment']['sentiment_label']} "
              f"(得分: {sentiment_result['sentiment']['sentiment_score']:.2f})")
        
        # 关键词分析
        keyword_result = matcher.comprehensive_analysis(news['content'], news['title'])
        print(f"政策影响: {keyword_result['policy_impact']['impact_level']} "
              f"(得分: {keyword_result['policy_impact']['impact_score']:.2f})")
        print(f"风险信号: {keyword_result['risk_signals']['risk_level']} "
              f"(得分: {keyword_result['risk_signals']['risk_score']:.2f})")
        
        if keyword_result['industry_relevance']:
            industries = list(keyword_result['industry_relevance'].keys())[:3]
            print(f"相关行业: {', '.join(industries)}")
        
        # 风险评估
        risk_result = assessor.assess_news_risk(
            news, sentiment_result, keyword_result
        )
        print(f"综合风险: {risk_result['risk_level']} "
              f"(评分: {risk_result['risk_score']:.2f}, "
              f"置信度: {risk_result['confidence_score']:.2f})")
        
        # 生成策略信号
        if risk_result['risk_level'] in ['high', 'medium']:
            signal = adapter.process_risk_assessment(risk_result, news)
            all_signals.append(signal)
            print(f"策略建议: {signal.action.value} | {signal.trading_mode.value}")
    
    # 3. 政策日历检查
    print(f"\n📅 政策日历状态:")
    print("-" * 40)
    
    # 获取未来事件
    upcoming_events = calendar_mgr.get_upcoming_events(30)
    print(f"未来30天重要事件: {len(upcoming_events)}个")
    
    for event in upcoming_events[:3]:
        print(f"  • {event['name']}: {event.get('calculated_date', event.get('start_date'))} "
              f"({event['days_until']}天后) [{event.get('importance', 'unknown')}]")
    
    # 敏感期检查
    sensitivity = calendar_mgr.is_policy_sensitive_period()
    print(f"当前敏感期: {'是' if sensitivity['is_sensitive'] else '否'}")
    print(f"操作建议: {sensitivity['recommendation']}")
    
    # 生成政策信号
    policy_signal = adapter.process_policy_calendar(sensitivity)
    if policy_signal:
        all_signals.append(policy_signal)
    
    # 4. 综合策略建议
    print(f"\n🎯 综合策略建议:")
    print("-" * 40)
    
    if all_signals:
        aggregated_signal = adapter.aggregate_signals(all_signals)
        
        print(f"最终动作: {aggregated_signal['action'].value}")
        print(f"交易模式: {aggregated_signal['trading_mode'].value}")
        print(f"综合置信度: {aggregated_signal['confidence']:.2f}")
        
        if aggregated_signal['position_adjustment']:
            print("仓位调整建议:")
            for key, value in aggregated_signal['position_adjustment'].items():
                if value != 0:
                    action_desc = "增加" if value > 0 else "减少"
                    print(f"  • {key}: {action_desc}{abs(value)*100:.1f}%")
        
        print(f"决策依据: {aggregated_signal['reasoning'][:100]}...")
        
        # 风险等级汇总
        risk_levels = [s.signal_type for s in all_signals]
        print(f"活跃信号: {len(all_signals)}个 ({', '.join(set(risk_levels))})")
        
    else:
        print("当前无高风险信号，建议正常交易")
    
    # 5. 系统运行演示
    print(f"\n🖥️  完整系统演示:")
    print("-" * 40)
    
    # 创建完整监控系统
    monitor = create_monitor_system()
    
    # 模拟添加新闻到系统
    for news in sample_news:
        news['analyzed'] = False
        monitor.news_cache.append(news)
    
    print(f"系统初始化完成")
    print(f"模拟新闻数据: {len(monitor.news_cache)}条")
    
    # 执行分析流程
    monitor._analysis_job()
    monitor._risk_check_job()
    
    # 获取系统状态
    status = monitor.get_system_status()
    
    print(f"分析完成:")
    print(f"  • 缓存新闻: {status['system_info']['news_cache_size']}条")
    print(f"  • 活跃信号: {status['system_info']['active_signals_count']}个")
    print(f"  • 当前模式: {status['strategy_status']['current_mode']}")
    print(f"  • 仓位比例: {status['strategy_status']['current_position_ratio']:.2f}")
    
    if status['recent_news']:
        print(f"  • 最新分析:")
        for news in status['recent_news'][:2]:
            print(f"    - {news['title']} [{news['risk_level']}]")
    
    print(f"\n✅ 演示完成！")
    print("=" * 60)
    print("💡 系统已成功集成新闻监控、风险评估和策略联动功能")
    print("📈 可实现对A股市场的实时风险控制和策略优化")


if __name__ == "__main__":
    quick_demo()