#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基本面分析 Skill

分析股票的基本面数据

使用示例:
    from skills.stock_fundamental import FundamentalAnalyzer
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze("000001")
    print(result.summary())
"""

from .analyzer import (
    FundamentalAnalyzer,
    FundamentalResult,
    analyze_fundamental
)

__version__ = '1.0.0'

__all__ = [
    'FundamentalAnalyzer',
    'FundamentalResult',
    'analyze_fundamental',
]
