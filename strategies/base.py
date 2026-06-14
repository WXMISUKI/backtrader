#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略基础模块

包含:
- Signal: 交易信号
- Bar: K线数据封装
- Strategy: 策略基类

设计灵感:
- finquant: Strategy/Signal/Bar 设计
- QUANTAXIS: 统一数据结构
- vectorbt: 配置驱动
"""

from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np


# ==================== 信号类型枚举 ====================

class SignalType(Enum):
    """信号类型枚举"""
    BUY = 1         # 买入
    SELL = -1       # 卖出
    HOLD = 0        # 观望


# ==================== Signal 类 ====================

@dataclass
class Signal:
    """
    交易信号

    借鉴 finquant 的 Signal 设计

    示例:
        >>> signal = Signal(
        ...     type=SignalType.BUY,
        ...     confidence=0.7,
        ...     reason="MA金叉",
        ...     price=10.5,
        ...     stop_loss=10.0,
        ...     take_profit=12.0
        ... )
        >>> print(signal.is_buy)
        True
    """
    type: SignalType                    # 信号类型
    confidence: float = 0.0             # 置信度 (0-1)
    reason: str = ""                    # 原因说明
    price: Optional[float] = None       # 建议价格
    stop_loss: Optional[float] = None   # 止损价
    take_profit: Optional[float] = None # 止盈价

    @property
    def is_buy(self) -> bool:
        """是否是买入信号"""
        return self.type == SignalType.BUY

    @property
    def is_sell(self) -> bool:
        """是否是卖出信号"""
        return self.type == SignalType.SELL

    @property
    def is_hold(self) -> bool:
        """是否是观望信号"""
        return self.type == SignalType.HOLD

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'type': self.type.name,
            'value': self.type.value,
            'confidence': round(self.confidence, 4),
            'reason': self.reason,
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
        }

    def __str__(self) -> str:
        return f"Signal({self.type.name}, confidence={self.confidence:.2f}, reason='{self.reason}')"


# ==================== Bar 类 ====================

class Bar:
    """
    K线数据封装

    借鉴 finquant 的 Bar 设计，支持历史数据查询

    示例:
        >>> bar = Bar(df, index=99)
        >>> print(bar.close)
        >>> print(bar.history('close', 20))
        >>> print(bar.sma(5))
    """

    def __init__(self, data: pd.DataFrame, index: int):
        """
        初始化

        参数:
            data: 完整的 OHLCV DataFrame
            index: 当前 K 线的索引位置
        """
        self._data = data
        self._index = index

    @property
    def open(self) -> float:
        """开盘价"""
        return float(self._data['open'].iloc[self._index])

    @property
    def high(self) -> float:
        """最高价"""
        return float(self._data['high'].iloc[self._index])

    @property
    def low(self) -> float:
        """最低价"""
        return float(self._data['low'].iloc[self._index])

    @property
    def close(self) -> float:
        """收盘价"""
        return float(self._data['close'].iloc[self._index])

    @property
    def volume(self) -> float:
        """成交量"""
        return float(self._data['volume'].iloc[self._index])

    @property
    def datetime(self):
        """日期时间"""
        return self._data.index[self._index]

    @property
    def index(self) -> int:
        """当前索引"""
        return self._index

    def history(self, field: str, period: int) -> pd.Series:
        """
        获取历史数据

        参数:
            field: 字段名 (open/high/low/close/volume)
            period: 周期数

        返回:
            历史数据序列

        示例:
            >>> bar.history('close', 20)  # 获取最近20根K线的收盘价
        """
        start = max(0, self._index - period + 1)
        end = self._index + 1
        return self._data[field].iloc[start:end].reset_index(drop=True)

    def sma(self, period: int) -> float:
        """
        计算简单移动平均

        参数:
            period: 周期

        返回:
            SMA 值
        """
        return float(self.history('close', period).mean())

    def ema(self, period: int) -> float:
        """
        计算指数移动平均

        参数:
            period: 周期

        返回:
            EMA 值
        """
        return float(self.history('close', period).ewm(span=period, adjust=False).mean().iloc[-1])

    def rsi(self, period: int = 14) -> float:
        """
        计算 RSI

        参数:
            period: 周期

        返回:
            RSI 值
        """
        close = self.history('close', period + 1)
        diff = close.diff()
        gain = diff.clip(lower=0)
        loss = (-diff).clip(lower=0)
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    def __str__(self) -> str:
        return f"Bar(datetime={self.datetime}, close={self.close:.2f})"


# ==================== Strategy 基类 ====================

class Strategy(ABC):
    """
    策略基类

    借鉴 finquant 的 Strategy 设计
    所有策略必须继承此类并实现 on_bar 方法

    示例:
        >>> class MyStrategy(Strategy):
        ...     def on_bar(self, bar: Bar) -> Signal:
        ...         if bar.close > bar.sma(20):
        ...             return Signal(SignalType.BUY, 0.7, "价格高于均线")
        ...         return Signal(SignalType.HOLD)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化

        参数:
            config: 策略配置参数
        """
        self.config = config or {}
        self._position = 0  # 当前持仓
        self._buy_price = None  # 买入价格
        self._trades = []  # 交易记录

    @abstractmethod
    def on_bar(self, bar: Bar) -> Signal:
        """
        处理 K 线数据 (必须实现)

        参数:
            bar: K 线数据

        返回:
            交易信号
        """
        pass

    def on_init(self):
        """策略初始化回调"""
        pass

    def on_start(self):
        """策略启动回调"""
        pass

    def on_stop(self):
        """策略停止回调"""
        pass

    @property
    def position(self) -> int:
        """当前持仓"""
        return self._position

    @position.setter
    def position(self, value: int):
        """设置持仓"""
        self._position = value

    @property
    def buy_price(self) -> Optional[float]:
        """买入价格"""
        return self._buy_price

    @buy_price.setter
    def buy_price(self, value: float):
        """设置买入价格"""
        self._buy_price = value

    @property
    def has_position(self) -> bool:
        """是否有持仓"""
        return self._position > 0

    @property
    def trades(self) -> list:
        """交易记录"""
        return self._trades

    def buy(self, price: float, size: int = 100):
        """
        买入

        参数:
            price: 买入价格
            size: 买入数量
        """
        self._position += size
        self._buy_price = price
        self._trades.append({
            'type': 'BUY',
            'price': price,
            'size': size,
            'position': self._position
        })

    def sell(self, price: float, size: int = None):
        """
        卖出

        参数:
            price: 卖出价格
            size: 卖出数量，默认全部卖出
        """
        if size is None:
            size = self._position
        self._position = max(0, self._position - size)
        self._trades.append({
            'type': 'SELL',
            'price': price,
            'size': size,
            'position': self._position
        })
        if self._position == 0:
            self._buy_price = None

    @property
    def name(self) -> str:
        """策略名称"""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """策略描述"""
        return self.__doc__ or ""

    def reset(self):
        """重置策略状态"""
        self._position = 0
        self._buy_price = None
        self._trades.clear()


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("策略基础模块测试")
    print("=" * 60)

    # 测试 Signal
    print("\n1. Signal 测试:")
    buy_signal = Signal(
        type=SignalType.BUY,
        confidence=0.7,
        reason="MA金叉",
        price=10.5,
        stop_loss=10.0,
        take_profit=12.0
    )
    print(f"   买入信号: {buy_signal}")
    print(f"   is_buy: {buy_signal.is_buy}")
    print(f"   to_dict: {buy_signal.to_dict()}")

    sell_signal = Signal(SignalType.SELL, 0.6, "MA死叉")
    print(f"   卖出信号: {sell_signal}")

    hold_signal = Signal(SignalType.HOLD)
    print(f"   观望信号: {hold_signal}")

    # 测试 Bar
    print("\n2. Bar 测试:")
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(100) * 0.5),
        'high': 102 + np.cumsum(np.random.randn(100) * 0.5),
        'low': 98 + np.cumsum(np.random.randn(100) * 0.5),
        'close': 100 + np.cumsum(np.random.randn(100) * 0.5),
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)

    bar = Bar(df, index=99)
    print(f"   当前K线: {bar}")
    print(f"   收盘价: {bar.close:.2f}")
    print(f"   5日均线: {bar.sma(5):.2f}")
    print(f"   14日RSI: {bar.rsi(14):.2f}")

    # 测试历史数据
    history = bar.history('close', 5)
    print(f"   最近5日收盘价: {history.tolist()}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
