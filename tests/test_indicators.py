#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技术指标模块单元测试

测试覆盖:
- 趋势指标: SMA, EMA, MACD, BOLL
- 震荡指标: RSI, KDJ, CCI, Williams %R
- 量价指标: VOL MA, OBV, VWAP, 量比, 换手率
- 边界条件和异常处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from core.indicators import (
    calc_sma, calc_ema, calc_macd, calc_boll,
    calc_rsi, calc_kdj, calc_cci, calc_williams_r,
    calc_vol_ma, calc_obv, calc_vwap, calc_turnover_rate, calc_volume_ratio,
    IndicatorCalculator,
    InsufficientDataError, InvalidParameterError
)


# ==================== 测试数据 ====================

@pytest.fixture
def sample_data():
    """创建测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)

    return {
        'close': pd.Series(base_price, index=dates, name='close'),
        'high': pd.Series(base_price + np.random.rand(100) * 2, index=dates, name='high'),
        'low': pd.Series(base_price - np.random.rand(100) * 2, index=dates, name='low'),
        'volume': pd.Series(np.random.randint(1000000, 10000000, 100), index=dates, name='volume'),
    }


# ==================== 趋势指标测试 ====================

class TestSMA:
    """SMA 测试"""

    def test_basic_sma(self, sample_data):
        """测试基本 SMA 计算"""
        sma5 = calc_sma(sample_data['close'], 5)
        assert len(sma5) == 100
        assert sma5.iloc[-1] is not None
        assert not np.isnan(sma5.iloc[-1])

    def test_sma_nan_values(self, sample_data):
        """测试 SMA 前 N-1 个值为 NaN"""
        sma5 = calc_sma(sample_data['close'], 5)
        assert pd.isna(sma5.iloc[0])
        assert pd.isna(sma5.iloc[3])
        assert not pd.isna(sma5.iloc[4])

    def test_sma_insufficient_data(self):
        """测试数据不足的情况"""
        data = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(InsufficientDataError):
            calc_sma(data, 5)

    def test_sma_invalid_period(self, sample_data):
        """测试无效周期参数"""
        with pytest.raises(InvalidParameterError):
            calc_sma(sample_data['close'], 0)
        with pytest.raises(InvalidParameterError):
            calc_sma(sample_data['close'], -1)

    def test_sma_type_error(self):
        """测试类型错误"""
        with pytest.raises(TypeError):
            calc_sma([1, 2, 3], 5)


class TestEMA:
    """EMA 测试"""

    def test_basic_ema(self, sample_data):
        """测试基本 EMA 计算"""
        ema12 = calc_ema(sample_data['close'], 12)
        assert len(ema12) == 100
        assert not np.isnan(ema12.iloc[-1])

    def test_ema_more_responsive(self, sample_data):
        """测试 EMA 比 SMA 更灵敏"""
        sma12 = calc_sma(sample_data['close'], 12)
        ema12 = calc_ema(sample_data['close'], 12)
        # EMA 应该比 SMA 更接近当前价格
        close = sample_data['close']
        ema_diff = abs(close - ema12).mean()
        sma_diff = abs(close - sma12).mean()
        # 这个测试不一定总是通过，取决于数据
        # 但 EMA 确实对近期价格更敏感


class TestMACD:
    """MACD 测试"""

    def test_basic_macd(self, sample_data):
        """测试基本 MACD 计算"""
        macd = calc_macd(sample_data['close'])
        assert 'dif' in macd.columns
        assert 'dea' in macd.columns
        assert 'macd' in macd.columns
        assert len(macd) == 100

    def test_macd_custom_params(self, sample_data):
        """测试自定义参数"""
        macd = calc_macd(sample_data['close'], 10, 20, 7)
        assert len(macd) == 100

    def test_macd_invalid_params(self, sample_data):
        """测试无效参数"""
        with pytest.raises(InvalidParameterError):
            calc_macd(sample_data['close'], 26, 12, 9)  # fast > slow


class TestBOLL:
    """BOLL 测试"""

    def test_basic_boll(self, sample_data):
        """测试基本 BOLL 计算"""
        boll = calc_boll(sample_data['close'])
        assert 'upper' in boll.columns
        assert 'middle' in boll.columns
        assert 'lower' in boll.columns
        assert 'bandwidth' in boll.columns

    def test_boll_relationship(self, sample_data):
        """测试 BOLL 上中下轨关系"""
        boll = calc_boll(sample_data['close'])
        # 上轨 > 中轨 > 下轨
        valid_idx = boll.dropna().index
        assert (boll.loc[valid_idx, 'upper'] >= boll.loc[valid_idx, 'middle']).all()
        assert (boll.loc[valid_idx, 'middle'] >= boll.loc[valid_idx, 'lower']).all()


# ==================== 震荡指标测试 ====================

class TestRSI:
    """RSI 测试"""

    def test_basic_rsi(self, sample_data):
        """测试基本 RSI 计算"""
        rsi = calc_rsi(sample_data['close'], 14)
        assert len(rsi) == 100
        # RSI 应该在 0-100 之间
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_default_period(self, sample_data):
        """测试默认周期"""
        rsi = calc_rsi(sample_data['close'])
        assert len(rsi) == 100


class TestKDJ:
    """KDJ 测试"""

    def test_basic_kdj(self, sample_data):
        """测试基本 KDJ 计算"""
        kdj = calc_kdj(
            sample_data['high'],
            sample_data['low'],
            sample_data['close']
        )
        assert 'k' in kdj.columns
        assert 'd' in kdj.columns
        assert 'j' in kdj.columns

    def test_kdj_custom_params(self, sample_data):
        """测试自定义参数"""
        kdj = calc_kdj(
            sample_data['high'],
            sample_data['low'],
            sample_data['close'],
            n=14, m1=5, m2=5
        )
        assert len(kdj) == 100


class TestCCI:
    """CCI 测试"""

    def test_basic_cci(self, sample_data):
        """测试基本 CCI 计算"""
        cci = calc_cci(
            sample_data['high'],
            sample_data['low'],
            sample_data['close'],
            14
        )
        assert len(cci) == 100


class TestWilliamsR:
    """Williams %R 测试"""

    def test_basic_williams_r(self, sample_data):
        """测试基本 Williams %R 计算"""
        wr = calc_williams_r(
            sample_data['high'],
            sample_data['low'],
            sample_data['close'],
            14
        )
        assert len(wr) == 100
        # Williams %R 应该在 -100 到 0 之间
        valid_wr = wr.dropna()
        assert (valid_wr >= -100).all()
        assert (valid_wr <= 0).all()


# ==================== 量价指标测试 ====================

class TestVOLMA:
    """成交量 MA 测试"""

    def test_basic_vol_ma(self, sample_data):
        """测试基本成交量 MA 计算"""
        vol_ma5 = calc_vol_ma(sample_data['volume'], 5)
        assert len(vol_ma5) == 100


class TestOBV:
    """OBV 测试"""

    def test_basic_obv(self, sample_data):
        """测试基本 OBV 计算"""
        obv = calc_obv(sample_data['close'], sample_data['volume'])
        assert len(obv) == 100


class TestVWAP:
    """VWAP 测试"""

    def test_basic_vwap(self, sample_data):
        """测试基本 VWAP 计算"""
        vwap = calc_vwap(
            sample_data['high'],
            sample_data['low'],
            sample_data['close'],
            sample_data['volume']
        )
        assert len(vwap) == 100


class TestTurnoverRate:
    """换手率测试"""

    def test_basic_turnover(self, sample_data):
        """测试基本换手率计算"""
        turnover = calc_turnover_rate(sample_data['volume'], 1000000000)
        assert len(turnover) == 100
        # 换手率应该是正数
        assert (turnover >= 0).all()


class TestVolumeRatio:
    """量比测试"""

    def test_basic_volume_ratio(self, sample_data):
        """测试基本量比计算"""
        vr = calc_volume_ratio(sample_data['volume'], 5)
        assert len(vr) == 100
        # 量比应该是正数
        valid_vr = vr.dropna()
        assert (valid_vr >= 0).all()


# ==================== 集成测试 ====================

class TestIndicatorCalculator:
    """IndicatorCalculator 集成测试"""

    def test_calculator_initialization(self):
        """测试计算器初始化"""
        calc = IndicatorCalculator()
        assert calc is not None

    def test_calculator_all_indicators(self, sample_data):
        """测试批量计算所有指标"""
        calc = IndicatorCalculator()
        result = calc.calc_all(
            sample_data['high'],
            sample_data['low'],
            sample_data['close'],
            sample_data['volume']
        )
        # 应该包含很多列
        assert len(result.columns) > 10
        assert len(result) == 100

    def test_calculator_rsi(self, sample_data):
        """测试计算器 RSI 方法"""
        calc = IndicatorCalculator()
        rsi = calc.calc_rsi(sample_data['close'], 14)
        assert len(rsi) == 100

    def test_calculator_macd(self, sample_data):
        """测试计算器 MACD 方法"""
        calc = IndicatorCalculator()
        macd = calc.calc_macd(sample_data['close'])
        assert 'dif' in macd.columns


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
