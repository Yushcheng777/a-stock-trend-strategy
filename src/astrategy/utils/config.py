"""
配置管理器

处理策略配置文件的加载、验证和管理。
"""

import yaml
import os
from typing import Dict, Any, Optional
import logging


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config_path = config_path
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self._load_config()
        
        # 验证配置
        self._validate_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_path is None:
            # 使用默认配置文件
            default_config_path = os.path.join(
                os.path.dirname(__file__), '..', 'config', 'default.yaml'
            )
            self.config_path = os.path.abspath(default_config_path)
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                self.logger.info(f"配置文件加载成功: {self.config_path}")
        except FileNotFoundError:
            self.logger.error(f"配置文件未找到: {self.config_path}")
            self.config = self._get_default_config()
        except yaml.YAMLError as e:
            self.logger.error(f"配置文件格式错误: {str(e)}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'market': {
                'name': 'A股市场',
                'timezone': 'Asia/Shanghai',
                'trading_hours': {
                    'morning_start': '09:30',
                    'morning_end': '11:30',
                    'afternoon_start': '13:00',
                    'afternoon_end': '15:00'
                },
                'rules': {
                    't_plus_1': True,
                    'price_limit_normal': 0.10,
                    'price_limit_star': 0.20
                }
            },
            'strategy': {
                'triangular_ma': {
                    'fast_period': 5,
                    'slow_period': 30,
                    'smoothing': 3
                },
                'adx': {
                    'period': 14,
                    'threshold': 25,
                    'strong_trend': 40
                }
            },
            'risk': {
                'position': {
                    'max_position': 0.95,
                    'initial_position': 0.2,
                    'max_single_stock': 0.15
                },
                'stop_loss': {
                    'max_loss': 0.08,
                    'trailing_stop': 0.05
                }
            },
            'backtest': {
                'initial_capital': 1000000,
                'costs': {
                    'commission': 0.0003,
                    'stamp_tax': 0.001,
                    'min_commission': 5
                }
            }
        }
    
    def _validate_config(self):
        """验证配置文件"""
        required_sections = ['market', 'strategy', 'risk', 'backtest']
        
        for section in required_sections:
            if section not in self.config:
                self.logger.warning(f"配置文件缺少必要部分: {section}")
                self.config[section] = self._get_default_config().get(section, {})
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置的特定部分"""
        return self.config.get(section, {})
    
    def update_config(self, section: str, key: str, value: Any):
        """更新配置项"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        self.logger.info(f"配置更新: {section}.{key} = {value}")
    
    def save_config(self, output_path: Optional[str] = None):
        """保存配置到文件"""
        save_path = output_path or self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            self.logger.info(f"配置文件保存成功: {save_path}")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {str(e)}")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    快捷函数：加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    config_manager = ConfigManager(config_path)
    return config_manager.get_config()