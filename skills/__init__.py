# Skills 模块
"""
Skills 目录包含所有可插拔的功能模块
每个 Skill 都是一个独立的功能单元

可用的 Skills:
- stock_advisor: 个股买卖建议
- stock_visual: 可视化图表
- stock_recommender: 股票推荐 (规则+ML+在线学习)
"""

# 延迟导入，避免循环依赖
def get_stock_advisor():
    """获取 Stock Advisor Skill"""
    from .stock_advisor import StockAnalyzer, analyze, batch_analyze
    return {
        'StockAnalyzer': StockAnalyzer,
        'analyze': analyze,
        'batch_analyze': batch_analyze
    }


def get_stock_visual():
    """获取可视化模块"""
    from .stock_visual import (
        KLineChart,
        IndicatorChart,
        BacktestChart,
        Dashboard,
        plot_kline,
        plot_indicators,
        plot_backtest,
        create_stock_dashboard,
        create_backtest_dashboard
    )
    return {
        'KLineChart': KLineChart,
        'IndicatorChart': IndicatorChart,
        'BacktestChart': BacktestChart,
        'Dashboard': Dashboard,
        'plot_kline': plot_kline,
        'plot_indicators': plot_indicators,
        'plot_backtest': plot_backtest,
        'create_stock_dashboard': create_stock_dashboard,
        'create_backtest_dashboard': create_backtest_dashboard
    }


__all__ = ['get_stock_advisor', 'get_stock_visual']
