#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易模拟 Skill

模拟真实交易环境，验证策略有效性

使用示例:
    from skills.stock_simulator import TradingSimulator
    simulator = TradingSimulator(initial_cash=1000000)
    simulator.buy("000001", "平安银行", 10.5, 1000)
"""

from .simulator import (
    TradingSimulator,
    Position,
    TradeRecord,
    PortfolioSnapshot,
    create_simulator
)

__version__ = '1.0.0'

__all__ = [
    'TradingSimulator',
    'Position',
    'TradeRecord',
    'PortfolioSnapshot',
    'create_simulator',
]
