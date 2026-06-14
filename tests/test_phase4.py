#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 4 智能投顾系统单元测试

测试覆盖:
- 基本面分析模块
- 市场分析模块
- 股票推荐模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from skills.stock_fundamental import (
    FundamentalAnalyzer,
    FundamentalResult,
    analyze_fundamental
)
from skills.stock_market import (
    MarketAnalyzer,
    MarketOverview,
    MarketSentiment,
    IndexData,
    SectorData,
    get_market_overview
)
from skills.stock_recommender import (
    StockRecommender,
    StockRecommendation,
    recommend_long_term,
    recommend_short_term
)


# ==================== 基本面分析测试 ====================

class TestFundamentalResult:
    """FundamentalResult 测试"""

    def test_initialization(self):
        """测试初始化"""
        result = FundamentalResult(
            stock_code="000001",
            stock_name="平安银行",
            pe_ratio=8.5,
            pb_ratio=0.7,
            roe=12.5,
            score=75.0,
            rating="良好"
        )
        assert result.stock_code == "000001"
        assert result.pe_ratio == 8.5
        assert result.score == 75.0

    def test_to_dict(self):
        """测试转换为字典"""
        result = FundamentalResult(
            stock_code="000001",
            stock_name="平安银行",
            pe_ratio=8.5,
            score=75.0
        )
        d = result.to_dict()
        assert d['stock_code'] == "000001"
        assert d['valuation']['pe_ratio'] == 8.5

    def test_summary(self):
        """测试摘要生成"""
        result = FundamentalResult(
            stock_code="000001",
            stock_name="平安银行",
            pe_ratio=8.5,
            roe=12.5,
            score=75.0,
            rating="良好"
        )
        summary = result.summary()
        assert "平安银行" in summary
        assert "良好" in summary


class TestFundamentalAnalyzer:
    """FundamentalAnalyzer 测试"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = FundamentalAnalyzer()
        assert len(analyzer._mock_data) > 0

    def test_analyze(self):
        """测试分析"""
        analyzer = FundamentalAnalyzer()
        result = analyzer.analyze("600519")
        assert result.stock_code == "600519"
        assert result.stock_name == "贵州茅台"
        assert result.score > 0

    def test_analyze_unknown(self):
        """测试未知股票"""
        analyzer = FundamentalAnalyzer()
        result = analyzer.analyze("999999")
        assert result.stock_code == "999999"
        assert result.rating == "未知"

    def test_batch_analyze(self):
        """测试批量分析"""
        analyzer = FundamentalAnalyzer()
        results = analyzer.batch_analyze(["000001", "600519"])
        assert len(results) == 2

    def test_get_top_stocks(self):
        """测试获取排名"""
        analyzer = FundamentalAnalyzer()
        top = analyzer.get_top_stocks(3)
        assert len(top) <= 3
        assert top[0].score >= top[1].score


class TestAnalyzeFundamental:
    """analyze_fundamental 便捷函数测试"""

    def test_function(self):
        """测试函数"""
        result = analyze_fundamental("600519")
        assert result.stock_code == "600519"


# ==================== 市场分析测试 ====================

class TestIndexData:
    """IndexData 测试"""

    def test_initialization(self):
        """测试初始化"""
        idx = IndexData(name="上证指数", code="000001", current=3200.50, change_pct=0.85, volume=350000000000)
        assert idx.name == "上证指数"
        assert idx.current == 3200.50

    def test_to_dict(self):
        """测试转换为字典"""
        idx = IndexData(name="上证指数", code="000001", current=3200.50, change_pct=0.85, volume=350000000000)
        d = idx.to_dict()
        assert d['name'] == "上证指数"


class TestSectorData:
    """SectorData 测试"""

    def test_initialization(self):
        """测试初始化"""
        sector = SectorData(name="半导体", change_pct=3.50, leading_stock="中芯国际", stock_count=50)
        assert sector.name == "半导体"
        assert sector.change_pct == 3.50

    def test_to_dict(self):
        """测试转换为字典"""
        sector = SectorData(name="半导体", change_pct=3.50, leading_stock="中芯国际", stock_count=50)
        d = sector.to_dict()
        assert d['name'] == "半导体"


class TestMarketSentiment:
    """MarketSentiment 测试"""

    def test_initialization(self):
        """测试初始化"""
        sentiment = MarketSentiment(
            rise_count=3200,
            fall_count=1500,
            flat_count=300,
            rise_ratio=0.64,
            limit_up=45,
            limit_down=8,
            total_volume=1000000000000,
            northbound_flow=85.5
        )
        assert sentiment.rise_count == 3200
        assert sentiment.rise_ratio == 0.64


class TestMarketAnalyzer:
    """MarketAnalyzer 测试"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = MarketAnalyzer()
        assert len(analyzer._mock_indices) > 0

    def test_get_market_overview(self):
        """测试获取市场概览"""
        analyzer = MarketAnalyzer()
        overview = analyzer.get_market_overview()
        assert len(overview.indices) > 0
        assert len(overview.hot_sectors) > 0
        assert overview.market_trend in ["牛市", "熊市", "震荡"]

    def test_get_sector_performance(self):
        """测试获取板块表现"""
        analyzer = MarketAnalyzer()
        df = analyzer.get_sector_performance()
        assert len(df) > 0
        assert 'name' in df.columns

    def test_get_market_sentiment(self):
        """测试获取市场情绪"""
        analyzer = MarketAnalyzer()
        sentiment = analyzer.get_market_sentiment()
        assert 'rise_count' in sentiment
        assert 'rise_ratio' in sentiment

    def test_is_bullish(self):
        """测试判断牛市"""
        analyzer = MarketAnalyzer()
        result = analyzer.is_bullish()
        assert isinstance(result, bool)

    def test_get_hot_sectors(self):
        """测试获取热门板块"""
        analyzer = MarketAnalyzer()
        sectors = analyzer.get_hot_sectors(3)
        assert len(sectors) <= 3


