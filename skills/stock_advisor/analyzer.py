#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票分析器

整合数据获取、指标计算、信号生成、风险评估
提供完整的股票分析能力
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from .stock_data import StockData


# ==================== 数据类定义 ====================

@dataclass
class AnalysisConfig:
    """
    分析配置

    支持嵌套配置，借鉴 vectorbt 的配置系统设计
    """
    # 数据配置
    start_date: str = "20260101"
    end_date: str = "20260614"
    adjust: str = "qfq"  # qfq(前复权)/hfq(后复权)/空(不复权)

    # 指标参数
    ma_periods: list = field(default_factory=lambda: [5, 10, 20, 60])
    rsi_period: int = 14
    macd_params: tuple = (12, 26, 9)
    boll_params: tuple = (20, 2.0)

    # 风险配置
    risk_profile: str = "moderate"  # conservative/moderate/aggressive

    # 输出配置
    output_format: str = "dict"  # dict/json/dataframe

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'adjust': self.adjust,
            'risk_profile': self.risk_profile,
        }


@dataclass
class RiskAssessment:
    """
    风险评估结果
    """
    volatility: float          # 波动率 (年化)
    max_drawdown: float        # 最大回撤
    stop_loss_price: float     # 止损价
    take_profit_price: float   # 止盈价
    max_position: float        # 最大仓位比例
    risk_level: str = ""       # 风险等级

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'volatility': round(self.volatility, 4),
            'max_drawdown': round(self.max_drawdown, 4),
            'stop_loss_price': round(self.stop_loss_price, 2),
            'take_profit_price': round(self.take_profit_price, 2),
            'max_position': round(self.max_position, 2),
            'risk_level': self.risk_level,
        }


@dataclass
class Recommendation:
    """
    投资建议
    """
    action: str                # 操作: BUY/SELL/HOLD
    confidence: float          # 置信度 (0-1)
    reason: str                # 原因说明
    target_price: float        # 目标价
    stop_loss: float           # 止损价
    position_ratio: float      # 建议仓位比例

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'action': self.action,
            'confidence': round(self.confidence, 4),
            'reason': self.reason,
            'target_price': round(self.target_price, 2),
            'stop_loss': round(self.stop_loss, 2),
            'position_ratio': round(self.position_ratio, 2),
        }


@dataclass
class AnalysisResult:
    """
    分析结果

    包含股票数据、信号、风险评估和投资建议
    """
    stock_data: StockData
    signal: dict
    risk: RiskAssessment
    recommendation: Recommendation
    config: AnalysisConfig = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock': self.stock_data.to_dict(),
            'signal': self.signal,
            'risk': self.risk.to_dict(),
            'recommendation': self.recommendation.to_dict(),
            'data_source': getattr(self.stock_data, 'source', 'real'),
        }

    def summary(self) -> str:
        """
        生成摘要

        返回:
            格式化的分析摘要字符串
        """
        r = self.recommendation
        s = self.stock_data

        action_map = {
            'BUY': '📈 买入',
            'SELL': '📉 卖出',
            'HOLD': '⏸️ 观望'
        }

        return (
            f"{'='*50}\n"
            f"【{s.name}({s.code})】分析报告\n"
            f"{'='*50}\n"
            f"数据来源: {getattr(s, 'source', 'real')}\n"
            f"当前价格: {s.latest_price:.2f}\n"
            f"数据区间: {s.date_range[0].strftime('%Y-%m-%d')} ~ {s.date_range[1].strftime('%Y-%m-%d')}\n"
            f"{'─'*50}\n"
            f"操作建议: {action_map.get(r.action, r.action)}\n"
            f"置信度: {r.confidence:.1%}\n"
            f"原因: {r.reason}\n"
            f"{'─'*50}\n"
            f"目标价: {r.target_price:.2f}\n"
            f"止损价: {r.stop_loss:.2f}\n"
            f"建议仓位: {r.position_ratio:.0%}\n"
            f"{'─'*50}\n"
            f"波动率: {self.risk.volatility:.2%}\n"
            f"最大回撤: {self.risk.max_drawdown:.2%}\n"
            f"{'='*50}\n"
            f"⚠️ 以上建议仅供参考，投资有风险，入市需谨慎"
        )


# ==================== 分析器类 ====================

