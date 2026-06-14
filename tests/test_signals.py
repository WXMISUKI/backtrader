#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
信号系统模块单元测试

测试覆盖:
- 买入信号: MA金叉、MACD金叉、RSI超卖、KDJ金叉、BOLL支撑、放量
- 卖出信号: MA死叉、MACD死叉、RSI超买、KDJ死叉、BOLL压力、止损
- 信号强度: 强度计算、方向判断、置信度
- 集成测试: SignalGenerator
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from core.signals import (
    check_ma_cross, check_macd_cross, check_rsi_oversold,
    check_kdj_cross, check_boll_support, check_volume_breakout,
    check_ma_death_cross, check_macd_death_cross, check_rsi_overbought,
    check_kdj_death_cross, check_boll_pressure, check_stop_loss,
    calc_signal_strength, get_trade_direction, get_confidence,
    SignalGenerator, generate_signal
)


# ==================== 测试数据 ====================

@pytest.fixture
def cross_data():
    """创建金叉/死叉测试数据"""
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    # 设计金叉场景: fast 从下往上穿越 slow
    fast_values = np.concatenate([
        np.ones(40) * 10,  # 前40天低于slow
        np.arange(20) * 0.5 + 10,  # 中间20天上升
        np.ones(40) * 20  # 后40天高于slow
    ])
    fast = pd.Series(fast_values, index=dates)
    slow = pd.Series(np.ones(100) * 12, index=dates)

    return {'fast': fast, 'slow': slow, 'dates': dates}


@pytest.fixture
def rsi_data():
    """创建 RSI 测试数据"""
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    # 设计超卖反弹场景
    rsi = pd.Series(
        np.concatenate([
            np.ones(40) * 25,  # 超卖区域
            np.ones(10) * 35,  # 反弹
            np.ones(50) * 50   # 正常区域
        ]),
        index=dates
    )

    return {'rsi': rsi, 'dates': dates}


