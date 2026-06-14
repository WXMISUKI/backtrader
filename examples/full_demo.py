#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合功能演示

演示股票量化交易系统的完整功能
使用模拟数据，无需网络连接
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime

from skills.stock_advisor import StockData, StockAnalyzer, AnalysisConfig
from skills.stock_report import ReportGenerator
from skills.stock_simulator import TradingSimulator
from strategies import list_strategies, StrategyRegistry, Bar, Signal, SignalType


def create_sample_data():
    """创建模拟数据"""
    np.random.seed(42)
    dates = pd.date_range('2026-01-01', periods=120, freq='B')
    base_price = 100 + np.cumsum(np.random.randn(120) * 0.5)

    df = pd.DataFrame({
        'open': base_price + np.random.randn(120) * 0.2,
        'high': base_price + np.abs(np.random.randn(120)) * 1.5,
        'low': base_price - np.abs(np.random.randn(120)) * 1.5,
        'close': base_price,
        'volume': np.random.randint(1000000, 10000000, 120)
    }, index=dates)

    return df


def demo_stock_analysis():
    """演示个股分析功能"""
    print("\n" + "="*60)
    print("1. 个股分析演示")
    print("="*60)

    # 创建模拟数据
    df = create_sample_data()
    stock_data = StockData("000001", "平安银行", df)

    print(f"\n股票: {stock_data.name}({stock_data.code})")
    print(f"当前价格: {stock_data.latest_price:.2f}")
    print(f"数据点数: {stock_data.data_points}")
    print(f"波动率: {stock_data.get_volatility():.2%}")
    print(f"最大回撤: {stock_data.get_max_drawdown():.2%}")

    # 获取技术指标
    print("\n技术指标:")
    indicators = stock_data.indicators
    if 'ma5' in indicators.columns:
        print(f"  MA5: {indicators['ma5'].iloc[-1]:.2f}")
    if 'ma20' in indicators.columns:
        print(f"  MA20: {indicators['ma20'].iloc[-1]:.2f}")
    if 'rsi' in indicators.columns:
        print(f"  RSI: {indicators['rsi'].iloc[-1]:.2f}")

    # 获取信号
    print("\n交易信号:")
    signals = stock_data.signals
    if 'direction' in signals.columns:
        print(f"  方向: {signals['direction'].iloc[-1]}")
    if 'buy_strength' in signals.columns:
        print(f"  买入强度: {signals['buy_strength'].iloc[-1]:.2%}")
    if 'sell_strength' in signals.columns:
        print(f"  卖出强度: {signals['sell_strength'].iloc[-1]:.2%}")

    return stock_data


def demo_strategy_list():
    """演示策略列表"""
    print("\n" + "="*60)
    print("2. 可用策略列表")
    print("="*60)

    strategies = list_strategies()
    print(f"\n共有 {len(strategies)} 个可用策略:")
    for i, name in enumerate(strategies, 1):
        print(f"  {i}. {name}")


def demo_strategy_backtest():
    """演示策略回测"""
    print("\n" + "="*60)
    print("3. 策略回测演示")
    print("="*60)

    # 创建模拟数据
    df = create_sample_data()

    # 测试双均线策略
    strategy = StrategyRegistry.create("ma_cross", {
        'fast_period': 5,
        'slow_period': 20
    })

    print(f"\n策略: {strategy.name}")
    print(f"参数: fast_period={strategy.fast_period}, slow_period={strategy.slow_period}")

    # 模拟回测
    buy_count = 0
    sell_count = 0
    hold_count = 0

    for i in range(len(df)):
        bar = Bar(df, index=i)
        signal = strategy.on_bar(bar)

        if signal.is_buy:
            buy_count += 1
        elif signal.is_sell:
            sell_count += 1
        else:
            hold_count += 1

    print(f"\n回测结果:")
    print(f"  买入信号: {buy_count} 次")
    print(f"  卖出信号: {sell_count} 次")
    print(f"  观望信号: {hold_count} 次")


def demo_simulation():
    """演示模拟交易"""
    print("\n" + "="*60)
    print("4. 模拟交易演示")
    print("="*60)

    # 创建模拟器
    simulator = TradingSimulator(initial_cash=1000000)

    print(f"\n初始资金: {simulator.initial_cash:,.2f}")

    # 执行交易
    print("\n执行交易:")
    simulator.buy("000001", "平安银行", 10.50, 1000)
    simulator.buy("600519", "贵州茅台", 1800.00, 100)
    simulator.update_prices({"000001": 11.00, "600519": 1850.00})
    simulator.sell("000001", 11.00, 500)

    # 查看持仓
    print("\n当前持仓:")
    portfolio = simulator.get_portfolio()
    print(f"  现金: {portfolio['cash']:,.2f}")
    print(f"  持仓市值: {portfolio['market_value']:,.2f}")
    print(f"  总资产: {portfolio['total_assets']:,.2f}")

    # 查看业绩
    print("\n业绩统计:")
    performance = simulator.get_performance()
    print(f"  总收益: {performance['total_profit']:,.2f}")
    print(f"  收益率: {performance['total_profit_pct']:.2f}%")
    print(f"  总交易数: {performance['total_trades']}")

    # 查看交易记录
    print("\n交易记录:")
    trades = simulator.get_trades()
    for trade in trades:
        print(f"  {trade['datetime']}: {trade['direction']} {trade['stock_name']} {trade['size']}股 @ {trade['price']}")

    return simulator


def demo_report():
    """演示报告生成"""
    print("\n" + "="*60)
    print("5. 报告生成演示")
    print("="*60)

    # 生成 JSON 报告
    data = {
        'stock_code': '000001',
        'stock_name': '平安银行',
        'price': 11.24,
        'signal': 'BUY',
        'confidence': 0.75,
        'target_price': 12.50,
        'stop_loss': 10.68
    }

    report = ReportGenerator.generate_json_report(data)
    print(f"\nJSON 报告:")
    print(report)


def main():
    """主函数"""
    print("="*60)
    print("股票量化交易系统 - 综合功能演示")
    print("="*60)

    # 1. 个股分析
    stock_data = demo_stock_analysis()

    # 2. 策略列表
    demo_strategy_list()

    # 3. 策略回测
    demo_strategy_backtest()

    # 4. 模拟交易
    simulator = demo_simulation()

    # 5. 报告生成
    demo_report()

    # 总结
    print("\n" + "="*60)
    print("演示总结")
    print("="*60)
    print("\n✅ 个股分析功能正常")
    print("✅ 策略列表功能正常")
    print("✅ 策略回测功能正常")
    print("✅ 模拟交易功能正常")
    print("✅ 报告生成功能正常")

    print("\n" + "="*60)
    print("系统已就绪，可以开始使用！")
    print("="*60)


if __name__ == "__main__":
    main()