class StockAnalyzer:
    """
    股票分析器

    整合数据获取、指标计算、信号生成、风险评估

    示例:
        >>> analyzer = StockAnalyzer()
        >>> result = analyzer.analyze("000001")
        >>> print(result.summary())
    """

    def __init__(self, config: AnalysisConfig = None):
        """
        初始化分析器

        参数:
            config: 分析配置，如果为 None 则使用默认配置
        """
        self.config = config or AnalysisConfig()
        self._data_cache = {}  # 数据缓存

    def analyze(self, stock_code: str) -> AnalysisResult:
        """
        分析股票

        参数:
            stock_code: 股票代码 (如 "000001")

        返回:
            AnalysisResult 分析结果

        示例:
            >>> result = analyzer.analyze("000001")
            >>> print(result.summary())
            >>> print(result.to_dict())
        """
        # 1. 获取数据
        stock_data = self.get_stock_data(stock_code)

        # 2. 获取最新信号
        signal = stock_data.get_latest_signal(self.config.risk_profile)

        # 3. 评估风险
        risk = self._assess_risk(stock_data)

        # 4. 生成建议
        recommendation = self._generate_recommendation(signal, risk)

        # 5. 构建结果
        return AnalysisResult(
            stock_data=stock_data,
            signal=signal,
            risk=risk,
            recommendation=recommendation,
            config=self.config
        )

    def get_stock_data(self, stock_code: str) -> StockData:
        """
        获取股票数据 (带缓存)

        参数:
            stock_code: 股票代码

        返回:
            StockData 对象
        """
        # 检查缓存
        cache_key = f"{stock_code}_{self.config.start_date}_{self.config.end_date}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # 获取数据
        df = None
        source = "real"
        quality = {}
        reason = "ok"

        try:
            from core.data.eastmoney_api import fetch_stock_hist_governed

            governed = fetch_stock_hist_governed(
                stock_code,
                self.config.start_date,
                self.config.end_date
            )
            df = governed["payload"]
            source = governed.get("data_source", "real")
            quality = governed.get("quality", {})
            reason = governed.get("reason", "ok")
        except Exception as exc:
            print(f"获取 {stock_code} 实时数据失败，使用离线模拟数据: {exc}")
            df = self._build_fallback_stock_hist(stock_code)
            source = "mock"
            reason = str(exc)

        # 获取股票名称
        name = self._get_stock_name(stock_code)

        # 创建 StockData
        stock_data = StockData(stock_code, name, df, source=source)
        stock_data.data_governance = {
            "data_source": source,
            "quality": quality,
            "reason": reason,
        }

        # 缓存
        self._data_cache[cache_key] = stock_data

        return stock_data

    def _build_fallback_stock_hist(self, stock_code: str) -> pd.DataFrame:
        """
        构建离线模拟 OHLCV 数据。

        该数据仅用于降级演示与工具链验证，不应被视为真实行情。
        """
        seed = int(stock_code) % 10000
        rng = np.random.default_rng(seed)
        dates = pd.date_range(
            end=pd.to_datetime(self.config.end_date),
            periods=120,
            freq="B",
        )

        base_price = 10 + (seed % 500) / 10
        trend = np.linspace(0, rng.normal(8, 2), len(dates))
        noise = rng.normal(0, 0.6, len(dates)).cumsum()
        close = np.maximum(1, base_price + trend + noise)
        open_ = close + rng.normal(0, 0.25, len(dates))
        high = np.maximum(open_, close) + np.abs(rng.normal(0.4, 0.15, len(dates)))
        low = np.minimum(open_, close) - np.abs(rng.normal(0.4, 0.15, len(dates)))
        volume = rng.integers(1_000_000, 10_000_000, len(dates))

        return pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
            index=dates,
        )

    def _get_stock_name(self, stock_code: str) -> str:
        """
        获取股票名称

        参数:
            stock_code: 股票代码

        返回:
            股票名称
        """
        # 常见股票名称映射 (实际应用中可以从数据库或 API 获取)
        stock_names = {
            "000001": "平安银行",
            "000002": "万科A",
            "000063": "中兴通讯",
            "000333": "美的集团",
            "000651": "格力电器",
            "000858": "五粮液",
            "002594": "比亚迪",
            "600000": "浦发银行",
            "600036": "招商银行",
            "600519": "贵州茅台",
            "600900": "长江电力",
            "601318": "中国平安",
            "601398": "工商银行",
        }
        return stock_names.get(stock_code, f"股票{stock_code}")

    def _assess_risk(self, stock_data: StockData) -> RiskAssessment:
        """
        评估风险

        参数:
            stock_data: 股票数据

        返回:
            RiskAssessment 风险评估结果
        """
        from core.risk import RiskManager

        rm = RiskManager(self.config.risk_profile)

        # 获取最新价格
        current_price = stock_data.latest_price

        # 计算波动率
        volatility = stock_data.get_volatility()

        # 计算最大回撤
        max_drawdown = stock_data.get_max_drawdown()

        # 根据风险配置确定风险等级
        risk_levels = {
            "conservative": "低风险",
            "moderate": "中风险",
            "aggressive": "高风险"
        }

        return RiskAssessment(
            volatility=volatility,
            max_drawdown=max_drawdown,
            stop_loss_price=rm.calc_stop_loss_price(current_price),
            take_profit_price=rm.calc_take_profit_price(current_price),
            max_position=rm.get_max_position(),
            risk_level=risk_levels.get(self.config.risk_profile, "中风险")
        )

    def _generate_recommendation(
        self,
        signal: dict,
        risk: RiskAssessment
    ) -> Recommendation:
        """
        生成投资建议

        参数:
            signal: 信号信息
            risk: 风险评估

        返回:
            Recommendation 投资建议
        """
        direction = signal['direction']
        confidence = signal['confidence']

        # 获取风险配置对应的最小置信度
        min_confidences = {
            "conservative": 0.6,
            "moderate": 0.5,
            "aggressive": 0.4
        }
        min_confidence = min_confidences.get(self.config.risk_profile, 0.5)

        # 根据信号强度和风险调整建议
        if direction == 'BUY' and confidence >= min_confidence:
            action = 'BUY'
            reason = f"买入信号强度 {confidence:.1%}，建议适量买入"
        elif direction == 'SELL' and confidence >= min_confidence:
            action = 'SELL'
            reason = f"卖出信号强度 {confidence:.1%}，建议考虑卖出"
        else:
            action = 'HOLD'
            if confidence < min_confidence:
                reason = f"信号强度 {confidence:.1%} 不足，建议观望"
            else:
                reason = "信号不明确，建议观望"

        return Recommendation(
            action=action,
            confidence=confidence,
            reason=reason,
            target_price=risk.take_profit_price,
            stop_loss=risk.stop_loss_price,
            position_ratio=risk.max_position
        )

    def clear_cache(self):
        """清除缓存"""
        self._data_cache.clear()


