#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
趋势指标计算模块

包含:
- SMA: 简单移动平均线
- EMA: 指数移动平均线
- MACD: 移动平均收敛发散
- BOLL: 布林带
"""

import pandas as pd
import numpy as np
from typing import Optional, Union


class InsufficientDataError(Exception):
    """数据不足异常"""
    pass


class InvalidParameterError(Exception):
    """参数无效异常"""
    pass


def validate_input(data: pd.Series, min_length: int, name: str = "data") -> None:
    """
    验证输入数据

    参数:
        data: 输入数据序列
        min_length: 最小数据长度
        name: 数据名称 (用于错误提示)

    异常:
        TypeError: 数据类型错误
        InsufficientDataError: 数据长度不足
        ValueError: 数据全部为 NaN
    """
    if not isinstance(data, pd.Series):
        raise TypeError(f"{name} 必须是 pandas.Series 类型，实际类型: {type(data)}")

    if len(data) < min_length:
        raise InsufficientDataError(
            f"{name} 长度不足，需要至少 {min_length} 个数据点，实际只有 {len(data)} 个"
        )

    if data.isnull().all():
        raise ValueError(f"{name} 全部为 NaN")


def calc_sma(data: pd.Series, period: int) -> pd.Series:
    """
    计算简单移动平均线 (Simple Moving Average)

    参数:
        data: 价格序列 (通常是收盘价)
        period: 计算周期 (如 5, 10, 20, 60)

    返回:
        pd.Series: SMA 值序列，前 period-1 个值为 NaN

    示例:
        >>> sma5 = calc_sma(df['close'], 5)
        >>> sma20 = calc_sma(df['close'], 20)

    算法:
        SMA(N) = (C1 + C2 + ... + CN) / N
        其中 C 为收盘价，N 为周期

    应用:
        - 判断趋势方向
        - 支撑位和阻力位
        - 金叉死叉信号
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    validate_input(data, period, "data")

    # 计算 SMA
    return data.rolling(window=period, min_periods=period).mean()


