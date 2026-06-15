"""
股票可视化模块
提供 K 线图、指标图、回测图等可视化功能
"""

from .charts import StockChart
from .kline import KLineChart, plot_kline
from .indicators import IndicatorChart, plot_indicators
from .backtest import BacktestChart, plot_backtest
from .dashboard import Dashboard, create_stock_dashboard, create_backtest_dashboard
from .themes import THEMES, get_theme

__all__ = [
    # 基础类
    'StockChart',

    # K 线图
    'KLineChart',
    'plot_kline',

    # 指标图
    'IndicatorChart',
    'plot_indicators',

    # 回测图
    'BacktestChart',
    'plot_backtest',

    # 仪表盘
    'Dashboard',
    'create_stock_dashboard',
    'create_backtest_dashboard',

    # 主题
    'THEMES',
    'get_theme',
]
