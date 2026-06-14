#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略模块

提供可扩展的策略框架，支持多策略组合

模块结构:
- base.py: 策略基类、Signal、Bar
- registry.py: 策略注册表
- ma_cross.py: 双均线策略
- macd_strategy.py: MACD 策略
- rsi_strategy.py: RSI 策略
- boll_strategy.py: 布林带策略
- composite.py: 综合策略

使用示例:
    # 使用注册表创建策略
    from strategies import StrategyRegistry
    strategy = StrategyRegistry.create("ma_cross", {'fast_period': 5})

    # 使用便捷函数
    from strategies import get_strategy
    strategy = get_strategy("macd", {'fast_period': 12})

    # 列出所有策略
    from strategies import list_strategies
    print(list_strategies())
"""

# 导入基础类
from .base import Strategy, Bar, Signal, SignalType

# 导入注册表
from .registry import (
    StrategyRegistry,
    register_strategy,
    get_strategy,
    list_strategies
)

# 导入内置策略 (触发注册)
from .ma_cross import MACrossStrategy
from .macd_strategy import MACDStrategy
from .rsi_strategy import RSIStrategy
from .boll_strategy import BollStrategy
from .composite import CompositeStrategy

# 模块版本
__version__ = '1.0.0'

# 导出所有公共接口
__all__ = [
    # 基础类
    'Strategy',
    'Bar',
    'Signal',
    'SignalType',

    # 注册表
    'StrategyRegistry',
    'register_strategy',
    'get_strategy',
    'list_strategies',

    # 内置策略
    'MACrossStrategy',
    'MACDStrategy',
    'RSIStrategy',
    'BollStrategy',
    'CompositeStrategy',
]
