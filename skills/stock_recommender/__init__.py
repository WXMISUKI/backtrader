#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票推荐 Skill

综合技术面、基本面、市场面推荐股票

使用示例:
    # 基于规则的推荐
    from skills.stock_recommender import StockRecommender
    recommender = StockRecommender()
    recommendations = recommender.recommend_long_term(top_n=5)

    # 基于机器学习的推荐
    from skills.stock_recommender import MLRecommender
    ml_recommender = MLRecommender()
    ml_recommender.train()
    predictions = ml_recommender.recommend(top_n=5)
"""

from .recommender import (
    StockRecommender,
    StockRecommendation,
    recommend_long_term,
    recommend_short_term
)

from .ml_recommender import (
    MLRecommender,
    MLPrediction,
    train_ml_model
)

__version__ = '1.0.0'

__all__ = [
    # 基于规则的推荐
    'StockRecommender',
    'StockRecommendation',
    'recommend_long_term',
    'recommend_short_term',

    # 基于机器学习的推荐
    'MLRecommender',
    'MLPrediction',
    'train_ml_model',
]
