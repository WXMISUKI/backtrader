#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
卖出信号检测模块

包含各种卖出信号的检测函数:
- MA 死叉
- MACD 死叉
- RSI 超买
- KDJ 死叉
- BOLL 上轨压力
- 止损触发
"""

import pandas as pd
import numpy as np
from typing import Optional


def check_ma_death_cross(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """
    检测 MA 死叉信号

    参数:
        fast_ma: 短期均线 (如 MA5)
        slow_ma: 长期均线 (如 MA20)

    返回:
        pd.Series: 信号值 (1: 死叉, 0: 无信号)

    算法:
        死叉: fast_ma < slow_ma 且 前一日 fast_ma >= slow_ma

    示例:
        >>> ma5 = calc_sma(close, 5)
        >>> ma20 = calc_sma(close, 20)
        >>> signal = check_ma_death_cross(ma5, ma20)
    """
    # 当前日: fast < slow
    current_cross = fast_ma < slow_ma
    # 前一日: fast >= slow
    prev_cross = fast_ma.shift(1) >= slow_ma.shift(1)

    # 死叉信号
    signal = (current_cross & prev_cross).astype(int)

    return signal


def check_macd_death_cross(dif: pd.Series, dea: pd.Series) -> pd.Series:
    """
    检测 MACD 死叉信号

    参数:
        dif: DIF 线
        dea: DEA 线

    返回:
        pd.Series: 信号值 (1: 死叉, 0: 无信号)

    算法:
        死叉: dif < dea 且 前一日 dif >= dea

    示例:
        >>> macd = calc_macd(close)
        >>> signal = check_macd_death_cross(macd['dif'], macd['dea'])
    """
    # 当前日: dif < dea
    current_cross = dif < dea
    # 前一日: dif >= dea
    prev_cross = dif.shift(1) >= dea.shift(1)

    # 死叉信号
    signal = (current_cross & prev_cross).astype(int)

    return signal


def check_rsi_overbought(rsi: pd.Series, threshold: int = 70) -> pd.Series:
    """
    检测 RSI 超买信号

    参数:
        rsi: RSI 值序列
        threshold: 超买阈值，默认 70

    返回:
        pd.Series: 信号值 (1: 超买, 0: 无信号)

    算法:
        超买: rsi > threshold

    示例:
        >>> rsi = calc_rsi(close, 14)
        >>> signal = check_rsi_overbought(rsi, 70)
    """
    # 超买信号
    signal = (rsi > threshold).astype(int)

    return signal


def check_kdj_death_cross(k: pd.Series, d: pd.Series) -> pd.Series:
    """
    检测 KDJ 死叉信号

    参数:
        k: K 值
        d: D 值

    返回:
        pd.Series: 信号值 (1: 死叉, 0: 无信号)

    算法:
        死叉: k < d 且 前一日 k >= d

    示例:
        >>> kdj = calc_kdj(high, low, close)
        >>> signal = check_kdj_death_cross(kdj['k'], kdj['d'])
    """
    # 当前日: k < d
    current_cross = k < d
    # 前一日: k >= d
    prev_cross = k.shift(1) >= d.shift(1)

    # 死叉信号
    signal = (current_cross & prev_cross).astype(int)

    return signal


def check_boll_pressure(
    close: pd.Series,
    upper: pd.Series
) -> pd.Series:
    """
    检测 BOLL 上轨压力信号

    参数:
        close: 收盘价
        upper: BOLL 上轨

    返回:
        pd.Series: 信号值 (1: 压力回落, 0: 无信号)

    算法:
        压力回落: close < upper 且 前一日 close >= upper

    示例:
        >>> boll = calc_boll(close)
        >>> signal = check_boll_pressure(close, boll['upper'])
    """
    # 当前日: close < upper
    current_below = close < upper
    # 前一日: close >= upper
    prev_above = close.shift(1) >= upper.shift(1)

    # 压力回落信号
    signal = (current_below & prev_above).astype(int)

    return signal


def check_stop_loss(
    current_price: float,
    buy_price: float,
    stop_loss_pct: float = 0.05
) -> bool:
    """
    检测止损信号

    参数:
        current_price: 当前价格
        buy_price: 买入价格
        stop_loss_pct: 止损百分比，默认 5%

    返回:
        bool: 是否触发止损

    算法:
        止损: (buy_price - current_price) / buy_price > stop_loss_pct

    示例:
        >>> should_stop = check_stop_loss(9.5, 10.0, 0.05)
        >>> # 返回 True，因为亏损 5% 等于阈值
    """
    if buy_price <= 0:
        return False

    loss_pct = (buy_price - current_price) / buy_price
    return loss_pct >= stop_loss_pct


def check_stop_loss_series(
    close: pd.Series,
    buy_price: float,
    stop_loss_pct: float = 0.05
) -> pd.Series:
    """
    检测止损信号 (序列版本)

    参数:
        close: 收盘价序列
        buy_price: 买入价格
        stop_loss_pct: 止损百分比

    返回:
        pd.Series: 信号值 (1: 触发止损, 0: 未触发)
    """
    if buy_price <= 0:
        return pd.Series(0, index=close.index)

    loss_pct = (buy_price - close) / buy_price
    signal = (loss_pct >= stop_loss_pct).astype(int)

    return signal


def get_sell_signals(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    indicators: pd.DataFrame,
    risk_profile: str = "moderate",
    buy_price: Optional[float] = None
) -> pd.DataFrame:
    """
    获取所有卖出信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        indicators: 指标数据
        risk_profile: 风险配置
        buy_price: 买入价格 (用于止损判断)

    返回:
        pd.DataFrame: 包含所有卖出信号的 DataFrame
            - signal_ma_death: MA 死叉
            - signal_macd_death: MACD 死叉
            - signal_rsi_overbought: RSI 超买
            - signal_kdj_death: KDJ 死叉
            - signal_boll_pressure: BOLL 上轨压力
            - signal_stop_loss: 止损触发
            - signal_count: 信号数量
    """
    result = pd.DataFrame(index=close.index)

    # 风险配置对应的 RSI 阈值
    rsi_thresholds = {
        "conservative": 65,
        "moderate": 70,
        "aggressive": 80
    }
    rsi_threshold = rsi_thresholds.get(risk_profile, 70)

    # 止损百分比
    stop_loss_pcts = {
        "conservative": 0.03,
        "moderate": 0.05,
        "aggressive": 0.08
    }
    stop_loss_pct = stop_loss_pcts.get(risk_profile, 0.05)

    # 1. MA 死叉
    if 'ma5' in indicators.columns and 'ma20' in indicators.columns:
        result['signal_ma_death'] = check_ma_death_cross(
            indicators['ma5'], indicators['ma20']
        )
    else:
        result['signal_ma_death'] = 0

    # 2. MACD 死叉
    if 'macd_dif' in indicators.columns and 'macd_dea' in indicators.columns:
        result['signal_macd_death'] = check_macd_death_cross(
            indicators['macd_dif'], indicators['macd_dea']
        )
    else:
        result['signal_macd_death'] = 0

    # 3. RSI 超买
    if 'rsi' in indicators.columns:
        result['signal_rsi_overbought'] = check_rsi_overbought(
            indicators['rsi'], rsi_threshold
        )
    else:
        result['signal_rsi_overbought'] = 0

    # 4. KDJ 死叉
    if 'kdj_k' in indicators.columns and 'kdj_d' in indicators.columns:
        result['signal_kdj_death'] = check_kdj_death_cross(
            indicators['kdj_k'], indicators['kdj_d']
        )
    else:
        result['signal_kdj_death'] = 0

    # 5. BOLL 上轨压力
    if 'boll_upper' in indicators.columns:
        result['signal_boll_pressure'] = check_boll_pressure(
            close, indicators['boll_upper']
        )
    else:
        result['signal_boll_pressure'] = 0

    # 6. 止损
    if buy_price is not None:
        result['signal_stop_loss'] = check_stop_loss_series(
            close, buy_price, stop_loss_pct
        )
    else:
        result['signal_stop_loss'] = 0

    # 计算信号数量
    signal_cols = [col for col in result.columns if col.startswith('signal_')]
    result['signal_count'] = result[signal_cols].sum(axis=1)

    return result


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    # 模拟均线数据 (设计一个死叉场景)
    fast_ma = pd.Series(
        np.concatenate([np.ones(50) * 15, np.ones(50) * 10]),
        index=dates
    )
    slow_ma = pd.Series(np.ones(100) * 12, index=dates)

    print("=" * 60)
    print("卖出信号测试")
    print("=" * 60)

    # 测试 MA 死叉
    print("\n1. MA 死叉测试:")
    signal = check_ma_death_cross(fast_ma, slow_ma)
    print(f"   死叉信号数量: {signal.sum()}")
    print(f"   死叉位置: {signal[signal == 1].index.tolist()}")

    # 测试 RSI 超买
    print("\n2. RSI 超买测试:")
    rsi = pd.Series(
        np.concatenate([np.ones(50) * 50, np.ones(50) * 80]),
        index=dates
    )
    signal = check_rsi_overbought(rsi, 70)
    print(f"   超买信号数量: {signal.sum()}")

    # 测试止损
    print("\n3. 止损测试:")
    print(f"   当前价9.5, 买入价10.0, 止损5%: {check_stop_loss(9.5, 10.0, 0.05)}")
    print(f"   当前价9.4, 买入价10.0, 止损5%: {check_stop_loss(9.4, 10.0, 0.05)}")
    print(f"   当前价9.6, 买入价10.0, 止损5%: {check_stop_loss(9.6, 10.0, 0.05)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
