#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据获取模块
"""

from .eastmoney_api import get_stock_hist
from .real_provider import RealDataProvider, FinancialIndicators, get_financial_indicators
from .governance import CacheManager, DataQualityChecker, DataSnapshot, build_snapshot

__all__ = [
    'get_stock_hist',
    'RealDataProvider',
    'FinancialIndicators',
    'get_financial_indicators',
    'CacheManager',
    'DataQualityChecker',
    'DataSnapshot',
    'build_snapshot',
]
