#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟交易演示

演示如何使用交易模拟器进行模拟交易
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.stock_simulator import TradingSimulator
from skills.stock_advisor import analyze
from skills.stock_report import ReportGenerator


def simulate_trading():
    """
    模拟交易流程
    """
    print("="*60)
    print("股票量化交易系统 - 模拟交易演示")
    print("="*60)

    # 创建模拟器
    simulator = TradingSimulator(initial_cash=1000000)

    print(f"\n初始资金: {simulator.initial_cash:,.2f}")

    # 模拟交易序列
    trades = [
        # (股票代码, 股票名称, 价格, 数量, 方向)
        ("000001", "平安银行", 10.50, 1000, "BUY"),
        ("600519", "贵州茅台", 1800.00, 100, "BUY"),
        ("000858", "五粮液", 150.00, 500, "BUY"),
        ("000001", "平安银行", 10.80, 500, "BUY"),  # 加仓
        ("600519", "贵州茅台", 1850.00, 50, "SELL"),  # 减仓
        ("000001", "平安银行", 11.20, 1500, "SELL"),  # 清仓
        ("000858", "五粮液", 155.00, 500, "SELL"),  # 清仓
        ("600519", "贵州茅台", 1900.00, 50, "SELL"),  # 清仓
    ]

    print("\n" + "-"*60)
    print("交易记录")
    print("-"*60)

    for stock_code, stock_name, price, size, direction in trades:
        if direction == "BUY":
            simulator.buy(stock_code, stock_name, price, size)
        else:
            simulator.sell(stock_code, price, size)

    # 打印持仓信息
    print("\n" + "-"*60)
    print("当前持仓")
    print("-"*60)
    portfolio = simulator.get_portfolio()
    print(f"现金: {portfolio['cash']:,.2f}")
    print(f"持仓市值: {portfolio['market_value']:,.2f}")
    print(f"总资产: {portfolio['total_assets']:,.2f}")

    if portfolio['positions']:
        print("\n持仓明细:")
        for pos in portfolio['positions']:
            print(f"  {pos['stock_name']}({pos['stock_code']}): "
                  f"{pos['size']}股 @ {pos['avg_cost']:.2f}, "
                  f"市值={pos['market_value']:,.2f}, "
                  f"盈亏={pos['profit']:,.2f} ({pos['profit_pct']:.2f}%)")

    # 打印业绩信息
    print("\n" + "-"*60)
    print("业绩统计")
    print("-"*60)
    performance = simulator.get_performance()
    print(f"初始资金: {performance['initial_cash']:,.2f}")
    print(f"当前资产: {performance['total_assets']:,.2f}")
    print(f"总收益: {performance['total_profit']:,.2f}")
    print(f"收益率: {performance['total_profit_pct']:.2f}%")
    print(f"总交易数: {performance['total_trades']}")
    print(f"买入次数: {performance['buy_trades']}")
    print(f"卖出次数: {performance['sell_trades']}")
    print(f"总手续费: {performance['total_commission']:,.2f}")
    print(f"总印花税: {performance['total_tax']:,.2f}")

    # 打印交易记录
    print("\n" + "-"*60)
    print("交易明细")
    print("-"*60)
    trades = simulator.get_trades()
    for trade in trades:
        print(f"  {trade['datetime']}: "
              f"{trade['direction']} {trade['stock_name']} "
              f"{trade['size']}股 @ {trade['price']:.2f}, "
              f"金额={trade['amount']:,.2f}, "
              f"手续费={trade['commission']:.2f}")

    # 生成报告
    print("\n" + "-"*60)
    print("交易报告")
    print("-"*60)
    report = ReportGenerator.generate_json_report(performance)
    print(report)

    print("\n" + "="*60)
    print("模拟交易演示完成！")
    print("="*60)


if __name__ == "__main__":
    simulate_trading()
