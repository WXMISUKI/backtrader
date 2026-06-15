"""
智能交易决策模块
综合技术面、基本面、趋势判断，提供精准的买卖时机建议
"""

from .advisor import TradingAdvisor, TradeDecision
from .trend_detector import TrendDetector, TrendInfo, TrendType
from .entry_exit import EntryExitTiming, EntrySignal, ExitSignal
from .position_manager import PositionManager
from .risk_controller import RiskController

__version__ = '1.0.0'

__all__ = [
    # 核心决策
    'TradingAdvisor',
    'TradeDecision',

    # 趋势检测
    'TrendDetector',
    'TrendInfo',
    'TrendType',

    # 入场出场
    'EntryExitTiming',
    'EntrySignal',
    'ExitSignal',

    # 仓位管理
    'PositionManager',

    # 风险控制
    'RiskController',
]
