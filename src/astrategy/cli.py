"""
命令行接口

提供策略的命令行操作接口。
"""

import click
import os
import sys
from datetime import datetime, timedelta
import logging

# 添加src路径到Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from astrategy.core.engine import StrategyEngine
from astrategy.utils.config import load_config
from astrategy.data.providers import DataProvider


@click.group()
@click.option('--config', '-c', help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config, verbose):
    """A股趋势策略系统命令行工具"""
    # 设置日志级别
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 存储配置路径到上下文
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.option('--start-date', '-s', default='2022-01-01', help='开始日期 (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='结束日期 (YYYY-MM-DD)，默认为今天')
@click.option('--symbols', help='股票代码列表，用逗号分隔，默认使用预设股票池')
@click.option('--output', '-o', help='结果输出文件夹')
@click.pass_context
def backtest(ctx, start_date, end_date, symbols, output):
    """运行回测"""
    click.echo("🚀 开始运行A股趋势策略回测...")
    
    # 处理日期
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 处理股票池
    if symbols is None:
        # 使用默认股票池
        universe = ['000001', '000002', '000858', '600000', '600036', '600519', '600887', '002415']
        click.echo(f"使用默认股票池: {len(universe)} 只股票")
    else:
        universe = [s.strip() for s in symbols.split(',')]
        click.echo(f"使用自定义股票池: {len(universe)} 只股票")
    
    try:
        # 初始化策略引擎
        config_path = ctx.obj.get('config_path')
        engine = StrategyEngine(config_path)
        
        # 初始化
        engine.initialize(start_date, end_date, universe)
        
        # 运行回测
        click.echo(f"📊 回测期间: {start_date} 至 {end_date}")
        with click.progressbar(length=100, label='回测进度') as bar:
            # 这里可以添加进度回调
            results = engine.run_backtest()
            bar.update(100)
        
        # 显示结果
        metrics = results['performance_metrics']
        click.echo("\n📈 回测结果:")
        click.echo(f"总收益率: {metrics.get('total_return', 0):.2%}")
        click.echo(f"年化收益率: {metrics.get('annual_return', 0):.2%}")
        click.echo(f"年化波动率: {metrics.get('annual_volatility', 0):.2%}")
        click.echo(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        click.echo(f"最大回撤: {metrics.get('max_drawdown', 0):.2%}")
        click.echo(f"胜率: {metrics.get('win_rate', 0):.2%}")
        click.echo(f"总交易次数: {metrics.get('total_trades', 0)}")
        
        # 保存结果
        if output:
            click.echo(f"\n💾 保存结果到: {output}")
            # 这里可以添加结果保存逻辑
        
    except Exception as e:
        click.echo(f"❌ 回测失败: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--symbol', '-s', required=True, help='股票代码')
@click.option('--days', '-d', default=30, help='获取天数')
@click.pass_context
def data(ctx, symbol, days):
    """获取股票数据"""
    click.echo(f"📥 获取 {symbol} 最近 {days} 天的数据...")
    
    try:
        config_path = ctx.obj.get('config_path')
        config = load_config(config_path)
        
        data_provider = DataProvider(config)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = data_provider.get_stock_data(
            symbol, 
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if data is not None and len(data) > 0:
            click.echo(f"✅ 成功获取 {len(data)} 条数据")
            click.echo("\n最近5天数据:")
            click.echo(data.tail().to_string())
        else:
            click.echo("❌ 未获取到数据")
            
    except Exception as e:
        click.echo(f"❌ 数据获取失败: {str(e)}", err=True)


@cli.command()
@click.pass_context
def config_check(ctx):
    """检查配置文件"""
    click.echo("🔧 检查配置文件...")
    
    try:
        config_path = ctx.obj.get('config_path')
        config = load_config(config_path)
        
        click.echo("✅ 配置文件加载成功")
        click.echo(f"策略名称: {config.get('strategy', {}).get('name', '未知')}")
        click.echo(f"初始资金: {config.get('backtest', {}).get('initial_capital', 0):,}")
        click.echo(f"数据源: {config.get('data', {}).get('primary_source', '未知')}")
        
    except Exception as e:
        click.echo(f"❌ 配置检查失败: {str(e)}", err=True)


@cli.command()
def version():
    """显示版本信息"""
    click.echo("A股趋势策略系统 v1.0.0")
    click.echo("基于三角移动平均线的A股趋势跟踪策略")


def main():
    """主函数入口"""
    cli()


if __name__ == '__main__':
    main()