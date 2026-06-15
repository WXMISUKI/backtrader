"""
智能交易决策系统测试
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.trading_advisor import (
    TradingAdvisor,
    TradeDecision,
    TrendDetector,
    TrendInfo,
    TrendType,
    EntryExitTiming,
    EntrySignal,
    ExitSignal,
    PositionManager,
    RiskController
)


def create_sample_data(n=100, trend='bull'):
    """创建示例股票数据"""
    np.random.seed(42)

    dates = pd.date_range('2024-01-01', periods=n, freq='B')

    if trend == 'bull':
        # 牛市：价格整体上涨
        price = 100 + np.cumsum(np.random.randn(n) * 1.5 + 0.3)
    elif trend == 'bear':
        # 熊市：价格整体下跌
        price = 100 + np.cumsum(np.random.randn(n) * 1.5 - 0.3)
    else:
        # 震荡市
        price = 100 + np.cumsum(np.random.randn(n) * 1.5)

    df = pd.DataFrame({
        'date': dates,
        'open': price + np.random.randn(n) * 0.5,
        'high': price + abs(np.random.randn(n)) * 2,
        'low': price - abs(np.random.randn(n)) * 2,
        'close': price,
        'volume': np.random.randint(1000000, 10000000, n)
    })

    return df


class TestTrendDetector:
    """趋势检测器测试"""

    def test_init(self):
        """测试初始化"""
        detector = TrendDetector()
        assert detector.weights is not None

    def test_detect_bull_trend(self):
        """测试牛市检测"""
        df = create_sample_data(100, 'bull')
        detector = TrendDetector()
        trend = detector.detect(df)

        assert isinstance(trend, TrendInfo)
        assert trend.trend_type in ['BULL', 'BEAR', 'RANGING']
        assert 0 <= trend.strength <= 1
        assert trend.support_level > 0
        assert trend.resistance_level > 0

    def test_detect_bear_trend(self):
        """测试熊市检测"""
        df = create_sample_data(100, 'bear')
        detector = TrendDetector()
        trend = detector.detect(df)

        assert isinstance(trend, TrendInfo)

    def test_detect_ranging_trend(self):
        """测试震荡市检测"""
        df = create_sample_data(100, 'ranging')
        detector = TrendDetector()
        trend = detector.detect(df)

        assert isinstance(trend, TrendInfo)

    def test_short_data(self):
        """测试数据不足"""
        df = create_sample_data(30)
        detector = TrendDetector()
        trend = detector.detect(df)

        assert trend.trend_type == 'RANGING'


class TestEntryExitTiming:
    """入场出场时机测试"""

    def test_init(self):
        """测试初始化"""
        timing = EntryExitTiming()
        assert timing.entry_weights is not None

    def test_check_entry(self):
        """测试入场检查"""
        df = create_sample_data(100)
        timing = EntryExitTiming()

        entry = timing.check_entry(df)

        assert isinstance(entry, EntrySignal)
        assert isinstance(entry.can_enter, bool)
        assert 0 <= entry.strength <= 1

    def test_check_exit(self):
        """测试出场检查"""
        df = create_sample_data(100)
        timing = EntryExitTiming()

        # 设置买入价
        buy_price = df['close'].iloc[-20]

        exit_signal = timing.check_exit(df, buy_price)

        assert isinstance(exit_signal, ExitSignal)
        assert isinstance(exit_signal.should_exit, bool)

    def test_check_entry_with_trend(self):
        """测试带趋势的入场检查"""
        df = create_sample_data(100)
        timing = EntryExitTiming()

        entry = timing.check_entry(df, 'BULL')

        assert isinstance(entry, EntrySignal)


class TestPositionManager:
    """仓位管理器测试"""

    def test_init(self):
        """测试初始化"""
        manager = PositionManager('moderate')
        assert manager.risk_profile == 'moderate'
        assert manager.max_position_ratio == 0.50

    def test_calc_position(self):
        """测试仓位计算"""
        manager = PositionManager('moderate')

        position = manager.calc_position(
            capital=100000,
            price=10.0,
            confidence=0.7,
            trend_type='BULL'
        )

        assert position.shares >= 100
        assert position.position_ratio > 0
        assert position.capital_used > 0
        assert position.risk_level in ['LOW', 'MEDIUM', 'HIGH']

    def test_calc_position_conservative(self):
        """测试保守型仓位"""
        manager = PositionManager('conservative')

        position = manager.calc_position(
            capital=100000,
            price=10.0,
            confidence=0.7,
            trend_type='BULL'
        )

        assert position.position_ratio <= 0.30

    def test_calc_position_aggressive(self):
        """测试激进型仓位"""
        manager = PositionManager('aggressive')

        position = manager.calc_position(
            capital=100000,
            price=10.0,
            confidence=0.7,
            trend_type='BULL'
        )

        assert position.position_ratio <= 0.80

    def test_should_add_position(self):
        """测试加仓判断"""
        manager = PositionManager('moderate')

        # 盈利5%以上，牛市，高置信度
        assert manager.should_add_position(0.06, 'BULL', 0.8) == True

        # 盈利不足
        assert manager.should_add_position(0.03, 'BULL', 0.8) == False

        # 熊市
        assert manager.should_add_position(0.06, 'BEAR', 0.8) == False


class TestRiskController:
    """风险控制器测试"""

    def test_init(self):
        """测试初始化"""
        controller = RiskController('moderate')
        assert controller.risk_profile == 'moderate'

    def test_calc_stop_loss(self):
        """测试止损计算"""
        controller = RiskController('moderate')

        stop_loss = controller.calc_stop_loss(100.0, 'BULL')

        assert stop_loss < 100.0
        assert stop_loss > 90.0  # 止损不会太低

    def test_calc_stop_loss_bear(self):
        """测试熊市止损"""
        controller = RiskController('moderate')

        stop_loss_bull = controller.calc_stop_loss(100.0, 'BULL')
        stop_loss_bear = controller.calc_stop_loss(100.0, 'BEAR')

        # 熊市止损更严格
        assert stop_loss_bear > stop_loss_bull

    def test_calc_take_profit(self):
        """测试止盈计算"""
        controller = RiskController('moderate')

        take_profit = controller.calc_take_profit(100.0, 'BULL', 0.7)

        assert take_profit > 100.0

    def test_calc_risk_metrics(self):
        """测试风险指标"""
        controller = RiskController('moderate')

        metrics = controller.calc_risk_metrics(100.0, 100.0, 95.0, 120.0)

        assert metrics.stop_loss_price == 95.0
        assert metrics.take_profit_price == 120.0
        assert metrics.max_loss_pct < 0
        assert metrics.expected_profit_pct > 0
        assert metrics.risk_reward_ratio > 0

    def test_should_trail_stop(self):
        """测试移动止损"""
        controller = RiskController('moderate')

        # 盈利4% (104/100 - 1 = 4%)，不满足10%条件
        assert controller.should_trail_stop(104, 100, 110) == False

        # 盈利15% (115/100 - 1 = 15%)，从高点120回撤4.2% ((120-115)/120 = 4.2%)
        assert controller.should_trail_stop(115, 100, 120) == False

        # 盈利15% (115/100 - 1 = 15%)，从高点122回撤5.7% ((122-115)/122 = 5.7%)
        assert controller.should_trail_stop(115, 100, 122) == True

    def test_check_daily_loss_limit(self):
        """测试日内亏损限制"""
        controller = RiskController('moderate')

        # 正常亏损
        assert controller.check_daily_loss_limit(-0.01) == False

        # 超过限制
        assert controller.check_daily_loss_limit(-0.05) == True


class TestTradingAdvisor:
    """交易顾问测试"""

    def test_init(self):
        """测试初始化"""
        advisor = TradingAdvisor('moderate')
        assert advisor.risk_profile == 'moderate'

    def test_analyze_no_position(self):
        """测试无持仓分析"""
        df = create_sample_data(100)
        advisor = TradingAdvisor('moderate')

        decision = advisor.analyze(df)

        assert isinstance(decision, TradeDecision)
        assert decision.action in ['BUY', 'SELL', 'HOLD']
        assert 0 <= decision.confidence <= 1
        assert decision.timestamp != ""

    def test_analyze_with_position(self):
        """测试有持仓分析"""
        df = create_sample_data(100)
        advisor = TradingAdvisor('moderate')

        buy_price = df['close'].iloc[-20]
        decision = advisor.analyze(df, buy_price=buy_price)

        assert isinstance(decision, TradeDecision)

    def test_analyze_with_capital(self):
        """测试带资金分析"""
        df = create_sample_data(100)
        advisor = TradingAdvisor('moderate')

        decision = advisor.analyze(df, capital=100000, current_positions=0)

        assert isinstance(decision, TradeDecision)

    def test_analyze_with_signals(self):
        """测试详细分析"""
        df = create_sample_data(100)
        advisor = TradingAdvisor('moderate')

        result = advisor.analyze_with_signals(df)

        assert 'current_price' in result
        assert 'trend' in result
        assert 'entry' in result
        assert 'risk' in result

    def test_decision_summary(self):
        """测试决策摘要"""
        df = create_sample_data(100)
        advisor = TradingAdvisor('moderate')

        decision = advisor.analyze(df)
        summary = decision.summary()

        assert '交易决策' in summary
        assert '操作' in summary
        assert '置信度' in summary

    def test_different_risk_profiles(self):
        """测试不同风险偏好"""
        df = create_sample_data(100)

        for profile in ['conservative', 'moderate', 'aggressive']:
            advisor = TradingAdvisor(profile)
            decision = advisor.analyze(df)
            assert isinstance(decision, TradeDecision)

    def test_bull_market_analysis(self):
        """测试牛市分析"""
        df = create_sample_data(100, 'bull')
        advisor = TradingAdvisor('moderate')

        decision = advisor.analyze(df)

        assert isinstance(decision, TradeDecision)

    def test_bear_market_analysis(self):
        """测试熊市分析"""
        df = create_sample_data(100, 'bear')
        advisor = TradingAdvisor('moderate')

        decision = advisor.analyze(df)

        assert isinstance(decision, TradeDecision)


class TestIntegration:
    """集成测试"""

    def test_full_decision_flow(self):
        """测试完整决策流程"""
        df = create_sample_data(200)
        advisor = TradingAdvisor('moderate')

        # 模拟多次分析
        decisions = []
        for i in range(5):
            start_idx = i * 20
            end_idx = start_idx + 100
            if end_idx > len(df):
                break

            sub_df = df.iloc[start_idx:end_idx].reset_index(drop=True)
            decision = advisor.analyze(sub_df)
            decisions.append(decision)

        # 验证决策
        assert len(decisions) > 0
        for decision in decisions:
            assert decision.action in ['BUY', 'SELL', 'HOLD']

    def test_decision_consistency(self):
        """测试决策一致性"""
        df = create_sample_data(100)
        advisor = TradingAdvisor('moderate')

        # 多次分析相同数据
        decision1 = advisor.analyze(df)
        decision2 = advisor.analyze(df)

        # 结果应该相同
        assert decision1.action == decision2.action
        assert decision1.confidence == decision2.confidence


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
