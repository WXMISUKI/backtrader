#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实数据和机器学习模块单元测试

测试覆盖:
- RealDataProvider
- MLRecommender
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from core.data.real_provider import (
    RealDataProvider,
    FinancialIndicators,
    get_financial_indicators
)
from skills.stock_recommender.ml_recommender import (
    MLRecommender,
    MLPrediction,
    train_ml_model
)


# ==================== RealDataProvider 测试 ====================

class TestFinancialIndicators:
    """FinancialIndicators 测试"""

    def test_initialization(self):
        """测试初始化"""
        indicators = FinancialIndicators(
            stock_code="000001",
            report_date="2026-03-31",
            eps=0.75,
            roe=12.5,
            debt_ratio=92.0
        )
        assert indicators.stock_code == "000001"
        assert indicators.eps == 0.75
        assert indicators.roe == 12.5

    def test_to_dict(self):
        """测试转换为字典"""
        indicators = FinancialIndicators(
            stock_code="000001",
            eps=0.75,
            roe=12.5
        )
        d = indicators.to_dict()
        assert d['stock_code'] == "000001"
        assert d['eps'] == 0.75
        assert d['roe'] == 12.5


class TestRealDataProvider:
    """RealDataProvider 测试"""

    def test_initialization(self):
        """测试初始化"""
        provider = RealDataProvider()
        assert provider.use_cache == True

    def test_initialization_no_cache(self):
        """测试不使用缓存"""
        provider = RealDataProvider(use_cache=False)
        assert provider.use_cache == False

    def test_safe_float(self):
        """测试安全转换"""
        provider = RealDataProvider()
        assert provider._safe_float(None) == 0.0
        assert provider._safe_float(np.nan) == 0.0
        assert provider._safe_float(1.5) == 1.5
        assert provider._safe_float("2.5") == 2.5

    def test_cache(self):
        """测试缓存"""
        provider = RealDataProvider(use_cache=True)
        provider._set_cache("test_key", "test_value")
        assert provider._get_cache("test_key") == "test_value"

    def test_cache_expired(self):
        """测试缓存过期"""
        provider = RealDataProvider(use_cache=True, cache_ttl=0)
        provider._set_cache("test_key", "test_value")
        import time
        time.sleep(0.1)
        assert provider._get_cache("test_key") is None


class TestGetFinancialIndicators:
    """get_financial_indicators 便捷函数测试"""

    def test_function(self):
        """测试函数"""
        indicators = get_financial_indicators("000001")
        assert isinstance(indicators, FinancialIndicators)
        assert indicators.stock_code == "000001"


# ==================== MLRecommender 测试 ====================

class TestMLPrediction:
    """MLPrediction 测试"""

    def test_initialization(self):
        """测试初始化"""
        pred = MLPrediction(
            stock_code="000001",
            stock_name="平安银行",
            predicted_return=0.15,
            confidence=0.75,
            signal="BUY",
            features={'pe_ratio': 8.5}
        )
        assert pred.stock_code == "000001"
        assert pred.predicted_return == 0.15
        assert pred.signal == "BUY"

    def test_to_dict(self):
        """测试转换为字典"""
        pred = MLPrediction(
            stock_code="000001",
            stock_name="平安银行",
            predicted_return=0.15,
            confidence=0.75,
            signal="BUY",
            features={}
        )
        d = pred.to_dict()
        assert d['stock_code'] == "000001"
        assert d['signal'] == "BUY"


class TestMLRecommender:
    """MLRecommender 测试"""

    def test_initialization(self):
        """测试初始化"""
        recommender = MLRecommender()
        assert recommender.model_type == "random_forest"
        assert recommender.model is None

    def test_initialization_with_type(self):
        """测试指定模型类型"""
        recommender = MLRecommender(model_type="xgboost")
        assert recommender.model_type == "xgboost"

    def test_prepare_features(self):
        """测试准备特征"""
        recommender = MLRecommender()
        X, y = recommender.prepare_features(["000001", "600519"])
        assert len(X) > 0
        assert len(y) > 0
        assert len(X) == len(y)

    def test_train(self):
        """测试训练"""
        import sklearn
        recommender = MLRecommender()
        recommender.train(["000001", "600519", "000858"])
        assert recommender.model is not None

    def test_predict_without_training(self):
        """测试未训练时预测"""
        recommender = MLRecommender()
        predictions = recommender.predict(["000001"])
        assert len(predictions) == 0

    def test_predict_after_training(self):
        """测试训练后预测"""
        import sklearn
        recommender = MLRecommender()
        recommender.train(["000001", "600519", "000858"])
        predictions = recommender.predict(["000001"])
        assert len(predictions) > 0
        assert predictions[0].stock_code == "000001"

    def test_recommend(self):
        """测试推荐"""
        import sklearn
        recommender = MLRecommender()
        recommender.train()
        recommendations = recommender.recommend(top_n=3)
        assert len(recommendations) <= 3


class TestTrainMLModel:
    """train_ml_model 便捷函数测试"""

    def test_function(self):
        """测试函数"""
        import sklearn
        recommender = train_ml_model(["000001", "600519"])
        assert recommender.model is not None


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
