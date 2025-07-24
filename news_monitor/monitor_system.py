#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A股新闻政策监控系统主模块

集成所有子模块，提供统一的新闻监控和风险控制功能：
1. 新闻数据采集和分析
2. 风险评估和预警
3. 策略信号生成
4. 系统调度和管理
"""

import logging
import schedule
import time
import yaml
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from .news_crawler import NewsCrawler
from .sentiment_analyzer import SentimentAnalyzer
from .keyword_matcher import KeywordMatcher
from .policy_calendar import PolicyCalendar
from .risk_assessor import RiskAssessor
from .strategy_adapter import StrategyAdapter, StrategySignal


class NewsMonitorSystem:
    """A股新闻政策监控系统主类"""
    
    def __init__(self, config_file: str = None):
        """
        初始化监控系统
        
        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_file)
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个子模块
        self.news_crawler = NewsCrawler(self.config.get('news_sources', {}))
        self.sentiment_analyzer = SentimentAnalyzer(self.config.get('sentiment_analysis', {}))
        self.keyword_matcher = KeywordMatcher()
        self.policy_calendar = PolicyCalendar(self.config.get('policy_calendar', {}))
        self.risk_assessor = RiskAssessor(self.config.get('risk_assessment', {}))
        self.strategy_adapter = StrategyAdapter(self.config.get('strategy_adapter', {}))
        
        # 系统状态
        self.is_running = False
        self.last_analysis_time = None
        self.news_cache = []
        self.active_signals = []
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.logger.info("A股新闻政策监控系统初始化完成")
    
    def _load_config(self, config_file: str = None) -> Dict:
        """加载配置文件"""
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__), 
                '..', 'config', 'news_monitor_config.yaml'
            )
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'monitoring': {
                'news_crawl_interval': 30,
                'analysis_interval': 15,
                'risk_check_interval': 5,
                'max_news_per_cycle': 100
            },
            'logging': {
                'level': 'INFO',
                'file_enabled': False
            }
        }
    
    def _setup_logging(self):
        """设置日志系统"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=level,
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # 文件日志
        if log_config.get('file_enabled', False):
            log_file = log_config.get('file_path', 'logs/news_monitor.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            formatter = logging.Formatter(log_config.get('format'))
            file_handler.setFormatter(formatter)
            
            logging.getLogger().addHandler(file_handler)
    
    def start_monitoring(self):
        """启动监控系统"""
        if self.is_running:
            self.logger.warning("监控系统已在运行中")
            return
        
        self.is_running = True
        self.logger.info("启动A股新闻政策监控系统")
        
        # 设置定时任务
        monitoring_config = self.config.get('monitoring', {})
        
        # 新闻爬取任务
        crawl_interval = monitoring_config.get('news_crawl_interval', 30)
        schedule.every(crawl_interval).minutes.do(self._crawl_news_job)
        
        # 分析任务
        analysis_interval = monitoring_config.get('analysis_interval', 15)
        schedule.every(analysis_interval).minutes.do(self._analysis_job)
        
        # 风险检查任务
        risk_interval = monitoring_config.get('risk_check_interval', 5)
        schedule.every(risk_interval).minutes.do(self._risk_check_job)
        
        # 立即执行一次
        self._crawl_news_job()
        self._analysis_job()
        
        # 启动调度循环
        self._run_scheduler()
    
    def stop_monitoring(self):
        """停止监控系统"""
        self.is_running = False
        schedule.clear()
        self.executor.shutdown(wait=True)
        self.logger.info("A股新闻政策监控系统已停止")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("接收到停止信号")
                break
            except Exception as e:
                self.logger.error(f"调度器运行错误: {e}")
                time.sleep(5)
    
    def _crawl_news_job(self):
        """新闻爬取任务"""
        try:
            self.logger.info("开始爬取新闻数据")
            
            # 并行爬取不同数据源
            futures = []
            
            # 新浪财经
            futures.append(
                self.executor.submit(self.news_crawler.crawl_sina_finance_news, 2)
            )
            
            # 东方财富
            futures.append(
                self.executor.submit(self.news_crawler.crawl_eastmoney_news, 2)
            )
            
            # 官方公告
            futures.append(
                self.executor.submit(self.news_crawler.crawl_official_announcements)
            )
            
            # 收集结果
            all_news = []
            for future in as_completed(futures):
                try:
                    news_list = future.result(timeout=30)
                    all_news.extend(news_list)
                except Exception as e:
                    self.logger.error(f"新闻爬取失败: {e}")
            
            # 更新缓存
            self.news_cache.extend(all_news)
            
            # 保持缓存大小
            max_cache_size = self.config.get('monitoring', {}).get('max_news_per_cycle', 100) * 5
            if len(self.news_cache) > max_cache_size:
                self.news_cache = self.news_cache[-max_cache_size:]
            
            self.logger.info(f"爬取完成，新增 {len(all_news)} 条新闻，缓存总计 {len(self.news_cache)} 条")
            
        except Exception as e:
            self.logger.error(f"新闻爬取任务失败: {e}")
    
    def _analysis_job(self):
        """分析任务"""
        try:
            if not self.news_cache:
                self.logger.info("无新闻数据，跳过分析")
                return
            
            self.logger.info("开始新闻分析任务")
            
            # 获取需要分析的新闻（未分析的新闻）
            unanalyzed_news = [
                news for news in self.news_cache 
                if not news.get('analyzed', False)
            ]
            
            if not unanalyzed_news:
                self.logger.info("无新的未分析新闻")
                return
            
            # 限制单次分析数量
            max_analysis = self.config.get('monitoring', {}).get('max_news_per_cycle', 100)
            news_to_analyze = unanalyzed_news[:max_analysis]
            
            # 批量分析
            analysis_results = []
            
            for news_item in news_to_analyze:
                try:
                    # 情感分析
                    sentiment_result = self.sentiment_analyzer.analyze_news_comprehensive(news_item)
                    
                    # 关键词匹配
                    keyword_result = self.keyword_matcher.comprehensive_analysis(
                        news_item.get('content', ''), 
                        news_item.get('title', '')
                    )
                    
                    # 合并分析结果
                    analysis_result = {
                        'news_item': news_item,
                        'sentiment': sentiment_result,
                        'keyword_analysis': keyword_result,
                        'analysis_time': datetime.now().isoformat()
                    }
                    
                    analysis_results.append(analysis_result)
                    
                    # 标记为已分析
                    news_item['analyzed'] = True
                    news_item['analysis_result'] = analysis_result
                    
                except Exception as e:
                    self.logger.error(f"分析新闻失败: {e}")
                    continue
            
            self.logger.info(f"分析完成，处理了 {len(analysis_results)} 条新闻")
            
            # 更新最后分析时间
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"分析任务失败: {e}")
    
    def _risk_check_job(self):
        """风险检查任务"""
        try:
            if not self.news_cache:
                return
            
            self.logger.info("开始风险检查任务")
            
            # 获取最近分析的新闻
            recent_analyzed = [
                news for news in self.news_cache 
                if news.get('analyzed', False) and 'analysis_result' in news
            ]
            
            if not recent_analyzed:
                return
            
            # 获取政策上下文
            policy_context = self.policy_calendar.is_policy_sensitive_period()
            
            # 风险评估
            high_risk_signals = []
            
            for news in recent_analyzed[-20:]:  # 检查最近20条新闻
                analysis_result = news['analysis_result']
                
                # 风险评估
                risk_assessment = self.risk_assessor.assess_news_risk(
                    news,
                    analysis_result.get('sentiment'),
                    analysis_result.get('keyword_analysis'),
                    policy_context
                )
                
                # 生成策略信号
                if risk_assessment['risk_level'] in ['high', 'medium']:
                    signal = self.strategy_adapter.process_risk_assessment(risk_assessment, news)
                    high_risk_signals.append(signal)
                
                # 保存风险评估结果
                news['risk_assessment'] = risk_assessment
            
            # 处理政策窗口信号
            policy_signal = self.strategy_adapter.process_policy_calendar(policy_context)
            if policy_signal:
                high_risk_signals.append(policy_signal)
            
            # 更新活跃信号
            self._update_active_signals(high_risk_signals)
            
            # 生成综合策略建议
            if self.active_signals:
                aggregated_signal = self.strategy_adapter.aggregate_signals(self.active_signals)
                self._handle_strategy_signal(aggregated_signal)
            
            self.logger.info(f"风险检查完成，生成 {len(high_risk_signals)} 个新信号，当前活跃信号 {len(self.active_signals)} 个")
            
        except Exception as e:
            self.logger.error(f"风险检查任务失败: {e}")
    
    def _update_active_signals(self, new_signals: List[StrategySignal]):
        """更新活跃信号列表"""
        # 移除过期信号
        current_time = datetime.now()
        self.active_signals = [
            signal for signal in self.active_signals 
            if signal.valid_until > current_time
        ]
        
        # 添加新信号
        self.active_signals.extend(new_signals)
        
        # 限制最大信号数量
        max_signals = self.config.get('strategy_adapter', {}).get('signal_settings', {}).get('max_simultaneous', 5)
        if len(self.active_signals) > max_signals:
            # 按置信度排序，保留前N个
            self.active_signals.sort(key=lambda x: x.confidence, reverse=True)
            self.active_signals = self.active_signals[:max_signals]
    
    def _handle_strategy_signal(self, aggregated_signal: Dict[str, Any]):
        """处理策略信号"""
        action = aggregated_signal['action']
        confidence = aggregated_signal['confidence']
        
        # 只处理高置信度信号
        confidence_threshold = self.config.get('strategy_adapter', {}).get('signal_settings', {}).get('confidence_threshold', 0.6)
        
        if confidence >= confidence_threshold:
            self.logger.warning(f"策略信号触发: {action.value}, 置信度: {confidence:.2f}")
            self.logger.warning(f"建议: {aggregated_signal['reasoning']}")
            
            # 更新策略状态
            self.strategy_adapter.update_strategy_state(aggregated_signal)
            
            # 这里可以添加实际的交易执行逻辑
            # 例如: 发送交易指令、调整仓位等
            
        else:
            self.logger.info(f"策略信号置信度不足: {confidence:.2f} < {confidence_threshold}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'system_info': {
                'is_running': self.is_running,
                'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                'news_cache_size': len(self.news_cache),
                'active_signals_count': len(self.active_signals)
            },
            'strategy_status': self.strategy_adapter.get_strategy_status(),
            'policy_context': self.policy_calendar.is_policy_sensitive_period(),
            'recent_news': [
                {
                    'title': news.get('title', '')[:50] + '...',
                    'source': news.get('source', ''),
                    'risk_level': news.get('risk_assessment', {}).get('risk_level', 'unknown'),
                    'publish_time': news.get('publish_time', '')
                }
                for news in self.news_cache[-10:] if news.get('analyzed', False)
            ],
            'generated_at': datetime.now().isoformat()
        }
    
    def export_data(self, start_date: str = None, end_date: str = None) -> str:
        """导出数据"""
        try:
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            else:
                start_dt = datetime.now() - timedelta(days=7)
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            else:
                end_dt = datetime.now()
            
            # 筛选时间范围内的新闻
            filtered_news = []
            for news in self.news_cache:
                if news.get('publish_time'):
                    try:
                        publish_dt = datetime.fromisoformat(news['publish_time'].replace('Z', '+00:00'))
                        if start_dt <= publish_dt <= end_dt:
                            filtered_news.append(news)
                    except:
                        continue
            
            export_data = {
                'export_info': {
                    'start_date': start_dt.isoformat(),
                    'end_date': end_dt.isoformat(),
                    'total_news': len(filtered_news),
                    'export_time': datetime.now().isoformat()
                },
                'news_data': filtered_news,
                'system_status': self.get_system_status()
            }
            
            return json.dumps(export_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"数据导出失败: {e}")
            return json.dumps({'error': str(e)})


def create_monitor_system(config_file: str = None) -> NewsMonitorSystem:
    """创建监控系统实例"""
    return NewsMonitorSystem(config_file)


if __name__ == "__main__":
    # 创建并启动监控系统
    monitor = create_monitor_system()
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n正在停止监控系统...")
        monitor.stop_monitoring()
        print("监控系统已停止")