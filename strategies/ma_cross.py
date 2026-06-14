#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双均线交叉策略

策略逻辑:
- 短期均线上穿长期均线：买入 (金叉)
- 短期均线下穿长期均线：卖出 (死叉)

配置参数:
- fast_period: 短期均线周期，默认 5
- slow_period: 长期均线周期，默认 20
- stop_loss: 止损比例，默认 0.05 (5%)
- take_profit: 止盈比例，默认 0.15 (15%)
"""

from typing import Dict, Any
from .base import Strategy, Bar, Signal, SignalType
from .registry import StrategyRegistry


@StrategyRegistry.register("ma_cross")
class MACrossStrategy(Strategy):
    """
    双均线交叉策略

    - 短期均线上穿长期均线：买入 (金叉)
    - 短期均线下穿长期均线：卖出 (死叉)

    参数:
        fast_period: 短期均线周期 (默认 5)
        slow_period: 长期均线周期 (默认 20)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)

    示例:
        >>> strategy = MACrossStrategy({
        ...     'fast_period': 5,
        ...     'slow_period': 20,
        ...     'stop_loss': 0.05,
        ...     'take_profit': 0.15
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
        self.fast_period = self.config.get('fast_period', 5)
        self.slow_period = self.config.get('slow_period', 20)
        self.stop_loss = self.config.get('stop_loss', 0.05)
        self.take_profit = self.config.get('take_profit', 0.15)

        # 存储前一日的均线值
        self._prev_fast_ma = None
        self._prev_slow_ma = None

    def on_bar(self, bar: Bar) -> Signal:
        """
        处理 K 线

        参数:
            bar: K 线数据

        返回:
            交易信号
        """
        # 数据不足时观望
        if bar.index < self.slow_period:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="数据不足"
            )

        # 计算当前均线
        fast_ma = bar.sma(self.fast_period)
        slow_ma = bar.sma(self.slow_period)

        # 获取前一日均线
        prev_fast_ma = self._prev_fast_ma
        prev_slow_ma = self._prev_slow_ma

        # 更新前一日均线
        self._prev_fast_ma = fast_ma
        self._prev_slow_ma = slow_ma

        # 前一日均线为空时观望
        if prev_fast_ma is None or prev_slow_ma is None:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="等待均线形成"
            )

        # 止损检查
        if self.has_position and self.buy_price:
            loss_pct = (self.buy_price - bar.close) / self.buy_price
            if loss_pct >= self.stop_loss:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.9,
                    reason=f"止损触发: 亏损 {loss_pct:.1%}",
                    price=bar.close
                )

        # 止盈检查
        if self.has_position and self.buy_price:
            profit_pct = (bar.close - self.buy_price) / self.buy_price
            if profit_pct >= self.take_profit:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.8,
                    reason=f"止盈触发: 盈利 {profit_pct:.1%}",
                    price=bar.close
                )

        # 金叉买入
        if fast_ma > slow_ma and prev_fast_ma <= prev_slow_ma:
            if not self.has_position:
                return Signal(
                    type=SignalType.BUY,
                    confidence=0.7,
                    reason=f"MA{self.fast_period} 上穿 MA{self.slow_period} (金叉)",
                    price=bar.close,
                    stop_loss=bar.close * (1 - self.stop_loss),
                    take_profit=bar.close * (1 + self.take_profit)
                )

        # 死叉卖出
        if fast_ma < slow_ma and prev_fast_ma >= prev_slow_ma:
            if self.has_position:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.7,
                    reason=f"MA{self.fast_period} 下穿 MA{self.slow_period} (死叉)",
                    price=bar.close
                )

        # 观望
        return Signal(
            type=SignalType.HOLD,
            confidence=0,
            reason="无信号"
        )

    def reset(self):
        """重置策略状态"""
        super().reset()
        self._prev_fast_ma = None
        self._prev_slow_ma = None


# 测试代码
if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    print("=" * 60)
    print("双均线策略测试")
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
    strategy = MACrossStrategy({
        'fast_period': 5,
        'slow_period': 20,
        'stop_loss': 0.05,
        'take_profit': 0.15
    })

    print(f"\n策略名称: {strategy.name}")
    print(f"策略描述: {strategy.description}")

    # 模拟回测
    print("\n模拟回测:")
    buy_count = 0
    sell_count = 0
    hold_count = 0

    for i in range(len(df)):
        bar = Bar(df, index=i)
        signal = strategy.on_bar(bar)

        if signal.is_buy:
            buy_count += 1
            if buy_count <= 3:  # 只显示前3次
                print(f"  {bar.datetime.strftime('%Y-%m-%d')}: {signal}")
        elif signal.is_sell:
            sell_count += 1
            if sell_count <= 3:  # 只显示前3次
                print(f"  {bar.datetime.strftime('%Y-%m-%d')}: {signal}")
        else:
            hold_count += 1

    print(f"\n统计:")
    print(f"  买入信号: {buy_count} 次")
    print(f"  卖出信号: {sell_count} 次")
    print(f"  观望信号: {hold_count} 次")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
