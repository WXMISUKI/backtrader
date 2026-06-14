#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
震荡指标计算模块

包含:
- RSI: 相对强弱指数
- KDJ: 随机指标
- CCI: 商品通道指数
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


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
    """
    if not isinstance(data, pd.Series):
        raise TypeError(f"{name} 必须是 pandas.Series 类型，实际类型: {type(data)}")

    if len(data) < min_length:
        raise InsufficientDataError(
            f"{name} 长度不足，需要至少 {min_length} 个数据点，实际只有 {len(data)} 个"
        )

    if data.isnull().all():
        raise ValueError(f"{name} 全部为 NaN")


def calc_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI 指标 (Relative Strength Index)

    参数:
        data: 价格序列 (通常是收盘价)
        period: 计算周期，默认 14

    返回:
        pd.Series: RSI 值序列 (0-100)

    算法:
        1. 计算价格变化: diff = C - C(-1)
        2. 分离涨跌: gain = max(diff, 0), loss = max(-diff, 0)
        3. 计算平均涨跌: avg_gain = SMA(gain, N), avg_loss = SMA(loss, N)
        4. 计算相对强度: RS = avg_gain / avg_loss
        5. 计算 RSI: RSI = 100 - (100 / (1 + RS))

    应用:
        - RSI > 70: 超买区域，可能回调
        - RSI < 30: 超卖区域，可能反弹
        - RSI 背离: 趋势可能反转
        - RSI 50 线: 多空分界

    阈值 (可配置):
        - 超买: 70 (激进型: 80)
        - 超卖: 30 (激进型: 20)

    示例:
        >>> rsi = calc_rsi(df['close'], 14)
        >>> # 超买信号
        >>> overbought = rsi > 70
        >>> # 超卖信号
        >>> oversold = rsi < 30
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    validate_input(data, period + 1, "data")

    # 计算价格变化
    diff = data.diff()

    # 分离涨跌
    gain = diff.clip(lower=0)  # 上涨
    loss = (-diff).clip(lower=0)  # 下跌

    # 计算平均涨跌 (使用 EMA 平滑)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    # 计算相对强度 RS
    rs = avg_gain / avg_loss

    # 计算 RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calc_kdj(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> pd.DataFrame:
    """
    计算 KDJ 指标 (随机指标)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        n: RSV 周期，默认 9
        m1: K 值平滑周期，默认 3
        m2: D 值平滑周期，默认 3

    返回:
        pd.DataFrame: 包含以下列
            - k: K 值
            - d: D 值
            - j: J 值 (3K - 2D)

    算法:
        1. RSV = (C - Ln) / (Hn - Ln) * 100
           其中 C 为当前收盘价，Ln 为 N 日最低价，Hn 为 N 日最高价
        2. K = SMA(RSV, M1)  (实际上是 EMA)
        3. D = SMA(K, M2)
        4. J = 3 * K - 2 * D

    应用:
        - K 上穿 D: 买入信号 (金叉)
        - K 下穿 D: 卖出信号 (死叉)
        - J > 100: 超买
        - J < 0: 超卖
        - K/D 在 20 以下: 超卖区域
        - K/D 在 80 以上: 超买区域

    示例:
        >>> kdj = calc_kdj(df['high'], df['low'], df['close'])
        >>> # 金叉信号
        >>> golden_cross = (kdj['k'] > kdj['d']) & (kdj['k'].shift(1) <= kdj['d'].shift(1))
        >>> # 超买超卖
        >>> overbought = kdj['j'] > 100
        >>> oversold = kdj['j'] < 0
    """
    # 参数验证
    if not isinstance(n, int) or n < 1:
        raise InvalidParameterError(f"n 必须是正整数，实际值: {n}")
    if not isinstance(m1, int) or m1 < 1:
        raise InvalidParameterError(f"m1 必须是正整数，实际值: {m1}")
    if not isinstance(m2, int) or m2 < 1:
        raise InvalidParameterError(f"m2 必须是正整数，实际值: {m2}")

    # 验证所有输入
    validate_input(high, n, "high")
    validate_input(low, n, "low")
    validate_input(close, n, "close")

    # 检查索引是否一致
    if not (high.index.equals(low.index) and low.index.equals(close.index)):
        raise ValueError("high, low, close 的索引必须一致")

    # 计算 N 日最高价和最低价
    low_n = low.rolling(window=n, min_periods=n).min()
    high_n = high.rolling(window=n, min_periods=n).max()

    # 计算 RSV
    rsv = ((close - low_n) / (high_n - low_n)) * 100

    # 处理除零情况 (当 high_n == low_n 时)
    rsv = rsv.replace([np.inf, -np.inf], np.nan)

    # 计算 K 值 (使用 EMA 平滑)
    k = rsv.ewm(span=m1, adjust=False).mean()

    # 计算 D 值 (使用 EMA 平滑)
    d = k.ewm(span=m2, adjust=False).mean()

    # 计算 J 值
    j = 3 * k - 2 * d

    # 组合成 DataFrame
    result = pd.DataFrame({
        'k': k,
        'd': d,
        'j': j
    }, index=high.index)

    return result


def calc_cci(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    计算 CCI 指标 (Commodity Channel Index)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 计算周期，默认 14

    返回:
        pd.Series: CCI 值序列

    算法:
        1. TP = (H + L + C) / 3 (典型价格)
        2. MA_TP = SMA(TP, N)
        3. MD = mean(abs(TP - MA_TP))
        4. CCI = (TP - MA_TP) / (0.015 * MD)

    应用:
        - CCI > 100: 超买
        - CCI < -100: 超卖
        - CCI 穿越 0: 趋势变化
        - CCI 背离: 趋势可能反转

    示例:
        >>> cci = calc_cci(df['high'], df['low'], df['close'], 14)
        >>> # 超买信号
        >>> overbought = cci > 100
        >>> # 超卖信号
        >>> oversold = cci < -100
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    # 验证所有输入
    validate_input(high, period, "high")
    validate_input(low, period, "low")
    validate_input(close, period, "close")

    # 检查索引是否一致
    if not (high.index.equals(low.index) and low.index.equals(close.index)):
        raise ValueError("high, low, close 的索引必须一致")

    # 计算典型价格 TP
    tp = (high + low + close) / 3

    # 计算 TP 的移动平均
    ma_tp = tp.rolling(window=period, min_periods=period).mean()

    # 计算平均偏差 MD
    md = tp.rolling(window=period, min_periods=period).apply(
        lambda x: np.mean(np.abs(x - x.mean())),
        raw=True
    )

    # 计算 CCI
    cci = (tp - ma_tp) / (0.015 * md)

    return cci


def calc_williams_r(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    计算威廉指标 (Williams %R)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 计算周期，默认 14

    返回:
        pd.Series: Williams %R 值序列 (-100 到 0)

    算法:
        %R = (Hn - C) / (Hn - Ln) * (-100)
        其中 Hn 为 N 日最高价，Ln 为 N 日最低价

    应用:
        %R > -20: 超买
        %R < -80: 超卖
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    # 验证所有输入
    validate_input(high, period, "high")
    validate_input(low, period, "low")
    validate_input(close, period, "close")

    # 计算 N 日最高价和最低价
    high_n = high.rolling(window=period, min_periods=period).max()
    low_n = low.rolling(window=period, min_periods=period).min()

    # 计算 Williams %R
    williams_r = ((high_n - close) / (high_n - low_n)) * (-100)

    return williams_r


# 便捷函数：获取所有震荡指标
def calc_all_oscillator(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    rsi_period: int = 14,
    kdj_params: tuple = (9, 3, 3),
    cci_period: int = 14
) -> pd.DataFrame:
    """
    计算所有震荡指标

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        rsi_period: RSI 周期，默认 14
        kdj_params: KDJ 参数，默认 (9, 3, 3)
        cci_period: CCI 周期，默认 14

    返回:
        pd.DataFrame: 包含所有震荡指标的 DataFrame
    """
    result = pd.DataFrame(index=close.index)

    # 计算 RSI
    result['rsi'] = calc_rsi(close, rsi_period)

    # 计算 KDJ
    kdj = calc_kdj(high, low, close, *kdj_params)
    result['kdj_k'] = kdj['k']
    result['kdj_d'] = kdj['d']
    result['kdj_j'] = kdj['j']

    # 计算 CCI
    result['cci'] = calc_cci(high, low, close, cci_period)

    # 计算 Williams %R
    result['williams_r'] = calc_williams_r(high, low, close, rsi_period)

    return result


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    # 模拟 OHLC 数据
    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high = pd.Series(base_price + np.random.rand(100) * 2, index=dates, name='high')
    low = pd.Series(base_price - np.random.rand(100) * 2, index=dates, name='low')
    close = pd.Series(base_price + np.random.randn(100) * 0.3, index=dates, name='close')

    print("=" * 60)
    print("震荡指标计算测试")
    print("=" * 60)

    # 测试 RSI
    print("\n1. RSI 测试:")
    rsi = calc_rsi(close, 14)
    print(f"   RSI 最后5个值:\n{rsi.tail()}")
    print(f"   超买信号 (RSI>70): {(rsi > 70).sum()} 个")
    print(f"   超卖信号 (RSI<30): {(rsi < 30).sum()} 个")

    # 测试 KDJ
    print("\n2. KDJ 测试:")
    kdj = calc_kdj(high, low, close)
    print(f"   KDJ 最后5个值:\n{kdj.tail()}")
    print(f"   J>100 (超买): {(kdj['j'] > 100).sum()} 个")
    print(f"   J<0 (超卖): {(kdj['j'] < 0).sum()} 个")

    # 测试 CCI
    print("\n3. CCI 测试:")
    cci = calc_cci(high, low, close, 14)
    print(f"   CCI 最后5个值:\n{cci.tail()}")
    print(f"   CCI>100 (超买): {(cci > 100).sum()} 个")
    print(f"   CCI<-100 (超卖): {(cci < -100).sum()} 个")

    # 测试 Williams %R
    print("\n4. Williams %R 测试:")
    williams_r = calc_williams_r(high, low, close, 14)
    print(f"   Williams %R 最后5个值:\n{williams_r.tail()}")

    # 测试批量计算
    print("\n5. 批量计算测试:")
    all_oscillator = calc_all_oscillator(high, low, close)
    print(f"   所有指标列名: {list(all_oscillator.columns)}")
    print(f"   数据形状: {all_oscillator.shape}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
