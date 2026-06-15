"""
回测结果图模块
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Any
from .charts import StockChart


class BacktestChart(StockChart):
    """
    回测结果图
    支持资金曲线、回撤、月度收益、交易分布
    """

    def __init__(self, theme: str = 'dark'):
        super().__init__(theme)

    def plot_equity_curve(self, equity: pd.Series,
                          benchmark: pd.Series = None,
                          ax_index: int = 0) -> 'BacktestChart':
        """
        绘制资金曲线

        Args:
            equity: 策略资金序列
            benchmark: 基准资金序列 (可选)
            ax_index: axes 索引
        """
        ax = self.get_ax(ax_index)

        # 绘制策略资金曲线
        ax.plot(equity.index, equity, label='策略',
               color=self.theme['equity_line'], linewidth=1.5)
        ax.fill_between(equity.index, equity,
                        color=self.theme['equity_fill'],
                        alpha=self.theme['equity_alpha'])

        # 绘制基准
        if benchmark is not None:
            ax.plot(benchmark.index, benchmark, label='基准',
                   color=self.theme['benchmark_line'], linewidth=1, linestyle='--')

        # 标注起始和结束资金
        start_equity = equity.iloc[0]
        end_equity = equity.iloc[-1]
        returns = (end_equity / start_equity - 1) * 100

        ax.annotate(f'起始: {start_equity:,.0f}',
                   xy=(equity.index[0], start_equity),
                   xytext=(10, 10), textcoords='offset points',
                   color=self.theme['annotation_text'], fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3',
                            facecolor=self.theme['annotation_bg'],
                            edgecolor=self.theme['annotation_border']))

        ax.annotate(f'结束: {end_equity:,.0f} ({returns:+.1f}%)',
                   xy=(equity.index[-1], end_equity),
                   xytext=(-100, 10), textcoords='offset points',
                   color=self.theme['annotation_text'], fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3',
                            facecolor=self.theme['annotation_bg'],
                            edgecolor=self.theme['annotation_border']))

        ax.set_ylabel('资金', color=self.theme['ylabel'], fontsize=10)
        self.add_legend(ax_index)

        return self

    def plot_drawdown(self, equity: pd.Series,
                      ax_index: int = 0) -> 'BacktestChart':
        """
        绘制回撤曲线

        Args:
            equity: 资金序列
            ax_index: axes 索引
        """
        ax = self.get_ax(ax_index)

        # 计算回撤
        cummax = equity.cummax()
        drawdown = (equity / cummax - 1) * 100

        # 绘制回撤
        ax.fill_between(drawdown.index, drawdown, 0,
                        color=self.theme['drawdown_color'],
                        alpha=self.theme['drawdown_alpha'],
                        label='回撤')

        # 标注最大回撤
        max_drawdown = drawdown.min()
        max_drawdown_idx = drawdown.idxmin()

        ax.annotate(f'最大回撤: {max_drawdown:.1f}%',
                   xy=(max_drawdown_idx, max_drawdown),
                   xytext=(10, -20), textcoords='offset points',
                   color=self.theme['annotation_text'], fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3',
                            facecolor=self.theme['annotation_bg'],
                            edgecolor=self.theme['annotation_border']))

        ax.set_ylabel('回撤 (%)', color=self.theme['ylabel'], fontsize=10)
        self.add_legend(ax_index)

        return self

    def plot_monthly_returns(self, returns: pd.Series,
                             ax_index: int = 0) -> 'BacktestChart':
        """
        绘制月度收益热力图

        Args:
            returns: 日收益率序列 (index 为日期)
            ax_index: axes 索引
        """
        ax = self.get_ax(ax_index)

        # 转换为月度收益
        monthly = returns.resample('M').apply(lambda x: (1 + x).prod() - 1) * 100

        # 创建年-月矩阵
        monthly_df = pd.DataFrame({
            'year': monthly.index.year,
            'month': monthly.index.month,
            'return': monthly.values
        })

        pivot = monthly_df.pivot_table(values='return', index='year',
                                        columns='month', aggfunc='sum')

        # 绘制热力图
        im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto',
                       vmin=-10, vmax=10)

        # 设置刻度
        ax.set_xticks(range(12))
        ax.set_xticklabels(['1月', '2月', '3月', '4月', '5月', '6月',
                            '7月', '8月', '9月', '10月', '11月', '12月'],
                           color=self.theme['text'], fontsize=8)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, color=self.theme['text'], fontsize=9)

        # 添加数值
        for i in range(len(pivot.index)):
            for j in range(12):
                if not np.isnan(pivot.values[i, j]):
                    color = 'white' if abs(pivot.values[i, j]) > 5 else self.theme['text']
                    ax.text(j, i, f'{pivot.values[i, j]:.1f}%',
                           ha='center', va='center', color=color, fontsize=8)

        ax.set_title('月度收益 (%)', color=self.theme['title'], fontsize=12)

        return self

    def plot_trade_distribution(self, trades: List[Dict[str, Any]],
                                ax_index: int = 0) -> 'BacktestChart':
        """
        绘制交易分布

        Args:
            trades: 交易记录列表
            ax_index: axes 索引
        """
        ax = self.get_ax(ax_index)

        # 计算每笔交易收益
        returns = []
        for trade in trades:
            if 'entry_price' in trade and 'exit_price' in trade:
                ret = (trade['exit_price'] / trade['entry_price'] - 1) * 100
                returns.append(ret)

        if not returns:
            return self

        # 绘制直方图
        ax.hist(returns, bins=30, color=self.theme['equity_line'],
                alpha=0.7, edgecolor=self.theme['equity_fill'])

        # 标注统计信息
        avg_return = np.mean(returns)
        win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100

        ax.axvline(x=avg_return, color=self.theme['buy_signal'],
                   linestyle='--', linewidth=1, label=f'平均: {avg_return:.1f}%')

        ax.set_xlabel('收益率 (%)', color=self.theme['xlabel'], fontsize=10)
        ax.set_ylabel('交易次数', color=self.theme['ylabel'], fontsize=10)
        ax.set_title(f'交易分布 (胜率: {win_rate:.0f}%)',
                     color=self.theme['title'], fontsize=12)
        self.add_legend(ax_index)

        return self

    def plot_summary(self, equity: pd.Series,
                     returns: pd.Series = None,
                     trades: List[Dict] = None,
                     save_path: str = None) -> 'BacktestChart':
        """
        绘制回测总结图

        Args:
            equity: 资金序列
            returns: 收益率序列
            trades: 交易记录
            save_path: 保存路径
        """
        nrows = 2
        if trades:
            nrows = 3

        self.create_figure(nrows=nrows, height_ratios=[2, 1, 1][:nrows],
                          figsize=(14, 4*nrows))

        # 资金曲线
        self.plot_equity_curve(equity, ax_index=0)
        self.set_title('回测结果')

        # 回撤
        self.plot_drawdown(equity, ax_index=1)

        # 交易分布
        if trades and nrows > 2:
            self.plot_trade_distribution(trades, ax_index=2)

        plt.tight_layout()

        if save_path:
            self.save(save_path)

        return self


def plot_backtest(equity: pd.Series, returns: pd.Series = None,
                  trades: List[Dict] = None,
                  save_path: str = None, theme: str = 'dark') -> BacktestChart:
    """
    快捷绘制回测结果

    Args:
        equity: 资金序列
        returns: 收益率序列
        trades: 交易记录
        save_path: 保存路径
        theme: 主题

    Returns:
        BacktestChart 实例
    """
    chart = BacktestChart(theme=theme)
    chart.plot_summary(equity, returns, trades, save_path)
    return chart
