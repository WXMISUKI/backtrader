#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票筛选器

根据用户设定的条件筛选股票

筛选维度:
- 技术面: MA 金叉、RSI 超卖、MACD 金叉
- 基本面: PE、PB、ROE
- 资金面: 成交量放大、主力净流入
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from skills.stock_advisor import StockData, StockAnalyzer, AnalysisConfig
from core.indicators import IndicatorCalculator
from core.signals import SignalGenerator


@dataclass
class ScreeningConditions:
    """
    筛选条件

    支持多维度筛选条件组合
    """
    # 技术面条件
    ma_cross: bool = False          # MA 金叉
    rsi_oversold: bool = False      # RSI 超卖
    macd_cross: bool = False        # MACD 金叉

    # 基本面条件
    pe_max: Optional[float] = None  # 最大市盈率
    pb_max: Optional[float] = None  # 最大市净率
    roe_min: Optional[float] = None # 最小净资产收益率

    # 资金面条件
    volume_ratio_min: Optional[float] = None  # 最小量比

    # 风险配置
    risk_profile: str = "moderate"


@dataclass
class StockCandidate:
    """
    候选股票
    """
    code: str                       # 股票代码
    name: str                       # 股票名称
    price: float                    # 当前价格
    change_pct: float               # 涨跌幅
    signals: List[str] = field(default_factory=list)  # 触发的信号
    score: float = 0.0              # 综合得分

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'price': round(self.price, 2),
            'change_pct': round(self.change_pct, 2),
            'signals': self.signals,
            'score': round(self.score, 2)
        }


class StockScreener:
    """
    股票筛选器

    根据条件筛选股票

    示例:
        >>> screener = StockScreener()
        >>> conditions = ScreeningConditions(
        ...     ma_cross=True,
        ...     rsi_oversold=True,
        ...     risk_profile="moderate"
        ... )
        >>> candidates = screener.screen(conditions)
        >>> for stock in candidates:
        ...     print(f"{stock.code} {stock.name}: {stock.score}")
    """

    # 常用股票列表 (实际应用中可以从 API 获取)
    STOCK_LIST = [
        ("000001", "平安银行"),
        ("000002", "万科A"),
        ("000333", "美的集团"),
        ("000651", "格力电器"),
        ("000858", "五粮液"),
        ("002594", "比亚迪"),
        ("600000", "浦发银行"),
        ("600036", "招商银行"),
        ("600519", "贵州茅台"),
        ("600900", "长江电力"),
        ("601318", "中国平安"),
        ("601398", "工商银行"),
        ("601857", "中国石油"),
        ("601988", "中国银行"),
        ("600276", "恒瑞医药"),
    ]

    def __init__(self, max_workers: int = 4):
        """
        初始化

        参数:
            max_workers: 最大并发数
        """
        self.max_workers = max_workers
        self._analyzer_cache = {}

    def screen(self, conditions: ScreeningConditions) -> List[StockCandidate]:
        """
        筛选股票

        参数:
            conditions: 筛选条件

        返回:
            符合条件的候选股票列表
        """
        candidates = []

        # 并发分析股票
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for code, name in self.STOCK_LIST:
                future = executor.submit(
                    self._analyze_stock, code, name, conditions
                )
                futures[future] = (code, name)

            for future in as_completed(futures):
                try:
                    candidate = future.result()
                    if candidate is not None:
                        candidates.append(candidate)
                except Exception as e:
                    code, name = futures[future]
                    print(f"分析 {code} {name} 失败: {e}")

        # 按得分排序
        candidates.sort(key=lambda x: x.score, reverse=True)

        return candidates

    def _analyze_stock(
        self,
        code: str,
        name: str,
        conditions: ScreeningConditions
    ) -> Optional[StockCandidate]:
        """
        分析单只股票

        参数:
            code: 股票代码
            name: 股票名称
            conditions: 筛选条件

        返回:
            如果符合条件返回 StockCandidate，否则返回 None
        """
        try:
            # 获取分析结果
            config = AnalysisConfig(risk_profile=conditions.risk_profile)
            analyzer = StockAnalyzer(config)
            result = analyzer.analyze(code)

            # 检查条件
            signals = []
            score = 0.0

            # 技术面条件
            if conditions.ma_cross:
                if result.signal.get('direction') == 'BUY':
                    if 'MA金叉' in str(result.signal.get('reason', '')):
                        signals.append("MA金叉")
                        score += 30

            if conditions.rsi_oversold:
                rsi = result.stock_data.indicators.get('rsi')
                if rsi is not None and len(rsi) > 0:
                    current_rsi = rsi.iloc[-1]
                    if current_rsi < 30:
                        signals.append("RSI超卖")
                        score += 25

            if conditions.macd_cross:
                if result.signal.get('direction') == 'BUY':
                    if 'MACD' in str(result.signal.get('reason', '')):
                        signals.append("MACD金叉")
                        score += 30

            # 综合得分
            if result.signal.get('direction') == 'BUY':
                score += result.signal.get('confidence', 0) * 20

            # 如果没有触发任何信号，返回 None
            if not signals and score < 20:
                return None

            # 创建候选股票
            candidate = StockCandidate(
                code=code,
                name=name,
                price=result.stock_data.latest_price,
                change_pct=0,  # 需要从实时数据获取
                signals=signals,
                score=score
            )

            return candidate

        except Exception as e:
            print(f"分析 {code} 失败: {e}")
            return None

    def screen_from_list(
        self,
        stock_list: List[tuple],
        conditions: ScreeningConditions
    ) -> List[StockCandidate]:
        """
        从指定列表筛选股票

        参数:
            stock_list: 股票列表 [(code, name), ...]
            conditions: 筛选条件

        返回:
            符合条件的候选股票列表
        """
        candidates = []

        for code, name in stock_list:
            try:
                candidate = self._analyze_stock(code, name, conditions)
                if candidate is not None:
                    candidates.append(candidate)
            except Exception as e:
                print(f"分析 {code} {name} 失败: {e}")

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates


# 便捷函数
def screen_stocks(
    ma_cross: bool = False,
    rsi_oversold: bool = False,
    macd_cross: bool = False,
    risk_profile: str = "moderate"
) -> List[StockCandidate]:
    """
    筛选股票 (便捷函数)

    参数:
        ma_cross: 是否筛选 MA 金叉
        rsi_oversold: 是否筛选 RSI 超卖
        macd_cross: 是否筛选 MACD 金叉
        risk_profile: 风险配置

    返回:
        候选股票列表

    示例:
        >>> from skills.stock_selector import screen_stocks
        >>> stocks = screen_stocks(ma_cross=True, risk_profile="moderate")
        >>> for s in stocks:
        ...     print(f"{s.code} {s.name}: {s.score}")
    """
    conditions = ScreeningConditions(
        ma_cross=ma_cross,
        rsi_oversold=rsi_oversold,
        macd_cross=macd_cross,
        risk_profile=risk_profile
    )
    screener = StockScreener()
    return screener.screen(conditions)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("股票筛选器测试")
    print("=" * 60)

    # 测试筛选条件
    print("\n1. 筛选条件测试:")
    conditions = ScreeningConditions(
        ma_cross=True,
        rsi_oversold=True,
        risk_profile="moderate"
    )
    print(f"   MA金叉: {conditions.ma_cross}")
    print(f"   RSI超卖: {conditions.rsi_oversold}")
    print(f"   风险配置: {conditions.risk_profile}")

    # 测试筛选器
    print("\n2. 筛选器测试:")
    screener = StockScreener()
    print(f"   股票池大小: {len(screener.STOCK_LIST)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
