#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略回测演示

演示如何使用回测引擎测试不同策略
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest import run_backtest
from strategies import list_strategies


def backtest_single_strategy(stock_code, strategy_name, config=None):
    """
    回测单个策略

    参数:
        stock_code: 股票代码
        strategy_name: 策略名称
        config: 策略配置
    """
    print(f"\n{'='*60}")
    print(f"回测策略: {strategy_name}")
    print(f"股票代码: {stock_code}")
    print(f"{'='*60}")

    try:
        result = run_backtest(
            stock_code=stock_code,
            strategy_name=strategy_name,
            config=config,
            start_date="20260101",
            end_date="20260614",
            initial_cash=100000
        )

        print(result.summary())
        return result

    except Exception as e:
        print(f"回测失败: {e}")
        return None


def backtest_all_strategies(stock_code):
    """
    回测所有策略

    参数:
        stock_code: 股票代码
    """
    print(f"\n{'='*60}")
    print(f"回测所有策略 - {stock_code}")
    print(f"{'='*60}")

    strategies = list_strategies()
    results = []

    for strategy_name in strategies:
        if strategy_name == 'composite':
            # 综合策略使用特殊配置
            config = {
                'strategies': ['ma_cross', 'macd', 'rsi'],
                'min_agreement': 2
            }
        else:
            config = None

        result = backtest_single_strategy(stock_code, strategy_name, config)
        if result:
            results.append((strategy_name, result))

    # 汇总比较
    if results:
        print(f"\n{'='*60}")
        print("策略对比汇总")
        print(f"{'='*60}")
        print(f"{'策略名称':<15} {'总收益率':<12} {'年化收益':<12} {'最大回撤':<12} {'夏普比率':<12} {'胜率':<12}")
        print(f"{'─'*75}")

        for name, r in results:
            print(f"{name:<15} {r.total_return:<12.2%} {r.annual_return:<12.2%} {r.max_drawdown:<12.2%} {r.sharpe_ratio:<12.2f} {r.win_rate:<12.2%}")

        # 找出最佳策略
        best = max(results, key=lambda x: x[1].total_return)
        print(f"\n🏆 最佳策略: {best[0]} (收益率: {best[1].total_return:.2%})")


def main():
    """主函数"""
    print("="*60)
    print("股票量化交易系统 - 策略回测演示")
    print("="*60)

    # 测试股票
    stock_code = "000001"

    # 回测所有策略
    backtest_all_strategies(stock_code)

    print("\n" + "="*60)
    print("回测演示完成！")
    print("="*60)


if __name__ == "__main__":
    main()
