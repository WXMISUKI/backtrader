#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票推荐器

综合技术面、基本面、市场面，推荐买入/卖出股票

推荐类型:
- 长线推荐: 基本面优质 + 技术面支撑
- 短线推荐: 技术面强势 + 市场热点
- 风险匹配推荐: 根据风险偏好推荐
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from skills.stock_fundamental import FundamentalAnalyzer, FundamentalResult
from skills.stock_market import MarketAnalyzer
from skills.stock_advisor import StockAnalyzer, AnalysisConfig


@dataclass
class StockRecommendation:
    """
    股票推荐结果
    """
    stock_code: str           # 股票代码
    stock_name: str           # 股票名称
    recommend_type: str       # 推荐类型 (long_term/short_term)
    current_price: float      # 当前价格
    target_price: float       # 目标价格
    stop_loss: float          # 止损价格
    expected_return: float    # 预期收益
    confidence: float         # 置信度
    reasons: List[str]        # 推荐原因
    risk_level: str           # 风险等级

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'recommend_type': self.recommend_type,
            'current_price': round(self.current_price, 2),
            'target_price': round(self.target_price, 2),
            'stop_loss': round(self.stop_loss, 2),
            'expected_return': round(self.expected_return, 2),
            'confidence': round(self.confidence, 2),
            'reasons': self.reasons,
            'risk_level': self.risk_level,
        }


class StockRecommender:
    """
    股票推荐器

    综合技术面、基本面、市场面推荐股票

    示例:
        >>> recommender = StockRecommender()
        >>> recommendations = recommender.recommend_long_term(top_n=5)
        >>> for rec in recommendations:
        ...     print(f"{rec.stock_name}: {rec.expected_return:.1%}")
    """

    # 股票池
    STOCK_POOL = [
        ("000001", "平安银行"),
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("000333", "美的集团"),
        ("000651", "格力电器"),
        ("600036", "招商银行"),
        ("002594", "比亚迪"),
        ("601318", "中国平安"),
        ("600276", "恒瑞医药"),
        ("000725", "京东方A"),
    ]

    def __init__(self):
        """初始化"""
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.market_analyzer = MarketAnalyzer()

    def recommend_long_term(self, top_n: int = 5) -> List[StockRecommendation]:
        """
        长线推荐

        参数:
            top_n: 返回数量

        返回:
            推荐结果列表
        """
        recommendations = []

        for stock_code, stock_name in self.STOCK_POOL:
            try:
                # 基本面分析
                fundamental = self.fundamental_analyzer.analyze(stock_code)

                # 计算长线得分
                score = self._calc_long_term_score(fundamental)

                if score > 60:  # 只推荐得分超过60的
                    # 获取当前价格 (模拟)
                    current_price = self._get_mock_price(stock_code)

                    # 计算目标价和止损价
                    target_price = current_price * 1.3  # 目标收益30%
                    stop_loss = current_price * 0.9    # 止损10%

                    # 生成推荐原因
                    reasons = self._generate_long_term_reasons(fundamental)

                    recommendation = StockRecommendation(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        recommend_type="long_term",
                        current_price=current_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        expected_return=0.30,
                        confidence=score / 100,
                        reasons=reasons,
                        risk_level="中"
                    )
                    recommendations.append(recommendation)

            except Exception as e:
                print(f"分析 {stock_code} 失败: {e}")

        # 按得分排序
        recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return recommendations[:top_n]

    def recommend_short_term(self, top_n: int = 5) -> List[StockRecommendation]:
        """
        短线推荐

        参数:
            top_n: 返回数量

        返回:
            推荐结果列表
        """
        recommendations = []

        for stock_code, stock_name in self.STOCK_POOL:
            try:
                # 技术面分析 (模拟)
                technical_score = self._calc_short_term_score(stock_code)

                if technical_score > 70:  # 只推荐得分超过70的
                    # 获取当前价格 (模拟)
                    current_price = self._get_mock_price(stock_code)

                    # 计算目标价和止损价
                    target_price = current_price * 1.15  # 目标收益15%
                    stop_loss = current_price * 0.95    # 止损5%

                    # 生成推荐原因
                    reasons = self._generate_short_term_reasons(stock_code)

                    recommendation = StockRecommendation(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        recommend_type="short_term",
                        current_price=current_price,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        expected_return=0.15,
                        confidence=technical_score / 100,
                        reasons=reasons,
                        risk_level="高"
                    )
                    recommendations.append(recommendation)

            except Exception as e:
                print(f"分析 {stock_code} 失败: {e}")

        # 按得分排序
        recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return recommendations[:top_n]

    def recommend_by_risk(self, risk_level: str = "moderate") -> List[StockRecommendation]:
        """
        按风险偏好推荐

        参数:
            risk_level: 风险等级 (conservative/moderate/aggressive)

        返回:
            推荐结果列表
        """
        if risk_level == "conservative":
            # 保守型：长线为主
            return self.recommend_long_term(top_n=5)
        elif risk_level == "aggressive":
            # 激进型：短线为主
            return self.recommend_short_term(top_n=5)
        else:
            # 稳健型：混合推荐
            long_term = self.recommend_long_term(top_n=3)
            short_term = self.recommend_short_term(top_n=2)
            return long_term + short_term

    def _calc_long_term_score(self, fundamental: FundamentalResult) -> float:
        """
        计算长线得分

        参数:
            fundamental: 基本面分析结果

        返回:
            得分 (0-100)
        """
        return fundamental.score

    def _calc_short_term_score(self, stock_code: str) -> float:
        """
        计算短线得分

        参数:
            stock_code: 股票代码

        返回:
            得分 (0-100)
        """
        # 模拟技术面得分
        np.random.seed(hash(stock_code) % 1000)
        return np.random.uniform(50, 95)

    def _get_mock_price(self, stock_code: str) -> float:
        """
        获取模拟价格

        参数:
            stock_code: 股票代码

        返回:
            价格
        """
        prices = {
            '000001': 11.50,
            '600519': 1850.00,
            '000858': 155.00,
            '000333': 65.00,
            '000651': 38.00,
            '600036': 35.00,
            '002594': 250.00,
            '601318': 52.00,
            '600276': 45.00,
            '000725': 4.50,
        }
        return prices.get(stock_code, 100.0)

    def _generate_long_term_reasons(self, fundamental: FundamentalResult) -> List[str]:
        """
        生成长线推荐原因

        参数:
            fundamental: 基本面分析结果

        返回:
            原因列表
        """
        reasons = []

        if fundamental.roe > 15:
            reasons.append(f"ROE={fundamental.roe:.1f}%，盈利能力强")
        if fundamental.pe_ratio < 20:
            reasons.append(f"PE={fundamental.pe_ratio:.1f}，估值合理")
        if fundamental.revenue_growth > 10:
            reasons.append(f"营收增长{fundamental.revenue_growth:.1f}%，成长性好")
        if fundamental.debt_ratio < 60:
            reasons.append(f"资产负债率{fundamental.debt_ratio:.1f}%，财务稳健")

        if not reasons:
            reasons.append("基本面综合评分较高")

        return reasons

    def _generate_short_term_reasons(self, stock_code: str) -> List[str]:
        """
        生成短线推荐原因

        参数:
            stock_code: 股票代码

        返回:
            原因列表
        """
        # 模拟短线原因
        reasons_pool = [
            "技术面金叉信号",
            "MACD向上突破",
            "RSI超卖反弹",
            "成交量放大",
            "突破关键阻力位",
            "板块轮动受益",
            "主力资金流入",
        ]

        np.random.seed(hash(stock_code) % 1000)
        return list(np.random.choice(reasons_pool, size=3, replace=False))


