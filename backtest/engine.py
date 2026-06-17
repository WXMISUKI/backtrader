#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测引擎

封装 backtrader，提供简洁的回测接口
"""

import backtrader as bt
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from .adapter import StockDataFeed, StrategyAdapter
from skills.stock_advisor import StockData
from strategies import StrategyRegistry


@dataclass
class BacktestResult:
    """
    回测结果

    包含回测的所有统计信息
    """
    # 基本信息
    stock_code: str = ""
    strategy_name: str = ""
    start_date: str = ""
    end_date: str = ""

    # 资金信息
    initial_cash: float = 100000.0
    final_value: float = 0.0
    total_return: float = 0.0
    annual_return: float = 0.0

    # 风险指标
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    volatility: float = 0.0

    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # 盈亏统计
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # 数据来源
    data_source: str = "real"

    # 交易记录
    trades: List[Dict] = field(default_factory=list)

    def summary(self) -> str:
        """
        生成摘要

        返回:
            格式化的回测摘要字符串
        """
        return (
            f"{'='*60}\n"
            f"回测报告\n"
            f"{'='*60}\n"
            f"股票代码: {self.stock_code}\n"
            f"策略名称: {self.strategy_name}\n"
            f"回测区间: {self.start_date} ~ {self.end_date}\n"
            f"数据来源: {self.data_source}\n"
            f"{'─'*60}\n"
            f"资金信息:\n"
            f"  初始资金: {self.initial_cash:,.2f}\n"
            f"  最终资金: {self.final_value:,.2f}\n"
            f"  总收益率: {self.total_return:.2%}\n"
            f"  年化收益: {self.annual_return:.2%}\n"
            f"{'─'*60}\n"
            f"风险指标:\n"
            f"  最大回撤: {self.max_drawdown:.2%}\n"
            f"  夏普比率: {self.sharpe_ratio:.2f}\n"
            f"  波动率: {self.volatility:.2%}\n"
            f"{'─'*60}\n"
            f"交易统计:\n"
            f"  总交易数: {self.total_trades}\n"
            f"  盈利次数: {self.winning_trades}\n"
            f"  亏损次数: {self.losing_trades}\n"
            f"  胜率: {self.win_rate:.2%}\n"
            f"  平均盈利: {self.avg_profit:.2f}\n"
            f"  平均亏损: {self.avg_loss:.2f}\n"
            f"  盈亏比: {self.profit_factor:.2f}\n"
            f"{'='*60}\n"
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_cash': self.initial_cash,
            'final_value': round(self.final_value, 2),
            'total_return': round(self.total_return, 4),
            'annual_return': round(self.annual_return, 4),
            'max_drawdown': round(self.max_drawdown, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 4),
            'volatility': round(self.volatility, 4),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 4),
            'avg_profit': round(self.avg_profit, 2),
            'avg_loss': round(self.avg_loss, 2),
            'profit_factor': round(self.profit_factor, 2),
            'data_source': self.data_source,
        }


class BacktestEngine:
    """
    回测引擎

    封装 backtrader，提供简洁的回测接口

    示例:
        >>> engine = BacktestEngine(initial_cash=100000)
        >>> result = engine.run(
        ...     stock_code="000001",
        ...     strategy_name="ma_cross",
        ...     config={'fast_period': 5, 'slow_period': 20}
        ... )
        >>> print(result.summary())
    """

    def __init__(self, initial_cash: float = 100000, commission: float = 0.001):
        """
        初始化

        参数:
            initial_cash: 初始资金
            commission: 手续费率
        """
        self.initial_cash = initial_cash
        self.commission = commission

    def run(
        self,
        stock_code: str,
        strategy_name: str,
        config: Dict[str, Any] = None,
        start_date: str = "20260101",
        end_date: str = "20260614"
    ) -> BacktestResult:
        """
        运行回测

        参数:
            stock_code: 股票代码
            strategy_name: 策略名称
            config: 策略配置
            start_date: 开始日期
            end_date: 结束日期

        返回:
            BacktestResult 回测结果
        """
        # 获取数据
        df = None
        data_source = "real"
        quality = {}
        reason = "ok"
        try:
            from core.data.eastmoney_api import fetch_stock_hist_governed

            governed = fetch_stock_hist_governed(stock_code, start_date, end_date)
            df = governed["payload"]
            data_source = governed.get("data_source", "real")
            quality = governed.get("quality", {})
            reason = governed.get("reason", "ok")
        except Exception as exc:
            print(f"获取 {stock_code} 实时数据失败，使用离线模拟数据: {exc}")
            df = self._build_fallback_stock_hist(stock_code, start_date, end_date)
            data_source = "mock"
            reason = str(exc)

        # 创建 StockData
        stock_data = StockData(stock_code, f"股票{stock_code}", df, source=data_source)
        stock_data.data_governance = {
            "data_source": data_source,
            "quality": quality,
            "reason": reason,
        }

        # 创建 backtrader 引擎
        cerebro = bt.Cerebro()

        # 添加数据
        data_feed = StockDataFeed.from_stock_data(stock_data)
        cerebro.adddata(data_feed)

        # 设置资金
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=self.commission)

        # 添加策略
        cerebro.addstrategy(
            StrategyAdapter,
            strategy_name=strategy_name,
            config=config or {}
        )

        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

        # 运行回测
        results = cerebro.run()
        strat = results[0]

        # 提取结果
        final_value = cerebro.broker.getvalue()

        # 提取分析结果
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        returns = strat.analyzers.returns.get_analysis()

        # 计算胜率
        total_trades = trades.total.total if hasattr(trades, 'total') else 0
        won_trades = trades.won.total if hasattr(trades, 'won') else 0
        lost_trades = trades.lost.total if hasattr(trades, 'lost') else 0
        win_rate = won_trades / total_trades if total_trades > 0 else 0

        # 计算平均盈亏
        avg_profit = trades.won.pnl.average if hasattr(trades, 'won') and trades.won.total > 0 else 0
        avg_loss = trades.lost.pnl.average if hasattr(trades, 'lost') and trades.lost.total > 0 else 0

        # 计算盈亏比
        profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else 0

        # 构建结果
        result = BacktestResult(
            stock_code=stock_code,
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_cash=self.initial_cash,
            final_value=final_value,
            total_return=(final_value / self.initial_cash - 1),
            annual_return=returns.get('rnorm100', 0) / 100,
            max_drawdown=drawdown.max.drawdown / 100,
            sharpe_ratio=sharpe.get('sharperatio', 0) or 0,
            volatility=0,  # 需要额外计算
            total_trades=total_trades,
            winning_trades=won_trades,
            losing_trades=lost_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            data_source=data_source,
        )

        return result

    def _build_fallback_stock_hist(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        构建离线模拟 OHLCV 数据。
        """
        seed = int(stock_code) % 10000
        rng = np.random.default_rng(seed)
        dates = pd.date_range(
            end=pd.to_datetime(end_date),
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


def run_backtest(
    stock_code: str,
    strategy_name: str,
    config: Dict[str, Any] = None,
    start_date: str = "20260101",
    end_date: str = "20260614",
    initial_cash: float = 100000
) -> BacktestResult:
    """
    运行回测 (便捷函数)

    参数:
        stock_code: 股票代码
        strategy_name: 策略名称
        config: 策略配置
        start_date: 开始日期
        end_date: 结束日期
        initial_cash: 初始资金

    返回:
        BacktestResult 回测结果

    示例:
        >>> from backtest import run_backtest
        >>> result = run_backtest("000001", "ma_cross")
        >>> print(result.summary())
    """
    engine = BacktestEngine(initial_cash=initial_cash)
    return engine.run(stock_code, strategy_name, config, start_date, end_date)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("回测引擎测试")
    print("=" * 60)

    # 测试 BacktestResult
    print("\n1. BacktestResult 测试:")
    result = BacktestResult(
        stock_code="000001",
        strategy_name="ma_cross",
        start_date="20260101",
        end_date="20260614",
        initial_cash=100000,
        final_value=110000,
        total_return=0.10,
        annual_return=0.20,
        max_drawdown=0.05,
        sharpe_ratio=1.5,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate=0.6,
    )
    print(result.summary())

    # 测试 BacktestEngine
    print("\n2. BacktestEngine 测试:")
    engine = BacktestEngine(initial_cash=100000)
    print(f"   引擎创建成功: 初始资金={engine.initial_cash}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