class TestGetMarketOverview:
    """get_market_overview 便捷函数测试"""

    def test_function(self):
        """测试函数"""
        overview = get_market_overview()
        assert len(overview.indices) > 0


# ==================== 股票推荐测试 ====================

class TestStockRecommendation:
    """StockRecommendation 测试"""

    def test_initialization(self):
        """测试初始化"""
        rec = StockRecommendation(
            stock_code="000001",
            stock_name="平安银行",
            recommend_type="long_term",
            current_price=11.50,
            target_price=15.00,
            stop_loss=10.00,
            expected_return=0.30,
            confidence=0.75,
            reasons=["ROE高", "PE低"],
            risk_level="中"
        )
        assert rec.stock_code == "000001"
        assert rec.expected_return == 0.30

    def test_to_dict(self):
        """测试转换为字典"""
        rec = StockRecommendation(
            stock_code="000001",
            stock_name="平安银行",
            recommend_type="long_term",
            current_price=11.50,
            target_price=15.00,
            stop_loss=10.00,
            expected_return=0.30,
            confidence=0.75,
            reasons=["ROE高"],
            risk_level="中"
        )
        d = rec.to_dict()
        assert d['stock_code'] == "000001"
        assert 'reasons' in d


class TestStockRecommender:
    """StockRecommender 测试"""

    def test_initialization(self):
        """测试初始化"""
        recommender = StockRecommender()
        assert len(recommender.STOCK_POOL) > 0

    def test_recommend_long_term(self):
        """测试长线推荐"""
        recommender = StockRecommender()
        recs = recommender.recommend_long_term(top_n=3)
        assert len(recs) <= 3
        for rec in recs:
            assert rec.recommend_type == "long_term"
            assert rec.confidence > 0

    def test_recommend_short_term(self):
        """测试短线推荐"""
        recommender = StockRecommender()
        recs = recommender.recommend_short_term(top_n=3)
        assert len(recs) <= 3
        for rec in recs:
            assert rec.recommend_type == "short_term"
            assert rec.confidence > 0

    def test_recommend_by_risk(self):
        """测试风险匹配推荐"""
        recommender = StockRecommender()

        # 保守型
        conservative = recommender.recommend_by_risk("conservative")
        assert len(conservative) > 0

        # 稳健型
        moderate = recommender.recommend_by_risk("moderate")
        assert len(moderate) > 0

        # 激进型
        aggressive = recommender.recommend_by_risk("aggressive")
        assert len(aggressive) > 0


class TestRecommendFunctions:
    """便捷函数测试"""

    def test_recommend_long_term(self):
        """测试长线推荐函数"""
        recs = recommend_long_term(3)
        assert len(recs) <= 3

    def test_recommend_short_term(self):
        """测试短线推荐函数"""
        recs = recommend_short_term(3)
        assert len(recs) <= 3


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
