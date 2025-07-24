#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="a-stock-trend-strategy",
    version="0.1.0",
    description="A股趋势策略系统 - 集成新闻政策监控的风险控制策略",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Yushcheng777",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.0.0", 
        "numpy>=1.24.0",
        "jieba>=0.42.1",
        "schedule>=1.2.0",
        "python-dateutil>=2.8.2",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "scikit-learn>=1.3.0",
        "textblob>=0.17.1",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0", 
            "flake8>=6.0.0",
        ],
        "data": [
            "akshare>=1.11.0",
            "tushare>=1.2.0",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="stock trading strategy news monitoring A股 policy risk control",
)