#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能选股 Skill

根据条件筛选股票

使用示例:
    from skills.stock_selector import screen_stocks
    stocks = screen_stocks(ma_cross=True, risk_profile="moderate")
"""

from .screener import (
    StockScreener,
    ScreeningConditions,
    StockCandidate,
    screen_stocks
)

__version__ = '1.0.0'

__all__ = [
    'StockScreener',
    'ScreeningConditions',
    'StockCandidate',
    'screen_stocks',
]
