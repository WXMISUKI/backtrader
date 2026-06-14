#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3 高级功能单元测试

测试覆盖:
- 智能选股模块
- 报告生成模块
- 模拟交易模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from skills.stock_selector import (
    StockScreener,
    ScreeningConditions,
    StockCandidate,
    screen_stocks
)
from skills.stock_report import (
    ReportGenerator,
    generate_stock_report,
    generate_backtest_report,
    generate_screening_report
)
from skills.stock_simulator import (
    TradingSimulator,
    Position,
    TradeRecord,
    PortfolioSnapshot,
    create_simulator
)


# ==================== 智能选股测试 ====================

class TestScreeningConditions:
    """ScreeningConditions 测试"""

    def test_initialization(self):
        """测试初始化"""
        conditions = ScreeningConditions(
            ma_cross=True,
            rsi_oversold=True,
            risk_profile="moderate"
        )
        assert conditions.ma_cross == True
        assert conditions.rsi_oversold == True
        assert conditions.risk_profile == "moderate"

    def test_default_values(self):
        """测试默认值"""
        conditions = ScreeningConditions()
        assert conditions.ma_cross == False
        assert conditions.rsi_oversold == False
        assert conditions.macd_cross == False


class TestStockCandidate:
    """StockCandidate 测试"""

    def test_initialization(self):
        """测试初始化"""
        candidate = StockCandidate(
            code="000001",
            name="平安银行",
            price=11.24,
            change_pct=1.5,
            signals=["MA金叉", "RSI超卖"],
            score=85.0
        )
        assert candidate.code == "000001"
        assert candidate.name == "平安银行"
        assert candidate.score == 85.0

    def test_to_dict(self):
        """测试转换为字典"""
        candidate = StockCandidate(
            code="000001",
            name="平安银行",
            price=11.24,
            change_pct=1.5,
            signals=["MA金叉"],
            score=85.0
        )
        d = candidate.to_dict()
        assert d['code'] == "000001"
        assert d['price'] == 11.24
        assert "MA金叉" in d['signals']


class TestStockScreener:
    """StockScreener 测试"""

    def test_initialization(self):
        """测试初始化"""
        screener = StockScreener()
        assert len(screener.STOCK_LIST) > 0

    def test_stock_list(self):
        """测试股票列表"""
        screener = StockScreener()
        assert ("000001", "平安银行") in screener.STOCK_LIST


# ==================== 报告生成测试 ====================

class TestReportGenerator:
    """ReportGenerator 测试"""

    def test_json_report(self):
        """测试 JSON 报告"""
        data = {
            'stock_code': '000001',
            'price': 11.24
        }
        report = ReportGenerator.generate_json_report(data)
        assert '000001' in report
        assert '11.24' in report

    def test_screening_report(self):
        """测试选股报告"""
        candidates = [
            StockCandidate(
                code="000001",
                name="平安银行",
                price=11.24,
                change_pct=1.5,
                signals=["MA金叉"],
                score=85.0
            )
        ]
        report = ReportGenerator.generate_screening_report(candidates)
        assert "平安银行" in report
        assert "000001" in report


# ==================== 模拟交易测试 ====================

class TestTradingSimulator:
    """TradingSimulator 测试"""

    def test_initialization(self):
        """测试初始化"""
        simulator = TradingSimulator(initial_cash=1000000)
        assert simulator.initial_cash == 1000000
        assert simulator.cash == 1000000

    def test_buy(self):
        """测试买入"""
        simulator = TradingSimulator(initial_cash=1000000)
        result = simulator.buy("000001", "平安银行", 10.5, 1000)
        assert result == True
        assert simulator.cash < 1000000
        assert "000001" in simulator._positions

    def test_buy_insufficient_funds(self):
        """测试资金不足"""
        simulator = TradingSimulator(initial_cash=1000)
        result = simulator.buy("000001", "平安银行", 10.5, 1000)
        assert result == False

    def test_buy_invalid_size(self):
        """测试无效数量"""
        simulator = TradingSimulator(initial_cash=1000000)
        result = simulator.buy("000001", "平安银行", 10.5, 150)
        assert result == False

    def test_sell(self):
        """测试卖出"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        initial_cash = simulator.cash
        result = simulator.sell("000001", 11.0, 500)
        assert result == True
        assert simulator.cash > initial_cash

    def test_sell_all(self):
        """测试全部卖出"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        result = simulator.sell("000001", 11.0)
        assert result == True
        assert "000001" not in simulator._positions

    def test_sell_no_position(self):
        """测试没有持仓"""
        simulator = TradingSimulator(initial_cash=1000000)
        result = simulator.sell("000001", 11.0)
        assert result == False

    def test_get_portfolio(self):
        """测试获取持仓"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        portfolio = simulator.get_portfolio()
        assert 'cash' in portfolio
        assert 'positions' in portfolio
        assert len(portfolio['positions']) == 1

    def test_get_performance(self):
        """测试获取业绩"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        performance = simulator.get_performance()
        assert 'total_assets' in performance
        assert 'total_profit' in performance

    def test_get_trades(self):
        """测试获取交易记录"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        simulator.sell("000001", 11.0, 500)
        trades = simulator.get_trades()
        assert len(trades) == 2

    def test_update_prices(self):
        """测试更新价格"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        simulator.update_prices({"000001": 11.0})
        pos = simulator._positions["000001"]
        assert pos.current_price == 11.0

    def test_snapshot(self):
        """测试组合快照"""
        simulator = TradingSimulator(initial_cash=1000000)
        simulator.buy("000001", "平安银行", 10.5, 1000)
        simulator.take_snapshot("2026-06-14")
        snapshots = simulator.get_snapshots()
        assert len(snapshots) == 1

    def test_create_simulator(self):
        """测试便捷函数"""
        simulator = create_simulator(500000)
        assert simulator.initial_cash == 500000


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
