# A股趋势策略 - 新闻政策监控系统

一个集成新闻政策监控功能的A股趋势跟踪策略系统，通过实时监控重要新闻和政策发布，为策略提供风险控制和决策支持。

## 功能特性

### 🔍 新闻数据采集
- **多数据源支持**: 新浪财经、东方财富、官方渠道(央行、证监会、发改委)
- **实时监控**: 定时爬取最新新闻和政策公告
- **智能去重**: 自动识别和过滤重复新闻

### 🧠 智能分析
- **中文情感分析**: 基于jieba分词的情感识别和强度评估
- **关键词监控**: 多层级关键词匹配(政策、行业、风险)
- **影响评估**: 自动评估新闻对不同行业的影响程度

### 📅 政策日历
- **重要事件跟踪**: 两会、政治局会议、央行例会等
- **敏感期识别**: 自动识别政策敏感时间窗口
- **提前预警**: 重要事件前的风险提示

### ⚠️ 风险评估
- **多维度评分**: 综合情感、关键词、政策等因素
- **风险分级**: 高、中、低三级风险等级
- **实时预警**: 及时发现和响应风险事件

### 🎯 策略联动
- **自动化响应**: 根据风险级别自动调整仓位
- **行业轮动**: 基于政策导向优化行业配置
- **交易模式切换**: 正常、保守、防御等多种模式

## 快速开始

### 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 或者安装开发版本
pip install -e .[dev]

# 如果需要股票数据接口
pip install -e .[data]
```

### 基本使用

```python
from news_monitor import create_monitor_system

# 创建监控系统
monitor = create_monitor_system()

# 启动监控
monitor.start_monitoring()

# 获取系统状态
status = monitor.get_system_status()
print(f"当前策略模式: {status['strategy_status']['current_mode']}")
print(f"仓位比例: {status['strategy_status']['current_position_ratio']}")
```

### 单独使用各个模块

#### 新闻爬虫
```python
from news_monitor.news_crawler import NewsCrawler

crawler = NewsCrawler()
news_data = crawler.crawl_all_sources(hours_back=24)
```

#### 情感分析
```python
from news_monitor.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze_news_comprehensive(news_item)
print(f"情感: {result['sentiment']['sentiment_label']}")
print(f"风险评分: {result['risk_score']}")
```

#### 关键词匹配
```python
from news_monitor.keyword_matcher import KeywordMatcher

matcher = KeywordMatcher()
result = matcher.comprehensive_analysis(text)
print(f"政策影响: {result['policy_impact']['impact_score']}")
```

## 系统架构

```
A股新闻政策监控系统
├── 数据采集层
│   ├── 新闻爬虫 (news_crawler.py)
│   ├── 政策日历 (policy_calendar.py)
│   └── 数据源配置
├── 分析处理层
│   ├── 情感分析 (sentiment_analyzer.py)
│   ├── 关键词匹配 (keyword_matcher.py)
│   └── 风险评估 (risk_assessor.py)
├── 策略联动层
│   ├── 策略适配器 (strategy_adapter.py)
│   ├── 信号生成
│   └── 仓位管理
└── 系统管理层
    ├── 监控系统 (monitor_system.py)
    ├── 任务调度
    └── 状态管理
```

## 配置说明

系统配置文件位于 `config/news_monitor_config.yaml`:

### 数据源配置
```yaml
news_sources:
  sina_finance:
    enabled: true
    priority: 7
    request_delay: 1.0
  official_sources:
    enabled: true
    priority: 10
```

### 风险阈值配置
```yaml
risk_assessment:
  thresholds:
    high_risk: 0.7
    medium_risk: 0.4
  weights:
    sentiment_weight: 0.3
    impact_weight: 0.4
```

### 策略参数配置
```yaml
strategy_adapter:
  position_limits:
    max_reduction: 0.8
    min_position: 0.2
  industry_weights:
    finance: 0.25
    technology: 0.20
```

## 主要模块说明

### NewsCrawler (新闻爬虫)
- 支持多个数据源并行爬取
- 自动处理请求频率限制
- 统一数据格式输出

### SentimentAnalyzer (情感分析)
- 中文文本情感识别
- 影响程度和时效性评估
- 相关行业自动识别

### KeywordMatcher (关键词匹配)
- 多层级关键词库
- 正则表达式优化
- 动态关键词管理

### PolicyCalendar (政策日历)
- 重要政策事件管理
- 周期性事件计算
- 敏感期自动识别

### RiskAssessor (风险评估)
- 多维度风险评分
- 历史数据对比
- 风险级别自动判定

### StrategyAdapter (策略适配)
- 风险事件自动响应
- 行业轮动信号生成
- 仓位动态调整

## 风险响应机制

### 高风险事件响应
- **触发条件**: 风险评分 ≥ 0.7
- **响应动作**: 立即减仓50-80%
- **交易模式**: 切换到防御模式
- **监控级别**: 密集监控

### 中风险事件响应
- **触发条件**: 风险评分 0.4-0.7
- **响应动作**: 适当减仓20-50%
- **交易模式**: 保守交易模式
- **监控级别**: 加强监控

### 政策敏感期处理
- **事件前**: 提前1-2天减仓
- **事件中**: 暂停新开仓
- **事件后**: 根据结果调整策略

## 使用示例

运行完整功能演示:
```bash
python examples/demo.py
```

这将展示:
- 新闻数据采集
- 情感分析处理
- 风险评估流程
- 策略信号生成
- 完整系统运行

## 监控界面

系统提供实时状态监控:

```python
# 获取系统状态
status = monitor.get_system_status()

# 查看最近新闻
recent_news = status['recent_news']

# 查看策略状态
strategy_status = status['strategy_status']

# 查看政策日历
policy_info = status['policy_context']
```

## 数据导出

支持历史数据导出:
```python
# 导出最近7天数据
export_data = monitor.export_data()

# 导出指定时间范围
export_data = monitor.export_data(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

## 扩展开发

### 添加新的数据源
1. 在 `NewsCrawler` 中添加新的爬取方法
2. 更新配置文件中的数据源设置
3. 测试数据格式兼容性

### 自定义关键词库
```python
matcher = KeywordMatcher()
matcher.add_custom_keywords(
    category="custom_policy",
    subcategory="new_regulation", 
    keywords=["新规", "监管细则"]
)
```

### 扩展风险评估模型
继承 `RiskAssessor` 类并重写评估方法:
```python
class CustomRiskAssessor(RiskAssessor):
    def _calculate_custom_risk(self, data):
        # 自定义风险计算逻辑
        pass
```

## 注意事项

1. **数据源限制**: 部分数据源可能有访问频率限制
2. **网络依赖**: 系统需要稳定的网络连接
3. **计算资源**: 大量新闻分析需要足够的CPU资源
4. **存储空间**: 历史数据积累需要考虑存储容量

## 免责声明

本系统仅供学习和研究使用，不构成投资建议。使用者应当:
- 充分了解系统的局限性
- 结合其他分析工具做决策
- 控制风险，合理配置资金
- 遵守相关法律法规

## 开发路线图

- [ ] 增加更多数据源支持
- [ ] 优化情感分析算法
- [ ] 添加机器学习模型
- [ ] 实现Web可视化界面
- [ ] 集成实时交易接口
- [ ] 增加回测功能

## 贡献指南

欢迎提交Issue和Pull Request来完善系统功能。

## 许可证

MIT License