# 便捷函数
def recommend_long_term(top_n: int = 5) -> List[StockRecommendation]:
    """
    长线推荐 (便捷函数)

    参数:
        top_n: 返回数量

    返回:
        推荐结果列表
    """
    recommender = StockRecommender()
    return recommender.recommend_long_term(top_n)


def recommend_short_term(top_n: int = 5) -> List[StockRecommendation]:
    """
    短线推荐 (便捷函数)

    参数:
        top_n: 返回数量

    返回:
        推荐结果列表
    """
    recommender = StockRecommender()
    return recommender.recommend_short_term(top_n)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("股票推荐器测试")
    print("=" * 60)

    # 创建推荐器
    recommender = StockRecommender()

    # 测试长线推荐
    print("\n1. 长线推荐:")
    long_term = recommender.recommend_long_term(top_n=3)
    for rec in long_term:
        print(f"  {rec.stock_name}: 预期收益={rec.expected_return:.0%}, 置信度={rec.confidence:.0%}")
        print(f"    原因: {', '.join(rec.reasons)}")

    # 测试短线推荐
    print("\n2. 短线推荐:")
    short_term = recommender.recommend_short_term(top_n=3)
    for rec in short_term:
        print(f"  {rec.stock_name}: 预期收益={rec.expected_return:.0%}, 置信度={rec.confidence:.0%}")
        print(f"    原因: {', '.join(rec.reasons)}")

    # 测试风险匹配推荐
    print("\n3. 风险匹配推荐 (稳健型):")
    risk_recs = recommender.recommend_by_risk("moderate")
    for rec in risk_recs:
        print(f"  {rec.stock_name} [{rec.recommend_type}]: 置信度={rec.confidence:.0%}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
