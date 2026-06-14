#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
市场分析 Skill

分析大盘走势、板块轮动、市场情绪

使用示例:
    from skills.stock_market import MarketAnalyzer
    analyzer = MarketAnalyzer()
    overview = analyzer.get_market_overview()
    print(overview.summary())
"""

from .analyzer import (
    MarketAnalyzer,
    MarketOverview,
    MarketSentiment,
    IndexData,
    SectorData,
    get_market_overview
)

__version__ = '1.0.0'

__all__ = [
    'MarketAnalyzer',
    'MarketOverview',
    'MarketSentiment',
    'IndexData',
    'SectorData',
    'get_market_overview',
]
