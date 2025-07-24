#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
政策日历模块

管理重要政策事件和会议日程：
1. 重要会议日程 (两会、政治局会议等)
2. 政策发布时间窗口
3. 敏感时点识别
4. 政策预期管理
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import calendar
from dateutil.relativedelta import relativedelta
import json


class PolicyCalendar:
    """政策日历管理器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化政策日历
        
        Args:
            config: 配置参数
        """
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 加载政策事件日历
        self.policy_events = self._load_policy_events()
        self.recurring_events = self._load_recurring_events()
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'advance_warning_days': 3,  # 提前预警天数
            'policy_window_buffer': 2,  # 政策窗口缓冲天数
            'enable_recurring_events': True,
            'enable_economic_calendar': True,
        }
    
    def _load_policy_events(self) -> List[Dict[str, Any]]:
        """加载政策事件列表"""
        # 这里应该从配置文件或数据库加载，这里提供示例数据
        events = [
            {
                'name': '全国人大会议 (两会)',
                'description': '全国人民代表大会年度会议',
                'start_date': '2024-03-05',
                'end_date': '2024-03-15',
                'importance': 'high',
                'category': 'legislative',
                'impact_areas': ['政策', '经济', '金融'],
                'recurring': True,
                'recurring_pattern': 'yearly_march'
            },
            {
                'name': '全国政协会议 (两会)',
                'description': '全国政治协商会议年度会议',
                'start_date': '2024-03-03',
                'end_date': '2024-03-12',
                'importance': 'high',
                'category': 'legislative',
                'impact_areas': ['政策', '经济'],
                'recurring': True,
                'recurring_pattern': 'yearly_march'
            },
            {
                'name': '中央经济工作会议',
                'description': '中央年度经济工作部署会议',
                'start_date': '2023-12-12',
                'end_date': '2023-12-12',
                'importance': 'high',
                'category': 'economic_policy',
                'impact_areas': ['货币政策', '财政政策', '经济'],
                'recurring': True,
                'recurring_pattern': 'yearly_december'
            },
            {
                'name': '中央政治局会议',
                'description': '中央政治局例行会议',
                'importance': 'high',
                'category': 'policy_meeting',
                'impact_areas': ['政策', '经济'],
                'recurring': True,
                'recurring_pattern': 'monthly_last_friday'
            }
        ]
        return events
    
    def _load_recurring_events(self) -> List[Dict[str, Any]]:
        """加载周期性事件"""
        recurring_events = [
            {
                'name': '央行货币政策委员会例会',
                'description': '央行货币政策委员会季度例会',
                'importance': 'high',
                'category': 'monetary_policy',
                'impact_areas': ['货币政策', '利率', '流动性'],
                'frequency': 'quarterly',
                'typical_months': [3, 6, 9, 12],
                'typical_days': [15, 20]  # 通常在月中到下旬
            },
            {
                'name': '统计局CPI/PPI数据发布',
                'description': '国家统计局发布居民消费价格指数和工业生产者价格指数',
                'importance': 'medium',
                'category': 'economic_data',
                'impact_areas': ['通胀', '货币政策'],
                'frequency': 'monthly',
                'typical_days': [9, 10, 11]  # 通常每月9-11日
            },
            {
                'name': 'PMI数据发布',
                'description': '制造业采购经理指数发布',
                'importance': 'medium',
                'category': 'economic_data',
                'impact_areas': ['制造业', '经济增长'],
                'frequency': 'monthly',
                'typical_days': [1]  # 每月第一个工作日
            },
            {
                'name': 'GDP数据发布',
                'description': '国内生产总值季度数据发布',
                'importance': 'high',
                'category': 'economic_data',
                'impact_areas': ['经济增长', '政策'],
                'frequency': 'quarterly',
                'typical_months': [1, 4, 7, 10],
                'typical_days': [15, 20]
            }
        ]
        return recurring_events
    
    def get_upcoming_events(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        获取未来指定天数内的政策事件
        
        Args:
            days_ahead: 查看未来天数
            
        Returns:
            事件列表
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming_events = []
        
        # 检查固定日期事件
        for event in self.policy_events:
            if 'start_date' in event:
                event_date = datetime.strptime(event['start_date'], '%Y-%m-%d').date()
                
                # 如果是周期性事件，需要计算下一次发生的日期
                if event.get('recurring', False):
                    next_date = self._calculate_next_occurrence(event, today)
                    if next_date and today <= next_date <= end_date:
                        event_copy = event.copy()
                        event_copy['calculated_date'] = next_date.strftime('%Y-%m-%d')
                        event_copy['days_until'] = (next_date - today).days
                        upcoming_events.append(event_copy)
                elif today <= event_date <= end_date:
                    event_copy = event.copy()
                    event_copy['days_until'] = (event_date - today).days
                    upcoming_events.append(event_copy)
        
        # 检查周期性事件
        for event in self.recurring_events:
            next_dates = self._calculate_recurring_dates(event, today, end_date)
            for next_date in next_dates:
                event_copy = event.copy()
                event_copy['calculated_date'] = next_date.strftime('%Y-%m-%d')
                event_copy['days_until'] = (next_date - today).days
                upcoming_events.append(event_copy)
        
        # 按时间排序
        upcoming_events.sort(key=lambda x: x['days_until'])
        
        return upcoming_events
    
    def _calculate_next_occurrence(self, event: Dict, from_date: date) -> Optional[date]:
        """计算周期性事件的下一次发生日期"""
        pattern = event.get('recurring_pattern', '')
        
        if pattern == 'yearly_march':
            # 每年3月的事件
            current_year = from_date.year
            event_date = date(current_year, 3, 5)  # 默认3月5日
            if event_date < from_date:
                event_date = date(current_year + 1, 3, 5)
            return event_date
            
        elif pattern == 'yearly_december':
            # 每年12月的事件
            current_year = from_date.year
            event_date = date(current_year, 12, 12)  # 默认12月12日
            if event_date < from_date:
                event_date = date(current_year + 1, 12, 12)
            return event_date
            
        elif pattern == 'monthly_last_friday':
            # 每月最后一个周五
            next_month = from_date.replace(day=1) + relativedelta(months=1)
            last_day = (next_month - timedelta(days=1))
            
            # 找到最后一个周五 (weekday=4)
            while last_day.weekday() != 4:
                last_day -= timedelta(days=1)
            
            if last_day < from_date:
                # 计算下个月的最后一个周五
                next_month = from_date.replace(day=1) + relativedelta(months=2)
                last_day = (next_month - timedelta(days=1))
                while last_day.weekday() != 4:
                    last_day -= timedelta(days=1)
                    
            return last_day
        
        return None
    
    def _calculate_recurring_dates(self, event: Dict, start_date: date, end_date: date) -> List[date]:
        """计算周期性事件在指定时间范围内的所有日期"""
        dates = []
        frequency = event.get('frequency', '')
        
        if frequency == 'monthly':
            typical_days = event.get('typical_days', [1])
            current_date = start_date.replace(day=1)
            
            while current_date <= end_date:
                for day in typical_days:
                    try:
                        event_date = current_date.replace(day=day)
                        if start_date <= event_date <= end_date:
                            dates.append(event_date)
                    except ValueError:
                        # 处理月份天数不足的情况
                        continue
                current_date += relativedelta(months=1)
                
        elif frequency == 'quarterly':
            typical_months = event.get('typical_months', [3, 6, 9, 12])
            typical_days = event.get('typical_days', [15])
            
            current_year = start_date.year
            for year in [current_year, current_year + 1]:
                for month in typical_months:
                    for day in typical_days:
                        try:
                            event_date = date(year, month, day)
                            if start_date <= event_date <= end_date:
                                dates.append(event_date)
                        except ValueError:
                            continue
        
        return dates
    
    def is_policy_sensitive_period(self, check_date: date = None) -> Dict[str, Any]:
        """
        检查是否为政策敏感期
        
        Args:
            check_date: 检查日期，默认为今天
            
        Returns:
            敏感期信息
        """
        if check_date is None:
            check_date = date.today()
            
        # 获取前后几天的事件
        buffer_days = self.config['policy_window_buffer']
        upcoming_events = self.get_upcoming_events(days_ahead=buffer_days * 2)
        
        sensitive_events = []
        is_sensitive = False
        
        for event in upcoming_events:
            event_date = datetime.strptime(
                event.get('calculated_date', event.get('start_date', '')), 
                '%Y-%m-%d'
            ).date()
            
            days_diff = abs((event_date - check_date).days)
            
            if days_diff <= buffer_days:
                sensitive_events.append({
                    'event': event,
                    'days_diff': days_diff,
                    'position': 'before' if event_date > check_date else 'after'
                })
                
                if event.get('importance') == 'high':
                    is_sensitive = True
        
        return {
            'is_sensitive': is_sensitive,
            'sensitive_events': sensitive_events,
            'recommendation': self._get_sensitivity_recommendation(sensitive_events),
            'check_date': check_date.strftime('%Y-%m-%d')
        }
    
    def _get_sensitivity_recommendation(self, sensitive_events: List[Dict]) -> str:
        """获取敏感期操作建议"""
        if not sensitive_events:
            return 'normal_trading'
        
        high_importance_events = [
            e for e in sensitive_events 
            if e['event'].get('importance') == 'high'
        ]
        
        if high_importance_events:
            return 'reduce_position'  # 减仓
        else:
            return 'cautious_trading'  # 谨慎交易
    
    def get_policy_calendar_summary(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        获取政策日历摘要
        
        Args:
            days_ahead: 查看未来天数
            
        Returns:
            日历摘要
        """
        upcoming_events = self.get_upcoming_events(days_ahead)
        
        # 按重要性分类
        high_importance = [e for e in upcoming_events if e.get('importance') == 'high']
        medium_importance = [e for e in upcoming_events if e.get('importance') == 'medium']
        low_importance = [e for e in upcoming_events if e.get('importance') == 'low']
        
        # 按类别分类
        categories = {}
        for event in upcoming_events:
            category = event.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(event)
        
        # 即将到来的高重要性事件
        next_high_importance = high_importance[0] if high_importance else None
        
        # 敏感期检查
        sensitivity_info = self.is_policy_sensitive_period()
        
        return {
            'summary': {
                'total_events': len(upcoming_events),
                'high_importance': len(high_importance),
                'medium_importance': len(medium_importance),
                'low_importance': len(low_importance)
            },
            'categories': {k: len(v) for k, v in categories.items()},
            'next_high_importance_event': next_high_importance,
            'current_sensitivity': sensitivity_info,
            'high_importance_events': high_importance[:5],  # 最近5个重要事件
            'generated_at': datetime.now().isoformat()
        }
    
    def add_custom_event(self, event: Dict[str, Any]):
        """
        添加自定义政策事件
        
        Args:
            event: 事件信息字典
        """
        required_fields = ['name', 'start_date', 'importance', 'category']
        
        for field in required_fields:
            if field not in event:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 验证日期格式
        try:
            datetime.strptime(event['start_date'], '%Y-%m-%d')
        except ValueError:
            raise ValueError("日期格式错误，应为 YYYY-MM-DD")
        
        # 验证重要性级别
        if event['importance'] not in ['high', 'medium', 'low']:
            raise ValueError("重要性级别必须为: high, medium, low")
        
        self.policy_events.append(event)
        self.logger.info(f"添加自定义事件: {event['name']}")
    
    def export_calendar(self, days_ahead: int = 90) -> str:
        """
        导出政策日历为JSON格式
        
        Args:
            days_ahead: 导出未来天数
            
        Returns:
            JSON字符串
        """
        calendar_data = {
            'export_date': datetime.now().isoformat(),
            'days_ahead': days_ahead,
            'upcoming_events': self.get_upcoming_events(days_ahead),
            'summary': self.get_policy_calendar_summary(days_ahead)
        }
        
        return json.dumps(calendar_data, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    calendar_manager = PolicyCalendar()
    
    # 获取未来30天的事件
    upcoming_events = calendar_manager.get_upcoming_events(30)
    print(f"未来30天有 {len(upcoming_events)} 个政策事件")
    
    for event in upcoming_events[:5]:  # 显示前5个
        print(f"- {event['name']}: {event.get('calculated_date', event.get('start_date'))} "
              f"({event['days_until']}天后)")
    
    # 检查敏感期
    sensitivity = calendar_manager.is_policy_sensitive_period()
    print(f"\n当前是否为敏感期: {sensitivity['is_sensitive']}")
    print(f"建议操作: {sensitivity['recommendation']}")
    
    # 获取日历摘要
    summary = calendar_manager.get_policy_calendar_summary()
    print(f"\n政策日历摘要:")
    print(f"- 总事件数: {summary['summary']['total_events']}")
    print(f"- 高重要性事件: {summary['summary']['high_importance']}")
    print(f"- 当前敏感期: {summary['current_sensitivity']['is_sensitive']}")