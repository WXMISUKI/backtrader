"""
图表主题样式
"""

# 暗色主题
DARK_THEME = {
    'name': 'dark',
    'background': '#1a1a2e',
    'figure_face': '#16213e',
    'axes_face': '#1a1a2e',
    'grid': '#2d3436',
    'text': '#dfe6e9',
    'title': '#ffffff',
    'xlabel': '#b2bec3',
    'ylabel': '#b2bec3',

    # K 线颜色
    'up_color': '#ff4757',      # 涨 - 红色 (中国习惯)
    'down_color': '#2ed573',    # 跌 - 绿色
    'up_edge': '#ff6b81',
    'down_edge': '#7bed9f',

    # 成交量颜色
    'volume_up': '#ff4757',
    'volume_down': '#2ed573',
    'volume_alpha': 0.7,

    # 均线颜色
    'ma_colors': ['#f0932b', '#eb4d4b', '#6ab04c', '#22a6b3', '#9b59b6'],

    # 布林带
    'boll_mid': '#3498db',
    'boll_fill': '#3498db',
    'boll_alpha': 0.15,

    # MACD
    'macd_dif': '#3498db',
    'macd_dea': '#e74c3c',
    'macd_positive': '#ff4757',
    'macd_negative': '#2ed573',

    # RSI
    'rsi_line': '#3498db',
    'rsi_overbought': '#e74c3c',
    'rsi_oversold': '#2ed573',
    'rsi_fill_alpha': 0.1,

    # KDJ
    'kdj_k': '#f0932b',
    'kdj_d': '#3498db',
    'kdj_j': '#e74c3c',

    # 信号标记
    'buy_signal': '#ff4757',
    'sell_signal': '#2ed573',
    'buy_marker': '^',
    'sell_marker': 'v',
    'signal_size': 120,

    # 资金曲线
    'equity_line': '#3498db',
    'equity_fill': '#3498db',
    'equity_alpha': 0.3,
    'benchmark_line': '#95a5a6',

    # 回撤
    'drawdown_color': '#e74c3c',
    'drawdown_alpha': 0.4,

    # 标注
    'annotation_bg': '#2d3436',
    'annotation_text': '#ffffff',
    'annotation_border': '#636e72',

    # 图例
    'legend_face': '#2d3436',
    'legend_edge': '#636e72',
    'legend_text': '#dfe6e9',
}

# 亮色主题
LIGHT_THEME = {
    'name': 'light',
    'background': '#ffffff',
    'figure_face': '#f5f6fa',
    'axes_face': '#ffffff',
    'grid': '#e1e5e9',
    'text': '#2d3436',
    'title': '#2d3436',
    'xlabel': '#636e72',
    'ylabel': '#636e72',

    # K 线颜色
    'up_color': '#ff4757',
    'down_color': '#2ed573',
    'up_edge': '#ff6b81',
    'down_edge': '#7bed9f',

    # 成交量颜色
    'volume_up': '#ff4757',
    'volume_down': '#2ed573',
    'volume_alpha': 0.6,

    # 均线颜色
    'ma_colors': ['#e17055', '#0984e3', '#00b894', '#6c5ce7', '#fdcb6e'],

    # 布林带
    'boll_mid': '#0984e3',
    'boll_fill': '#0984e3',
    'boll_alpha': 0.1,

    # MACD
    'macd_dif': '#0984e3',
    'macd_dea': '#e17055',
    'macd_positive': '#ff4757',
    'macd_negative': '#2ed573',

    # RSI
    'rsi_line': '#0984e3',
    'rsi_overbought': '#d63031',
    'rsi_oversold': '#00b894',
    'rsi_fill_alpha': 0.08,

    # KDJ
    'kdj_k': '#e17055',
    'kdj_d': '#0984e3',
    'kdj_j': '#d63031',

    # 信号标记
    'buy_signal': '#d63031',
    'sell_signal': '#00b894',
    'buy_marker': '^',
    'sell_marker': 'v',
    'signal_size': 120,

    # 资金曲线
    'equity_line': '#0984e3',
    'equity_fill': '#0984e3',
    'equity_alpha': 0.2,
    'benchmark_line': '#b2bec3',

    # 回撤
    'drawdown_color': '#d63031',
    'drawdown_alpha': 0.3,

    # 标注
    'annotation_bg': '#ffffff',
    'annotation_text': '#2d3436',
    'annotation_border': '#b2bec3',

    # 图例
    'legend_face': '#ffffff',
    'legend_edge': '#b2bec3',
    'legend_text': '#2d3436',
}

# 主题字典
THEMES = {
    'dark': DARK_THEME,
    'light': LIGHT_THEME,
}

def get_theme(name: str = 'dark') -> dict:
    """
    获取主题

    Args:
        name: 主题名称 ('dark', 'light')

    Returns:
        主题配置字典
    """
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}. Available: {list(THEMES.keys())}")
    return THEMES[name]
