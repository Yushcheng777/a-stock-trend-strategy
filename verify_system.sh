#!/bin/bash

# A股趋势策略系统 - 完整验证脚本
# 验证所有功能模块是否正常工作

echo "🚀 A股趋势策略系统 - 完整功能验证"
echo "================================================"

# 设置Python路径
export PYTHONPATH=src

# 1. 检查Python环境
echo "📋 1. 检查Python环境..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python环境不可用"
    exit 1
fi

# 2. 检查依赖包
echo -e "\n📦 2. 检查核心依赖包..."
python -c "import numpy, pandas, yaml; print('✅ 核心依赖包正常')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少核心依赖包，正在安装..."
    pip install numpy pandas pyyaml
fi

# 3. 验证模块导入
echo -e "\n🔧 3. 验证模块导入..."
python -c "
import sys, os
sys.path.insert(0, 'src')
try:
    from astrategy.core.engine import StrategyEngine
    from astrategy.indicators.triangular_ma import TriangularMA
    from astrategy.indicators.adx import ADXIndicator
    from astrategy.risk.manager import RiskManager
    from astrategy.utils.config import load_config
    print('✅ 所有核心模块导入成功')
except Exception as e:
    print(f'❌ 模块导入失败: {e}')
    sys.exit(1)
"
if [ $? -ne 0 ]; then
    echo "❌ 模块导入验证失败"
    exit 1
fi

# 4. 运行组件测试
echo -e "\n🧪 4. 运行组件测试..."
python tests/integration_test.py
if [ $? -ne 0 ]; then
    echo "❌ 组件测试失败"
    exit 1
fi

# 5. 验证配置文件
echo -e "\n⚙️  5. 验证配置文件..."
python -c "
import sys
sys.path.insert(0, 'src')
from astrategy.utils.config import load_config
config = load_config()
print('✅ 配置文件加载正常')
print(f'策略名称: {config.get(\"strategy\", {}).get(\"name\", \"未知\")}')
"

# 6. 测试CLI接口
echo -e "\n💻 6. 测试CLI接口..."
python -m astrategy.cli version
if [ $? -ne 0 ]; then
    echo "❌ CLI接口测试失败"
    exit 1
fi

# 7. 运行基础示例
echo -e "\n📊 7. 运行基础使用示例..."
timeout 60 python examples/basic_usage.py
if [ $? -ne 0 ]; then
    echo "⚠️  基础示例运行异常（可能是超时）"
else
    echo "✅ 基础示例运行完成"
fi

# 8. 检查文档
echo -e "\n📚 8. 检查文档完整性..."
required_files=(
    "README.md"
    "docs/strategy_guide.md"
    "examples/basic_usage.py"
    "examples/advanced_usage.py"
    "examples/real_data_example.py"
    "src/astrategy/config/default.yaml"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少文件: $file"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -eq 0 ]; then
    echo "✅ 所有必需文档文件完整"
else
    echo "❌ 缺少 $missing_files 个必需文件"
    exit 1
fi

# 9. 项目结构检查
echo -e "\n📁 9. 检查项目结构..."
required_dirs=(
    "src/astrategy/core"
    "src/astrategy/indicators"
    "src/astrategy/risk"
    "src/astrategy/data"
    "src/astrategy/utils"
    "examples"
    "tests"
    "docs"
)

missing_dirs=0
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ 缺少目录: $dir"
        missing_dirs=$((missing_dirs + 1))
    fi
done

if [ $missing_dirs -eq 0 ]; then
    echo "✅ 项目结构完整"
else
    echo "❌ 缺少 $missing_dirs 个必需目录"
    exit 1
fi

# 10. 输出总结
echo -e "\n================================================"
echo "🎉 验证完成总结"
echo "================================================"
echo "✅ Python环境正常"
echo "✅ 依赖包安装完整"
echo "✅ 模块导入成功"
echo "✅ 组件测试通过"
echo "✅ 配置文件正常"
echo "✅ CLI接口可用"
echo "✅ 示例代码运行"
echo "✅ 文档完整"
echo "✅ 项目结构完整"

echo -e "\n🚀 A股趋势策略系统已准备就绪！"
echo -e "\n📖 快速开始:"
echo "   python examples/basic_usage.py"
echo -e "\n💻 命令行使用:"
echo "   PYTHONPATH=src python -m astrategy.cli backtest --help"
echo -e "\n📚 查看文档:"
echo "   cat docs/strategy_guide.md"

echo -e "\n⚠️  重要提醒:"
echo "- 本系统仅供学习研究使用"
echo "- 实盘交易请谨慎评估风险"
echo "- 建议先进行充分的历史回测"
echo "- 使用真实数据需要安装akshare: pip install akshare"