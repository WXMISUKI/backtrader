#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测模块单元测试

测试覆盖:
- BacktestResult 类
- BacktestEngine 类
- run_backtest 便捷函数
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from backtest import (
    BacktestEngine,
    BacktestResult,
    run_backtest,
    StockDataFeed,
    StrategyAdapter
)


# ==================== BacktestResult 测试 ====================

class TestBacktestResult:
    """BacktestResult 测试"""

    def test_initialization(self):
        """测试初始化"""
        result = BacktestResult(
            stock_code="000001",
            strategy_name="ma_cross",
            initial_cash=100000,
            final_value=110000
        )
        assert result.stock_code == "000001"
        assert result.strategy_name == "ma_cross"
        assert result.initial_cash == 100000
        assert result.final_value == 110000

    def test_summary(self):
        """测试摘要生成"""
        result = BacktestResult(
            stock_code="000001",
            strategy_name="ma_cross",
            start_date="20260101",
            end_date="20260614",
            initial_cash=100000,
            final_value=110000,
            total_return=0.10,
            annual_return=0.20,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
        )
        summary = result.summary()
        assert "000001" in summary
        assert "ma_cross" in summary
        assert "110,000" in summary

    def test_to_dict(self):
        """测试转换为字典"""
        result = BacktestResult(
            stock_code="000001",
            strategy_name="ma_cross",
            initial_cash=100000,
            final_value=110000,
            total_return=0.10
        )
        d = result.to_dict()
        assert d['stock_code'] == "000001"
        assert d['final_value'] == 110000
        assert d['total_return'] == 0.10


# ==================== BacktestEngine 测试 ====================

class TestBacktestEngine:
    """BacktestEngine 测试"""

    def test_initialization(self):
        """测试初始化"""
        engine = BacktestEngine(initial_cash=100000, commission=0.001)
        assert engine.initial_cash == 100000
        assert engine.commission == 0.001

    def test_default_params(self):
        """测试默认参数"""
        engine = BacktestEngine()
        assert engine.initial_cash == 100000
        assert engine.commission == 0.001


# ==================== StockDataFeed 测试 ====================

class TestStockDataFeed:
    """StockDataFeed 测试"""

    def test_from_stock_data(self):
        """测试从 StockData 创建"""
        from skills.stock_advisor import StockData

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

        stock_data = StockData("000001", "平安银行", df)
        data_feed = StockDataFeed.from_stock_data(stock_data)

        assert data_feed is not None


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
