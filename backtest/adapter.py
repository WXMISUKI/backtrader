#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测适配器

将自定义的 StockData 和 Strategy 适配为 backtrader 格式
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

from skills.stock_advisor import StockData
from strategies import StrategyRegistry, Bar, Signal, SignalType


class StockDataFeed(bt.feeds.PandasData):
    """
    股票数据适配器

    将 StockData 适配为 backtrader 数据源

    示例:
        >>> stock_data = StockData("000001", "平安银行", df)
        >>> data_feed = StockDataFeed.from_stock_data(stock_data)
        >>> cerebro.adddata(data_feed)
    """

    # 定义列映射
    params = (
        ('datetime', None),  # 使用索引作为日期
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),  # 不使用持仓量
    )

    @classmethod
    def from_stock_data(cls, stock_data: StockData) -> 'StockDataFeed':
        """
        从 StockData 创建 backtrader 数据源

        参数:
            stock_data: StockData 对象

        返回:
            StockDataFeed 对象
        """
        return cls(dataname=stock_data.df)


class StrategyAdapter(bt.Strategy):
    """
    策略适配器

    将自定义 Strategy 适配为 backtrader 策略

    示例:
        >>> cerebro.addstrategy(
        ...     StrategyAdapter,
        ...     strategy_name='ma_cross',
        ...     config={'fast_period': 5, 'slow_period': 20}
        ... )
    """

    params = (
        ('strategy_name', 'ma_cross'),
        ('config', {}),
    )

    def __init__(self):
        """初始化"""
        # 创建自定义策略实例
        self.custom_strategy = StrategyRegistry.create(
            self.params.strategy_name,
            self.params.config
        )

        # 获取数据列
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        # 记录交易
        self.order = None
        self.buy_price = None
        self.buy_comm = None

    def log(self, txt, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        # print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """订单通知"""
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

        self.order = None

    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        self.log(f'交易利润: 毛利润={trade.pnl:.2f}, 净利润={trade.pnlcomm:.2f}')

    def _create_dataframe(self) -> pd.DataFrame:
        """创建 DataFrame"""
        # 获取所有数据
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []

        for i in range(len(self.datas[0])):
            dates.append(self.datas[0].datetime.date(-len(self.datas[0]) + i + 1))
            opens.append(self.datas[0].open[-len(self.datas[0]) + i + 1])
            highs.append(self.datas[0].high[-len(self.datas[0]) + i + 1])
            lows.append(self.datas[0].low[-len(self.datas[0]) + i + 1])
            closes.append(self.datas[0].close[-len(self.datas[0]) + i + 1])
            volumes.append(self.datas[0].volume[-len(self.datas[0]) + i + 1])

        df = pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        }, index=dates)

        return df

    def next(self):
        """处理每根 K 线"""
        # 如果有挂单，不处理
        if self.order:
            return

        # 创建 DataFrame
        df = self._create_dataframe()

        # 当前索引
        current_index = len(df) - 1

        # 创建 Bar 对象
        bar = Bar(df, index=current_index)

        # 更新自定义策略的持仓状态
        self.custom_strategy.position = self.position.size
        if self.position.size > 0 and self.buy_price:
            self.custom_strategy.buy_price = self.buy_price

        # 调用自定义策略
        signal = self.custom_strategy.on_bar(bar)

        # 执行交易
        if signal.is_buy and not self.position:
            self.log(f'买入信号: {signal.reason}')
            self.order = self.buy()

        elif signal.is_sell and self.position:
            self.log(f'卖出信号: {signal.reason}')
            self.order = self.sell()


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("回测适配器测试")
    print("=" * 60)

    # 测试 StockDataFeed
    print("\n1. StockDataFeed 测试:")
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)

    df = pd.DataFrame({
        'open': base_price + np.random.randn(100) * 0.2,
        'high': base_price + np.abs(np.random.randn(100)) * 1.5,
        'low': base_price - np.abs(np.random.randn(100)) * 1.5,
        'close': base_price,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)

    stock_data = StockData("000001", "平安银行", df)
    data_feed = StockDataFeed.from_stock_data(stock_data)
    print(f"   数据源创建成功: {type(data_feed).__name__}")

    # 测试 StrategyAdapter
    print("\n2. StrategyAdapter 测试:")
    print(f"   策略适配器类: {StrategyAdapter.__name__}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
