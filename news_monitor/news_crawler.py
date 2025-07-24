#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新闻数据爬虫模块

支持多个数据源的新闻采集：
1. 官方渠道：央行、证监会、发改委等
2. 财经媒体：新浪财经、东方财富、金融界等
3. 公司公告：重大资产重组、业绩预告等
"""

import requests
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd


class NewsCrawler:
    """新闻爬虫类"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化新闻爬虫
        
        Args:
            config: 配置字典，包含数据源配置、请求参数等
        """
        self.config = config or self._get_default_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logger = logging.getLogger(__name__)
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'sina_finance_enabled': True,
            'eastmoney_enabled': True,
            'official_sources_enabled': True,
            'request_delay': 1.0,  # 请求间隔秒数
            'timeout': 30,
            'max_retries': 3,
        }
    
    def crawl_sina_finance_news(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        爬取新浪财经新闻
        
        Args:
            hours_back: 获取过去几小时的新闻
            
        Returns:
            新闻列表，每个新闻包含title, content, url, publish_time等字段
        """
        news_list = []
        
        try:
            # 新浪财经API (简化实现)
            # 实际使用时需要根据新浪财经的真实API接口调整
            url = "https://finance.sina.com.cn/api/roll_news.php"
            params = {
                'channel': 'finance',
                'num': 50,
                'time': int(time.time())
            }
            
            response = self.session.get(url, params=params, timeout=self.config['timeout'])
            
            if response.status_code == 200:
                # 解析JSON响应或HTML（根据实际API格式）
                self.logger.info(f"成功获取新浪财经新闻数据")
                
                # 示例数据结构（实际实现时需要解析真实响应）
                sample_news = {
                    'source': 'sina_finance',
                    'title': '央行发布最新货币政策执行报告',
                    'content': '央行在最新的货币政策执行报告中表示...',
                    'url': 'https://finance.sina.com.cn/news/example',
                    'publish_time': datetime.now().isoformat(),
                    'keywords': ['央行', '货币政策'],
                    'raw_data': response.text[:500]  # 保存原始数据片段
                }
                news_list.append(sample_news)
                
        except Exception as e:
            self.logger.error(f"爬取新浪财经新闻失败: {e}")
            
        time.sleep(self.config['request_delay'])
        return news_list
    
    def crawl_eastmoney_news(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        爬取东方财富新闻
        
        Args:
            hours_back: 获取过去几小时的新闻
            
        Returns:
            新闻列表
        """
        news_list = []
        
        try:
            # 东方财富网新闻API (简化实现)
            url = "http://api.eastmoney.com/news/list"
            params = {
                'type': 'finance',
                'pageSize': 50,
                'timestamp': int(time.time())
            }
            
            response = self.session.get(url, params=params, timeout=self.config['timeout'])
            
            if response.status_code == 200:
                self.logger.info(f"成功获取东方财富新闻数据")
                
                # 示例数据
                sample_news = {
                    'source': 'eastmoney',
                    'title': '证监会发布新规支持科技创新',
                    'content': '证监会近日发布关于支持科技创新的新规...',
                    'url': 'http://finance.eastmoney.com/news/example', 
                    'publish_time': datetime.now().isoformat(),
                    'keywords': ['证监会', '科技创新'],
                    'raw_data': response.text[:500]
                }
                news_list.append(sample_news)
                
        except Exception as e:
            self.logger.error(f"爬取东方财富新闻失败: {e}")
            
        time.sleep(self.config['request_delay'])
        return news_list
    
    def crawl_official_announcements(self) -> List[Dict[str, Any]]:
        """
        爬取官方公告
        包括央行、证监会、发改委等官方网站公告
        
        Returns:
            官方公告列表
        """
        announcements = []
        
        # 央行公告
        try:
            pbc_url = "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html"
            response = self.session.get(pbc_url, timeout=self.config['timeout'])
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 示例解析逻辑（需要根据实际网站结构调整）
                sample_announcement = {
                    'source': 'pbc_official',
                    'title': '中国人民银行关于降准的公告',
                    'content': '为支持实体经济发展，决定降准0.5个百分点...',
                    'url': pbc_url,
                    'publish_time': datetime.now().isoformat(),
                    'keywords': ['央行', '降准', '货币政策'],
                    'importance': 'high',
                    'category': 'monetary_policy'
                }
                announcements.append(sample_announcement)
                
        except Exception as e:
            self.logger.error(f"爬取央行公告失败: {e}")
        
        # 证监会公告
        try:
            csrc_url = "http://www.csrc.gov.cn/csrc/c100028/common_list.shtml"
            # 类似的爬取逻辑...
            sample_csrc = {
                'source': 'csrc_official',
                'title': '关于完善资本市场基础制度的意见',
                'content': '为进一步完善资本市场基础制度...',
                'url': csrc_url,
                'publish_time': datetime.now().isoformat(),
                'keywords': ['证监会', '资本市场', '制度'],
                'importance': 'high',
                'category': 'market_regulation'
            }
            announcements.append(sample_csrc)
            
        except Exception as e:
            self.logger.error(f"爬取证监会公告失败: {e}")
            
        time.sleep(self.config['request_delay'])
        return announcements
    
    def crawl_company_announcements(self, stock_codes: List[str] = None) -> List[Dict[str, Any]]:
        """
        爬取公司公告
        
        Args:
            stock_codes: 股票代码列表，如果为None则获取所有重要公告
            
        Returns:
            公司公告列表
        """
        announcements = []
        
        try:
            # 巨潮资讯网公告查询（示例）
            cninfo_url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
            
            # 示例公司公告数据
            sample_announcement = {
                'source': 'cninfo',
                'title': '某科技公司重大资产重组公告',
                'content': '公司拟通过重大资产重组...',
                'url': 'http://www.cninfo.com.cn/new/disclosure/detail',
                'publish_time': datetime.now().isoformat(),
                'stock_code': '000001',
                'company_name': '某科技公司',
                'keywords': ['重大资产重组', '停牌'],
                'announcement_type': 'major_asset_restructuring',
                'importance': 'medium'
            }
            announcements.append(sample_announcement)
            
        except Exception as e:
            self.logger.error(f"爬取公司公告失败: {e}")
            
        return announcements
    
    def crawl_all_sources(self, hours_back: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """
        爬取所有配置的数据源
        
        Args:
            hours_back: 获取过去几小时的新闻
            
        Returns:
            按数据源分类的新闻字典
        """
        all_news = {
            'sina_finance': [],
            'eastmoney': [],
            'official_announcements': [],
            'company_announcements': []
        }
        
        if self.config.get('sina_finance_enabled', True):
            all_news['sina_finance'] = self.crawl_sina_finance_news(hours_back)
            
        if self.config.get('eastmoney_enabled', True):
            all_news['eastmoney'] = self.crawl_eastmoney_news(hours_back)
            
        if self.config.get('official_sources_enabled', True):
            all_news['official_announcements'] = self.crawl_official_announcements()
            all_news['company_announcements'] = self.crawl_company_announcements()
            
        # 统计信息
        total_news = sum(len(news_list) for news_list in all_news.values())
        self.logger.info(f"总共爬取到 {total_news} 条新闻/公告")
        
        return all_news
    
    def save_news_to_df(self, news_data: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        将新闻数据保存为DataFrame
        
        Args:
            news_data: 新闻数据字典
            
        Returns:
            新闻DataFrame
        """
        all_news_list = []
        
        for source, news_list in news_data.items():
            for news in news_list:
                news['data_source'] = source
                all_news_list.append(news)
                
        df = pd.DataFrame(all_news_list)
        
        if not df.empty:
            # 数据类型转换
            df['publish_time'] = pd.to_datetime(df['publish_time'])
            df['crawl_time'] = datetime.now()
            
        return df


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    crawler = NewsCrawler()
    news_data = crawler.crawl_all_sources(hours_back=24)
    
    df = crawler.save_news_to_df(news_data)
    print(f"爬取到 {len(df)} 条新闻")
    print(df.head())