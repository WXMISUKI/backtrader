#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的股票回测示例
双均线策略 + 风险控制 + 结果分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtrader as bt
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from datetime import datetime
from eastmoney_config import get_stock_hist


# ==================== 策略定义 ====================
class DualMovingAverageStrategy(bt.Strategy):
    """
    双均线交叉策略
    - 短期均线上穿长期均线：买入
    - 短期均线下穿长期均线：卖出
    - 包含止损和止盈机制
    """

    params = (
        ('fast_period', 5),      # 短期均线周期
        ('slow_period', 20),     # 长期均线周期
        ('stop_loss', 0.05),     # 止损比例 5%
        ('take_profit', 0.15),   # 止盈比例 15%
        ('printlog', True),      # 是否打印日志
    )

    def __init__(self):
        # 计算指标
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_period
        )

        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # RSI 指标（辅助判断）
        self.rsi = bt.indicators.RelativeStrengthIndex(self.data.close, period=14)

        # 记录买入价格
        self.buy_price = None
        self.buy_comm = None

    def log(self, txt, dt=None):
        """日志记录"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                self.log(f'买入: 价格={order.executed.price:.2f}, '
                        f'成本={order.executed.value:.2f}, '
                        f'手续费={order.executed.comm:.2f}')
            else:
                self.log(f'卖出: 价格={order.executed.price:.2f}, '
                        f'收入={order.executed.value:.2f}, '
                        f'手续费={order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

    def notify_trade(self, trade):
        """交易结果通知"""
        if not trade.isclosed:
            return
        self.log(f'交易利润: 毛利润={trade.pnl:.2f}, 净利润={trade.pnlcomm:.2f}')

    def next(self):
        """主策略逻辑"""

        # 持仓检查
        if not self.position:
            # 没有持仓，寻找买入信号
            if self.crossover > 0 and self.rsi < 70:  # 金叉且RSI不超买
                self.log(f'买入信号: 快线={self.fast_ma[0]:.2f}, '
                        f'慢线={self.slow_ma[0]:.2f}, RSI={self.rsi[0]:.2f}')
                # 使用 95% 的资金买入
                size = int(self.broker.getcash() * 0.95 / self.data.close[0])
                if size > 0:
                    self.buy(size=size)
        else:
            # 有持仓，检查卖出条件
            current_price = self.data.close[0]
            profit_pct = (current_price - self.buy_price) / self.buy_price

            # 条件1: 止损
            if profit_pct < -self.params.stop_loss:
                self.log(f'止损卖出: 亏损={profit_pct*100:.2f}%')
                self.close()

            # 条件2: 止盈
            elif profit_pct > self.params.take_profit:
                self.log(f'止盈卖出: 盈利={profit_pct*100:.2f}%')
                self.close()

            # 条件3: 死叉
            elif self.crossover < 0:
                self.log(f'死叉卖出: 快线={self.fast_ma[0]:.2f}, '
                        f'慢线={self.slow_ma[0]:.2f}')
                self.close()


# ==================== 回测引擎 ====================
class BacktestEngine:
    """回测引擎"""

    def __init__(self, initial_cash=100000):
        self.cerebro = bt.Cerebro()
        self.initial_cash = initial_cash

    def add_data(self, df, name="Stock"):
        """添加数据"""
        data = bt.feeds.PandasData(
            dataname=df,
            name=name
        )
        self.cerebro.adddata(data)

    def add_strategy(self, strategy_class, **kwargs):
        """添加策略"""
        self.cerebro.addstrategy(strategy_class, **kwargs)

    def set_broker(self, commission=0.001, slippage=0.001):
        """设置经纪商参数"""
        self.cerebro.broker.setcash(self.initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        self.cerebro.broker.set_slippage_perc(slippage)

    def add_analyzers(self):
        """添加分析器"""
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    def run(self):
        """运行回测"""
        print(f'初始资金: {self.initial_cash:,.2f}')
        print('=' * 60)

        results = self.cerebro.run()
        strat = results[0]

        print('=' * 60)
        final_value = self.cerebro.broker.getvalue()
        print(f'最终资金: {final_value:,.2f}')
        print(f'总收益率: {(final_value/self.initial_cash - 1)*100:.2f}%')

        return strat

    def plot(self, filename=None):
        """绘制图表"""
        if filename:
            self.cerebro.plot(style='candlestick', volume=True,
                            savefig=filename)
            print(f'图表已保存到: {filename}')
        else:
            self.cerebro.plot(style='candlestick', volume=True)


# ==================== 结果分析 ====================
def analyze_results(strat, initial_cash):
    """分析回测结果"""
    print('\n' + '=' * 60)
    print('回测结果分析')
    print('=' * 60)

    # 夏普比率
    sharpe = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe.get('sharperatio', 'N/A')
    print(f'夏普比率: {sharpe_ratio}')

    # 最大回撤
    drawdown = strat.analyzers.drawdown.get_analysis()
    print(f'最大回撤: {drawdown.max.drawdown:.2f}%')
    print(f'最大回撤持续时间: {drawdown.max.len} 天')

    # 交易统计
    trades = strat.analyzers.trades.get_analysis()
    total_trades = trades.total.total
    won_trades = trades.won.total if hasattr(trades, 'won') else 0
    lost_trades = trades.lost.total if hasattr(trades, 'lost') else 0

    print(f'\n交易统计:')
    print(f'  总交易次数: {total_trades}')
    print(f'  盈利次数: {won_trades}')
    print(f'  亏损次数: {lost_trades}')
    if total_trades > 0:
        print(f'  胜率: {won_trades/total_trades*100:.2f}%')

    # 收益分析
    returns = strat.analyzers.returns.get_analysis()
    print(f'\n收益分析:')
    print(f'  年化收益率: {returns.get("rnorm100", 0):.2f}%')

    return {
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': drawdown.max.drawdown,
        'total_trades': total_trades,
        'win_rate': won_trades/total_trades*100 if total_trades > 0 else 0,
        'annual_return': returns.get("rnorm100", 0)
    }


# ==================== 主程序 ====================
def main():
    """主函数"""

    # 配置参数
    STOCK_CODE = "000001"        # 平安银行
    START_DATE = "20250101"      # 回测开始日期
    END_DATE = "20260614"        # 回测结束日期
    INITIAL_CASH = 100000        # 初始资金

    # 策略参数
    FAST_PERIOD = 5              # 短期均线
    SLOW_PERIOD = 20             # 长期均线
    STOP_LOSS = 0.05             # 止损 5%
    TAKE_PROFIT = 0.15           # 止盈 15%

    print('=' * 60)
    print('股票回测系统')
    print('=' * 60)
    print(f'股票代码: {STOCK_CODE}')
    print(f'回测区间: {START_DATE} - {END_DATE}')
    print(f'初始资金: {INITIAL_CASH:,.2f}')
    print(f'策略参数: 快线={FAST_PERIOD}, 慢线={SLOW_PERIOD}')
    print(f'风险控制: 止损={STOP_LOSS*100}%, 止盈={TAKE_PROFIT*100}%')
    print('=' * 60)

    # 获取数据
    print('\n正在获取数据...')
    try:
        df = get_stock_hist(STOCK_CODE, START_DATE, END_DATE)
        print(f'获取到 {len(df)} 条数据')
        print(f'数据区间: {df.index[0]} 至 {df.index[-1]}')
    except Exception as e:
        print(f'获取数据失败: {e}')
        return

    # 创建回测引擎
    engine = BacktestEngine(initial_cash=INITIAL_CASH)

    # 添加数据
    engine.add_data(df, name=f"Stock_{STOCK_CODE}")

    # 添加策略
    engine.add_strategy(
        DualMovingAverageStrategy,
        fast_period=FAST_PERIOD,
        slow_period=SLOW_PERIOD,
        stop_loss=STOP_LOSS,
        take_profit=TAKE_PROFIT,
        printlog=True
    )

    # 设置经纪商
    engine.set_broker(commission=0.001, slippage=0.001)

    # 添加分析器
    engine.add_analyzers()

    # 运行回测
    strat = engine.run()

    # 分析结果
    results = analyze_results(strat, INITIAL_CASH)

    # 保存图表
    chart_file = os.path.join(os.path.dirname(__file__), 'backtest_result.png')
    engine.plot(filename=chart_file)

    # 生成报告
    print('\n' + '=' * 60)
    print('回测完成！')
    print('=' * 60)
    print(f'图表已保存到: {chart_file}')

    return results


if __name__ == '__main__':
    main()
