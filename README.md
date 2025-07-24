# A股趋势策略系统

## 项目简介

基于原有EasyLanguage三角移动平均线策略，专门为中国A股市场开发的趋势跟踪策略系统。该系统充分考虑了A股市场的特殊交易规则和市场特点，提供完整的策略开发、回测和风险管理功能。

## 主要特性

### 🎯 策略核心
- **三角移动平均线**：优化的快慢线交叉策略
- **ADX趋势确认**：避免震荡市假突破
- **突破入场机制**：多重确认的入场信号
- **动态仓位管理**：根据信号强度调整仓位

### 🇨🇳 A股特色功能
- **T+1交易约束**：自动处理当日买入限制
- **涨跌停板检测**：避免追涨停和杀跌停
- **午间休市控制**：降低午间跳空风险
- **节假日处理**：节前自动减仓机制
- **政策敏感期管理**：重大政策期间降低仓位

### 📊 技术指标集成
- **MACD指标**：趋势确认和背离检测
- **KDJ指标**：超买超卖判断
- **成交量分析**：放量确认和缩量警告
- **市场情绪指标**：多维度市场状态评估

### 🛡️ 风险控制
- **最大回撤控制**：动态调整仓位
- **止损止盈机制**：固定止损+追踪止损
- **仓位管理系统**：多层级风险控制
- **实时风险监控**：全面的风险指标跟踪

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/Yushcheng777/a-stock-trend-strategy.git
cd a-stock-trend-strategy

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 基础使用

```python
from astrategy.core.engine import StrategyEngine

# 初始化策略引擎
engine = StrategyEngine()

# 设置回测参数
start_date = "2023-01-01"
end_date = "2023-12-31"
universe = ['000001', '000002', '600000', '600519']  # 股票池

# 运行回测
engine.initialize(start_date, end_date, universe)
results = engine.run_backtest()

# 查看结果
print(f"总收益率: {results['performance_metrics']['total_return']:.2%}")
print(f"夏普比率: {results['performance_metrics']['sharpe_ratio']:.2f}")
```

### 命令行使用

```bash
# 运行回测
a-stock-strategy backtest --start-date 2023-01-01 --end-date 2023-12-31

# 获取股票数据
a-stock-strategy data --symbol 000001 --days 30

# 检查配置
a-stock-strategy config-check
```

## 项目结构

```
a-stock-trend-strategy/
├── src/astrategy/           # 核心代码
│   ├── core/               # 策略核心
│   │   ├── strategy.py     # 主策略逻辑
│   │   └── engine.py       # 策略执行引擎
│   ├── indicators/         # 技术指标
│   │   ├── triangular_ma.py # 三角移动平均线
│   │   └── adx.py          # ADX指标
│   ├── risk/              # 风险管理
│   │   └── manager.py      # 风险管理器
│   ├── data/              # 数据接口
│   │   └── providers.py    # 数据提供者
│   ├── utils/             # 工具模块
│   │   └── config.py       # 配置管理
│   ├── config/            # 配置文件
│   │   └── default.yaml    # 默认配置
│   └── cli.py             # 命令行接口
├── examples/              # 使用示例
├── tests/                 # 测试代码
├── docs/                  # 文档
├── requirements.txt       # 依赖列表
└── setup.py              # 安装配置
```

## 配置说明

### 策略参数配置

```yaml
strategy:
  # 三角移动平均线参数
  triangular_ma:
    fast_period: 5      # 快线周期
    slow_period: 30     # 慢线周期
    smoothing: 3        # 平滑系数
  
  # ADX参数
  adx:
    period: 14          # 计算周期
    threshold: 25       # 趋势阈值
    strong_trend: 40    # 强趋势阈值
```

### 风险控制配置

```yaml
risk:
  position:
    max_position: 0.95        # 最大仓位
    initial_position: 0.2     # 初始建仓比例
    max_single_stock: 0.15    # 单股最大仓位
  
  stop_loss:
    max_loss: 0.08           # 最大亏损比例
    trailing_stop: 0.05      # 追踪止损比例
```

### A股特色配置

```yaml
a_share_features:
  price_limit:
    avoid_limit_up: true      # 避免追涨停
    avoid_limit_down: true    # 避免追跌停
  
  lunch_break:
    reduce_position_before: true  # 午休前减仓
    avoid_new_entry: true        # 午休前避免开仓
```

## 数据源支持

### AkShare (推荐)

```python
# 自动配置，无需token
data_provider = DataProvider(config)
data = data_provider.get_stock_data('000001', '2023-01-01', '2023-12-31')
```

### TuShare

```python
# 需要配置token
config['data']['tushare_token'] = 'your_token_here'
```

### 模拟数据

系统提供模拟数据生成功能，用于测试和演示：

```python
# 自动生成模拟数据用于测试
data = data_provider._generate_mock_data('000001', '2023-01-01', '2023-12-31')
```

## 性能指标

系统提供完整的策略性能评估：

- **收益指标**：总收益率、年化收益率
- **风险指标**：年化波动率、最大回撤、VaR
- **风险调整收益**：夏普比率、卡尔马比率
- **交易指标**：胜率、盈亏比、交易频率

## 可视化分析

```python
# 生成回测报告（需要安装可视化依赖）
from astrategy.analysis import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(results)
analyzer.plot_equity_curve()      # 资金曲线
analyzer.plot_drawdown()          # 回撤图
analyzer.plot_monthly_returns()   # 月度收益热力图
```

## 实盘交易

⚠️ **风险提示**：本系统仅供学习研究使用，实盘交易需要：

1. 充分的回测验证
2. 小资金实盘测试
3. 持续的风险监控
4. 合规的券商接口

## 贡献指南

欢迎提交issue和pull request：

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 免责声明

本软件仅供教育和研究目的使用。股票投资存在风险，可能导致本金损失。使用本软件进行投资决策的风险由用户自行承担。开发者不对任何投资损失承担责任。

## 联系我们

- GitHub Issues: [提交问题](https://github.com/Yushcheng777/a-stock-trend-strategy/issues)
- 邮箱: [项目邮箱]

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**