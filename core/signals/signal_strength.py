#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
信号强度计算模块

功能:
- 信号强度计算
- 交易方向判断
- 综合信号生成
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple

from .buy_signals import get_buy_signals
from .sell_signals import get_sell_signals


# 信号权重配置
SIGNAL_WEIGHTS = {
    # 买入信号权重
    'buy': {
        'signal_ma_cross': 0.20,
        'signal_macd_cross': 0.25,
        'signal_rsi_oversold': 0.15,
        'signal_kdj_cross': 0.15,
        'signal_boll_support': 0.10,
        'signal_volume': 0.15,
    },
    # 卖出信号权重
    'sell': {
        'signal_ma_death': 0.20,
        'signal_macd_death': 0.25,
        'signal_rsi_overbought': 0.15,
        'signal_kdj_death': 0.15,
        'signal_boll_pressure': 0.10,
        'signal_stop_loss': 0.15,
    }
}


def calc_signal_strength(
    signals: pd.DataFrame,
    weights: Dict[str, float]
) -> pd.Series:
    """
    计算信号强度

    参数:
        signals: 信号 DataFrame (每列是一个信号，值为 0 或 1)
        weights: 权重字典 {信号列名: 权重}

    返回:
        pd.Series: 信号强度 (0-1)

    算法:
        强度 = Σ(信号值 × 权重) / Σ(权重)

    示例:
        >>> signals = pd.DataFrame({
        ...     'signal_ma_cross': [0, 1, 0],
        ...     'signal_macd_cross': [0, 0, 1],
        ... })
        >>> weights = {'signal_ma_cross': 0.5, 'signal_macd_cross': 0.5}
        >>> strength = calc_signal_strength(signals, weights)
        >>> # 返回 [0.0, 0.5, 0.5]
    """
    # 筛选存在的信号列
    valid_weights = {k: v for k, v in weights.items() if k in signals.columns}

    if not valid_weights:
        return pd.Series(0.0, index=signals.index)

    # 计算加权和
    weighted_sum = pd.Series(0.0, index=signals.index)
    total_weight = 0.0

    for col, weight in valid_weights.items():
        weighted_sum += signals[col] * weight
        total_weight += weight

    # 计算强度
    if total_weight > 0:
        strength = weighted_sum / total_weight
    else:
        strength = pd.Series(0.0, index=signals.index)

    return strength


def get_trade_direction(
    buy_strength: pd.Series,
    sell_strength: pd.Series,
    min_strength: float = 0.3
) -> pd.Series:
    """
    判断交易方向

    参数:
        buy_strength: 买入信号强度 (0-1)
        sell_strength: 卖出信号强度 (0-1)
        min_strength: 最小信号强度阈值

    返回:
        pd.Series: 交易方向
            - 1: 买入
            - -1: 卖出
            - 0: 观望

    算法:
        如果 buy_strength >= min_strength 且 buy_strength > sell_strength: 买入 (1)
        如果 sell_strength >= min_strength 且 sell_strength > buy_strength: 卖出 (-1)
        否则: 观望 (0)

    示例:
        >>> buy = pd.Series([0.6, 0.2, 0.4])
        >>> sell = pd.Series([0.1, 0.7, 0.3])
        >>> direction = get_trade_direction(buy, sell, 0.3)
        >>> # 返回 [1, -1, 0]
    """
    direction = pd.Series(0, index=buy_strength.index)

    # 买入条件: 买入强度 >= 阈值 且 买入强度 > 卖出强度
    buy_condition = (buy_strength >= min_strength) & (buy_strength > sell_strength)
    direction[buy_condition] = 1

    # 卖出条件: 卖出强度 >= 阈值 且 卖出强度 > 买入强度
    sell_condition = (sell_strength >= min_strength) & (sell_strength > buy_strength)
    direction[sell_condition] = -1

    return direction


def get_confidence(
    buy_strength: pd.Series,
    sell_strength: pd.Series,
    direction: pd.Series
) -> pd.Series:
    """
    计算置信度

    参数:
        buy_strength: 买入信号强度
        sell_strength: 卖出信号强度
        direction: 交易方向

    返回:
        pd.Series: 置信度 (0-1)

    算法:
        买入时: 置信度 = buy_strength
        卖出时: 置信度 = sell_strength
        观望时: 置信度 = 0
    """
    confidence = pd.Series(0.0, index=buy_strength.index)

    # 买入时的置信度
    buy_mask = direction == 1
    confidence[buy_mask] = buy_strength[buy_mask]

    # 卖出时的置信度
    sell_mask = direction == -1
    confidence[sell_mask] = sell_strength[sell_mask]

    return confidence


