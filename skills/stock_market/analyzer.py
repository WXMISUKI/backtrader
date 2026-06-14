#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
市场分析器

分析大盘走势、板块轮动、市场情绪等

分析维度:
- 大盘: 上证指数、深证成指、创业板指
- 板块: 行业板块、概念板块
- 情绪: 涨跌比、成交量、北向资金
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class IndexData:
    """
    指数数据
    """
    name: str           # 指数名称
    code: str           # 指数代码
    current: float      # 当前点位
    change_pct: float   # 涨跌幅
    volume: float       # 成交量

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'code': self.code,
            'current': round(self.current, 2),
            'change_pct': round(self.change_pct, 2),
            'volume': self.volume,
        }


@dataclass
class SectorData:
    """
    板块数据
    """
    name: str           # 板块名称
    change_pct: float   # 涨跌幅
    leading_stock: str  # 领涨股票
    stock_count: int    # 股票数量

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'change_pct': round(self.change_pct, 2),
            'leading_stock': self.leading_stock,
            'stock_count': self.stock_count,
        }


@dataclass
class MarketSentiment:
    """
    市场情绪
    """
    rise_count: int       # 上涨数量
    fall_count: int       # 下跌数量
    flat_count: int       # 平盘数量
    rise_ratio: float     # 上涨比例
    limit_up: int         # 涨停数量
    limit_down: int       # 跌停数量
    total_volume: float   # 总成交量
    northbound_flow: float  # 北向资金流向

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'rise_count': self.rise_count,
            'fall_count': self.fall_count,
            'flat_count': self.flat_count,
            'rise_ratio': round(self.rise_ratio, 2),
            'limit_up': self.limit_up,
            'limit_down': self.limit_down,
            'total_volume': self.total_volume,
            'northbound_flow': round(self.northbound_flow, 2),
        }


@dataclass
class MarketOverview:
    """
    市场概览
    """
    datetime: str                    # 时间
    indices: List[IndexData]         # 指数数据
    hot_sectors: List[SectorData]    # 热门板块
    sentiment: MarketSentiment       # 市场情绪
    market_trend: str                # 市场趋势 (牛市/熊市/震荡)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'datetime': self.datetime,
            'indices': [idx.to_dict() for idx in self.indices],
            'hot_sectors': [s.to_dict() for s in self.hot_sectors],
            'sentiment': self.sentiment.to_dict(),
            'market_trend': self.market_trend,
        }

    def summary(self) -> str:
        """生成摘要"""
        report = f"""
{'='*60}
                    市场分析报告
{'='*60}

生成时间: {self.datetime}

{'─'*60}
【大盘指数】
"""
        for idx in self.indices:
            direction = "↑" if idx.change_pct > 0 else "↓" if idx.change_pct < 0 else "→"
            report += f"  {idx.name}: {idx.current:.2f} {direction} {idx.change_pct:+.2f}%\n"

        report += f"""
{'─'*60}
【热门板块】
"""
        for sector in self.hot_sectors[:5]:
            report += f"  {sector.name}: {sector.change_pct:+.2f}% (领涨: {sector.leading_stock})\n"

        report += f"""
{'─'*60}
【市场情绪】
  上涨: {self.sentiment.rise_count} 只 ({self.sentiment.rise_ratio:.1%})
  下跌: {self.sentiment.fall_count} 只
  涨停: {self.sentiment.limit_up} 只
  跌停: {self.sentiment.limit_down} 只
  北向资金: {self.sentiment.northbound_flow:+.2f} 亿

{'─'*60}
【市场趋势】
  当前趋势: {self.market_trend}

{'='*60}
"""
        return report