def calc_ema(data: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线 (Exponential Moving Average)

    参数:
        data: 价格序列
        period: 计算周期

    返回:
        pd.Series: EMA 值序列

    算法:
        EMA(N) = C * K + EMA(yesterday) * (1 - K)
        其中 K = 2 / (N + 1)

    特点:
        - 对近期价格赋予更高权重
        - 比 SMA 更灵敏
        - 趋势跟踪效果更好
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    validate_input(data, period, "data")

    # 计算 EMA
    return data.ewm(span=period, adjust=False).mean()


def calc_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """
    计算 MACD 指标 (Moving Average Convergence Divergence)

    参数:
        data: 价格序列 (通常是收盘价)
        fast_period: 快线周期，默认 12
        slow_period: 慢线周期，默认 26
        signal_period: 信号线周期，默认 9

    返回:
        pd.DataFrame: 包含以下列
            - dif: 快线与慢线的差值
            - dea: DIF 的 EMA (信号线)
            - macd: (DIF - DEA) * 2 (柱状图)

    算法:
        DIF = EMA(fast) - EMA(slow)
        DEA = EMA(DIF, signal)
        MACD = (DIF - DEA) * 2

    应用:
        - DIF 上穿 DEA: 买入信号 (金叉)
        - DIF 下穿 DEA: 卖出信号 (死叉)
        - MACD 柱状图: 动量强弱
        - DIF 与价格背离: 趋势可能反转

    示例:
        >>> macd = calc_macd(df['close'])
        >>> # 金叉信号: dif 上穿 dea
        >>> golden_cross = (macd['dif'] > macd['dea']) & (macd['dif'].shift(1) <= macd['dea'].shift(1))
    """
    # 参数验证
    if not isinstance(fast_period, int) or fast_period < 1:
        raise InvalidParameterError(f"fast_period 必须是正整数，实际值: {fast_period}")
    if not isinstance(slow_period, int) or slow_period < 1:
        raise InvalidParameterError(f"slow_period 必须是正整数，实际值: {slow_period}")
    if not isinstance(signal_period, int) or signal_period < 1:
        raise InvalidParameterError(f"signal_period 必须是正整数，实际值: {signal_period}")
    if fast_period >= slow_period:
        raise InvalidParameterError(f"fast_period ({fast_period}) 必须小于 slow_period ({slow_period})")

    validate_input(data, slow_period, "data")

    # 计算快线和慢线的 EMA
    ema_fast = calc_ema(data, fast_period)
    ema_slow = calc_ema(data, slow_period)

    # 计算 DIF
    dif = ema_fast - ema_slow

    # 计算 DEA (DIF 的 EMA)
    dea = dif.ewm(span=signal_period, adjust=False).mean()

    # 计算 MACD 柱状图
    macd = (dif - dea) * 2

    # 组合成 DataFrame
    result = pd.DataFrame({
        'dif': dif,
        'dea': dea,
        'macd': macd
    }, index=data.index)

    return result


def calc_boll(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:
    """
    计算布林带 (Bollinger Bands)

    参数:
        data: 价格序列 (通常是收盘价)
        period: 移动平均周期，默认 20
        std_dev: 标准差倍数，默认 2.0

    返回:
        pd.DataFrame: 包含以下列
            - upper: 上轨
            - middle: 中轨 (SMA)
            - lower: 下轨
            - bandwidth: 带宽 (上轨-下轨)/中轨

    算法:
        中轨 = SMA(N)
        标准差 = STD(CLOSE, N)
        上轨 = 中轨 + K * 标准差
        下轨 = 中轨 - K * 标准差

    应用:
        - 价格触及上轨: 可能超买，考虑卖出
        - 价格触及下轨: 可能超卖，考虑买入
        - 带宽收窄: 可能变盘，注意突破方向
        - 价格突破上轨: 强势信号
        - 价格跌破下轨: 弱势信号

    示例:
        >>> boll = calc_boll(df['close'], 20, 2.0)
        >>> # 判断价格位置
        >>> above_upper = df['close'] > boll['upper']
        >>> below_lower = df['close'] < boll['lower']
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")
    if not isinstance(std_dev, (int, float)) or std_dev <= 0:
        raise InvalidParameterError(f"std_dev 必须是正数，实际值: {std_dev}")

    validate_input(data, period, "data")

    # 计算中轨 (SMA)
    middle = calc_sma(data, period)

    # 计算标准差
    std = data.rolling(window=period, min_periods=period).std()

    # 计算上轨和下轨
    upper = middle + std_dev * std
    lower = middle - std_dev * std

    # 计算带宽
    bandwidth = (upper - lower) / middle

    # 组合成 DataFrame
    result = pd.DataFrame({
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'bandwidth': bandwidth
    }, index=data.index)

    return result


# 便捷函数：获取所有趋势指标
def calc_all_trend(
    close: pd.Series,
    ma_periods: list = [5, 10, 20, 60],
    macd_params: tuple = (12, 26, 9),
    boll_params: tuple = (20, 2.0)
) -> pd.DataFrame:
    """
    计算所有趋势指标

    参数:
        close: 收盘价序列
        ma_periods: MA 周期列表，默认 [5, 10, 20, 60]
        macd_params: MACD 参数，默认 (12, 26, 9)
        boll_params: BOLL 参数，默认 (20, 2.0)

    返回:
        pd.DataFrame: 包含所有趋势指标的 DataFrame
    """
    result = pd.DataFrame(index=close.index)

    # 计算各周期 MA
    for period in ma_periods:
        result[f'ma{period}'] = calc_sma(close, period)

    # 计算 MACD
    macd = calc_macd(close, *macd_params)
    result['macd_dif'] = macd['dif']
    result['macd_dea'] = macd['dea']
    result['macd_hist'] = macd['macd']

    # 计算 BOLL
    boll = calc_boll(close, *boll_params)
    result['boll_upper'] = boll['upper']
    result['boll_middle'] = boll['middle']
    result['boll_lower'] = boll['lower']

    return result


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    prices = pd.Series(
        np.cumsum(np.random.randn(100) * 0.5) + 100,
        index=dates,
        name='close'
    )

    print("=" * 60)
    print("趋势指标计算测试")
    print("=" * 60)

    # 测试 SMA
    print("\n1. SMA 测试:")
    sma5 = calc_sma(prices, 5)
    sma20 = calc_sma(prices, 20)
    print(f"   SMA5 最后5个值:\n{sma5.tail()}")
    print(f"   SMA20 最后5个值:\n{sma20.tail()}")

    # 测试 EMA
    print("\n2. EMA 测试:")
    ema12 = calc_ema(prices, 12)
    print(f"   EMA12 最后5个值:\n{ema12.tail()}")

    # 测试 MACD
    print("\n3. MACD 测试:")
    macd = calc_macd(prices)
    print(f"   MACD 最后5个值:\n{macd.tail()}")

    # 测试 BOLL
    print("\n4. BOLL 测试:")
    boll = calc_boll(prices)
    print(f"   BOLL 最后5个值:\n{boll.tail()}")

    # 测试批量计算
    print("\n5. 批量计算测试:")
    all_trend = calc_all_trend(prices)
    print(f"   所有指标列名: {list(all_trend.columns)}")
    print(f"   数据形状: {all_trend.shape}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
