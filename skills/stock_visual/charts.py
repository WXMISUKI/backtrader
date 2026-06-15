"""
图表基类
"""

import matplotlib
matplotlib.use('Agg')  # 非交互式后端

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple
from .themes import get_theme


# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class StockChart:
    """
    股票图表基类
    提供通用的图表创建和保存功能
    """

    def __init__(self, theme: str = 'dark'):
        """
        初始化图表

        Args:
            theme: 主题名称 ('dark', 'light')
        """
        self.theme = get_theme(theme)
        self.fig: Optional[Figure] = None
        self.axes: Optional[List[Axes]] = None
        self._current_ax: Optional[Axes] = None

    def create_figure(self, nrows: int = 1, ncols: int = 1,
                      figsize: Tuple[int, int] = (14, 10),
                      height_ratios: Optional[List[float]] = None) -> 'StockChart':
        """
        创建图表

        Args:
            nrows: 行数
            ncols: 列数
            figsize: 图表大小
            height_ratios: 行高比例

        Returns:
            self
        """
        self.fig, axes = plt.subplots(
            nrows=nrows,
            ncols=ncols,
            figsize=figsize,
            gridspec_kw={'height_ratios': height_ratios} if height_ratios else None
        )

        # 设置图表样式
        self.fig.patch.set_facecolor(self.theme['figure_face'])

        # 处理 axes
        if nrows == 1 and ncols == 1:
            self.axes = [axes]
        elif nrows == 1 or ncols == 1:
            self.axes = list(axes) if hasattr(axes, '__len__') else [axes]
        else:
            self.axes = axes.flatten().tolist()

        self._current_ax = self.axes[0]

        # 设置每个 axes 的样式
        for ax in self.axes:
            ax.set_facecolor(self.theme['axes_face'])
            ax.tick_params(colors=self.theme['text'], labelsize=9)
            ax.grid(True, color=self.theme['grid'], alpha=0.5, linewidth=0.5)

            for spine in ax.spines.values():
                spine.set_color(self.theme['grid'])

        return self

    def get_ax(self, index: int = 0) -> Axes:
        """
        获取指定位置的 axes

        Args:
            index: axes 索引

        Returns:
            matplotlib Axes 对象
        """
        if self.axes is None:
            raise RuntimeError("Call create_figure first")
        return self.axes[index]

    def set_title(self, title: str, ax_index: int = 0):
        """设置标题"""
        ax = self.get_ax(ax_index)
        ax.set_title(title, color=self.theme['title'], fontsize=14, fontweight='bold')

    def set_xlabel(self, label: str, ax_index: int = 0):
        """设置 X 轴标签"""
        ax = self.get_ax(ax_index)
        ax.set_xlabel(label, color=self.theme['xlabel'], fontsize=10)

    def set_ylabel(self, label: str, ax_index: int = 0):
        """设置 Y 轴标签"""
        ax = self.get_ax(ax_index)
        ax.set_ylabel(label, color=self.theme['ylabel'], fontsize=10)

    def add_legend(self, ax_index: int = 0, loc: str = 'upper left'):
        """添加图例"""
        ax = self.get_ax(ax_index)
        legend = ax.legend(
            loc=loc,
            facecolor=self.theme['legend_face'],
            edgecolor=self.theme['legend_edge'],
            fontsize=9
        )
        for text in legend.get_texts():
            text.set_color(self.theme['legend_text'])

    def save(self, path: str, dpi: int = 150, bbox_inches: str = 'tight'):
        """
        保存图表

        Args:
            path: 保存路径
            dpi: 分辨率
            bbox_inches: 边界
        """
        if self.fig is None:
            raise RuntimeError("No figure to save")

        self.fig.savefig(path, dpi=dpi, bbox_inches=bbox_inches,
                        facecolor=self.fig.get_facecolor())
        plt.close(self.fig)

    def show(self):
        """显示图表"""
        if self.fig is None:
            raise RuntimeError("No figure to show")
        plt.show()

    def _format_xaxis(self, ax: Axes, dates: pd.DatetimeIndex):
        """格式化 X 轴日期"""
        if len(dates) > 60:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        elif len(dates) > 10:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def _format_volume(self, value: float, pos=None) -> str:
        """格式化成交量显示"""
        if value >= 1e8:
            return f'{value/1e8:.1f}亿'
        elif value >= 1e4:
            return f'{value/1e4:.1f}万'
        else:
            return f'{value:.0f}'
