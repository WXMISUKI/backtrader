#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版回测示例 - 快速验证策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtrader as bt
from eastmoney_config import get_stock_hist


# 简单双均线策略
class SimpleMAStrategy(bt.Strategy):
    params = (
        ('fast', 5),
        ('slow', 20),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.p.fast)
        self.slow_ma = bt.indicators.SMA(period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                size = int(self.broker.getcash() * 0.95 / self.data.close[0])
                if size > 0:
                    self.buy(size=size)
        else:
            if self.crossover < 0:
                self.close()


print("=" * 50)
print("股票回测 - 双均线策略")
print("=" * 50)

# 获取数据
print("获取平安银行(000001)数据...")
df = get_stock_hist("000001", "20250101", "20260614")
print(f"获取到 {len(df)} 条数据")

# 创建引擎
cerebro = bt.Cerebro()

# 添加数据
data = bt.feeds.PandasData(dataname=df, name="平安银行")
cerebro.adddata(data)

# 设置资金
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.001)

# 添加策略
cerebro.addstrategy(SimpleMAStrategy, fast=5, slow=20)

# 添加分析器
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

# 运行回测
print("\n运行回测...")
print(f"初始资金: {cerebro.broker.getvalue():,.2f}")

results = cerebro.run()
strat = results[0]

final_value = cerebro.broker.getvalue()
print(f"最终资金: {final_value:,.2f}")
print(f"总收益率: {(final_value/100000 - 1)*100:.2f}%")

# 输出分析结果
print("\n" + "=" * 50)
print("回测统计")
print("=" * 50)

sharpe = strat.analyzers.sharpe.get_analysis()
print(f"夏普比率: {sharpe.get('sharperatio', 'N/A')}")

drawdown = strat.analyzers.drawdown.get_analysis()
print(f"最大回撤: {drawdown.max.drawdown:.2f}%")

trades = strat.analyzers.trades.get_analysis()
total = trades.total.total
won = trades.won.total if hasattr(trades, 'won') else 0
print(f"交易次数: {total}")
print(f"盈利次数: {won}")
if total > 0:
    print(f"胜率: {won/total*100:.1f}%")

print("\n回测完成！")
