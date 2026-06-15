#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实数据回测测试
验证策略在真实市场数据上的盈利能力
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入项目模块
from eastmoney_config import get_stock_hist
from strategies.base import Bar, SignalType
from strategies.ma_cross import MACrossStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.boll_strategy import BollStrategy


def get_real_data(symbol='000001', days=250):
    """获取真实股票数据"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

    df = get_stock_hist(symbol=symbol, start_date=start_date, end_date=end_date)

    if df is None or len(df) == 0:
        print(f"❌ 无法获取 {symbol} 的数据")
        return None

    # 确保列名正确
    df = df.rename(columns={
        'open': 'open',
        'close': 'close',
        'high': 'high',
        'low': 'low',
        'volume': 'volume'
    })

    return df


def run_strategy_backtest(strategy_class, df, strategy_name, initial_capital=100000):
    """
    运行单个策略的回测

    Args:
        strategy_class: 策略类
        df: 股票数据
        strategy_name: 策略名称
        initial_capital: 初始资金

    Returns:
        回测结果字典
    """
    try:
        # 创建策略实例
        strategy = strategy_class()

        # 模拟交易
        capital = initial_capital
        position = 0  # 持仓数量
        shares = 0
        trades = []
        equity_curve = [capital]

        for i in range(1, len(df)):
            # 创建正确的 Bar 对象
            bar = Bar(df, index=i)

            # 获取策略信号
            try:
                signal = strategy.on_bar(bar)
            except Exception as e:
                signal = None

            # 执行交易
            if signal and hasattr(signal, 'type'):
                if signal.type == SignalType.BUY and position == 0:
                    # 买入
                    buy_price = bar.close
                    shares = int(capital * 0.95 / buy_price / 100) * 100  # 按手买入
                    if shares > 0:
                        cost = shares * buy_price
                        capital -= cost
                        position = shares
                        trades.append({
                            'type': 'BUY',
                            'date': bar.datetime,
                            'price': buy_price,
                            'shares': shares,
                            'cost': cost
                        })

                elif signal.type == SignalType.SELL and position > 0:
                    # 卖出
                    sell_price = bar.close
                    revenue = shares * sell_price
                    capital += revenue

                    if trades:
                        buy_price = trades[-1]['price']
                        profit = (sell_price - buy_price) / buy_price * 100
                    else:
                        profit = 0

                    trades.append({
                        'type': 'SELL',
                        'date': bar.datetime,
                        'price': sell_price,
                        'shares': shares,
                        'revenue': revenue,
                        'profit': profit
                    })
                    position = 0
                    shares = 0

            # 计算当前权益
            current_equity = capital + position * bar.close
            equity_curve.append(current_equity)

        # 计算最终权益
        final_equity = capital + position * df.iloc[-1]['close']

        # 计算统计指标
        total_return = (final_equity / initial_capital - 1) * 100

        # 计算最大回撤
        equity_series = pd.Series(equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series / cummax - 1) * 100
        max_drawdown = drawdown.min()

        # 计算胜率
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        if sell_trades:
            win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
            win_rate = len(win_trades) / len(sell_trades) * 100
        else:
            win_rate = 0

        # 计算年化收益
        trading_days = len(df)
        annual_return = ((1 + total_return/100) ** (252/trading_days) - 1) * 100

        return {
            'strategy': strategy_name,
            'initial_capital': initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'sell_trades': len(sell_trades),
            'win_rate': win_rate,
            'trades': trades,
            'equity_curve': equity_curve
        }

    except Exception as e:
        print(f"策略 {strategy_name} 回测出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_backtest_result(result):
    """打印回测结果"""
    if result is None:
        print("  ❌ 回测失败")
        return

    print(f"\n{'='*50}")
    print(f"策略: {result['strategy']}")
    print(f"{'='*50}")
    print(f"初始资金: ¥{result['initial_capital']:,.2f}")
    print(f"最终权益: ¥{result['final_equity']:,.2f}")
    print(f"总收益率: {result['total_return']:+.2f}%")
    print(f"年化收益: {result['annual_return']:+.2f}%")
    print(f"最大回撤: {result['max_drawdown']:.2f}%")
    print(f"交易次数: {result['total_trades']}")
    print(f"卖出次数: {result['sell_trades']}")
    print(f"胜率: {result['win_rate']:.1f}%")

    # 打印最近几笔交易
    trades = result['trades']
    if len(trades) > 0:
        print(f"\n最近交易:")
        for t in trades[-6:]:
            if t['type'] == 'BUY':
                print(f"  {t['date']}: 买入 {t['shares']}股 @ ¥{t['price']:.2f}")
            else:
                profit = t.get('profit', 0)
                emoji = '✅' if profit > 0 else '❌'
                print(f"  {t['date']}: 卖出 {t['shares']}股 @ ¥{t['price']:.2f} ({profit:+.2f}%) {emoji}")


def main():
    """主函数"""
    print("="*60)
    print("真实数据回测测试 - 验证策略盈利能力")
    print("="*60)

    # 测试股票列表
    stocks = [
        ('000001', '平安银行'),
        ('600036', '招商银行'),
        ('000858', '五粮液'),
    ]

    strategies = [
        (MACrossStrategy, 'MA交叉策略'),
        (MACDStrategy, 'MACD策略'),
        (RSIStrategy, 'RSI策略'),
        (BollStrategy, '布林带策略'),
    ]

    all_results = []

    for symbol, name in stocks:
        print(f"\n{'#'*60}")
        print(f"# 股票: {name} ({symbol})")
        print(f"{'#'*60}")

        # 获取真实数据
        df = get_real_data(symbol, days=365)

        if df is None:
            continue

        print(f"获取到 {len(df)} 条数据")
        print(f"时间范围: {df.index[0]} ~ {df.index[-1]}")
        print(f"起始价格: ¥{df.iloc[0]['close']:.2f}")
        print(f"结束价格: ¥{df.iloc[-1]['close']:.2f}")
        print(f"买入持有收益: {(df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100:+.2f}%")

        # 运行各策略
        for strategy_class, strategy_name in strategies:
            print(f"\n运行 {strategy_name}...")
            result = run_strategy_backtest(strategy_class, df, f"{name}-{strategy_name}")
            print_backtest_result(result)

            if result:
                result['stock'] = name
                result['symbol'] = symbol
                all_results.append(result)

    # 汇总比较
    print(f"\n{'='*60}")
    print("策略汇总比较")
    print(f"{'='*60}")

    if all_results:
        # 按收益率排序
        all_results.sort(key=lambda x: x['total_return'], reverse=True)

        print(f"\n{'股票':<10} {'策略':<12} {'收益率':>10} {'年化收益':>10} {'最大回撤':>10} {'胜率':>8}")
        print("-"*65)

        for r in all_results:
            print(f"{r['stock']:<10} {r['strategy']:<12} {r['total_return']:>+9.2f}% {r['annual_return']:>+9.2f}% {r['max_drawdown']:>9.2f}% {r['win_rate']:>7.1f}%")

        # 计算平均表现
        avg_return = np.mean([r['total_return'] for r in all_results])
        avg_win_rate = np.mean([r['win_rate'] for r in all_results])

        print("-"*65)
        print(f"{'平均':<22} {avg_return:>+9.2f}% {'':>10} {'':>10} {avg_win_rate:>7.1f}%")

        # 找出最佳策略
        best = all_results[0]
        print(f"\n🏆 最佳表现: {best['stock']} - {best['strategy']}")
        print(f"   收益率: {best['total_return']:+.2f}%")
        print(f"   胜率: {best['win_rate']:.1f}%")


if __name__ == '__main__':
    main()
