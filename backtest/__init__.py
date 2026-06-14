#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测模块

提供回测引擎和相关工具

模块结构:
- adapter.py: 数据和策略适配器
- engine.py: 回测引擎
- analyzer.py: 结果分析器
- report.py: 报告生成器

使用示例:
    # 使用便捷函数
    from backtest import run_backtest
    result = run_backtest("000001", "ma_cross")
    print(result.summary())

    # 使用引擎
    from backtest import BacktestEngine
    engine = BacktestEngine(initial_cash=100000)
    result = engine.run("000001", "ma_cross")
"""

from .adapter import StockDataFeed, StrategyAdapter
from .engine import BacktestEngine, BacktestResult, run_backtest

# 模块版本
__version__ = '1.0.0'

# 导出所有公共接口
__all__ = [
    # 适配器
    'StockDataFeed',
    'StrategyAdapter',

    # 引擎
    'BacktestEngine',
    'BacktestResult',
    'run_backtest',
]
