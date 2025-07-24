"""
真实数据连接示例

演示如何连接akshare获取真实A股数据进行回测。
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def install_akshare():
    """安装akshare数据源"""
    import subprocess
    import sys
    
    print("📦 正在安装 AkShare 数据源...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare"])
        print("✅ AkShare 安装成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ AkShare 安装失败")
        return False


def test_akshare_connection():
    """测试akshare连接"""
    try:
        import akshare as ak
        print("🔗 测试 AkShare 数据连接...")
        
        # 获取股票基本信息
        stock_info = ak.stock_info_a_code_name()
        print(f"✅ 成功获取股票列表: {len(stock_info)} 只股票")
        
        # 获取单只股票数据测试
        print("📊 测试获取平安银行(000001)数据...")
        data = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                                 start_date="20240101", end_date="20240131", adjust="qfq")
        
        if data is not None and len(data) > 0:
            print(f"✅ 成功获取 {len(data)} 条历史数据")
            print("最近5天数据:")
            print(data.tail())
            return True
        else:
            print("❌ 未获取到数据")
            return False
            
    except ImportError:
        print("❌ AkShare 未安装")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {str(e)}")
        return False


def run_real_data_backtest():
    """使用真实数据运行回测"""
    print("\n🚀 使用真实A股数据进行回测")
    print("=" * 50)
    
    from astrategy.core.engine import StrategyEngine
    from astrategy.utils.config import load_config
    
    # 加载配置
    config = load_config()
    
    # 确保使用akshare作为主要数据源
    config['data']['primary_source'] = 'akshare'
    
    # 创建策略引擎
    engine = StrategyEngine()
    engine.config = config
    
    # 重新初始化数据提供者以使用真实数据源
    from astrategy.data.providers import DataProvider
    engine.data_provider = DataProvider(config)
    
    # 设置回测参数
    start_date = "2024-01-01"
    end_date = "2024-06-30"
    
    # 选择流动性好的大盘股
    universe = [
        '000001',  # 平安银行
        '000002',  # 万科A
        '600000',  # 浦发银行
        '600036',  # 招商银行
        '600519',  # 贵州茅台
        '000858'   # 五粮液
    ]
    
    print(f"📊 回测设置:")
    print(f"   期间: {start_date} 至 {end_date}")
    print(f"   股票池: {universe}")
    print(f"   数据源: {config['data']['primary_source']}")
    
    try:
        # 初始化
        print("\n📥 加载真实市场数据...")
        engine.initialize(start_date, end_date, universe)
        
        # 运行回测
        print("🔄 开始回测...")
        results = engine.run_backtest()
        
        # 展示结果
        print("\n" + "=" * 50)
        print("📈 真实数据回测结果")
        print("=" * 50)
        
        metrics = results['performance_metrics']
        
        print(f"总收益率:     {metrics.get('total_return', 0):.2%}")
        print(f"年化收益率:   {metrics.get('annual_return', 0):.2%}")
        print(f"年化波动率:   {metrics.get('annual_volatility', 0):.2%}")
        print(f"夏普比率:     {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"最大回撤:     {metrics.get('max_drawdown', 0):.2%}")
        print(f"胜率:         {metrics.get('win_rate', 0):.2%}")
        print(f"总交易次数:   {metrics.get('total_trades', 0)}")
        
        # 交易记录
        trade_history = results['trade_history']
        if trade_history:
            print(f"\n📋 交易记录 (共{len(trade_history)}笔):")
            for i, trade in enumerate(trade_history[:10]):
                action = "买入" if trade['action'] == 'buy' else "卖出"
                pnl_info = ""
                if 'pnl' in trade:
                    pnl_info = f" | 盈亏:{trade['pnl']:.2f}"
                
                print(f"{i+1:2d}. {trade['date'].strftime('%Y-%m-%d')} {action} {trade['symbol']} "
                      f"{trade['quantity']}股 @ {trade['price']:.2f}{pnl_info}")
        
        print("\n✅ 真实数据回测完成!")
        
        # 与基准比较
        print(f"\n📊 基准比较:")
        print(f"同期沪深300收益: [需要获取基准数据]")
        print(f"超额收益: [需要计算]")
        
        return results
        
    except Exception as e:
        print(f"❌ 回测失败: {str(e)}")
        print("\n可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 确认akshare版本兼容性")
        print("3. 检查股票代码格式")
        print("4. 减少请求频率避免限制")
        return None


def compare_data_sources():
    """比较不同数据源的差异"""
    print("\n🔍 数据源比较")
    print("=" * 50)
    
    print("AkShare 优势:")
    print("- 免费开源")
    print("- 数据全面 (股票、期货、基金等)")
    print("- 更新及时")
    print("- 接口丰富")
    
    print("\nTuShare 优势:")
    print("- 数据质量稳定")
    print("- 历史数据完整")
    print("- 提供基本面数据")
    print("- 接口标准化")
    print("- 需要积分/付费")
    
    print("\n使用建议:")
    print("- 开发测试: 使用AkShare")
    print("- 生产环境: 考虑TuShare Pro")
    print("- 数据备份: 建立本地数据库")
    print("- 多源验证: 重要数据多源对比")


def main():
    """主函数"""
    print("🌐 A股趋势策略 - 真实数据连接示例")
    print("=" * 60)
    
    # 1. 检查是否已安装akshare
    try:
        import akshare
        print("✅ AkShare 已安装")
        akshare_available = True
    except ImportError:
        print("❌ AkShare 未安装")
        akshare_available = False
        
        # 询问是否安装
        try:
            response = input("是否现在安装 AkShare? (y/n): ").lower()
            if response == 'y':
                akshare_available = install_akshare()
        except KeyboardInterrupt:
            print("\n操作取消")
            return
    
    if akshare_available:
        # 2. 测试连接
        if test_akshare_connection():
            # 3. 运行真实数据回测
            print("\n" + "="*60)
            try:
                response = input("是否运行真实数据回测? (y/n): ").lower()
                if response == 'y':
                    results = run_real_data_backtest()
                    if results:
                        print("回测成功完成!")
                else:
                    print("跳过真实数据回测")
            except KeyboardInterrupt:
                print("\n操作取消")
        else:
            print("数据连接失败，请检查网络或稍后重试")
    else:
        print("❌ 无法使用真实数据源")
        print("💡 建议:")
        print("- 手动安装: pip install akshare")
        print("- 或使用模拟数据进行测试")
    
    # 4. 数据源比较说明
    compare_data_sources()
    
    print("\n✅ 示例运行完成!")
    print("\n💡 后续步骤:")
    print("1. 建立定期数据更新机制")
    print("2. 实现数据质量检查")
    print("3. 考虑数据缓存和备份")
    print("4. 监控数据源稳定性")


if __name__ == "__main__":
    main()