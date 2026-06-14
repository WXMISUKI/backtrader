#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSI 策略

策略逻辑:
- RSI < oversold 后回升：买入 (超卖反弹)
- RSI > overbought：卖出 (超买)

配置参数:
- period: RSI 周期，默认 14
- overbought: 超买阈值，默认 70
- oversold: 超卖阈值，默认 30
- stop_loss: 止损比例，默认 0.05 (5%)
- take_profit: 止盈比例，默认 0.15 (15%)
"""

from typing import Dict, Any
from .base import Strategy, Bar, Signal, SignalType
from .registry import StrategyRegistry


@StrategyRegistry.register("rsi")
class RSIStrategy(Strategy):
    """
    RSI 策略

    - RSI < oversold 后回升：买入 (超卖反弹)
    - RSI > overbought：卖出 (超买)

    参数:
        period: RSI 周期 (默认 14)
        overbought: 超买阈值 (默认 70)
        oversold: 超卖阈值 (默认 30)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)

    示例:
        >>> strategy = RSIStrategy({
        ...     'period': 14,
        ...     'overbought': 70,
        ...     'oversold': 30
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
        self.period = self.config.get('period', 14)
        self.overbought = self.config.get('overbought', 70)
        self.oversold = self.config.get('oversold', 30)
        self.stop_loss = self.config.get('stop_loss', 0.05)
        self.take_profit = self.config.get('take_profit', 0.15)

        # 存储前一日的 RSI 值
        self._prev_rsi = None
        # 记录是否处于超卖区域
        self._was_oversold = False

    def _calc_rsi(self, bar: Bar) -> float:
        """
        计算 RSI

        返回:
            RSI 值
        """
        # 获取足够的历史数据
        period = self.period + 10
        close = bar.history('close', period)

        # 计算价格变化
        diff = close.diff()

        # 分离涨跌
        gain = diff.clip(lower=0)
        loss = (-diff).clip(lower=0)

        # 计算平均涨跌
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()

        # 计算 RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1])

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

        # 计算 RSI
        rsi = self._calc_rsi(bar)

        # 获取前一日值
        prev_rsi = self._prev_rsi

        # 更新前一日值
        self._prev_rsi = rsi

        # 前一日值为空时观望
        if prev_rsi is None:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="等待 RSI 形成"
            )

        # 更新超卖状态
        if rsi < self.oversold:
            self._was_oversold = True

        # 止损检查
        if self.has_position and self.buy_price:
            loss_pct = (self.buy_price - bar.close) / self.buy_price
            if loss_pct >= self.stop_loss:
                self._was_oversold = False
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
                self._was_oversold = False
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.8,
                    reason=f"止盈触发: 盈利 {profit_pct:.1%}",
                    price=bar.close
                )

        # 超卖反弹买入
        if self._was_oversold and rsi > self.oversold and prev_rsi <= self.oversold:
            if not self.has_position:
                self._was_oversold = False
                return Signal(
                    type=SignalType.BUY,
                    confidence=0.7,
                    reason=f"RSI 超卖反弹 (RSI={rsi:.2f}, 从 {prev_rsi:.2f} 回升)",
                    price=bar.close,
                    stop_loss=bar.close * (1 - self.stop_loss),
                    take_profit=bar.close * (1 + self.take_profit)
                )

        # 超买卖出
        if rsi > self.overbought:
            if self.has_position:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.7,
                    reason=f"RSI 超买 (RSI={rsi:.2f} > {self.overbought})",
                    price=bar.close
                )

        # 观望
        return Signal(
            type=SignalType.HOLD,
            confidence=0,
            reason=f"无信号 (RSI={rsi:.2f})"
        )

    def reset(self):
        """重置策略状态"""
        super().reset()
        self._prev_rsi = None
        self._was_oversold = False


# 测试代码
if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    print("=" * 60)
    print("RSI 策略测试")
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
    strategy = RSIStrategy({
        'period': 14,
        'overbought': 70,
        'oversold': 30
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
