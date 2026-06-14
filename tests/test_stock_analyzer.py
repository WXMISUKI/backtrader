#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票分析器单元测试

测试覆盖:
- StockData 类
- StockAnalyzer 类
- AnalysisConfig 类
- AnalysisResult 类
- 便捷函数
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from skills.stock_advisor import (
    StockData,
    StockAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    RiskAssessment,
    Recommendation,
    analyze,
    batch_analyze
)


# ==================== 测试数据 ====================

@pytest.fixture
def sample_df():
    """创建测试数据"""
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=100, freq='D')
    base_price = 100 + np.cumsum(np.random.randn(100) * 0.5)

    return pd.DataFrame({
        'open': base_price + np.random.randn(100) * 0.2,
        'high': base_price + np.abs(np.random.randn(100)) * 1.5,
        'low': base_price - np.abs(np.random.randn(100)) * 1.5,
        'close': base_price,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)


@pytest.fixture
def sample_stock(sample_df):
    """创建测试 StockData"""
    return StockData("000001", "平安银行", sample_df)


# ==================== StockData 测试 ====================

class TestStockData:
    """StockData 测试"""

    def test_initialization(self, sample_stock):
        """测试初始化"""
        assert sample_stock.code == "000001"
        assert sample_stock.name == "平安银行"
        assert sample_stock.data_points == 100

    def test_properties(self, sample_stock):
        """测试基础属性"""
        assert sample_stock.latest_price is not None
        assert len(sample_stock.close) == 100
        assert len(sample_stock.open) == 100
        assert len(sample_stock.high) == 100
        assert len(sample_stock.low) == 100
        assert len(sample_stock.volume) == 100

    def test_date_range(self, sample_stock):
        """测试日期范围"""
        start, end = sample_stock.date_range
        assert start < end

    def test_statistics(self, sample_stock):
        """测试统计方法"""
        volatility = sample_stock.get_volatility()
        max_drawdown = sample_stock.get_max_drawdown()
        sharpe = sample_stock.get_sharpe_ratio()

        assert isinstance(volatility, float)
        assert isinstance(max_drawdown, float)
        assert isinstance(sharpe, float)
        assert volatility >= 0
        assert max_drawdown <= 0

    def test_lazy_indicators(self, sample_stock):
        """测试指标懒计算"""
        # 第一次访问
        indicators1 = sample_stock.indicators
        # 第二次访问 (应该返回缓存)
        indicators2 = sample_stock.indicators
        assert indicators1 is indicators2

    def test_lazy_signals(self, sample_stock):
        """测试信号懒计算"""
        # 第一次访问
        signals1 = sample_stock.signals
        # 第二次访问 (应该返回缓存)
        signals2 = sample_stock.signals
        assert signals1 is signals2

    def test_to_dict(self, sample_stock):
        """测试转换为字典"""
        d = sample_stock.to_dict()
        assert 'code' in d
        assert 'name' in d
        assert 'latest_price' in d

    def test_summary(self, sample_stock):
        """测试摘要生成"""
        summary = sample_stock.summary()
        assert "000001" in summary
        assert "平安银行" in summary

    def test_invalid_dataframe(self):
        """测试无效 DataFrame"""
        df = pd.DataFrame({'a': [1, 2, 3]})
        with pytest.raises(ValueError):
            StockData("000001", "test", df)


# ==================== AnalysisConfig 测试 ====================

class TestAnalysisConfig:
    """AnalysisConfig 测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = AnalysisConfig()
        assert config.risk_profile == "moderate"
        assert config.start_date == "20260101"
        assert config.end_date == "20260614"

    def test_custom_config(self):
        """测试自定义配置"""
        config = AnalysisConfig(
            risk_profile="aggressive",
            start_date="20250101"
        )
        assert config.risk_profile == "aggressive"
        assert config.start_date == "20250101"

    def test_to_dict(self):
        """测试转换为字典"""
        config = AnalysisConfig()
        d = config.to_dict()
        assert 'risk_profile' in d
        assert 'start_date' in d


# ==================== StockAnalyzer 测试 ====================

class TestStockAnalyzer:
    """StockAnalyzer 测试"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = StockAnalyzer()
        assert analyzer.config is not None

    def test_custom_config(self):
        """测试自定义配置"""
        config = AnalysisConfig(risk_profile="aggressive")
        analyzer = StockAnalyzer(config)
        assert analyzer.config.risk_profile == "aggressive"

    def test_cache(self, sample_df):
        """测试数据缓存"""
        # 注意: 这个测试需要 mock 数据获取
        # 这里只测试缓存机制
        analyzer = StockAnalyzer()
        # 模拟缓存
        analyzer._data_cache["test"] = StockData("test", "test", sample_df)
        assert "test" in analyzer._data_cache

    def test_clear_cache(self, sample_df):
        """测试清除缓存"""
        analyzer = StockAnalyzer()
        analyzer._data_cache["test"] = StockData("test", "test", sample_df)
        analyzer.clear_cache()
        assert len(analyzer._data_cache) == 0


# ==================== 数据类测试 ====================

class TestDataClasses:
    """数据类测试"""

    def test_risk_assessment(self):
        """测试 RiskAssessment"""
        risk = RiskAssessment(
            volatility=0.25,
            max_drawdown=-0.15,
            stop_loss_price=10.0,
            take_profit_price=12.0,
            max_position=0.5,
            risk_level="中风险"
        )
        d = risk.to_dict()
        assert 'volatility' in d
        assert 'risk_level' in d

    def test_recommendation(self):
        """测试 Recommendation"""
        rec = Recommendation(
            action="BUY",
            confidence=0.7,
            reason="测试原因",
            target_price=12.0,
            stop_loss=10.0,
            position_ratio=0.5
        )
        d = rec.to_dict()
        assert d['action'] == "BUY"
        assert d['confidence'] == 0.7


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
