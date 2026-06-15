"""
技术指标图模块
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List
from .charts import StockChart


class IndicatorChart(StockChart):
    """
    技术指标图
    支持 MACD、RSI、KDJ、成交量等指标
    """

    def __init__(self, theme: str = 'dark'):
        super().__init__(theme)

    def plot_macd(self, df: pd.DataFrame, ax_index: int = 0,
                  fast: int = 12, slow: int = 26, signal: int = 9) -> 'IndicatorChart':
        """
        绘制 MACD

        Args:
            df: DataFrame with columns [close]
            ax_index: axes 索引
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
        """
        ax = self.get_ax(ax_index)

        # 计算 MACD
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        macd = 2 * (dif - dea)

        # 绘制 DIF 和 DEA
        ax.plot(df.index, dif, label='DIF',
               color=self.theme['macd_dif'], linewidth=1)
        ax.plot(df.index, dea, label='DEA',
               color=self.theme['macd_dea'], linewidth=1)

        # 绘制 MACD 柱
        positive = macd[macd >= 0]
        negative = macd[macd < 0]

        ax.bar(positive.index, positive, color=self.theme['macd_positive'],
               alpha=0.7, width=0.8)
        ax.bar(negative.index, negative, color=self.theme['macd_negative'],
               alpha=0.7, width=0.8)

        # 零轴
        ax.axhline(y=0, color=self.theme['grid'], linewidth=0.5)

        ax.set_ylabel('MACD', color=self.theme['ylabel'], fontsize=10)
        self.add_legend(ax_index)

        return self

    def plot_rsi(self, df: pd.DataFrame, ax_index: int = 0,
                 period: int = 14) -> 'IndicatorChart':
        """
        绘制 RSI

        Args:
            df: DataFrame with columns [close]
            ax_index: axes 索引
            period: RSI 周期
        """
        ax = self.get_ax(ax_index)

        # 计算 RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 绘制 RSI
        ax.plot(df.index, rsi, label=f'RSI({period})',
               color=self.theme['rsi_line'], linewidth=1)

        # 超买超卖线
        ax.axhline(y=70, color=self.theme['rsi_overbought'],
                   linestyle='--', linewidth=0.8, label='超买(70)')
        ax.axhline(y=30, color=self.theme['rsi_oversold'],
                   linestyle='--', linewidth=0.8, label='超卖(30)')

        # 填充区域
        ax.fill_between(df.index, 70, 100,
                        color=self.theme['rsi_overbought'],
                        alpha=self.theme['rsi_fill_alpha'])
        ax.fill_between(df.index, 0, 30,
                        color=self.theme['rsi_oversold'],
                        alpha=self.theme['rsi_fill_alpha'])

        # 设置 Y 轴范围
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 30, 50, 70, 100])

        ax.set_ylabel('RSI', color=self.theme['ylabel'], fontsize=10)
        self.add_legend(ax_index)

        return self

    def plot_kdj(self, df: pd.DataFrame, ax_index: int = 0,
                 n: int = 9, m1: int = 3, m2: int = 3) -> 'IndicatorChart':
        """
        绘制 KDJ

        Args:
            df: DataFrame with columns [high, low, close]
            ax_index: axes 索引
            n: RSV 周期
            m1: K 平滑因子
            m2: D 平滑因子
        """
        ax = self.get_ax(ax_index)

        # 计算 KDJ
        low_n = df['low'].rolling(n).min()
        high_n = df['high'].rolling(n).max()
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100

        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d

        # 绘制 KDJ
        ax.plot(df.index, k, label='K', color=self.theme['kdj_k'], linewidth=1)
        ax.plot(df.index, d, label='D', color=self.theme['kdj_d'], linewidth=1)
        ax.plot(df.index, j, label='J', color=self.theme['kdj_j'], linewidth=1)

        # 超买超卖线
        ax.axhline(y=80, color=self.theme['rsi_overbought'],
                   linestyle='--', linewidth=0.5, alpha=0.5)
        ax.axhline(y=20, color=self.theme['rsi_oversold'],
                   linestyle='--', linewidth=0.5, alpha=0.5)

        ax.set_ylabel('KDJ', color=self.theme['ylabel'], fontsize=10)
        self.add_legend(ax_index)

        return self

    def plot_volume(self, df: pd.DataFrame, ax_index: int = 0) -> 'IndicatorChart':
        """
        绘制成交量

        Args:
            df: DataFrame with columns [open, close, volume]
            ax_index: axes 索引
        """
        ax = self.get_ax(ax_index)

        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]

        ax.bar(up.index, up['volume'], color=self.theme['volume_up'],
               alpha=self.theme['volume_alpha'], label='涨')
        ax.bar(down.index, down['volume'], color=self.theme['volume_down'],
               alpha=self.theme['volume_alpha'], label='跌')

        ax.yaxis.set_major_formatter(plt.FuncFormatter(self._format_volume))
        ax.set_ylabel('成交量', color=self.theme['ylabel'], fontsize=10)
        self.add_legend(ax_index)

        return self


def plot_indicators(df: pd.DataFrame, indicators: List[str] = None,
                    save_path: str = None, theme: str = 'dark') -> IndicatorChart:
    """
    快捷绘制技术指标

    Args:
        df: OHLCV 数据
        indicators: 指标列表 ['macd', 'rsi', 'kdj', 'volume']
        save_path: 保存路径
        theme: 主题

    Returns:
        IndicatorChart 实例
    """
    if indicators is None:
        indicators = ['macd', 'rsi', 'volume']

    nrows = len(indicators)
    chart = IndicatorChart(theme=theme)
    chart.create_figure(nrows=nrows, height_ratios=[1]*nrows, figsize=(14, 3*nrows))

    for i, indicator in enumerate(indicators):
        if indicator == 'macd':
            chart.plot_macd(df, ax_index=i)
        elif indicator == 'rsi':
            chart.plot_rsi(df, ax_index=i)
        elif indicator == 'kdj':
            chart.plot_kdj(df, ax_index=i)
        elif indicator == 'volume':
            chart.plot_volume(df, ax_index=i)

    if save_path:
        chart.save(save_path)

    return chart
