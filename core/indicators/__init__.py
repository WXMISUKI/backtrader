#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技术指标计算模块

提供各种股票技术指标的计算功能

模块结构:
- trend.py: 趋势指标 (SMA, EMA, MACD, BOLL)
- oscillator.py: 震荡指标 (RSI, KDJ, CCI, Williams %R)
- volume.py: 量价指标 (VOL MA, OBV, VWAP, 量比, 换手率)

使用示例:
    from core.indicators import IndicatorCalculator

    calc = IndicatorCalculator()
    rsi = calc.calc_rsi(close, period=14)
    macd = calc.calc_macd(close)
"""

# 导入趋势指标
from .trend import (
    calc_sma,
    calc_ema,
    calc_macd,
    calc_boll,
    calc_all_trend
)

# 导入震荡指标
from .oscillator import (
    calc_rsi,
    calc_kdj,
    calc_cci,
    calc_williams_r,
    calc_all_oscillator
)

# 导入量价指标
from .volume import (
    calc_vol_ma,
    calc_obv,
    calc_vwap,
    calc_turnover_rate,
    calc_volume_ratio,
    calc_all_volume
)

# 导入异常类
from .trend import InsufficientDataError, InvalidParameterError


class IndicatorCalculator:
    """
    技术指标计算器

    提供统一的接口来计算各种技术指标

    示例:
        >>> calc = IndicatorCalculator()
        >>> # 计算 RSI
        >>> rsi = calc.calc_rsi(close, period=14)
        >>> # 计算 MACD
        >>> macd = calc.calc_macd(close)
        >>> # 批量计算所有指标
        >>> all_indicators = calc.calc_all(high, low, close, volume)
    """

    def calc_sma(self, data, period):
        """计算简单移动平均"""
        return calc_sma(data, period)

    def calc_ema(self, data, period):
        """计算指数移动平均"""
        return calc_ema(data, period)

    def calc_macd(self, data, fast_period=12, slow_period=26, signal_period=9):
        """计算 MACD"""
        return calc_macd(data, fast_period, slow_period, signal_period)

    def calc_boll(self, data, period=20, std_dev=2.0):
        """计算布林带"""
        return calc_boll(data, period, std_dev)

    def calc_rsi(self, data, period=14):
        """计算 RSI"""
        return calc_rsi(data, period)

    def calc_kdj(self, high, low, close, n=9, m1=3, m2=3):
        """计算 KDJ"""
        return calc_kdj(high, low, close, n, m1, m2)

    def calc_cci(self, high, low, close, period=14):
        """计算 CCI"""
        return calc_cci(high, low, close, period)

    def calc_williams_r(self, high, low, close, period=14):
        """计算 Williams %R"""
        return calc_williams_r(high, low, close, period)

    def calc_vol_ma(self, volume, period=5):
        """计算成交量移动平均"""
        return calc_vol_ma(volume, period)

    def calc_obv(self, close, volume):
        """计算 OBV"""
        return calc_obv(close, volume)

    def calc_vwap(self, high, low, close, volume, period=None):
        """计算 VWAP"""
        return calc_vwap(high, low, close, volume, period)

    def calc_turnover_rate(self, volume, total_shares):
        """计算换手率"""
        return calc_turnover_rate(volume, total_shares)

    def calc_volume_ratio(self, volume, period=5):
        """计算量比"""
        return calc_volume_ratio(volume, period)

    def calc_all(self, high, low, close, volume, total_shares=None):
        """
        计算所有指标

        参数:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            volume: 成交量序列
            total_shares: 总股本 (可选)

        返回:
            pd.DataFrame: 包含所有指标的 DataFrame
        """
        import pandas as pd

        result = pd.DataFrame(index=close.index)

        # 趋势指标
        trend = calc_all_trend(close)
        result = pd.concat([result, trend], axis=1)

        # 震荡指标
        oscillator = calc_all_oscillator(high, low, close)
        result = pd.concat([result, oscillator], axis=1)

        # 量价指标
        vol = calc_all_volume(high, low, close, volume, total_shares=total_shares)
        result = pd.concat([result, vol], axis=1)

        return result


# 模块版本
__version__ = '1.0.0'

# 导出所有公共接口
__all__ = [
    # 计算器类
    'IndicatorCalculator',

    # 趋势指标
    'calc_sma',
    'calc_ema',
    'calc_macd',
    'calc_boll',
    'calc_all_trend',

    # 震荡指标
    'calc_rsi',
    'calc_kdj',
    'calc_cci',
    'calc_williams_r',
    'calc_all_oscillator',

    # 量价指标
    'calc_vol_ma',
    'calc_obv',
    'calc_vwap',
    'calc_turnover_rate',
    'calc_volume_ratio',
    'calc_all_volume',

    # 异常类
    'InsufficientDataError',
    'InvalidParameterError',
]
