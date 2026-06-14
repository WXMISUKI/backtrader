#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基本面分析器

分析股票的基本面数据，包括财务指标、估值指标、成长性指标等

指标类别:
- 估值指标: PE、PB、PS
- 盈利指标: ROE、ROA、毛利率
- 成长指标: 营收增长率、净利润增长率
- 安全指标: 资产负债率、流动比率
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class FundamentalResult:
    """
    基本面分析结果
    """
    stock_code: str = ""           # 股票代码
    stock_name: str = ""           # 股票名称

    # 估值指标
    pe_ratio: float = 0.0          # 市盈率
    pb_ratio: float = 0.0          # 市净率
    ps_ratio: float = 0.0          # 市销率

    # 盈利指标
    roe: float = 0.0               # 净资产收益率
    roa: float = 0.0               # 总资产收益率
    gross_margin: float = 0.0      # 毛利率
    net_margin: float = 0.0        # 净利率

    # 成长指标
    revenue_growth: float = 0.0    # 营收增长率
    profit_growth: float = 0.0     # 净利润增长率

    # 安全指标
    debt_ratio: float = 0.0        # 资产负债率
    current_ratio: float = 0.0     # 流动比率

    # 综合评分
    score: float = 0.0             # 综合得分 (0-100)
    rating: str = ""               # 评级 (优秀/良好/一般/较差)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'valuation': {
                'pe_ratio': round(self.pe_ratio, 2),
                'pb_ratio': round(self.pb_ratio, 2),
                'ps_ratio': round(self.ps_ratio, 2),
            },
            'profitability': {
                'roe': round(self.roe, 2),
                'roa': round(self.roa, 2),
                'gross_margin': round(self.gross_margin, 2),
                'net_margin': round(self.net_margin, 2),
            },
            'growth': {
                'revenue_growth': round(self.revenue_growth, 2),
                'profit_growth': round(self.profit_growth, 2),
            },
            'safety': {
                'debt_ratio': round(self.debt_ratio, 2),
                'current_ratio': round(self.current_ratio, 2),
            },
            'score': round(self.score, 2),
            'rating': self.rating,
        }

    def summary(self) -> str:
        """生成摘要"""
        return (
            f"{'='*50}\n"
            f"基本面分析报告 - {self.stock_name}({self.stock_code})\n"
            f"{'='*50}\n"
            f"【估值指标】\n"
            f"  PE: {self.pe_ratio:.2f}\n"
            f"  PB: {self.pb_ratio:.2f}\n"
            f"  PS: {self.ps_ratio:.2f}\n"
            f"{'─'*50}\n"
            f"【盈利指标】\n"
            f"  ROE: {self.roe:.2f}%\n"
            f"  ROA: {self.roa:.2f}%\n"
            f"  毛利率: {self.gross_margin:.2f}%\n"
            f"  净利率: {self.net_margin:.2f}%\n"
            f"{'─'*50}\n"
            f"【成长指标】\n"
            f"  营收增长: {self.revenue_growth:.2f}%\n"
            f"  利润增长: {self.profit_growth:.2f}%\n"
            f"{'─'*50}\n"
            f"【安全指标】\n"
            f"  资产负债率: {self.debt_ratio:.2f}%\n"
            f"  流动比率: {self.current_ratio:.2f}\n"
            f"{'─'*50}\n"
            f"【综合评价】\n"
            f"  得分: {self.score:.2f}/100\n"
            f"  评级: {self.rating}\n"
            f"{'='*50}\n"
        )


