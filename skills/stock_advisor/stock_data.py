#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票数据统一封装

借鉴 QUANTAXIS 的 QADataStruct 设计理念
提供懒计算、缓存、统一接口等功能
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class StockData:
    """
    股票数据统一封装

    特点:
    - 统一的 OHLCV 数据接口
    - 技术指标懒计算和缓存
    - 交易信号懒计算和缓存
    - 支持多种输出格式

    示例:
        >>> df = get_stock_hist("000001", "20260101", "20260614")
        >>> stock = StockData("000001", "平安银行", df)
        >>> print(stock.latest_price)
        >>> print(stock.indicators)
        >>> print(stock.signals)
    """

    def __init__(self, code: str, name: str, df: pd.DataFrame, source: str = "real"):
        """
        初始化股票数据

        参数:
            code: 股票代码 (如 "000001")
            name: 股票名称 (如 "平安银行")
            df: OHLCV DataFrame，必须包含 open/high/low/close/volume 列

        异常:
            ValueError: DataFrame 缺少必要的列
        """
        # 验证 DataFrame
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"DataFrame 缺少必要的列: {missing_cols}")

        self.code = code
        self.name = name
        self.source = source
        self.df = df.copy()

        # 确保索引是 datetime 类型
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)

        # 懒计算缓存
        self._indicators = None
        self._signals = None

    # ==================== 基础属性 ====================

    @property
    def close(self) -> pd.Series:
        """收盘价序列"""
        return self.df['close']

    @property
    def open(self) -> pd.Series:
        """开盘价序列"""
        return self.df['open']

    @property
    def high(self) -> pd.Series:
        """最高价序列"""
        return self.df['high']

    @property
    def low(self) -> pd.Series:
        """最低价序列"""
        return self.df['low']

    @property
    def volume(self) -> pd.Series:
        """成交量序列"""
        return self.df['volume']

    @property
    def latest_price(self) -> float:
        """最新价格"""
        return float(self.close.iloc[-1])

    @property
    def data_points(self) -> int:
        """数据点数量"""
        return len(self.df)

    @property
    def date_range(self) -> tuple:
        """日期范围"""
        return (self.df.index[0], self.df.index[-1])

    # ==================== 计算属性 (懒计算) ====================

    @property
    def indicators(self) -> pd.DataFrame:
        """
        技术指标 (懒计算)

        首次访问时计算并缓存，后续直接返回缓存结果

        返回:
            包含所有技术指标的 DataFrame
        """
        if self._indicators is None:
            self._indicators = self._calc_indicators()
        return self._indicators

    @property
    def signals(self) -> pd.DataFrame:
        """
        交易信号 (懒计算)

        首次访问时计算并缓存，后续直接返回缓存结果

        返回:
            包含买卖信号的 DataFrame
        """
        if self._signals is None:
            self._signals = self._calc_signals()
        return self._signals

    # ==================== 计算方法 ====================

    def _calc_indicators(self) -> pd.DataFrame:
        """计算技术指标"""
        from core.indicators import IndicatorCalculator
        calc = IndicatorCalculator()
        return calc.calc_all(self.high, self.low, self.close, self.volume)

    def _calc_signals(self) -> pd.DataFrame:
        """计算交易信号"""
        from core.signals import SignalGenerator
        gen = SignalGenerator()
        return gen.generate(
            self.close, self.high, self.low,
            self.volume, self.indicators
        )

    def get_latest_signal(self, risk_profile: str = "moderate") -> dict:
        """
        获取最新交易信号

        参数:
            risk_profile: 风险配置 (conservative/moderate/aggressive)

        返回:
            最新信号信息字典
        """
        from core.signals import SignalGenerator
        gen = SignalGenerator(risk_profile)
        return gen.get_latest_signal(
            self.close, self.high, self.low,
            self.volume, self.indicators
        )

    # ==================== 统计方法 ====================

    def get_returns(self) -> pd.Series:
        """计算收益率序列"""
        return self.close.pct_change().dropna()

    def get_volatility(self, annualize: bool = True) -> float:
        """
        计算波动率

        参数:
            annualize: 是否年化

        返回:
            波动率
        """
        returns = self.get_returns()
        vol = returns.std()
        if annualize:
            vol = vol * np.sqrt(252)
        return float(vol)

    def get_max_drawdown(self) -> float:
        """
        计算最大回撤

        返回:
            最大回撤 (负数)
        """
        returns = self.get_returns()
        cumulative = (1 + returns).cumprod()
        drawdown = cumulative / cumulative.cummax() - 1
        return float(drawdown.min())

    def get_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率

        参数:
            risk_free_rate: 无风险利率，默认 3%

        返回:
            夏普比率
        """
        returns = self.get_returns()
        excess_returns = returns.mean() * 252 - risk_free_rate
        volatility = returns.std() * np.sqrt(252)
        if volatility == 0:
            return 0.0
        return float(excess_returns / volatility)

    # ==================== 输出方法 ====================

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'source': self.source,
            'latest_price': self.latest_price,
            'data_points': self.data_points,
            'date_range': f"{self.date_range[0].strftime('%Y-%m-%d')} ~ {self.date_range[1].strftime('%Y-%m-%d')}",
            'volatility': round(self.get_volatility(), 4),
            'max_drawdown': round(self.get_max_drawdown(), 4),
        }

    def summary(self) -> str:
        """生成摘要"""
        return (
            f"股票: {self.name}({self.code})\n"
            f"数据来源: {self.source}\n"
            f"最新价: {self.latest_price:.2f}\n"
            f"数据点: {self.data_points}\n"
            f"日期范围: {self.date_range[0].strftime('%Y-%m-%d')} ~ {self.date_range[1].strftime('%Y-%m-%d')}\n"
            f"波动率: {self.get_volatility():.2%}\n"
            f"最大回撤: {self.get_max_drawdown():.2%}"
        )

    def __repr__(self) -> str:
        return f"StockData(code='{self.code}', name='{self.name}', points={self.data_points})"

    def __str__(self) -> str:
        return self.summary()


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)

    df = pd.DataFrame({
        'open': base_price + np.random.randn(100) * 0.2,
        'high': base_price + np.abs(np.random.randn(100)) * 1.5,
        'low': base_price - np.abs(np.random.randn(100)) * 1.5,
        'close': base_price,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)

    print("=" * 60)
    print("StockData 测试")
    print("=" * 60)

    # 创建 StockData
    stock = StockData("000001", "平安银行", df)

    # 测试基础属性
    print("\n1. 基础属性:")
    print(f"   股票代码: {stock.code}")
    print(f"   股票名称: {stock.name}")
    print(f"   最新价格: {stock.latest_price:.2f}")
    print(f"   数据点数: {stock.data_points}")

    # 测试统计方法
    print("\n2. 统计指标:")
    print(f"   波动率: {stock.get_volatility():.2%}")
    print(f"   最大回撤: {stock.get_max_drawdown():.2%}")
    print(f"   夏普比率: {stock.get_sharpe_ratio():.2f}")

    # 测试懒计算
    print("\n3. 技术指标 (懒计算):")
    indicators = stock.indicators
    print(f"   指标列数: {len(indicators.columns)}")
    print(f"   指标列名: {list(indicators.columns)[:5]}...")

    print("\n4. 交易信号 (懒计算):")
    signals = stock.signals
    print(f"   信号列数: {len(signals.columns)}")
    print(f"   最新方向: {signals['direction'].iloc[-1]}")

    # 测试输出
    print("\n5. 摘要:")
    print(stock.summary())

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
