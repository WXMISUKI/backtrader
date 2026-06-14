#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
信号系统模块

提供股票买卖信号的生成功能

模块结构:
- buy_signals.py: 买入信号检测
- sell_signals.py: 卖出信号检测
- signal_strength.py: 信号强度计算和综合信号生成

使用示例:
    from core.signals import SignalGenerator

    generator = SignalGenerator(risk_profile="moderate")
    signal = generator.get_latest_signal(close, high, low, volume, indicators)
"""

# 导入买入信号
from .buy_signals import (
    check_ma_cross,
    check_macd_cross,
    check_rsi_oversold,
    check_kdj_cross,
    check_boll_support,
    check_volume_breakout,
    get_buy_signals
)

# 导入卖出信号
from .sell_signals import (
    check_ma_death_cross,
    check_macd_death_cross,
    check_rsi_overbought,
    check_kdj_death_cross,
    check_boll_pressure,
    check_stop_loss,
    check_stop_loss_series,
    get_sell_signals
)

# 导入信号强度
from .signal_strength import (
    calc_signal_strength,
    get_trade_direction,
    get_confidence,
    generate_signal,
    get_latest_signal,
    SIGNAL_WEIGHTS
)


class SignalGenerator:
    """
    信号生成器

    提供统一的接口来生成交易信号

    示例:
        >>> generator = SignalGenerator(risk_profile="moderate")
        >>> # 生成所有信号
        >>> signals = generator.generate(close, high, low, volume, indicators)
        >>> # 获取最新信号
        >>> latest = generator.get_latest_signal(close, high, low, volume, indicators)
        >>> print(latest)
        {'direction': 'BUY', 'confidence': 0.65, ...}
    """

    def __init__(self, risk_profile: str = "moderate"):
        """
        初始化信号生成器

        参数:
            risk_profile: 风险配置 (conservative/moderate/aggressive)
        """
        if risk_profile not in ["conservative", "moderate", "aggressive"]:
            raise ValueError(
                f"无效的风险配置: {risk_profile}，"
                f"可选: conservative, moderate, aggressive"
            )
        self.risk_profile = risk_profile

    def generate(
        self,
        close,
        high,
        low,
        volume,
        indicators,
        buy_price=None
    ):
        """
        生成交易信号

        参数:
            close: 收盘价序列
            high: 最高价序列
            low: 最低价序列
            volume: 成交量序列
            indicators: 指标数据 (来自 IndicatorCalculator)
            buy_price: 买入价格 (用于止损判断)

        返回:
            pd.DataFrame: 包含信号的 DataFrame
        """
        return generate_signal(
            close, high, low, volume, indicators,
            self.risk_profile, buy_price
        )

    def get_latest_signal(
        self,
        close,
        high,
        low,
        volume,
        indicators,
        buy_price=None
    ):
        """
        获取最新交易信号

        参数:
            close: 收盘价序列
            high: 最高价序列
            low: 最低价序列
            volume: 成交量序列
            indicators: 指标数据
            buy_price: 买入价格

        返回:
            dict: 最新信号信息
        """
        return get_latest_signal(
            close, high, low, volume, indicators,
            self.risk_profile, buy_price
        )

    def get_buy_signals(self, close, high, low, volume, indicators):
        """获取买入信号"""
        return get_buy_signals(
            close, high, low, volume, indicators, self.risk_profile
        )

    def get_sell_signals(self, close, high, low, indicators, buy_price=None):
        """获取卖出信号"""
        return get_sell_signals(
            close, high, low, indicators, self.risk_profile, buy_price
        )

    def set_risk_profile(self, risk_profile: str):
        """设置风险配置"""
        if risk_profile not in ["conservative", "moderate", "aggressive"]:
            raise ValueError(f"无效的风险配置: {risk_profile}")
        self.risk_profile = risk_profile


# 模块版本
__version__ = '1.0.0'

# 导出所有公共接口
__all__ = [
    # 生成器类
    'SignalGenerator',

    # 买入信号
    'check_ma_cross',
    'check_macd_cross',
    'check_rsi_oversold',
    'check_kdj_cross',
    'check_boll_support',
    'check_volume_breakout',
    'get_buy_signals',

    # 卖出信号
    'check_ma_death_cross',
    'check_macd_death_cross',
    'check_rsi_overbought',
    'check_kdj_death_cross',
    'check_boll_pressure',
    'check_stop_loss',
    'check_stop_loss_series',
    'get_sell_signals',

    # 信号强度
    'calc_signal_strength',
    'get_trade_direction',
    'get_confidence',
    'generate_signal',
    'get_latest_signal',
    'SIGNAL_WEIGHTS',
]