@pytest.fixture
def indicator_data():
    """创建指标测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')

    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 0.5), index=dates)
    high = close + np.random.rand(100) * 2
    low = close - np.random.rand(100) * 2
    volume = pd.Series(np.random.randint(1000000, 10000000, 100), index=dates)

    # 创建指标数据
    indicators = pd.DataFrame(index=dates)
    indicators['ma5'] = close.rolling(5).mean()
    indicators['ma20'] = close.rolling(20).mean()
    indicators['macd_dif'] = close.ewm(span=12).mean() - close.ewm(span=26).mean()
    indicators['macd_dea'] = indicators['macd_dif'].ewm(span=9).mean()
    indicators['rsi'] = 50 + np.random.randn(100) * 15  # 模拟 RSI
    indicators['kdj_k'] = 50 + np.random.randn(100) * 20
    indicators['kdj_d'] = indicators['kdj_k'].ewm(span=3).mean()
    indicators['boll_upper'] = close + 2
    indicators['boll_lower'] = close - 2
    indicators['vol_ma5'] = volume.rolling(5).mean()

    return {
        'close': close,
        'high': high,
        'low': low,
        'volume': volume,
        'indicators': indicators,
        'dates': dates
    }


# ==================== 买入信号测试 ====================

class TestMACross:
    """MA 金叉测试"""

    def test_golden_cross(self, cross_data):
        """测试金叉信号"""
        signal = check_ma_cross(cross_data['fast'], cross_data['slow'])
        # 在第50个点附近应该有金叉
        assert signal.sum() > 0
        assert signal.iloc[45:55].sum() > 0

    def test_no_cross(self):
        """测试无交叉情况"""
        fast = pd.Series([10, 10, 10, 10, 10])
        slow = pd.Series([12, 12, 12, 12, 12])
        signal = check_ma_cross(fast, slow)
        assert signal.sum() == 0


class TestMACDCross:
    """MACD 金叉测试"""

    def test_golden_cross(self):
        """测试 MACD 金叉"""
        dif = pd.Series([-1, -1, 0, 1, 1])
        dea = pd.Series([0, 0, 0, 0, 0])
        signal = check_macd_cross(dif, dea)
        # 第4个点应该有金叉
        assert signal.iloc[3] == 1


class TestRSIOversold:
    """RSI 超卖反弹测试"""

    def test_oversold_bounce(self, rsi_data):
        """测试超卖反弹信号"""
        signal = check_rsi_oversold(rsi_data['rsi'], 30)
        # 在第41个点附近应该有信号
        assert signal.sum() > 0

    def test_no_signal_in_normal(self):
        """测试正常区域无信号"""
        rsi = pd.Series([50, 55, 60, 55, 50])
        signal = check_rsi_oversold(rsi, 30)
        assert signal.sum() == 0


class TestKDJCross:
    """KDJ 金叉测试"""

    def test_golden_cross(self):
        """测试 KDJ 金叉"""
        k = pd.Series([20, 25, 30, 35, 40])
        d = pd.Series([30, 30, 30, 30, 30])
        signal = check_kdj_cross(k, d)
        # 第4个点应该有金叉
        assert signal.iloc[3] == 1


class TestBollSupport:
    """BOLL 支撑测试"""

    def test_support_bounce(self):
        """测试下轨支撑反弹"""
        # 设计: close从下轨下方反弹到上方
        # 第1天: close=10 > lower=9 (在上方)
        # 第2天: close=8 < lower=9 (跌破)
        # 第3天: close=7 < lower=9 (继续跌破)
        # 第4天: close=9.5 > lower=9 (反弹到上方) - 应该产生信号
        close = pd.Series([10.0, 8.0, 7.0, 9.5, 10.0])
        lower = pd.Series([9.0, 9.0, 9.0, 9.0, 9.0])
        signal = check_boll_support(close, lower)
        # 第4天: close=9.5 > lower=9 (True), 前一天close=7 <= lower=9 (True)
        assert signal.iloc[3] == 1


class TestVolumeBreakout:
    """放量突破测试"""

    def test_breakout(self):
        """测试放量信号"""
        volume = pd.Series([100, 100, 100, 200, 100])
        vol_ma = pd.Series([100, 100, 100, 100, 100])
        signal = check_volume_breakout(volume, vol_ma, 1.5)
        # 第4个点应该有信号
        assert signal.iloc[3] == 1


# ==================== 卖出信号测试 ====================

class TestMADeathCross:
    """MA 死叉测试"""

    def test_death_cross(self):
        """测试死叉信号"""
        # 设计: fast从上方穿越到下方
        # 第1天: fast=15 > slow=12
        # 第2天: fast=14 > slow=12
        # 第3天: fast=13 > slow=12
        # 第4天: fast=12 = slow=12 (临界点，不产生信号因为是>=)
        # 第5天: fast=11 < slow=12 - 应该产生死叉信号
        fast = pd.Series([15, 14, 13, 12, 11])
        slow = pd.Series([12, 12, 12, 12, 12])
        signal = check_ma_death_cross(fast, slow)
        # 第5天: fast=11 < slow=12 (True), 前一天fast=12 >= slow=12 (True)
        assert signal.iloc[4] == 1


class TestRSIOverbought:
    """RSI 超买测试"""

    def test_overbought(self):
        """测试超买信号"""
        rsi = pd.Series([50, 60, 70, 80, 75])
        signal = check_rsi_overbought(rsi, 70)
        # 第4个点应该有信号
        assert signal.iloc[3] == 1


class TestStopLoss:
    """止损测试"""

    def test_stop_loss_triggered(self):
        """测试止损触发"""
        assert check_stop_loss(9.4, 10.0, 0.05) == True
        assert check_stop_loss(9.5, 10.0, 0.05) == True
        assert check_stop_loss(9.6, 10.0, 0.05) == False

    def test_stop_loss_edge_cases(self):
        """测试止损边界情况"""
        assert check_stop_loss(10.0, 10.0, 0.05) == False
        assert check_stop_loss(10.5, 10.0, 0.05) == False
        assert check_stop_loss(0, 10.0, 0.05) == True


# ==================== 信号强度测试 ====================

class TestSignalStrength:
    """信号强度测试"""

    def test_strength_calculation(self):
        """测试强度计算"""
        signals = pd.DataFrame({
            'signal_a': [1, 0, 1],
            'signal_b': [0, 1, 1]
        })
        weights = {'signal_a': 0.6, 'signal_b': 0.4}
        strength = calc_signal_strength(signals, weights)
        assert abs(strength.iloc[0] - 0.6) < 0.01
        assert abs(strength.iloc[1] - 0.4) < 0.01
        assert abs(strength.iloc[2] - 1.0) < 0.01

    def test_empty_signals(self):
        """测试空信号"""
        signals = pd.DataFrame({'signal_a': [0, 0, 0]})
        weights = {'signal_a': 1.0}
        strength = calc_signal_strength(signals, weights)
        assert (strength == 0).all()


class TestTradeDirection:
    """交易方向测试"""

    def test_buy_direction(self):
        """测试买入方向"""
        # 设计更明确的场景
        buy = pd.Series([0.6, 0.2, 0.4, 0.1, 0.5])
        sell = pd.Series([0.1, 0.7, 0.3, 0.2, 0.3])
        direction = get_trade_direction(buy, sell, 0.3)
        # 第1个: buy=0.6 >= 0.3 且 buy > sell -> 买入 (1)
        assert direction.iloc[0] == 1
        # 第2个: sell=0.7 >= 0.3 且 sell > buy -> 卖出 (-1)
        assert direction.iloc[1] == -1
        # 第3个: buy=0.4 >= 0.3 且 buy > sell -> 买入 (1)
        assert direction.iloc[2] == 1
        # 第4个: buy=0.1 < 0.3 且 sell=0.2 < 0.3 -> 观望 (0)
        assert direction.iloc[3] == 0
        # 第5个: buy=0.5 >= 0.3 且 buy > sell -> 买入 (1)
        assert direction.iloc[4] == 1

    def test_hold_when_weak(self):
        """测试信号弱时观望"""
        buy = pd.Series([0.2, 0.1])
        sell = pd.Series([0.1, 0.2])
        direction = get_trade_direction(buy, sell, 0.3)
        assert (direction == 0).all()


class TestConfidence:
    """置信度测试"""

    def test_confidence_calculation(self):
        """测试置信度计算"""
        buy = pd.Series([0.6, 0.2, 0.4])
        sell = pd.Series([0.1, 0.7, 0.3])
        direction = pd.Series([1, -1, 0])
        confidence = get_confidence(buy, sell, direction)
        assert confidence.iloc[0] == 0.6  # 买入置信度
        assert confidence.iloc[1] == 0.7  # 卖出置信度
        assert confidence.iloc[2] == 0.0  # 观望置信度


# ==================== 集成测试 ====================

class TestSignalGenerator:
    """SignalGenerator 集成测试"""

    def test_initialization(self):
        """测试初始化"""
        gen = SignalGenerator("moderate")
        assert gen.risk_profile == "moderate"

    def test_invalid_profile(self):
        """测试无效风险配置"""
        with pytest.raises(ValueError):
            SignalGenerator("invalid")

    def test_generate_signals(self, indicator_data):
        """测试生成信号"""
        gen = SignalGenerator("moderate")
        signals = gen.generate(
            indicator_data['close'],
            indicator_data['high'],
            indicator_data['low'],
            indicator_data['volume'],
            indicator_data['indicators']
        )
        assert 'buy_strength' in signals.columns
        assert 'sell_strength' in signals.columns
        assert 'direction' in signals.columns
        assert 'confidence' in signals.columns

    def test_get_latest_signal(self, indicator_data):
        """测试获取最新信号"""
        gen = SignalGenerator("moderate")
        latest = gen.get_latest_signal(
            indicator_data['close'],
            indicator_data['high'],
            indicator_data['low'],
            indicator_data['volume'],
            indicator_data['indicators']
        )
        assert 'direction' in latest
        assert 'confidence' in latest
        assert latest['direction'] in ['BUY', 'SELL', 'HOLD']


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
