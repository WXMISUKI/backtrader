#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MACD 策略

策略逻辑:
- DIF 上穿 DEA：买入 (金叉)
- DIF 下穿 DEA：卖出 (死叉)

配置参数:
- fast_period: 快线周期，默认 12
- slow_period: 慢线周期，默认 26
- signal_period: 信号线周期，默认 9
- stop_loss: 止损比例，默认 0.05 (5%)
- take_profit: 止盈比例，默认 0.15 (15%)
"""

from typing import Dict, Any
from .base import Strategy, Bar, Signal, SignalType
from .registry import StrategyRegistry


@StrategyRegistry.register("macd")
class MACDStrategy(Strategy):
    """
    MACD 策略

    - DIF 上穿 DEA：买入 (金叉)
    - DIF 下穿 DEA：卖出 (死叉)

    参数:
        fast_period: 快线周期 (默认 12)
        slow_period: 慢线周期 (默认 26)
        signal_period: 信号线周期 (默认 9)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)

    示例:
        >>> strategy = MACDStrategy({
        ...     'fast_period': 12,
        ...     'slow_period': 26,
        ...     'signal_period': 9
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
        self.fast_period = self.config.get('fast_period', 12)
        self.slow_period = self.config.get('slow_period', 26)
        self.signal_period = self.config.get('signal_period', 9)
        self.stop_loss = self.config.get('stop_loss', 0.05)
        self.take_profit = self.config.get('take_profit', 0.15)

        # 存储前一日的 MACD 值
        self._prev_dif = None
        self._prev_dea = None

    def _calc_macd(self, bar: Bar) -> tuple:
        """
        计算 MACD

        返回:
            (dif, dea, macd_hist)
        """
        # 获取足够的历史数据
        period = self.slow_period + self.signal_period + 10
        close = bar.history('close', period)

        # 计算 EMA
        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()

        # 计算 DIF
        dif = ema_fast - ema_slow

        # 计算 DEA
        dea = dif.ewm(span=self.signal_period, adjust=False).mean()

        # 计算 MACD 柱状图
        macd_hist = (dif - dea) * 2

        return float(dif.iloc[-1]), float(dea.iloc[-1]), float(macd_hist.iloc[-1])

    def on_bar(self, bar: Bar) -> Signal:
        """
        处理 K 线

        参数:
            bar: K 线数据

        返回:
            交易信号
        """
        # 数据不足时观望
        min_period = self.slow_period + self.signal_period
        if bar.index < min_period:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="数据不足"
            )

        # 计算 MACD
        dif, dea, macd_hist = self._calc_macd(bar)

        # 获取前一日值
        prev_dif = self._prev_dif
        prev_dea = self._prev_dea

        # 更新前一日值
        self._prev_dif = dif
        self._prev_dea = dea

        # 前一日值为空时观望
        if prev_dif is None or prev_dea is None:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="等待 MACD 形成"
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
        if dif > dea and prev_dif <= prev_dea:
            if not self.has_position:
                return Signal(
                    type=SignalType.BUY,
                    confidence=0.7,
                    reason=f"MACD 金叉 (DIF={dif:.4f}, DEA={dea:.4f})",
                    price=bar.close,
                    stop_loss=bar.close * (1 - self.stop_loss),
                    take_profit=bar.close * (1 + self.take_profit)
                )

        # 死叉卖出
        if dif < dea and prev_dif >= prev_dea:
            if self.has_position:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.7,
                    reason=f"MACD 死叉 (DIF={dif:.4f}, DEA={dea:.4f})",
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
        self._prev_dif = None
        self._prev_dea = None


# 测试代码
if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    print("=" * 60)
    print("MACD 策略测试")
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
    strategy = MACDStrategy({
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9
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
