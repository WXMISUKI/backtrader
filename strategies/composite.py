#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合策略

策略逻辑:
- 综合多个子策略的信号
- 当多数子策略同意时生成信号

配置参数:
- strategies: 子策略名称列表
- min_agreement: 最少同意策略数，默认 2
- configs: 子策略配置字典
"""

from typing import Dict, Any, List
from .base import Strategy, Bar, Signal, SignalType
from .registry import StrategyRegistry


@StrategyRegistry.register("composite")
class CompositeStrategy(Strategy):
    """
    综合策略

    综合多个子策略的信号，当多数子策略同意时生成信号

    参数:
        strategies: 子策略名称列表 (默认 ['ma_cross', 'macd', 'rsi'])
        min_agreement: 最少同意策略数 (默认 2)
        configs: 子策略配置字典

    示例:
        >>> strategy = CompositeStrategy({
        ...     'strategies': ['ma_cross', 'macd', 'rsi'],
        ...     'min_agreement': 2,
        ...     'configs': {
        ...         'ma_cross': {'fast_period': 5, 'slow_period': 20},
        ...         'macd': {'fast_period': 12},
        ...         'rsi': {'period': 14}
        ...     }
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

        # 子策略名称列表
        self.strategy_names = self.config.get(
            'strategies',
            ['ma_cross', 'macd', 'rsi']
        )

        # 最少同意策略数
        self.min_agreement = self.config.get('min_agreement', 2)

        # 子策略配置
        self.configs = self.config.get('configs', {})

        # 创建子策略实例
        self._sub_strategies = []
        self._init_sub_strategies()

    def _init_sub_strategies(self):
        """初始化子策略"""
        for name in self.strategy_names:
            try:
                sub_config = self.configs.get(name, {})
                strategy = StrategyRegistry.create(name, sub_config)
                self._sub_strategies.append(strategy)
            except KeyError:
                print(f"警告: 未找到策略 '{name}'，已跳过")

    def on_bar(self, bar: Bar) -> Signal:
        """
        处理 K 线

        参数:
            bar: K 线数据

        返回:
            交易信号
        """
        # 收集子策略信号
        buy_signals = []
        sell_signals = []
        hold_signals = []

        for strategy in self._sub_strategies:
            signal = strategy.on_bar(bar)
            if signal.is_buy:
                buy_signals.append(signal)
            elif signal.is_sell:
                sell_signals.append(signal)
            else:
                hold_signals.append(signal)

        # 统计共识
        buy_count = len(buy_signals)
        sell_count = len(sell_signals)

        # 止损检查
        if self.has_position and self.buy_price:
            loss_pct = (self.buy_price - bar.close) / self.buy_price
            if loss_pct >= 0.05:  # 默认 5% 止损
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.9,
                    reason=f"止损触发: 亏损 {loss_pct:.1%}",
                    price=bar.close
                )

        # 止盈检查
        if self.has_position and self.buy_price:
            profit_pct = (bar.close - self.buy_price) / self.buy_price
            if profit_pct >= 0.15:  # 默认 15% 止盈
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.8,
                    reason=f"止盈触发: 盈利 {profit_pct:.1%}",
                    price=bar.close
                )

        # 多数同意买入
        if buy_count >= self.min_agreement:
            if not self.has_position:
                # 计算平均置信度
                avg_confidence = sum(s.confidence for s in buy_signals) / buy_count
                reasons = [s.reason for s in buy_signals]
                return Signal(
                    type=SignalType.BUY,
                    confidence=avg_confidence,
                    reason=f"综合买入 ({buy_count}个策略同意): {'; '.join(reasons)}",
                    price=bar.close,
                    stop_loss=bar.close * 0.95,
                    take_profit=bar.close * 1.15
                )

        # 多数同意卖出
        if sell_count >= self.min_agreement:
            if self.has_position:
                # 计算平均置信度
                avg_confidence = sum(s.confidence for s in sell_signals) / sell_count
                reasons = [s.reason for s in sell_signals]
                return Signal(
                    type=SignalType.SELL,
                    confidence=avg_confidence,
                    reason=f"综合卖出 ({sell_count}个策略同意): {'; '.join(reasons)}",
                    price=bar.close
                )

        # 观望
        return Signal(
            type=SignalType.HOLD,
            confidence=0,
            reason=f"无共识 (买入:{buy_count}, 卖出:{sell_count}, 观望:{len(hold_signals)})"
        )

    def reset(self):
        """重置策略状态"""
        super().reset()
        for strategy in self._sub_strategies:
            strategy.reset()

    @property
    def sub_strategies(self) -> list:
        """获取子策略列表"""
        return self._sub_strategies


# 测试代码
if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    print("=" * 60)
    print("综合策略测试")
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
    strategy = CompositeStrategy({
        'strategies': ['ma_cross', 'macd', 'rsi'],
        'min_agreement': 2,
        'configs': {
            'ma_cross': {'fast_period': 5, 'slow_period': 20},
            'macd': {'fast_period': 12, 'slow_period': 26},
            'rsi': {'period': 14}
        }
    })

    print(f"\n策略名称: {strategy.name}")
    print(f"子策略数量: {len(strategy.sub_strategies)}")

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
