#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
布林带策略

策略逻辑:
- 价格触及下轨后反弹：买入
- 价格触及上轨后回落：卖出

配置参数:
- period: 布林带周期，默认 20
- std_dev: 标准差倍数，默认 2.0
- stop_loss: 止损比例，默认 0.05 (5%)
- take_profit: 止盈比例，默认 0.15 (15%)
"""

from typing import Dict, Any
from .base import Strategy, Bar, Signal, SignalType
from .registry import StrategyRegistry


@StrategyRegistry.register("boll")
class BollStrategy(Strategy):
    """
    布林带策略

    - 价格触及下轨后反弹：买入
    - 价格触及上轨后回落：卖出

    参数:
        period: 布林带周期 (默认 20)
        std_dev: 标准差倍数 (默认 2.0)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)

    示例:
        >>> strategy = BollStrategy({
        ...     'period': 20,
        ...     'std_dev': 2.0
        ... })
        >>> signal = strategy.on_bar(bar)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化

        参数:
            config: 策略配置
        """
        super().__init__(config)
        self.period = self.config.get('period', 20)
        self.std_dev = self.config.get('std_dev', 2.0)
        self.stop_loss = self.config.get('stop_loss', 0.05)
        self.take_profit = self.config.get('take_profit', 0.15)

        # 存储前一日的价格位置
        self._prev_below_lower = False
        self._prev_above_upper = False

    def _calc_boll(self, bar: Bar) -> tuple:
        """
        计算布林带

        返回:
            (upper, middle, lower)
        """
        # 获取足够的历史数据
        close = bar.history('close', self.period)

        # 计算中轨 (SMA)
        middle = float(close.mean())

        # 计算标准差
        std = float(close.std())

        # 计算上下轨
        upper = middle + self.std_dev * std
        lower = middle - self.std_dev * std

        return upper, middle, lower

    def on_bar(self, bar: Bar) -> Signal:
        """
        处理 K 线

        参数:
            bar: K 线数据

        返回:
            交易信号
        """
        # 数据不足时观望
        if bar.index < self.period + 5:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="数据不足"
            )

        # 计算布林带
        upper, middle, lower = self._calc_boll(bar)

        # 当前价格
        price = bar.close

        # 判断价格位置
        below_lower = price < lower
        above_upper = price > upper

        # 获取前一日状态
        prev_below_lower = self._prev_below_lower
        prev_above_upper = self._prev_above_upper

        # 更新前一日状态
        self._prev_below_lower = below_lower
        self._prev_above_upper = above_upper

        # 止损检查
        if self.has_position and self.buy_price:
            loss_pct = (self.buy_price - price) / self.buy_price
            if loss_pct >= self.stop_loss:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.9,
                    reason=f"止损触发: 亏损 {loss_pct:.1%}",
                    price=price
                )

        # 止盈检查
        if self.has_position and self.buy_price:
            profit_pct = (price - self.buy_price) / self.buy_price
            if profit_pct >= self.take_profit:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.8,
                    reason=f"止盈触发: 盈利 {profit_pct:.1%}",
                    price=price
                )

        # 下轨反弹买入
        if not below_lower and prev_below_lower:
            if not self.has_position:
                return Signal(
                    type=SignalType.BUY,
                    confidence=0.7,
                    reason=f"布林带下轨反弹 (价格={price:.2f}, 下轨={lower:.2f})",
                    price=price,
                    stop_loss=price * (1 - self.stop_loss),
                    take_profit=price * (1 + self.take_profit)
                )

        # 上轨回落卖出
        if not above_upper and prev_above_upper:
            if self.has_position:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.7,
                    reason=f"布林带上轨回落 (价格={price:.2f}, 上轨={upper:.2f})",
                    price=price
                )

        # 观望
        return Signal(
            type=SignalType.HOLD,
            confidence=0,
            reason=f"无信号 (价格={price:.2f}, 中轨={middle:.2f})"
        )

    def reset(self):
        """重置策略状态"""
        super().reset()
        self._prev_below_lower = False
        self._prev_above_upper = False


# 测试代码
if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    print("=" * 60)
    print("布林带策略测试")
    print("=" * 60)

    # 创建测试数据
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

    # 创建策略
    strategy = BollStrategy({
        'period': 20,
        'std_dev': 2.0
    })

    print(f"\n策略名称: {strategy.name}")

    # 模拟回测
    print("\n模拟回测:")
    buy_count = 0
    sell_count = 0

    for i in range(len(df)):
        bar = Bar(df, index=i)
        signal = strategy.on_bar(bar)

        if signal.is_buy:
            buy_count += 1
            print(f"  {bar.datetime.strftime('%Y-%m-%d')}: {signal}")
        elif signal.is_sell:
            sell_count += 1
            print(f"  {bar.datetime.strftime('%Y-%m-%d')}: {signal}")

    print(f"\n统计:")
    print(f"  买入信号: {buy_count} 次")
    print(f"  卖出信号: {sell_count} 次")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