class MarketAnalyzer:
    """
    市场分析器

    分析大盘走势、板块轮动、市场情绪

    示例:
        >>> analyzer = MarketAnalyzer()
        >>> overview = analyzer.get_market_overview()
        >>> print(overview.summary())
    """

    def __init__(self):
        """初始化"""
        # 模拟数据
        self._mock_indices = self._get_mock_indices()
        self._mock_sectors = self._get_mock_sectors()
        self._mock_sentiment = self._get_mock_sentiment()

    def _get_mock_indices(self) -> List[IndexData]:
        """获取模拟指数数据"""
        return [
            IndexData(name="上证指数", code="000001", current=3200.50, change_pct=0.85, volume=350000000000),
            IndexData(name="深证成指", code="399001", current=10500.30, change_pct=1.20, volume=450000000000),
            IndexData(name="创业板指", code="399006", current=2100.80, change_pct=1.50, volume=200000000000),
            IndexData(name="科创50", code="000688", current=1050.20, change_pct=2.10, volume=80000000000),
        ]

    def _get_mock_sectors(self) -> List[SectorData]:
        """获取模拟板块数据"""
        return [
            SectorData(name="半导体", change_pct=3.50, leading_stock="中芯国际", stock_count=50),
            SectorData(name="新能源", change_pct=2.80, leading_stock="宁德时代", stock_count=80),
            SectorData(name="人工智能", change_pct=2.50, leading_stock="科大讯飞", stock_count=60),
            SectorData(name="医药生物", change_pct=1.80, leading_stock="恒瑞医药", stock_count=120),
            SectorData(name="白酒", change_pct=1.50, leading_stock="贵州茅台", stock_count=20),
            SectorData(name="银行", change_pct=0.80, leading_stock="招商银行", stock_count=30),
            SectorData(name="房地产", change_pct=-0.50, leading_stock="万科A", stock_count=100),
            SectorData(name="煤炭", change_pct=-1.20, leading_stock="中国神华", stock_count=25),
        ]

    def _get_mock_sentiment(self) -> MarketSentiment:
        """获取模拟市场情绪"""
        return MarketSentiment(
            rise_count=3200,
            fall_count=1500,
            flat_count=300,
            rise_ratio=0.64,
            limit_up=45,
            limit_down=8,
            total_volume=1000000000000,
            northbound_flow=85.5,
        )

    def get_market_overview(self) -> MarketOverview:
        """
        获取市场概览

        返回:
            MarketOverview 市场概览
        """
        # 判断市场趋势
        avg_change = np.mean([idx.change_pct for idx in self._mock_indices])
        if avg_change > 1.0:
            market_trend = "牛市"
        elif avg_change < -1.0:
            market_trend = "熊市"
        else:
            market_trend = "震荡"

        return MarketOverview(
            datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            indices=self._mock_indices,
            hot_sectors=sorted(self._mock_sectors, key=lambda x: x.change_pct, reverse=True),
            sentiment=self._mock_sentiment,
            market_trend=market_trend,
        )

    def get_sector_performance(self) -> pd.DataFrame:
        """
        获取板块表现

        返回:
            板块表现 DataFrame
        """
        data = []
        for sector in self._mock_sectors:
            data.append(sector.to_dict())
        return pd.DataFrame(data)

    def get_market_sentiment(self) -> dict:
        """
        获取市场情绪

        返回:
            市场情绪字典
        """
        return self._mock_sentiment.to_dict()

    def is_bullish(self) -> bool:
        """
        判断是否牛市

        返回:
            是否牛市
        """
        overview = self.get_market_overview()
        return overview.market_trend == "牛市"

    def get_hot_sectors(self, top_n: int = 5) -> List[SectorData]:
        """
        获取热门板块

        参数:
            top_n: 返回数量

        返回:
            热门板块列表
        """
        sectors = sorted(self._mock_sectors, key=lambda x: x.change_pct, reverse=True)
        return sectors[:top_n]


# 便捷函数
def get_market_overview() -> MarketOverview:
    """
    获取市场概览 (便捷函数)

    返回:
        MarketOverview 市场概览
    """
    analyzer = MarketAnalyzer()
    return analyzer.get_market_overview()


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("市场分析器测试")
    print("=" * 60)

    # 创建分析器
    analyzer = MarketAnalyzer()

    # 测试市场概览
    print("\n1. 市场概览:")
    overview = analyzer.get_market_overview()
    print(overview.summary())

    # 测试板块表现
    print("\n2. 板块表现:")
    sectors = analyzer.get_sector_performance()
    print(sectors)

    # 测试市场情绪
    print("\n3. 市场情绪:")
    sentiment = analyzer.get_market_sentiment()
    print(f"  上涨比例: {sentiment['rise_ratio']:.1%}")
    print(f"  北向资金: {sentiment['northbound_flow']:+.2f} 亿")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