def generate_signal(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    indicators: pd.DataFrame,
    risk_profile: str = "moderate",
    buy_price: Optional[float] = None
) -> pd.DataFrame:
    """
    生成综合交易信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        indicators: 指标数据 (来自 IndicatorCalculator)
        risk_profile: 风险配置
        buy_price: 买入价格 (用于止损判断)

    返回:
        pd.DataFrame: 包含以下列
            - buy_strength: 买入信号强度
            - sell_strength: 卖出信号强度
            - direction: 交易方向 (1/-1/0)
            - confidence: 置信度

    示例:
        >>> from core.indicators import IndicatorCalculator
        >>> calc = IndicatorCalculator()
        >>> indicators = calc.calc_all(high, low, close, volume)
        >>> signals = generate_signal(close, high, low, volume, indicators)
        >>> # 获取最新信号
        >>> latest = signals.iloc[-1]
        >>> print(f"方向: {latest['direction']}, 置信度: {latest['confidence']}")
    """
    # 获取风险配置对应的最小信号强度
    min_strengths = {
        "conservative": 0.5,
        "moderate": 0.3,
        "aggressive": 0.2
    }
    min_strength = min_strengths.get(risk_profile, 0.3)

    # 获取买入信号
    buy_signals = get_buy_signals(
        close, high, low, volume, indicators, risk_profile
    )

    # 获取卖出信号
    sell_signals = get_sell_signals(
        close, high, low, indicators, risk_profile, buy_price
    )

    # 计算信号强度
    buy_strength = calc_signal_strength(
        buy_signals, SIGNAL_WEIGHTS['buy']
    )
    sell_strength = calc_signal_strength(
        sell_signals, SIGNAL_WEIGHTS['sell']
    )

    # 判断交易方向
    direction = get_trade_direction(
        buy_strength, sell_strength, min_strength
    )

    # 计算置信度
    confidence = get_confidence(
        buy_strength, sell_strength, direction
    )

    # 组合结果
    result = pd.DataFrame({
        'buy_strength': buy_strength,
        'sell_strength': sell_strength,
        'direction': direction,
        'confidence': confidence
    }, index=close.index)

    return result


def get_latest_signal(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    indicators: pd.DataFrame,
    risk_profile: str = "moderate",
    buy_price: Optional[float] = None
) -> dict:
    """
    获取最新交易信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        indicators: 指标数据
        risk_profile: 风险配置
        buy_price: 买入价格

    返回:
        dict: 最新信号信息
            - direction: 交易方向 ("BUY"/"SELL"/"HOLD")
            - confidence: 置信度
            - buy_strength: 买入强度
            - sell_strength: 卖出强度
            - current_price: 当前价格
    """
    signals = generate_signal(
        close, high, low, volume, indicators, risk_profile, buy_price
    )

    latest = signals.iloc[-1]

    direction_map = {1: "BUY", -1: "SELL", 0: "HOLD"}

    return {
        'direction': direction_map.get(int(latest['direction']), "HOLD"),
        'confidence': round(float(latest['confidence']), 4),
        'buy_strength': round(float(latest['buy_strength']), 4),
        'sell_strength': round(float(latest['sell_strength']), 4),
        'current_price': round(float(close.iloc[-1]), 2)
    }


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    print("=" * 60)
    print("信号强度计算测试")
    print("=" * 60)

    # 测试信号强度计算
    print("\n1. 信号强度计算测试:")
    signals = pd.DataFrame({
        'signal_a': [0, 1, 1, 0, 1],
        'signal_b': [0, 0, 1, 1, 1],
        'signal_c': [1, 1, 0, 0, 1]
    }, index=dates[:5])
    weights = {'signal_a': 0.4, 'signal_b': 0.3, 'signal_c': 0.3}
    strength = calc_signal_strength(signals, weights)
    print(f"   信号数据:\n{signals}")
    print(f"   信号强度: {strength.tolist()}")

    # 测试交易方向判断
    print("\n2. 交易方向判断测试:")
    buy_str = pd.Series([0.6, 0.2, 0.4, 0.1, 0.7])
    sell_str = pd.Series([0.1, 0.7, 0.3, 0.2, 0.2])
    direction = get_trade_direction(buy_str, sell_str, 0.3)
    print(f"   买入强度: {buy_str.tolist()}")
    print(f"   卖出强度: {sell_str.tolist()}")
    print(f"   交易方向: {direction.tolist()} (1:买, -1:卖, 0:观望)")

    # 测试置信度
    print("\n3. 置信度计算测试:")
    confidence = get_confidence(buy_str, sell_str, direction)
    print(f"   置信度: {confidence.tolist()}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
