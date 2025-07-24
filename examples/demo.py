#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A股新闻政策监控系统使用示例

演示如何使用新闻监控系统的各个功能
"""

import sys
import os

# 添加路径以便导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_monitor import create_monitor_system
from news_monitor.news_crawler import NewsCrawler
from news_monitor.sentiment_analyzer import SentimentAnalyzer
from news_monitor.keyword_matcher import KeywordMatcher
from news_monitor.policy_calendar import PolicyCalendar
from news_monitor.risk_assessor import RiskAssessor
from news_monitor.strategy_adapter import StrategyAdapter
import time
import json


def demo_news_crawler():
    """演示新闻爬虫功能"""
    print("=" * 50)
    print("新闻爬虫功能演示")
    print("=" * 50)
    
    crawler = NewsCrawler()
    
    # 爬取新闻
    print("正在爬取新闻数据...")
    news_data = crawler.crawl_all_sources(hours_back=24)
    
    for source, news_list in news_data.items():
        print(f"\n{source}: {len(news_list)} 条新闻")
        for news in news_list[:2]:  # 显示前2条
            print(f"  - {news.get('title', '')[:50]}...")
    
    # 转换为DataFrame
    df = crawler.save_news_to_df(news_data)
    print(f"\n总计获取 {len(df)} 条新闻数据")
    
    return news_data


def demo_sentiment_analysis(news_data):
    """演示情感分析功能"""
    print("\n" + "=" * 50)
    print("情感分析功能演示")
    print("=" * 50)
    
    analyzer = SentimentAnalyzer()
    
    # 获取一条新闻进行分析
    sample_news = None
    for news_list in news_data.values():
        if news_list:
            sample_news = news_list[0]
            break
    
    if sample_news:
        print(f"分析新闻: {sample_news.get('title', '')}")
        
        result = analyzer.analyze_news_comprehensive(sample_news)
        
        print(f"情感标签: {result['sentiment']['sentiment_label']}")
        print(f"情感得分: {result['sentiment']['sentiment_score']:.3f}")
        print(f"影响级别: {result['impact_level']}")
        print(f"相关行业: {result['related_industries']}")
        print(f"时效性: {result['time_sensitivity']}")
        print(f"风险评分: {result['risk_score']:.3f}")
    
    return sample_news


def demo_keyword_matching(sample_news):
    """演示关键词匹配功能"""
    print("\n" + "=" * 50)
    print("关键词匹配功能演示")
    print("=" * 50)
    
    matcher = KeywordMatcher()
    
    if sample_news:
        content = sample_news.get('content', '') + " " + sample_news.get('title', '')
        print(f"分析文本: {content[:100]}...")
        
        result = matcher.comprehensive_analysis(content)
        
        print(f"政策影响得分: {result['policy_impact']['impact_score']}")
        print(f"风险得分: {result['risk_signals']['risk_score']}")
        print(f"市场情绪: {result['market_sentiment']['sentiment_label']}")
        print(f"综合重要性: {result['importance_score']}")
        
        if result['industry_relevance']:
            print("相关行业:")
            for industry, data in result['industry_relevance'].items():
                print(f"  {industry}: {data['matches']} (相关性: {data['relevance_score']:.2f})")


def demo_policy_calendar():
    """演示政策日历功能"""
    print("\n" + "=" * 50)
    print("政策日历功能演示")
    print("=" * 50)
    
    calendar_mgr = PolicyCalendar()
    
    # 获取未来事件
    events = calendar_mgr.get_upcoming_events(30)
    print(f"未来30天有 {len(events)} 个政策事件:")
    
    for event in events[:5]:
        print(f"  - {event['name']}: {event.get('calculated_date', event.get('start_date'))} "
              f"({event['days_until']}天后) [{event.get('importance', 'unknown')}]")
    
    # 检查敏感期
    sensitivity = calendar_mgr.is_policy_sensitive_period()
    print(f"\n当前敏感期状态: {sensitivity['is_sensitive']}")
    print(f"操作建议: {sensitivity['recommendation']}")
    
    # 获取摘要
    summary = calendar_mgr.get_policy_calendar_summary()
    print(f"\n政策日历摘要:")
    print(f"  总事件数: {summary['summary']['total_events']}")
    print(f"  高重要性: {summary['summary']['high_importance']}")
    print(f"  中重要性: {summary['summary']['medium_importance']}")
    
    return sensitivity


def demo_risk_assessment(sample_news, policy_context):
    """演示风险评估功能"""
    print("\n" + "=" * 50)
    print("风险评估功能演示")
    print("=" * 50)
    
    assessor = RiskAssessor()
    
    if sample_news:
        # 模拟分析结果
        sentiment_result = {
            'sentiment_label': 'negative',
            'sentiment_intensity': 0.6,
            'related_industries': ['finance']
        }
        
        keyword_result = {
            'policy_impact': {'impact_score': 0.5},
            'risk_signals': {'risk_score': 0.4},
            'industry_relevance': {'finance': {'count': 2}}
        }
        
        risk_result = assessor.assess_news_risk(
            sample_news, sentiment_result, keyword_result, policy_context
        )
        
        print(f"风险得分: {risk_result['risk_score']}")
        print(f"风险级别: {risk_result['risk_level']}")
        print(f"主要风险因子: {risk_result['main_risk_factors']}")
        print(f"影响领域: {risk_result['impact_areas']}")
        print(f"时间敏感性: {risk_result['time_sensitivity']}")
        print(f"建议操作: {risk_result['risk_recommendation']['position_action']}")
        print(f"置信度: {risk_result['confidence_score']:.2f}")
        
        return risk_result


def demo_strategy_adapter(risk_assessment, policy_context, sample_news):
    """演示策略适配器功能"""
    print("\n" + "=" * 50)
    print("策略适配器功能演示")
    print("=" * 50)
    
    adapter = StrategyAdapter()
    
    if risk_assessment and sample_news:
        # 生成风险响应信号
        risk_signal = adapter.process_risk_assessment(risk_assessment, sample_news)
        
        print(f"风险信号ID: {risk_signal.signal_id}")
        print(f"信号类型: {risk_signal.signal_type}")
        print(f"建议动作: {risk_signal.action.value}")
        print(f"交易模式: {risk_signal.trading_mode.value}")
        print(f"置信度: {risk_signal.confidence:.2f}")
        print(f"目标行业: {risk_signal.target_industries}")
        print(f"规避行业: {risk_signal.avoid_industries}")
        
        # 生成政策窗口信号
        policy_signal = adapter.process_policy_calendar(policy_context)
        
        signals = [risk_signal]
        if policy_signal:
            signals.append(policy_signal)
            print(f"\n政策窗口信号: {policy_signal.action.value}")
        
        # 聚合信号
        aggregated = adapter.aggregate_signals(signals)
        
        print(f"\n=== 聚合策略建议 ===")
        print(f"最终动作: {aggregated['action'].value}")
        print(f"交易模式: {aggregated['trading_mode'].value}")
        print(f"综合置信度: {aggregated['confidence']}")
        print(f"仓位调整: {aggregated['position_adjustment']}")
        print(f"推理: {aggregated['reasoning'][:150]}...")


def demo_full_system():
    """演示完整系统功能"""
    print("\n" + "=" * 50)
    print("完整监控系统演示")
    print("=" * 50)
    
    # 创建系统实例
    monitor = create_monitor_system()
    
    print("系统初始化完成")
    
    # 获取系统状态
    status = monitor.get_system_status()
    print(f"系统运行状态: {status['system_info']['is_running']}")
    print(f"策略模式: {status['strategy_status']['current_mode']}")
    print(f"当前仓位比例: {status['strategy_status']['current_position_ratio']:.2f}")
    
    # 手动执行一次分析流程
    print("\n执行手动分析流程...")
    
    # 爬取新闻
    monitor._crawl_news_job()
    time.sleep(2)
    
    # 分析新闻
    monitor._analysis_job()
    time.sleep(2)
    
    # 风险检查
    monitor._risk_check_job()
    
    # 获取更新后的状态
    updated_status = monitor.get_system_status()
    print(f"\n更新后状态:")
    print(f"新闻缓存: {updated_status['system_info']['news_cache_size']} 条")
    print(f"活跃信号: {updated_status['system_info']['active_signals_count']} 个")
    print(f"最近新闻:")
    for news in updated_status['recent_news'][:3]:
        print(f"  - {news['title']} [{news['risk_level']}]")
    
    return monitor


def main():
    """主演示函数"""
    print("A股新闻政策监控系统功能演示")
    print("=" * 60)
    
    try:
        # 1. 新闻爬虫演示
        news_data = demo_news_crawler()
        
        # 2. 情感分析演示
        sample_news = demo_sentiment_analysis(news_data)
        
        # 3. 关键词匹配演示
        demo_keyword_matching(sample_news)
        
        # 4. 政策日历演示
        policy_context = demo_policy_calendar()
        
        # 5. 风险评估演示
        risk_assessment = demo_risk_assessment(sample_news, policy_context)
        
        # 6. 策略适配器演示
        demo_strategy_adapter(risk_assessment, policy_context, sample_news)
        
        # 7. 完整系统演示
        monitor = demo_full_system()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        
        # 导出数据示例
        print("\n导出最近数据...")
        export_data = monitor.export_data()
        print(f"导出数据大小: {len(export_data)} 字符")
        
        # 保存到文件
        with open('demo_export.json', 'w', encoding='utf-8') as f:
            f.write(export_data)
        print("数据已保存到 demo_export.json")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()