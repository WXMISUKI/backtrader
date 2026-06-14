#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量价指标计算模块

包含:
- VOL MA: 成交量移动平均
- OBV: 能量潮
- VWAP: 成交量加权平均价
- 换手率计算
"""

import pandas as pd
import numpy as np
from typing import Optional


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


def calc_vol_ma(volume: pd.Series, period: int = 5) -> pd.Series:
    """
    计算成交量移动平均

    参数:
        volume: 成交量序列
        period: 计算周期，默认 5

    返回:
        pd.Series: 成交量 MA 值

    应用:
        - 量价齐升: 趋势确认
        - 量价背离: 趋势可能反转
        - 放量突破: 有效突破
        - 缩量回调: 调整可能结束

    示例:
        >>> vol_ma5 = calc_vol_ma(df['volume'], 5)
        >>> vol_ma10 = calc_vol_ma(df['volume'], 10)
        >>> # 放量信号
        >>> high_volume = df['volume'] > vol_ma5 * 1.5
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    validate_input(volume, period, "volume")

    # 计算移动平均
    return volume.rolling(window=period, min_periods=period).mean()


def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算 OBV 指标 (On Balance Volume，能量潮)

    参数:
        close: 收盘价序列
        volume: 成交量序列

    返回:
        pd.Series: OBV 值序列

    算法:
        如果 C > C(-1): OBV = OBV(-1) + V  (上涨，资金流入)
        如果 C < C(-1): OBV = OBV(-1) - V  (下跌，资金流出)
        如果 C = C(-1): OBV = OBV(-1)      (平盘，不变)

    应用:
        - OBV 上升: 资金流入，看多
        - OBV 下降: 资金流出，看空
        - OBV 与价格背离: 趋势可能反转
            - 价格创新高，OBV 未创新高: 顶背离
            - 价格创新低，OBV 未创新低: 底背离

    示例:
        >>> obv = calc_obv(df['close'], df['volume'])
        >>> # OBV 趋势
        >>> obv_ma = calc_vol_ma(obv, 20)
        >>> obv_trend = obv > obv_ma
    """
    # 参数验证
    validate_input(close, 2, "close")
    validate_input(volume, 2, "volume")

    # 检查索引是否一致
    if not close.index.equals(volume.index):
        raise ValueError("close 和 volume 的索引必须一致")

    # 计算价格变化方向
    price_diff = close.diff()

    # 计算 OBV
    # 上涨加成交量，下跌减成交量，平盘不变
    obv_change = pd.Series(0.0, index=close.index)
    obv_change[price_diff > 0] = volume[price_diff > 0]
    obv_change[price_diff < 0] = -volume[price_diff < 0]

    # 累积求和
    obv = obv_change.cumsum()

    return obv


def calc_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: Optional[int] = None
) -> pd.Series:
    """
    计算 VWAP (Volume Weighted Average Price，成交量加权平均价)

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        volume: 成交量序列
        period: 计算周期，None 表示从开始累积

    返回:
        pd.Series: VWAP 值序列

    算法:
        典型价格 TP = (H + L + C) / 3
        VWAP = cumsum(TP * V) / cumsum(V)

    应用:
        - 价格 > VWAP: 看多
        - 价格 < VWAP: 看空
        - VWAP 支撑/阻力

    示例:
        >>> vwap = calc_vwap(df['high'], df['low'], df['close'], df['volume'])
        >>> # 判断价格位置
        >>> above_vwap = df['close'] > vwap
    """
    # 参数验证
    validate_input(close, 1, "close")
    validate_input(volume, 1, "volume")

    # 检查索引是否一致
    if not (high.index.equals(low.index) and low.index.equals(close.index) and close.index.equals(volume.index)):
        raise ValueError("high, low, close, volume 的索引必须一致")

    # 计算典型价格
    tp = (high + low + close) / 3

    # 计算 TP * V
    tp_volume = tp * volume

    if period is None:
        # 从开始累积
        vwap = tp_volume.cumsum() / volume.cumsum()
    else:
        # 滚动窗口
        if not isinstance(period, int) or period < 1:
            raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")
        vwap = tp_volume.rolling(window=period).sum() / volume.rolling(window=period).sum()

    return vwap


def calc_turnover_rate(
    volume: pd.Series,
    total_shares: float
) -> pd.Series:
    """
    计算换手率

    参数:
        volume: 成交量序列 (股数)
        total_shares: 总股本 (股数)

    返回:
        pd.Series: 换手率序列 (百分比)

    算法:
        换手率 = 成交量 / 总股本 * 100%

    应用:
        - 换手率 > 10%: 高度活跃，可能见顶
        - 换手率 > 5%: 较为活跃
        - 换手率 < 1%: 低迷，可能见底

    示例:
        >>> turnover = calc_turnover_rate(df['volume'], 1000000000)
        >>> # 高换手率信号
        >>> high_turnover = turnover > 10
    """
    # 参数验证
    validate_input(volume, 1, "volume")

    if not isinstance(total_shares, (int, float)) or total_shares <= 0:
        raise InvalidParameterError(f"total_shares 必须是正数，实际值: {total_shares}")

    # 计算换手率
    turnover = (volume / total_shares) * 100

    return turnover


def calc_volume_ratio(volume: pd.Series, period: int = 5) -> pd.Series:
    """
    计算量比

    参数:
        volume: 成交量序列
        period: 计算周期，默认 5

    返回:
        pd.Series: 量比值

    算法:
        量比 = 当日成交量 / 过去 N 日平均成交量

    应用:
        - 量比 > 2: 明显放量
        - 量比 > 3: 巨量
        - 量比 < 0.5: 明显缩量

    示例:
        >>> vol_ratio = calc_volume_ratio(df['volume'], 5)
        >>> # 放量信号
        >>> high_volume = vol_ratio > 2
    """
    # 参数验证
    if not isinstance(period, int) or period < 1:
        raise InvalidParameterError(f"period 必须是正整数，实际值: {period}")

    validate_input(volume, period + 1, "volume")

    # 计算过去 N 日平均成交量
    vol_ma = volume.rolling(window=period, min_periods=period).mean()

    # 计算量比
    volume_ratio = volume / vol_ma

    return volume_ratio


# 便捷函数：获取所有量价指标
def calc_all_volume(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    vol_ma_periods: list = [5, 10],
    total_shares: Optional[float] = None
) -> pd.DataFrame:
    """
    计算所有量价指标

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        volume: 成交量序列
        vol_ma_periods: 成交量 MA 周期列表，默认 [5, 10]
        total_shares: 总股本 (用于计算换手率)

    返回:
        pd.DataFrame: 包含所有量价指标的 DataFrame
    """
    result = pd.DataFrame(index=close.index)

    # 计算各周期成交量 MA
    for period in vol_ma_periods:
        result[f'vol_ma{period}'] = calc_vol_ma(volume, period)

    # 计算 OBV
    result['obv'] = calc_obv(close, volume)

    # 计算 VWAP
    result['vwap'] = calc_vwap(high, low, close, volume)

    # 计算量比
    result['volume_ratio'] = calc_volume_ratio(volume, 5)

    # 计算换手率 (如果提供了总股本)
    if total_shares is not None:
        result['turnover_rate'] = calc_turnover_rate(volume, total_shares)

    return result


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    # 模拟 OHLCV 数据
    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high = pd.Series(base_price + np.random.rand(100) * 2, index=dates, name='high')
    low = pd.Series(base_price - np.random.rand(100) * 2, index=dates, name='low')
    close = pd.Series(base_price + np.random.randn(100) * 0.3, index=dates, name='close')
    volume = pd.Series(np.random.randint(1000000, 10000000, 100), index=dates, name='volume')

    print("=" * 60)
    print("量价指标计算测试")
    print("=" * 60)

    # 测试 VOL MA
    print("\n1. VOL MA 测试:")
    vol_ma5 = calc_vol_ma(volume, 5)
    vol_ma10 = calc_vol_ma(volume, 10)
    print(f"   VOL MA5 最后5个值:\n{vol_ma5.tail()}")
    print(f"   VOL MA10 最后5个值:\n{vol_ma10.tail()}")

    # 测试 OBV
    print("\n2. OBV 测试:")
    obv = calc_obv(close, volume)
    print(f"   OBV 最后5个值:\n{obv.tail()}")

    # 测试 VWAP
    print("\n3. VWAP 测试:")
    vwap = calc_vwap(high, low, close, volume)
    print(f"   VWAP 最后5个值:\n{vwap.tail()}")

    # 测试换手率
    print("\n4. 换手率测试:")
    total_shares = 1000000000  # 10亿股
    turnover = calc_turnover_rate(volume, total_shares)
    print(f"   换手率 最后5个值:\n{turnover.tail()}")
    print(f"   高换手率 (>5%): {(turnover > 5).sum()} 个")

    # 测试量比
    print("\n5. 量比测试:")
    volume_ratio = calc_volume_ratio(volume, 5)
    print(f"   量比 最后5个值:\n{volume_ratio.tail()}")
    print(f"   放量信号 (>2): {(volume_ratio > 2).sum()} 个")
    print(f"   缩量信号 (<0.5): {(volume_ratio < 0.5).sum()} 个")

    # 测试批量计算
    print("\n6. 批量计算测试:")
    all_volume = calc_all_volume(high, low, close, volume, total_shares=total_shares)
    print(f"   所有指标列名: {list(all_volume.columns)}")
    print(f"   数据形状: {all_volume.shape}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