class FundamentalAnalyzer:
    """
    基本面分析器

    分析股票的基本面数据

    示例:
        >>> analyzer = FundamentalAnalyzer()
        >>> result = analyzer.analyze("000001")
        >>> print(result.summary())
    """

    # 评级标准
    RATING_THRESHOLDS = {
        'excellent': 80,   # 优秀
        'good': 60,        # 良好
        'average': 40,     # 一般
        'poor': 0,         # 较差
    }

    def __init__(self):
        """初始化"""
        # 模拟基本面数据 (实际应用中应从API获取)
        self._mock_data = self._get_mock_data()

    def _get_mock_data(self) -> dict:
        """获取模拟数据"""
        return {
            '000001': {
                'name': '平安银行',
                'pe_ratio': 8.5,
                'pb_ratio': 0.7,
                'ps_ratio': 1.2,
                'roe': 12.5,
                'roa': 0.9,
                'gross_margin': 55.0,
                'net_margin': 35.0,
                'revenue_growth': 8.5,
                'profit_growth': 10.2,
                'debt_ratio': 92.0,
                'current_ratio': 1.1,
            },
            '600519': {
                'name': '贵州茅台',
                'pe_ratio': 35.0,
                'pb_ratio': 12.0,
                'ps_ratio': 18.0,
                'roe': 32.0,
                'roa': 25.0,
                'gross_margin': 92.0,
                'net_margin': 52.0,
                'revenue_growth': 15.0,
                'profit_growth': 18.0,
                'debt_ratio': 20.0,
                'current_ratio': 3.5,
            },
            '000858': {
                'name': '五粮液',
                'pe_ratio': 25.0,
                'pb_ratio': 7.0,
                'ps_ratio': 10.0,
                'roe': 25.0,
                'roa': 18.0,
                'gross_margin': 75.0,
                'net_margin': 38.0,
                'revenue_growth': 12.0,
                'profit_growth': 14.0,
                'debt_ratio': 30.0,
                'current_ratio': 2.8,
            },
            '000333': {
                'name': '美的集团',
                'pe_ratio': 12.0,
                'pb_ratio': 3.0,
                'ps_ratio': 1.5,
                'roe': 22.0,
                'roa': 8.0,
                'gross_margin': 25.0,
                'net_margin': 9.0,
                'revenue_growth': 10.0,
                'profit_growth': 12.0,
                'debt_ratio': 65.0,
                'current_ratio': 1.2,
            },
            '000651': {
                'name': '格力电器',
                'pe_ratio': 8.0,
                'pb_ratio': 2.5,
                'ps_ratio': 1.2,
                'roe': 28.0,
                'roa': 10.0,
                'gross_margin': 30.0,
                'net_margin': 13.0,
                'revenue_growth': 5.0,
                'profit_growth': 8.0,
                'debt_ratio': 68.0,
                'current_ratio': 1.1,
            },
        }

    def analyze(self, stock_code: str) -> FundamentalResult:
        """
        分析股票基本面

        参数:
            stock_code: 股票代码

        返回:
            FundamentalResult 分析结果
        """
        # 获取数据
        data = self._mock_data.get(stock_code)
        if data is None:
            # 返回默认值
            return FundamentalResult(
                stock_code=stock_code,
                stock_name=f"股票{stock_code}",
                rating="未知"
            )

        # 创建结果
        result = FundamentalResult(
            stock_code=stock_code,
            stock_name=data['name'],
            pe_ratio=data['pe_ratio'],
            pb_ratio=data['pb_ratio'],
            ps_ratio=data['ps_ratio'],
            roe=data['roe'],
            roa=data['roa'],
            gross_margin=data['gross_margin'],
            net_margin=data['net_margin'],
            revenue_growth=data['revenue_growth'],
            profit_growth=data['profit_growth'],
            debt_ratio=data['debt_ratio'],
            current_ratio=data['current_ratio'],
        )

        # 计算综合得分
        result.score = self._calc_score(result)
        result.rating = self._get_rating(result.score)

        return result

    def _calc_score(self, result: FundamentalResult) -> float:
        """
        计算综合得分

        参数:
            result: 基本面分析结果

        返回:
            综合得分 (0-100)
        """
        score = 0.0

        # 估值得分 (25分)
        valuation_score = 0
        if result.pe_ratio > 0 and result.pe_ratio < 15:
            valuation_score += 10
        elif result.pe_ratio >= 15 and result.pe_ratio < 25:
            valuation_score += 5

        if result.pb_ratio > 0 and result.pb_ratio < 3:
            valuation_score += 10
        elif result.pb_ratio >= 3 and result.pb_ratio < 5:
            valuation_score += 5

        if result.ps_ratio > 0 and result.ps_ratio < 5:
            valuation_score += 5

        score += valuation_score

        # 盈利得分 (30分)
        profitability_score = 0
        if result.roe > 20:
            profitability_score += 15
        elif result.roe > 15:
            profitability_score += 10
        elif result.roe > 10:
            profitability_score += 5

        if result.gross_margin > 50:
            profitability_score += 10
        elif result.gross_margin > 30:
            profitability_score += 5

        if result.net_margin > 20:
            profitability_score += 5

        score += profitability_score

        # 成长得分 (25分)
        growth_score = 0
        if result.revenue_growth > 20:
            growth_score += 12
        elif result.revenue_growth > 10:
            growth_score += 8
        elif result.revenue_growth > 5:
            growth_score += 4

        if result.profit_growth > 20:
            growth_score += 13
        elif result.profit_growth > 10:
            growth_score += 8
        elif result.profit_growth > 5:
            growth_score += 4

        score += growth_score

        # 安全得分 (20分)
        safety_score = 0
        if result.debt_ratio < 50:
            safety_score += 10
        elif result.debt_ratio < 70:
            safety_score += 5

        if result.current_ratio > 2:
            safety_score += 10
        elif result.current_ratio > 1.5:
            safety_score += 5

        score += safety_score

        return min(100, score)

    def _get_rating(self, score: float) -> str:
        """
        获取评级

        参数:
            score: 综合得分

        返回:
            评级字符串
        """
        if score >= self.RATING_THRESHOLDS['excellent']:
            return '优秀'
        elif score >= self.RATING_THRESHOLDS['good']:
            return '良好'
        elif score >= self.RATING_THRESHOLDS['average']:
            return '一般'
        else:
            return '较差'

    def batch_analyze(self, stock_codes: List[str]) -> List[FundamentalResult]:
        """
        批量分析

        参数:
            stock_codes: 股票代码列表

        返回:
            分析结果列表
        """
        return [self.analyze(code) for code in stock_codes]

    def get_top_stocks(self, top_n: int = 10) -> List[FundamentalResult]:
        """
        获取基本面最优质的股票

        参数:
            top_n: 返回数量

        返回:
            分析结果列表
        """
        results = self.batch_analyze(list(self._mock_data.keys()))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_n]


# 便捷函数
def analyze_fundamental(stock_code: str) -> FundamentalResult:
    """
    分析股票基本面 (便捷函数)

    参数:
        stock_code: 股票代码

    返回:
        FundamentalResult 分析结果
    """
    analyzer = FundamentalAnalyzer()
    return analyzer.analyze(stock_code)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("基本面分析器测试")
    print("=" * 60)

    # 创建分析器
    analyzer = FundamentalAnalyzer()

    # 测试单个分析
    print("\n1. 单个股票分析:")
    result = analyzer.analyze("600519")
    print(result.summary())

    # 测试批量分析
    print("\n2. 批量分析:")
    results = analyzer.batch_analyze(["000001", "600519", "000858"])
    for r in results:
        print(f"  {r.stock_name}: 得分={r.score:.2f}, 评级={r.rating}")

    # 测试排名
    print("\n3. 基本面排名:")
    top_stocks = analyzer.get_top_stocks(3)
    for i, r in enumerate(top_stocks, 1):
        print(f"  {i}. {r.stock_name}: 得分={r.score:.2f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
