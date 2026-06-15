"""
仪表盘模块
综合展示股票分析、回测结果、推荐列表
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Any
from .charts import StockChart
from .kline import KLineChart
from .indicators import IndicatorChart
from .backtest import BacktestChart


class Dashboard(StockChart):
    """
    综合仪表盘
    将多个图表组合到一个页面
    """

    def __init__(self, theme: str = 'dark'):
        super().__init__(theme)
        self.charts = []

    def create_stock_dashboard(self, df: pd.DataFrame,
                                indicators: Dict[str, Any] = None,
                                signals: pd.DataFrame = None,
                                analysis: Dict[str, Any] = None,
                                title: str = '股票分析仪表盘') -> 'Dashboard':
        """
        创建股票分析仪表盘

        Args:
            df: OHLCV 数据
            indicators: 指标数据
            signals: 信号数据
            analysis: 分析结果
            title: 标题
        """
        # 创建图表: K线 + 成交量 + MACD + RSI + 信息面板
        self.create_figure(nrows=4, ncols=2,
                          figsize=(16, 14),
                          height_ratios=[3, 1, 1, 1.2])

        # K 线图 (左上)
        ax_kline = self.get_ax(0)
        self._plot_kline_panel(ax_kline, df, signals)

        # 成交量 (左中1)
        ax_vol = self.get_ax(2)
        self._plot_volume_panel(ax_vol, df)

        # MACD (左中2)
        ax_macd = self.get_ax(4)
        self._plot_macd_panel(ax_macd, df)

        # RSI (左下)
        ax_rsi = self.get_ax(6)
        self._plot_rsi_panel(ax_rsi, df)

        # 信息面板 (右列，合并)
        ax_info = self.fig.add_subplot(1, 2, 2)
        self._plot_info_panel(ax_info, df, indicators, analysis)

        # 设置标题
        self.fig.suptitle(title, color=self.theme['title'],
                         fontsize=16, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        return self

    def _plot_kline_panel(self, ax: plt.Axes, df: pd.DataFrame,
                          signals: pd.DataFrame = None):
        """绘制 K 线面板"""
        # K 线
        width = 0.6
        width2 = 0.05

        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]

        ax.bar(up.index, up['close'] - up['open'], width,
               bottom=up['open'], color=self.theme['up_color'],
               edgecolor=self.theme['up_edge'], linewidth=0.5)
        ax.bar(up.index, up['high'] - up['close'], width2,
               bottom=up['close'], color=self.theme['up_color'])
        ax.bar(up.index, up['low'] - up['open'], width2,
               bottom=up['open'], color=self.theme['up_color'])

        ax.bar(down.index, down['close'] - down['open'], width,
               bottom=down['open'], color=self.theme['down_color'],
               edgecolor=self.theme['down_edge'], linewidth=0.5)
        ax.bar(down.index, down['high'] - down['open'], width2,
               bottom=down['open'], color=self.theme['down_color'])
        ax.bar(down.index, down['low'] - down['close'], width2,
               bottom=down['close'], color=self.theme['down_color'])

        # 均线
        for i, period in enumerate([5, 10, 20]):
            ma = df['close'].rolling(period).mean()
            color = self.theme['ma_colors'][i]
            ax.plot(ma.index, ma, color=color, linewidth=0.8, alpha=0.7)

        # 信号
        if signals is not None:
            buy = signals[signals['type'] == 'BUY']
            sell = signals[signals['type'] == 'SELL']
            if len(buy) > 0:
                ax.scatter(buy['date'], buy['price'],
                          marker='^', color=self.theme['buy_signal'],
                          s=100, zorder=5)
            if len(sell) > 0:
                ax.scatter(sell['date'], sell['price'],
                          marker='v', color=self.theme['sell_signal'],
                          s=100, zorder=5)

        ax.set_title('K 线图', color=self.theme['title'], fontsize=12)
        ax.set_ylabel('价格', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_volume_panel(self, ax: plt.Axes, df: pd.DataFrame):
        """绘制成交量面板"""
        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]

        ax.bar(up.index, up['volume'], color=self.theme['volume_up'],
               alpha=self.theme['volume_alpha'])
        ax.bar(down.index, down['volume'], color=self.theme['volume_down'],
               alpha=self.theme['volume_alpha'])

        ax.yaxis.set_major_formatter(plt.FuncFormatter(self._format_volume))
        ax.set_ylabel('成交量', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_macd_panel(self, ax: plt.Axes, df: pd.DataFrame):
        """绘制 MACD 面板"""
        ema_fast = df['close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=9, adjust=False).mean()
        macd = 2 * (dif - dea)

        ax.plot(df.index, dif, color=self.theme['macd_dif'], linewidth=0.8)
        ax.plot(df.index, dea, color=self.theme['macd_dea'], linewidth=0.8)

        positive = macd[macd >= 0]
        negative = macd[macd < 0]
        ax.bar(positive.index, positive, color=self.theme['macd_positive'],
               alpha=0.7, width=0.8)
        ax.bar(negative.index, negative, color=self.theme['macd_negative'],
               alpha=0.7, width=0.8)

        ax.axhline(y=0, color=self.theme['grid'], linewidth=0.5)
        ax.set_ylabel('MACD', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_rsi_panel(self, ax: plt.Axes, df: pd.DataFrame):
        """绘制 RSI 面板"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        ax.plot(df.index, rsi, color=self.theme['rsi_line'], linewidth=0.8)
        ax.axhline(y=70, color=self.theme['rsi_overbought'],
                   linestyle='--', linewidth=0.5)
        ax.axhline(y=30, color=self.theme['rsi_oversold'],
                   linestyle='--', linewidth=0.5)
        ax.fill_between(df.index, 70, 100,
                        color=self.theme['rsi_overbought'], alpha=0.1)
        ax.fill_between(df.index, 0, 30,
                        color=self.theme['rsi_oversold'], alpha=0.1)

        ax.set_ylim(0, 100)
        ax.set_ylabel('RSI', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_info_panel(self, ax: plt.Axes, df: pd.DataFrame,
                         indicators: Dict = None, analysis: Dict = None):
        """绘制信息面板"""
        ax.set_facecolor(self.theme['axes_face'])
        ax.axis('off')

        # 基本信息
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        change = (latest['close'] / prev['close'] - 1) * 100

        info_text = [
            f"{'='*40}",
            f"  最新价格: {latest['close']:.2f}",
            f"  涨跌幅: {change:+.2f}%",
            f"  开盘: {latest['open']:.2f}",
            f"  最高: {latest['high']:.2f}",
            f"  最低: {latest['low']:.2f}",
            f"  成交量: {latest['volume']:,.0f}",
            f"{'='*40}",
        ]

        # 均线信息
        ma5 = df['close'].rolling(5).mean().iloc[-1]
        ma10 = df['close'].rolling(10).mean().iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]

        info_text.extend([
            f"  MA5:  {ma5:.2f}",
            f"  MA10: {ma10:.2f}",
            f"  MA20: {ma20:.2f}",
            f"{'='*40}",
        ])

        # 技术指标
        ema_fast = df['close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema_fast.iloc[-1] - ema_slow.iloc[-1]
        dea = (ema_fast - ema_slow).ewm(span=9, adjust=False).mean().iloc[-1]

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        info_text.extend([
            f"  MACD DIF: {dif:.3f}",
            f"  MACD DEA: {dea:.3f}",
            f"  RSI(14):  {rsi:.1f}",
            f"{'='*40}",
        ])

        # 分析结果
        if analysis:
            info_text.extend([
                f"  综合评分: {analysis.get('score', 'N/A')}",
                f"  投资建议: {analysis.get('recommendation', 'N/A')}",
                f"  风险等级: {analysis.get('risk_level', 'N/A')}",
                f"{'='*40}",
            ])

        # 绘制文本
        y_pos = 0.95
        for line in info_text:
            ax.text(0.05, y_pos, line, transform=ax.transAxes,
                   color=self.theme['text'], fontsize=10,
                   fontfamily='monospace', verticalalignment='top')
            y_pos -= 0.05

        ax.set_title('分析信息', color=self.theme['title'], fontsize=12)

    def create_backtest_dashboard(self, equity: pd.Series,
                                   returns: pd.Series = None,
                                   trades: List[Dict] = None,
                                   metrics: Dict = None,
                                   title: str = '回测结果仪表盘') -> 'Dashboard':
        """
        创建回测结果仪表盘

        Args:
            equity: 资金序列
            returns: 收益率序列
            trades: 交易记录
            metrics: 回测指标
            title: 标题
        """
        self.create_figure(nrows=3, ncols=2,
                          figsize=(16, 12),
                          height_ratios=[2, 1, 1])

        # 资金曲线 (左上)
        ax_equity = self.get_ax(0)
        self._plot_equity_panel(ax_equity, equity)

        # 回撤 (左中)
        ax_drawdown = self.get_ax(2)
        self._plot_drawdown_panel(ax_drawdown, equity)

        # 交易分布 (左下)
        ax_trades = self.get_ax(4)
        if trades:
            self._plot_trades_panel(ax_trades, trades)

        # 指标面板 (右列)
        ax_metrics = self.fig.add_subplot(1, 2, 2)
        self._plot_metrics_panel(ax_metrics, equity, returns, trades, metrics)

        self.fig.suptitle(title, color=self.theme['title'],
                         fontsize=16, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        return self

    def _plot_equity_panel(self, ax: plt.Axes, equity: pd.Series):
        """绘制资金曲线面板"""
        ax.plot(equity.index, equity, color=self.theme['equity_line'], linewidth=1.5)
        ax.fill_between(equity.index, equity,
                        color=self.theme['equity_fill'],
                        alpha=self.theme['equity_alpha'])
        ax.set_title('资金曲线', color=self.theme['title'], fontsize=12)
        ax.set_ylabel('资金', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_drawdown_panel(self, ax: plt.Axes, equity: pd.Series):
        """绘制回撤面板"""
        cummax = equity.cummax()
        drawdown = (equity / cummax - 1) * 100

        ax.fill_between(drawdown.index, drawdown, 0,
                        color=self.theme['drawdown_color'],
                        alpha=self.theme['drawdown_alpha'])
        ax.set_title('回撤', color=self.theme['title'], fontsize=12)
        ax.set_ylabel('回撤 (%)', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_trades_panel(self, ax: plt.Axes, trades: List[Dict]):
        """绘制交易分布面板"""
        returns = []
        for trade in trades:
            if 'entry_price' in trade and 'exit_price' in trade:
                ret = (trade['exit_price'] / trade['entry_price'] - 1) * 100
                returns.append(ret)

        if returns:
            ax.hist(returns, bins=20, color=self.theme['equity_line'],
                    alpha=0.7, edgecolor=self.theme['equity_fill'])
            ax.axvline(x=np.mean(returns), color=self.theme['buy_signal'],
                       linestyle='--', linewidth=1)

        ax.set_title('交易收益分布', color=self.theme['title'], fontsize=12)
        ax.set_xlabel('收益率 (%)', color=self.theme['xlabel'], fontsize=10)
        ax.set_ylabel('次数', color=self.theme['ylabel'], fontsize=10)
        ax.grid(True, color=self.theme['grid'], alpha=0.3)

    def _plot_metrics_panel(self, ax: plt.Axes, equity: pd.Series,
                            returns: pd.Series = None,
                            trades: List[Dict] = None,
                            metrics: Dict = None):
        """绘制指标面板"""
        ax.set_facecolor(self.theme['axes_face'])
        ax.axis('off')

        # 计算指标
        total_return = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
        trading_days = len(equity)
        annual_return = ((1 + total_return/100) ** (252/trading_days) - 1) * 100

        cummax = equity.cummax()
        drawdown = (equity / cummax - 1)
        max_drawdown = drawdown.min() * 100

        # 胜率
        win_rate = 0
        if trades:
            wins = sum(1 for t in trades
                      if 'entry_price' in t and 'exit_price' in t
                      and t['exit_price'] > t['entry_price'])
            win_rate = wins / len(trades) * 100

        info_text = [
            f"{'='*35}",
            f"  回测指标",
            f"{'='*35}",
            f"  总收益率: {total_return:+.2f}%",
            f"  年化收益: {annual_return:+.2f}%",
            f"  最大回撤: {max_drawdown:.2f}%",
            f"  交易天数: {trading_days}",
            f"  交易次数: {len(trades) if trades else 0}",
            f"  胜率: {win_rate:.0f}%",
            f"{'='*35}",
        ]

        # 添加自定义指标
        if metrics:
            info_text.append(f"  自定义指标:")
            for key, value in metrics.items():
                info_text.append(f"    {key}: {value}")
            info_text.append(f"{'='*35}")

        y_pos = 0.95
        for line in info_text:
            ax.text(0.1, y_pos, line, transform=ax.transAxes,
                   color=self.theme['text'], fontsize=11,
                   fontfamily='monospace', verticalalignment='top')
            y_pos -= 0.06

    def create_recommendation_dashboard(self, recommendations: List[Dict],
                                         title: str = '股票推荐') -> 'Dashboard':
        """
        创建推荐结果仪表盘

        Args:
            recommendations: 推荐列表
            title: 标题
        """
        self.create_figure(nrows=1, figsize=(14, 8))
        ax = self.get_ax(0)

        ax.set_facecolor(self.theme['axes_face'])
        ax.axis('off')

        # 表头
        headers = ['股票代码', '股票名称', '当前价', '涨跌幅', '评分', '建议']
        col_widths = [0.15, 0.15, 0.12, 0.12, 0.12, 0.12]

        y_start = 0.9
        row_height = 0.06

        # 绘制表头
        x_pos = 0.05
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            ax.text(x_pos, y_start, header, transform=ax.transAxes,
                   color=self.theme['title'], fontsize=11, fontweight='bold')
            x_pos += width

        # 绘制数据
        for row_idx, rec in enumerate(recommendations):
            y_pos = y_start - (row_idx + 1) * row_height
            x_pos = 0.05

            row_data = [
                rec.get('code', ''),
                rec.get('name', ''),
                f"{rec.get('price', 0):.2f}",
                f"{rec.get('change', 0):+.2f}%",
                f"{rec.get('score', 0):.1f}",
                rec.get('recommendation', ''),
            ]

            for i, (data, width) in enumerate(zip(row_data, col_widths)):
                # 涨跌幅颜色
                if i == 3:
                    color = self.theme['up_color'] if '+' in data else self.theme['down_color']
                elif i == 5:
                    color = self.theme['buy_signal'] if '买' in data else self.theme['sell_signal']
                else:
                    color = self.theme['text']

                ax.text(x_pos, y_pos, data, transform=ax.transAxes,
                       color=color, fontsize=10)
                x_pos += width

            # 分隔线
            ax.axhline(y=y_pos - row_height/2, xmin=0.05, xmax=0.95,
                       color=self.theme['grid'], linewidth=0.5, alpha=0.3)

        ax.set_title(title, color=self.theme['title'],
                     fontsize=14, fontweight='bold', pad=20)

        return self

    def save(self, path: str, dpi: int = 150):
        """保存仪表盘"""
        if self.fig is None:
            raise RuntimeError("No figure to save")
        self.fig.savefig(path, dpi=dpi, bbox_inches='tight',
                        facecolor=self.fig.get_facecolor())
        plt.close(self.fig)


def create_stock_dashboard(df: pd.DataFrame, **kwargs) -> Dashboard:
    """创建股票分析仪表盘"""
    theme = kwargs.pop('theme', 'dark')
    dashboard = Dashboard(theme=theme)
    dashboard.create_stock_dashboard(df, **kwargs)
    return dashboard


def create_backtest_dashboard(equity: pd.Series, **kwargs) -> Dashboard:
    """创建回测结果仪表盘"""
    theme = kwargs.pop('theme', 'dark')
    dashboard = Dashboard(theme=theme)
    dashboard.create_backtest_dashboard(equity, **kwargs)
    return dashboard
