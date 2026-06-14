#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
买入信号检测模块

包含各种买入信号的检测函数:
- MA 金叉
- MACD 金叉
- RSI 超卖反弹
- KDJ 金叉
- BOLL 下轨支撑
- 放量突破
"""

import pandas as pd
import numpy as np
from typing import Optional


def check_ma_cross(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """
    检测 MA 金叉信号

    参数:
        fast_ma: 短期均线 (如 MA5)
        slow_ma: 长期均线 (如 MA20)

    返回:
        pd.Series: 信号值 (1: 金叉, 0: 无信号)

    算法:
        金叉: fast_ma > slow_ma 且 前一日 fast_ma <= slow_ma

    示例:
        >>> ma5 = calc_sma(close, 5)
        >>> ma20 = calc_sma(close, 20)
        >>> signal = check_ma_cross(ma5, ma20)
    """
    # 当前日: fast > slow
    current_cross = fast_ma > slow_ma
    # 前一日: fast <= slow
    prev_cross = fast_ma.shift(1) <= slow_ma.shift(1)

    # 金叉信号
    signal = (current_cross & prev_cross).astype(int)

    return signal


def check_macd_cross(dif: pd.Series, dea: pd.Series) -> pd.Series:
    """
    检测 MACD 金叉信号

    参数:
        dif: DIF 线
        dea: DEA 线

    返回:
        pd.Series: 信号值 (1: 金叉, 0: 无信号)

    算法:
        金叉: dif > dea 且 前一日 dif <= dea

    示例:
        >>> macd = calc_macd(close)
        >>> signal = check_macd_cross(macd['dif'], macd['dea'])
    """
    # 当前日: dif > dea
    current_cross = dif > dea
    # 前一日: dif <= dea
    prev_cross = dif.shift(1) <= dea.shift(1)

    # 金叉信号
    signal = (current_cross & prev_cross).astype(int)

    return signal


def check_rsi_oversold(rsi: pd.Series, threshold: int = 30) -> pd.Series:
    """
    检测 RSI 超卖反弹信号

    参数:
        rsi: RSI 值序列
        threshold: 超卖阈值，默认 30

    返回:
        pd.Series: 信号值 (1: 超卖反弹, 0: 无信号)

    算法:
        超卖反弹: rsi > threshold 且 前一日 rsi <= threshold

    示例:
        >>> rsi = calc_rsi(close, 14)
        >>> signal = check_rsi_oversold(rsi, 30)
    """
    # 当前日: rsi > threshold
    current_above = rsi > threshold
    # 前一日: rsi <= threshold
    prev_below = rsi.shift(1) <= threshold

    # 超卖反弹信号
    signal = (current_above & prev_below).astype(int)

    return signal


def check_kdj_cross(k: pd.Series, d: pd.Series) -> pd.Series:
    """
    检测 KDJ 金叉信号

    参数:
        k: K 值
        d: D 值

    返回:
        pd.Series: 信号值 (1: 金叉, 0: 无信号)

    算法:
        金叉: k > d 且 前一日 k <= d

    示例:
        >>> kdj = calc_kdj(high, low, close)
        >>> signal = check_kdj_cross(kdj['k'], kdj['d'])
    """
    # 当前日: k > d
    current_cross = k > d
    # 前一日: k <= d
    prev_cross = k.shift(1) <= d.shift(1)

    # 金叉信号
    signal = (current_cross & prev_cross).astype(int)

    return signal


def check_boll_support(
    close: pd.Series,
    lower: pd.Series
) -> pd.Series:
    """
    检测 BOLL 下轨支撑信号

    参数:
        close: 收盘价
        lower: BOLL 下轨

    返回:
        pd.Series: 信号值 (1: 支撑反弹, 0: 无信号)

    算法:
        支撑反弹: close > lower 且 前一日 close <= lower

    示例:
        >>> boll = calc_boll(close)
        >>> signal = check_boll_support(close, boll['lower'])
    """
    # 当前日: close > lower
    current_above = close > lower
    # 前一日: close <= lower
    prev_below = close.shift(1) <= lower.shift(1)

    # 支撑反弹信号
    signal = (current_above & prev_below).astype(int)

    return signal


def check_volume_breakout(
    volume: pd.Series,
    vol_ma: pd.Series,
    ratio: float = 1.5
) -> pd.Series:
    """
    检测放量突破信号

    参数:
        volume: 成交量
        vol_ma: 成交量均线
        ratio: 放量倍数，默认 1.5

    返回:
        pd.Series: 信号值 (1: 放量, 0: 无信号)

    算法:
        放量: volume > vol_ma * ratio

    示例:
        >>> vol_ma5 = calc_vol_ma(volume, 5)
        >>> signal = check_volume_breakout(volume, vol_ma5, 1.5)
    """
    # 放量信号
    signal = (volume > vol_ma * ratio).astype(int)

    return signal


def get_buy_signals(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    indicators: pd.DataFrame,
    risk_profile: str = "moderate"
) -> pd.DataFrame:
    """
    获取所有买入信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        indicators: 指标数据 (来自 IndicatorCalculator)
        risk_profile: 风险配置

    返回:
        pd.DataFrame: 包含所有买入信号的 DataFrame
            - signal_ma_cross: MA 金叉
            - signal_macd_cross: MACD 金叉
            - signal_rsi_oversold: RSI 超卖反弹
            - signal_kdj_cross: KDJ 金叉
            - signal_boll_support: BOLL 下轨支撑
            - signal_volume: 放量突破
            - signal_count: 信号数量
    """
    result = pd.DataFrame(index=close.index)

    # 风险配置对应的 RSI 阈值
    rsi_thresholds = {
        "conservative": 35,
        "moderate": 30,
        "aggressive": 20
    }
    rsi_threshold = rsi_thresholds.get(risk_profile, 30)

    # 放量倍数
    volume_ratios = {
        "conservative": 2.0,
        "moderate": 1.5,
        "aggressive": 1.2
    }
    volume_ratio = volume_ratios.get(risk_profile, 1.5)

    # 1. MA 金叉
    if 'ma5' in indicators.columns and 'ma20' in indicators.columns:
        result['signal_ma_cross'] = check_ma_cross(
            indicators['ma5'], indicators['ma20']
        )
    else:
        result['signal_ma_cross'] = 0

    # 2. MACD 金叉
    if 'macd_dif' in indicators.columns and 'macd_dea' in indicators.columns:
        result['signal_macd_cross'] = check_macd_cross(
            indicators['macd_dif'], indicators['macd_dea']
        )
    else:
        result['signal_macd_cross'] = 0

    # 3. RSI 超卖反弹
    if 'rsi' in indicators.columns:
        result['signal_rsi_oversold'] = check_rsi_oversold(
            indicators['rsi'], rsi_threshold
        )
    else:
        result['signal_rsi_oversold'] = 0

    # 4. KDJ 金叉
    if 'kdj_k' in indicators.columns and 'kdj_d' in indicators.columns:
        result['signal_kdj_cross'] = check_kdj_cross(
            indicators['kdj_k'], indicators['kdj_d']
        )
    else:
        result['signal_kdj_cross'] = 0

    # 5. BOLL 下轨支撑
    if 'boll_lower' in indicators.columns:
        result['signal_boll_support'] = check_boll_support(
            close, indicators['boll_lower']
        )
    else:
        result['signal_boll_support'] = 0

    # 6. 放量突破
    if 'vol_ma5' in indicators.columns:
        result['signal_volume'] = check_volume_breakout(
            volume, indicators['vol_ma5'], volume_ratio
        )
    else:
        result['signal_volume'] = 0

    # 计算信号数量
    signal_cols = [col for col in result.columns if col.startswith('signal_')]
    result['signal_count'] = result[signal_cols].sum(axis=1)

    return result


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    # 模拟均线数据 (设计一个金叉场景)
    fast_ma = pd.Series(
        np.concatenate([np.ones(50) * 10, np.ones(50) * 15]),
        index=dates
    )
    slow_ma = pd.Series(np.ones(100) * 12, index=dates)

    print("=" * 60)
    print("买入信号测试")
    print("=" * 60)

    # 测试 MA 金叉
    print("\n1. MA 金叉测试:")
    signal = check_ma_cross(fast_ma, slow_ma)
    print(f"   金叉信号数量: {signal.sum()}")
    print(f"   金叉位置: {signal[signal == 1].index.tolist()}")

    # 测试 MACD 金叉
    print("\n2. MACD 金叉测试:")
    dif = pd.Series(np.concatenate([np.ones(50) * -1, np.ones(50) * 1]), index=dates)
    dea = pd.Series(np.zeros(100), index=dates)
    signal = check_macd_cross(dif, dea)
    print(f"   金叉信号数量: {signal.sum()}")

    # 测试 RSI 超卖反弹
    print("\n3. RSI 超卖反弹测试:")
    rsi = pd.Series(
        np.concatenate([np.ones(50) * 25, np.ones(50) * 50]),
        index=dates
    )
    signal = check_rsi_oversold(rsi, 30)
    print(f"   超卖反弹信号数量: {signal.sum()}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
