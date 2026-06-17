#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实数据提供器

使用 akshare 获取真实的股票基本面数据

数据类型:
- 财务指标: ROE/ROA/毛利率等
- 财务摘要: 综合财务数据
- 成长能力: 增长率对比
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from functools import lru_cache
import time

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

from .governance import build_snapshot, DataQualityChecker


@dataclass
class FinancialIndicators:
    """
    财务指标
    """
    stock_code: str = ""
    report_date: str = ""

    # 每股指标
    eps: float = 0.0               # 每股收益
    bps: float = 0.0               # 每股净资产
    cfps: float = 0.0              # 每股现金流

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

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'report_date': self.report_date,
            'eps': round(self.eps, 4),
            'bps': round(self.bps, 4),
            'roe': round(self.roe, 2),
            'roa': round(self.roa, 2),
            'gross_margin': round(self.gross_margin, 2),
            'net_margin': round(self.net_margin, 2),
            'revenue_growth': round(self.revenue_growth, 2),
            'profit_growth': round(self.profit_growth, 2),
            'debt_ratio': round(self.debt_ratio, 2),
            'current_ratio': round(self.current_ratio, 2),
        }


class RealDataProvider:
    """
    真实数据提供器

    使用 akshare 获取真实的股票基本面数据

    示例:
        >>> provider = RealDataProvider()
        >>> indicators = provider.get_financial_indicators("000001")
        >>> print(indicators.roe)
    """

    def __init__(self, use_cache: bool = True, cache_ttl: int = 3600):
        """
        初始化

        参数:
            use_cache: 是否使用缓存
            cache_ttl: 缓存过期时间(秒)
        """
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_time = {}
        self._quality = DataQualityChecker()

    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.use_cache:
            return None
        if key in self._cache:
            if time.time() - self._cache_time.get(key, 0) < self.cache_ttl:
                return self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        if self.use_cache:
            self._cache[key] = value
            self._cache_time[key] = time.time()

    def get_financial_indicators(self, stock_code: str) -> FinancialIndicators:
        """
        获取财务指标

        参数:
            stock_code: 股票代码

        返回:
            FinancialIndicators 财务指标
        """
        cache_key = f"indicators_{stock_code}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        if not HAS_AKSHARE:
            return FinancialIndicators(stock_code=stock_code)

        try:
            # 获取财务分析指标
            df = ak.stock_financial_analysis_indicator(symbol=stock_code, start_year='2023')

            if df is None or len(df) == 0:
                return FinancialIndicators(stock_code=stock_code)

            # 获取最新数据
            latest = df.iloc[0]

            # 解析数据
            indicators = FinancialIndicators(
                stock_code=stock_code,
                report_date=str(latest.get('日期', '')),
                eps=self._safe_float(latest.get('摊薄每股收益(元)')),
                bps=self._safe_float(latest.get('每股净资产_调整前(元)')),
                cfps=self._safe_float(latest.get('每股经营性现金流(元)')),
                roe=self._safe_float(latest.get('净资产收益率(%)')),
                roa=self._safe_float(latest.get('总资产利润率(%)')),
                gross_margin=self._safe_float(latest.get('销售毛利率(%)')),
                net_margin=self._safe_float(latest.get('销售净利率(%)')),
                revenue_growth=self._safe_float(latest.get('主营业务收入增长率(%)')),
                profit_growth=self._safe_float(latest.get('净利润增长率(%)')),
                debt_ratio=self._safe_float(latest.get('资产负债率(%)')),
                current_ratio=self._safe_float(latest.get('流动比率')),
            )

            self._set_cache(cache_key, indicators)
            return indicators

        except Exception as e:
            print(f"获取 {stock_code} 财务指标失败: {e}")
            return FinancialIndicators(stock_code=stock_code)

    def get_financial_indicators_governed(self, stock_code: str) -> dict:
        """
        获取治理后的财务指标快照。

        返回结果保留财务指标，同时补充来源、质量和降级原因。
        """
        cached = self._get_cache(f"governed_indicators_{stock_code}")
        if cached is not None:
            return cached

        indicators = self.get_financial_indicators(stock_code)
        payload = indicators.to_dict()
        is_degraded = all(
            payload.get(field, 0) == 0
            for field in ("eps", "roe", "debt_ratio", "current_ratio")
        )

        snapshot = build_snapshot(
            name=f"financial_indicators:{stock_code}",
            payload=payload,
            source="real" if not is_degraded else "mock",
            degraded=is_degraded,
            reason="" if not is_degraded else "financial indicators unavailable or empty fallback",
        )
        snapshot.data_source = snapshot.source
        snapshot.quality = self._quality.check_dict(payload)
        governed = snapshot.to_dict()
        self._set_cache(f"governed_indicators_{stock_code}", governed)
        return governed

    def get_financial_abstract(self, stock_code: str) -> pd.DataFrame:
        """
        获取财务摘要

        参数:
            stock_code: 股票代码

        返回:
            财务摘要 DataFrame
        """
        cache_key = f"abstract_{stock_code}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        if not HAS_AKSHARE:
            return pd.DataFrame()

        try:
            df = ak.stock_financial_abstract(symbol=stock_code)
            self._set_cache(cache_key, df)
            return df
        except Exception as e:
            print(f"获取 {stock_code} 财务摘要失败: {e}")
            return pd.DataFrame()

    def get_growth_comparison(self, stock_code: str) -> dict:
        """
        获取成长能力对比

        参数:
            stock_code: 股票代码

        返回:
            成长数据字典
        """
        cache_key = f"growth_{stock_code}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        if not HAS_AKSHARE:
            return {}

        try:
            df = ak.stock_zh_growth_comparison_em(symbol=stock_code)

            if df is None or len(df) == 0:
                return {}

            # 获取数据
            row = df.iloc[0]
            result = {
                'eps_growth_3y': self._safe_float(row.get('基本每股收益增长率-3年复合')),
                'eps_growth_24a': self._safe_float(row.get('基本每股收益增长率-24A')),
                'revenue_growth_3y': self._safe_float(row.get('营业收入增长率-3年复合')),
                'revenue_growth_24a': self._safe_float(row.get('营业收入增长率-24A')),
            }

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"获取 {stock_code} 成长数据失败: {e}")
            return {}

    def batch_get_indicators(self, stock_codes: List[str]) -> List[FinancialIndicators]:
        """
        批量获取财务指标

        参数:
            stock_codes: 股票代码列表

        返回:
            财务指标列表
        """
        results = []
        for code in stock_codes:
            indicators = self.get_financial_indicators(code)
            results.append(indicators)
            time.sleep(0.5)  # 避免请求过快
        return results

    def _safe_float(self, value) -> float:
        """安全转换为浮点数"""
        if value is None or pd.isna(value):
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# 便捷函数
def get_financial_indicators(stock_code: str) -> FinancialIndicators:
    """
    获取财务指标 (便捷函数)

    参数:
        stock_code: 股票代码

    返回:
        FinancialIndicators 财务指标
    """
    provider = RealDataProvider()
    return provider.get_financial_indicators(stock_code)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("真实数据提供器测试")
    print("=" * 60)

    # 创建提供器
    provider = RealDataProvider()

    # 测试财务指标
    print("\n1. 获取平安银行(000001)财务指标:")
    indicators = provider.get_financial_indicators("000001")
    print(f"   报告期: {indicators.report_date}")
    print(f"   每股收益: {indicators.eps}")
    print(f"   净资产收益率: {indicators.roe}%")
    print(f"   资产负债率: {indicators.debt_ratio}%")

    # 测试财务摘要
    print("\n2. 获取平安银行(000001)财务摘要:")
    abstract = provider.get_financial_abstract("000001")
    if len(abstract) > 0:
        print(f"   获取到 {len(abstract)} 条数据")
        print(f"   指标列表: {abstract['指标'].tolist()[:5]}")
    else:
        print("   获取失败")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
