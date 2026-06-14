#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票推荐 Skill

综合技术面、基本面、市场面推荐股票

使用示例:
    from skills.stock_recommender import StockRecommender
    recommender = StockRecommender()
    recommendations = recommender.recommend_long_term(top_n=5)
"""

from .recommender import (
    StockRecommender,
    StockRecommendation,
    recommend_long_term,
    recommend_short_term
)

__version__ = '1.0.0'

__all__ = [
    'StockRecommender',
    'StockRecommendation',
    'recommend_long_term',
    'recommend_short_term',
]
