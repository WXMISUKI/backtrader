#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略模块单元测试

测试覆盖:
- Signal 类
- Bar 类
- Strategy 基类
- StrategyRegistry 类
- MACrossStrategy 策略
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from strategies import (
    Strategy, Bar, Signal, SignalType,
    StrategyRegistry, get_strategy, list_strategies,
    MACrossStrategy
)


# ==================== 测试数据 ====================

@pytest.fixture
def sample_df():
    """创建测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)

    return pd.DataFrame({
        'open': base_price + np.random.randn(100) * 0.2,
        'high': base_price + np.abs(np.random.randn(100)) * 1.5,
        'low': base_price - np.abs(np.random.randn(100)) * 1.5,
        'close': base_price,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)


@pytest.fixture
def sample_bar(sample_df):
    """创建测试 Bar"""
    return Bar(sample_df, index=50)


# ==================== Signal 测试 ====================

class TestSignal:
    """Signal 测试"""

    def test_buy_signal(self):
        """测试买入信号"""
        signal = Signal(
            type=SignalType.BUY,
            confidence=0.7,
            reason="测试买入",
            price=10.5,
            stop_loss=10.0,
            take_profit=12.0
        )
        assert signal.is_buy == True
        assert signal.is_sell == False
        assert signal.is_hold == False
        assert signal.confidence == 0.7

    def test_sell_signal(self):
        """测试卖出信号"""
        signal = Signal(SignalType.SELL, 0.6, "测试卖出")
        assert signal.is_sell == True
        assert signal.is_buy == False

    def test_hold_signal(self):
        """测试观望信号"""
        signal = Signal(SignalType.HOLD)
        assert signal.is_hold == True
        assert signal.confidence == 0.0

    def test_to_dict(self):
        """测试转换为字典"""
        signal = Signal(SignalType.BUY, 0.7, "测试", 10.5)
        d = signal.to_dict()
        assert d['type'] == 'BUY'
        assert d['confidence'] == 0.7
        assert d['price'] == 10.5

    def test_str(self):
        """测试字符串表示"""
        signal = Signal(SignalType.BUY, 0.7, "测试")
        assert "BUY" in str(signal)


# ==================== Bar 测试 ====================

class TestBar:
    """Bar 测试"""

    def test_properties(self, sample_bar):
        """测试基础属性"""
        assert isinstance(sample_bar.open, float)
        assert isinstance(sample_bar.high, float)
        assert isinstance(sample_bar.low, float)
        assert isinstance(sample_bar.close, float)
        assert isinstance(sample_bar.volume, float)

    def test_datetime(self, sample_bar):
        """测试日期时间"""
        assert sample_bar.datetime is not None

    def test_index(self, sample_bar):
        """测试索引"""
        assert sample_bar.index == 50

    def test_history(self, sample_bar):
        """测试历史数据"""
        history = sample_bar.history('close', 10)
        assert len(history) == 10

    def test_sma(self, sample_bar):
        """测试简单移动平均"""
        sma = sample_bar.sma(5)
        assert isinstance(sma, float)

    def test_ema(self, sample_bar):
        """测试指数移动平均"""
        ema = sample_bar.ema(5)
        assert isinstance(ema, float)

    def test_rsi(self, sample_bar):
        """测试 RSI"""
        rsi = sample_bar.rsi(14)
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_str(self, sample_bar):
        """测试字符串表示"""
        assert "Bar" in str(sample_bar)


# ==================== Strategy 测试 ====================

class TestStrategy:
    """Strategy 测试"""

    def test_abstract(self):
        """测试抽象类"""
        with pytest.raises(TypeError):
            # 不能实例化抽象类
            class TestStrategy(Strategy):
                pass
            TestStrategy()

    def test_concrete(self):
        """测试具体策略"""
        class MyStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy = MyStrategy({'param1': 1})
        assert strategy.name == "MyStrategy"
        assert strategy.config == {'param1': 1}

    def test_position(self):
        """测试持仓管理"""
        class MyStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy = MyStrategy()
        assert strategy.position == 0
        assert strategy.has_position == False

        strategy.position = 100
        assert strategy.position == 100
        assert strategy.has_position == True

    def test_buy_sell(self):
        """测试买卖操作"""
        class MyStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy = MyStrategy()

        # 买入
        strategy.buy(10.0, 100)
        assert strategy.position == 100
        assert strategy.buy_price == 10.0
        assert strategy.has_position == True

        # 卖出
        strategy.sell(11.0)
        assert strategy.position == 0
        assert strategy.buy_price is None
        assert strategy.has_position == False

    def test_trades(self):
        """测试交易记录"""
        class MyStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy = MyStrategy()
        strategy.buy(10.0, 100)
        strategy.sell(11.0, 100)

        assert len(strategy.trades) == 2
        assert strategy.trades[0]['type'] == 'BUY'
        assert strategy.trades[1]['type'] == 'SELL'

    def test_reset(self):
        """测试重置"""
        class MyStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy = MyStrategy()
        strategy.buy(10.0, 100)
        strategy.reset()

        assert strategy.position == 0
        assert strategy.buy_price is None
        assert len(strategy.trades) == 0


# ==================== StrategyRegistry 测试 ====================

class TestStrategyRegistry:
    """StrategyRegistry 测试"""

    def setup_method(self):
        """每个测试前清除注册"""
        StrategyRegistry.clear()

    def test_register(self):
        """测试注册"""
        @StrategyRegistry.register("test")
        class TestStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        assert "test" in StrategyRegistry.list()

    def test_get(self):
        """测试获取"""
        @StrategyRegistry.register("test")
        class TestStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy_cls = StrategyRegistry.get("test")
        assert strategy_cls.__name__ == "TestStrategy"

    def test_create(self):
        """测试创建实例"""
        @StrategyRegistry.register("test")
        class TestStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategy = StrategyRegistry.create("test", {'param1': 1})
        assert strategy.name == "TestStrategy"
        assert strategy.config == {'param1': 1}

    def test_list(self):
        """测试列出策略"""
        @StrategyRegistry.register("test1")
        class TestStrategy1(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        @StrategyRegistry.register("test2")
        class TestStrategy2(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        strategies = StrategyRegistry.list()
        assert "test1" in strategies
        assert "test2" in strategies

    def test_exists(self):
        """测试是否存在"""
        @StrategyRegistry.register("test")
        class TestStrategy(Strategy):
            def on_bar(self, bar):
                return Signal(SignalType.HOLD)

        assert StrategyRegistry.exists("test") == True
        assert StrategyRegistry.exists("nonexistent") == False

    def test_key_error(self):
        """测试异常"""
        with pytest.raises(KeyError):
            StrategyRegistry.get("nonexistent")

    def test_type_error(self):
        """测试类型错误"""
        with pytest.raises(TypeError):
            @StrategyRegistry.register("bad")
            class NotAStrategy:
                pass


# ==================== MACrossStrategy 测试 ====================

class TestMACrossStrategy:
    """MACrossStrategy 测试"""

    def test_initialization(self):
        """测试初始化"""
        strategy = MACrossStrategy({
            'fast_period': 5,
            'slow_period': 20
        })
        assert strategy.fast_period == 5
        assert strategy.slow_period == 20

    def test_default_params(self):
        """测试默认参数"""
        strategy = MACrossStrategy()
        assert strategy.fast_period == 5
        assert strategy.slow_period == 20
        assert strategy.stop_loss == 0.05
        assert strategy.take_profit == 0.15

    def test_on_bar_insufficient_data(self, sample_df):
        """测试数据不足"""
        strategy = MACrossStrategy({'slow_period': 20})
        bar = Bar(sample_df, index=10)  # 索引小于 slow_period
        signal = strategy.on_bar(bar)
        assert signal.is_hold

    def test_on_bar_normal(self, sample_df):
        """测试正常处理"""
        strategy = MACrossStrategy()
        bar = Bar(sample_df, index=50)
        signal = strategy.on_bar(bar)
        assert isinstance(signal, Signal)

    def test_backtest_simulation(self, sample_df):
        """测试回测模拟"""
        strategy = MACrossStrategy()
        signals = []

        for i in range(len(sample_df)):
            bar = Bar(sample_df, index=i)
            signal = strategy.on_bar(bar)
            signals.append(signal)

        # 应该有信号产生
        buy_signals = [s for s in signals if s.is_buy]
        sell_signals = [s for s in signals if s.is_sell]
        hold_signals = [s for s in signals if s.is_hold]

        assert len(buy_signals) + len(sell_signals) + len(hold_signals) == len(sample_df)


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
