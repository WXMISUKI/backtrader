"""
K 线图模块
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
from typing import Optional, List, Dict, Any
from .charts import StockChart


class KLineChart(StockChart):
    """
    K 线图
    支持 K 线绘制、均线、布林带、成交量、信号标注
    """

    def __init__(self, theme: str = 'dark'):
        super().__init__(theme)
        self.df: Optional[pd.DataFrame] = None

    def plot(self, df: pd.DataFrame, title: str = 'K 线图',
             show_volume: bool = True) -> 'KLineChart':
        """
        绘制 K 线图

        Args:
            df: DataFrame with columns [date, open, high, low, close, volume]
            title: 图表标题
            show_volume: 是否显示成交量

        Returns:
            self
        """
        self.df = df.copy()

        # 确保有 date 列或 index
        if 'date' in df.columns:
            df = df.set_index('date')

        # 创建图表
        if show_volume:
            self.create_figure(nrows=2, height_ratios=[3, 1], figsize=(14, 10))
            ax_price = self.get_ax(0)
            ax_volume = self.get_ax(1)
        else:
            self.create_figure(nrows=1, figsize=(14, 8))
            ax_price = self.get_ax(0)
            ax_volume = None

        # 绘制 K 线
        self._draw_candlesticks(ax_price, df)

        # 绘制成交量
        if show_volume and ax_volume is not None:
            self._draw_volume(ax_volume, df)
            ax_volume.set_ylabel('成交量', color=self.theme['ylabel'], fontsize=10)

        # 设置标题
        self.set_title(title)

        # 设置 X 轴
        self._format_xaxis(ax_price, df.index)
        if ax_volume is not None:
            ax_volume.set_xlim(ax_price.get_xlim())

        return self

    def _draw_candlesticks(self, ax: plt.Axes, df: pd.DataFrame):
        """绘制 K 线"""
        width = 0.6
        width2 = 0.05

        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]

        # 涨的 K 线
        ax.bar(up.index, up['close'] - up['open'], width,
               bottom=up['open'], color=self.theme['up_color'],
               edgecolor=self.theme['up_edge'], linewidth=0.5)
        ax.bar(up.index, up['high'] - up['close'], width2,
               bottom=up['close'], color=self.theme['up_color'])
        ax.bar(up.index, up['low'] - up['open'], width2,
               bottom=up['open'], color=self.theme['up_color'])

        # 跌的 K 线
        ax.bar(down.index, down['close'] - down['open'], width,
               bottom=down['open'], color=self.theme['down_color'],
               edgecolor=self.theme['down_edge'], linewidth=0.5)
        ax.bar(down.index, down['high'] - down['open'], width2,
               bottom=down['open'], color=self.theme['down_color'])
        ax.bar(down.index, down['low'] - down['close'], width2,
               bottom=down['close'], color=self.theme['down_color'])

        # 设置 Y 轴标签
        ax.set_ylabel('价格', color=self.theme['ylabel'], fontsize=10)

    def _draw_volume(self, ax: plt.Axes, df: pd.DataFrame):
        """绘制成交量"""
        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]

        ax.bar(up.index, up['volume'], color=self.theme['volume_up'],
               alpha=self.theme['volume_alpha'])
        ax.bar(down.index, down['volume'], color=self.theme['volume_down'],
               alpha=self.theme['volume_alpha'])

        # 格式化成交量
        ax.yaxis.set_major_formatter(plt.FuncFormatter(self._format_volume))

    def add_ma(self, periods: List[int] = [5, 10, 20, 60],
               ax_index: int = 0) -> 'KLineChart':
        """
        添加均线

        Args:
            periods: 均线周期列表
            ax_index: axes 索引

        Returns:
            self
        """
        if self.df is None:
            raise RuntimeError("Call plot() first")

        ax = self.get_ax(ax_index)
        df = self.df

        if 'date' in df.columns:
            df = df.set_index('date')

        for i, period in enumerate(periods):
            ma = df['close'].rolling(period).mean()
            color = self.theme['ma_colors'][i % len(self.theme['ma_colors'])]
            ax.plot(ma.index, ma, label=f'MA{period}',
                   color=color, linewidth=1, alpha=0.8)

        self.add_legend(ax_index)
        return self

    def add_boll(self, period: int = 20, std_dev: int = 2,
                 ax_index: int = 0) -> 'KLineChart':
        """
        添加布林带

        Args:
            period: 均线周期
            std_dev: 标准差倍数
            ax_index: axes 索引

        Returns:
            self
        """
        if self.df is None:
            raise RuntimeError("Call plot() first")

        ax = self.get_ax(ax_index)
        df = self.df

        if 'date' in df.columns:
            df = df.set_index('date')

        ma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()

        upper = ma + std_dev * std
        lower = ma - std_dev * std

        ax.plot(ma.index, ma, label='BOLL中轨',
               color=self.theme['boll_mid'], linewidth=1)
        ax.plot(upper.index, upper, label='BOLL上轨',
               color=self.theme['boll_mid'], linewidth=0.8, linestyle='--')
        ax.plot(lower.index, lower, label='BOLL下轨',
               color=self.theme['boll_mid'], linewidth=0.8, linestyle='--')
        ax.fill_between(ma.index, upper, lower,
                        color=self.theme['boll_fill'],
                        alpha=self.theme['boll_alpha'])

        self.add_legend(ax_index)
        return self

    def add_signals(self, signals: pd.DataFrame,
                    ax_index: int = 0) -> 'KLineChart':
        """
        添加买卖信号

        Args:
            signals: DataFrame with columns [date, type, price]
                    type: 'BUY' or 'SELL'
            ax_index: axes 索引

        Returns:
            self
        """
        if self.df is None:
            raise RuntimeError("Call plot() first")

        ax = self.get_ax(ax_index)

        buy_signals = signals[signals['type'] == 'BUY']
        sell_signals = signals[signals['type'] == 'SELL']

        if len(buy_signals) > 0:
            ax.scatter(buy_signals['date'], buy_signals['price'],
                      marker=self.theme['buy_marker'],
                      color=self.theme['buy_signal'],
                      s=self.theme['signal_size'],
                      label='买入信号', zorder=5)

        if len(sell_signals) > 0:
            ax.scatter(sell_signals['date'], sell_signals['price'],
                      marker=self.theme['sell_marker'],
                      color=self.theme['sell_signal'],
                      s=self.theme['signal_size'],
                      label='卖出信号', zorder=5)

        self.add_legend(ax_index)
        return self

    def add_price_annotations(self, ax_index: int = 0) -> 'KLineChart':
        """
        添加价格标注 (最新价、最高、最低)

        Args:
            ax_index: axes 索引

        Returns:
            self
        """
        if self.df is None:
            raise RuntimeError("Call plot() first")

        ax = self.get_ax(ax_index)
        df = self.df

        if 'date' in df.columns:
            df = df.set_index('date')

        latest = df['close'].iloc[-1]
        highest = df['high'].max()
        lowest = df['low'].min()

        # 最新价
        ax.axhline(y=latest, color=self.theme['text'],
                   linestyle='--', linewidth=0.5, alpha=0.5)
        ax.annotate(f'最新: {latest:.2f}',
                   xy=(df.index[-1], latest),
                   xytext=(10, 0), textcoords='offset points',
                   color=self.theme['annotation_text'],
                   fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3',
                            facecolor=self.theme['annotation_bg'],
                            edgecolor=self.theme['annotation_border']))

        return self


def plot_kline(df: pd.DataFrame, title: str = 'K 线图',
               ma_periods: List[int] = None,
               show_boll: bool = False,
               signals: pd.DataFrame = None,
               save_path: str = None,
               theme: str = 'dark') -> KLineChart:
    """
    快捷绘制 K 线图

    Args:
        df: OHLCV 数据
        title: 标题
        ma_periods: 均线周期列表
        show_boll: 是否显示布林带
        signals: 信号数据
        save_path: 保存路径
        theme: 主题

    Returns:
        KLineChart 实例
    """
    chart = KLineChart(theme=theme)
    chart.plot(df, title=title)

    if ma_periods:
        chart.add_ma(ma_periods)

    if show_boll:
        chart.add_boll()

    if signals is not None:
        chart.add_signals(signals)

    if save_path:
        chart.save(save_path)

    return chart