# ==================== 便捷函数 ====================

def analyze(
    stock_code: str,
    risk_profile: str = "moderate",
    start_date: str = "20260101",
    end_date: str = "20260614"
) -> AnalysisResult:
    """
    分析股票 (便捷函数)

    参数:
        stock_code: 股票代码
        risk_profile: 风险配置 (conservative/moderate/aggressive)
        start_date: 开始日期
        end_date: 结束日期

    返回:
        AnalysisResult 分析结果

    示例:
        >>> from skills.stock_advisor.analyzer import analyze
        >>> result = analyze("000001", "moderate")
        >>> print(result.summary())
    """
    config = AnalysisConfig(
        start_date=start_date,
        end_date=end_date,
        risk_profile=risk_profile
    )
    analyzer = StockAnalyzer(config)
    return analyzer.analyze(stock_code)


def batch_analyze(
    stock_codes: list,
    risk_profile: str = "moderate",
    start_date: str = "20260101",
    end_date: str = "20260614"
) -> List[AnalysisResult]:
    """
    批量分析股票

    参数:
        stock_codes: 股票代码列表
        risk_profile: 风险配置
        start_date: 开始日期
        end_date: 结束日期

    返回:
        AnalysisResult 列表

    示例:
        >>> results = batch_analyze(["000001", "600519"], "moderate")
        >>> for r in results:
        ...     print(r.summary())
    """
    config = AnalysisConfig(
        start_date=start_date,
        end_date=end_date,
        risk_profile=risk_profile
    )
    analyzer = StockAnalyzer(config)
    return [analyzer.analyze(code) for code in stock_codes]


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("StockAnalyzer 测试")
    print("=" * 60)

    # 测试配置
    print("\n1. 测试 AnalysisConfig:")
    config = AnalysisConfig(risk_profile="moderate")
    print(f"   配置: {config.to_dict()}")

    # 测试分析器
    print("\n2. 测试 StockAnalyzer:")
    analyzer = StockAnalyzer(config)
    print(f"   分析器创建成功")

    # 注意: 实际测试需要网络连接获取数据
    # result = analyzer.analyze("000001")
    # print(result.summary())

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
