#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易模拟器

模拟真实交易环境，验证策略有效性

功能:
- 虚拟资金管理
- 交易撮合
- 手续费计算
- 持仓管理
- 业绩计算
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Position:
    """
    持仓信息
    """
    stock_code: str          # 股票代码
    stock_name: str          # 股票名称
    size: int                # 持仓数量
    avg_cost: float          # 平均成本
    current_price: float     # 当前价格
    market_value: float      # 市值
    profit: float            # 盈亏
    profit_pct: float        # 盈亏比例

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'size': self.size,
            'avg_cost': round(self.avg_cost, 2),
            'current_price': round(self.current_price, 2),
            'market_value': round(self.market_value, 2),
            'profit': round(self.profit, 2),
            'profit_pct': round(self.profit_pct, 2)
        }


@dataclass
class TradeRecord:
    """
    交易记录
    """
    trade_id: int            # 交易ID
    datetime: str            # 交易时间
    stock_code: str          # 股票代码
    stock_name: str          # 股票名称
    direction: str           # 买卖方向 (BUY/SELL)
    price: float             # 成交价格
    size: int                # 成交数量
    amount: float            # 成交金额
    commission: float        # 手续费
    tax: float               # 印花税
    total_cost: float        # 总成本

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'trade_id': self.trade_id,
            'datetime': self.datetime,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'direction': self.direction,
            'price': round(self.price, 2),
            'size': self.size,
            'amount': round(self.amount, 2),
            'commission': round(self.commission, 2),
            'tax': round(self.tax, 2),
            'total_cost': round(self.total_cost, 2)
        }


@dataclass
class PortfolioSnapshot:
    """
    组合快照
    """
    datetime: str            # 时间
    total_assets: float      # 总资产
    cash: float              # 现金
    market_value: float      # 持仓市值
    total_profit: float      # 总盈亏
    total_profit_pct: float  # 总收益率

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'datetime': self.datetime,
            'total_assets': round(self.total_assets, 2),
            'cash': round(self.cash, 2),
            'market_value': round(self.market_value, 2),
            'total_profit': round(self.total_profit, 2),
            'total_profit_pct': round(self.total_profit_pct, 2)
        }


class TradingSimulator:
    """
    交易模拟器

    模拟真实交易环境

    示例:
        >>> simulator = TradingSimulator(initial_cash=1000000)
        >>> simulator.buy("000001", "平安银行", 10.5, 1000)
        >>> simulator.sell("000001", 11.0, 1000)
        >>> print(simulator.get_performance())
    """

    def __init__(
        self,
        initial_cash: float = 1000000,
        commission_rate: float = 0.001,
        tax_rate: float = 0.001,
        min_commission: float = 5.0
    ):
        """
        初始化

        参数:
            initial_cash: 初始资金
            commission_rate: 佣金费率
            tax_rate: 印花税费率 (仅卖出收取)
            min_commission: 最低佣金
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.min_commission = min_commission

        # 持仓 {stock_code: Position}
        self._positions: Dict[str, Position] = {}

        # 交易记录
        self._trades: List[TradeRecord] = []
        self._trade_id = 0

        # 组合快照
        self._snapshots: List[PortfolioSnapshot] = []

        # 股票名称缓存
        self._stock_names: Dict[str, str] = {}

    def buy(
        self,
        stock_code: str,
        stock_name: str,
        price: float,
        size: int,
        datetime_str: str = None
    ) -> bool:
        """
        买入股票

        参数:
            stock_code: 股票代码
            stock_name: 股票名称
            price: 买入价格
            size: 买入数量 (必须是100的整数倍)
            datetime_str: 交易时间

        返回:
            是否成功
        """
        # 验证数量
        if size <= 0 or size % 100 != 0:
            print(f"错误: 买入数量必须是100的整数倍，当前: {size}")
            return False

        # 计算费用
        amount = price * size
        commission = max(amount * self.commission_rate, self.min_commission)
        tax = 0  # 买入不收印花税
        total_cost = amount + commission

        # 检查资金
        if total_cost > self.cash:
            print(f"错误: 资金不足，需要 {total_cost:.2f}，可用 {self.cash:.2f}")
            return False

        # 扣除资金
        self.cash -= total_cost

        # 更新持仓
        if stock_code in self._positions:
            # 加仓
            pos = self._positions[stock_code]
            total_size = pos.size + size
            total_amount = pos.avg_cost * pos.size + price * size
            pos.avg_cost = total_amount / total_size
            pos.size = total_size
            pos.current_price = price
            pos.market_value = price * total_size
            pos.profit = (price - pos.avg_cost) * total_size
            pos.profit_pct = (price / pos.avg_cost - 1) * 100
        else:
            # 新建持仓
            self._positions[stock_code] = Position(
                stock_code=stock_code,
                stock_name=stock_name,
                size=size,
                avg_cost=price,
                current_price=price,
                market_value=price * size,
                profit=0,
                profit_pct=0
            )

        # 缓存股票名称
        self._stock_names[stock_code] = stock_name

        # 记录交易
        self._trade_id += 1
        trade = TradeRecord(
            trade_id=self._trade_id,
            datetime=datetime_str or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            stock_code=stock_code,
            stock_name=stock_name,
            direction='BUY',
            price=price,
            size=size,
            amount=amount,
            commission=commission,
            tax=tax,
            total_cost=total_cost
        )
        self._trades.append(trade)

        print(f"买入成功: {stock_name}({stock_code}) {size}股 @ {price:.2f}")
        return True

    def sell(
        self,
        stock_code: str,
        price: float,
        size: int = None,
        datetime_str: str = None
    ) -> bool:
        """
        卖出股票

        参数:
            stock_code: 股票代码
            price: 卖出价格
            size: 卖出数量，默认全部卖出
            datetime_str: 交易时间

        返回:
            是否成功
        """
        # 检查持仓
        if stock_code not in self._positions:
            print(f"错误: 没有持仓 {stock_code}")
            return False

        pos = self._positions[stock_code]

        # 默认全部卖出
        if size is None:
            size = pos.size

        # 验证数量
        if size <= 0 or size > pos.size:
            print(f"错误: 卖出数量无效，当前持仓: {pos.size}")
            return False

        # 计算费用
        amount = price * size
        commission = max(amount * self.commission_rate, self.min_commission)
        tax = amount * self.tax_rate  # 卖出收印花税
        total_income = amount - commission - tax

        # 增加资金
        self.cash += total_income

        # 更新持仓
        pos.size -= size
        if pos.size == 0:
            # 清仓
            del self._positions[stock_code]
        else:
            # 减仓
            pos.current_price = price
            pos.market_value = price * pos.size
            pos.profit = (price - pos.avg_cost) * pos.size
            pos.profit_pct = (price / pos.avg_cost - 1) * 100

        # 记录交易
        self._trade_id += 1
        stock_name = self._stock_names.get(stock_code, stock_code)
        trade = TradeRecord(
            trade_id=self._trade_id,
            datetime=datetime_str or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            stock_code=stock_code,
            stock_name=stock_name,
            direction='SELL',
            price=price,
            size=size,
            amount=amount,
            commission=commission,
            tax=tax,
            total_cost=commission + tax
        )
        self._trades.append(trade)

        print(f"卖出成功: {stock_name}({stock_code}) {size}股 @ {price:.2f}")
        return True

    def get_portfolio(self) -> dict:
        """
        获取持仓信息

        返回:
            持仓信息字典
        """
        positions = []
        total_market_value = 0

        for pos in self._positions.values():
            positions.append(pos.to_dict())
            total_market_value += pos.market_value

        return {
            'cash': round(self.cash, 2),
            'market_value': round(total_market_value, 2),
            'total_assets': round(self.cash + total_market_value, 2),
            'positions': positions
        }

    def get_performance(self) -> dict:
        """
        获取业绩信息

        返回:
            业绩信息字典
        """
        # 计算当前总资产
        total_market_value = sum(pos.market_value for pos in self._positions.values())
        total_assets = self.cash + total_market_value

        # 计算收益
        total_profit = total_assets - self.initial_cash
        total_profit_pct = (total_assets / self.initial_cash - 1) * 100

        # 计算交易统计
        total_trades = len(self._trades)
        buy_trades = len([t for t in self._trades if t.direction == 'BUY'])
        sell_trades = len([t for t in self._trades if t.direction == 'SELL'])

        # 计算手续费
        total_commission = sum(t.commission for t in self._trades)
        total_tax = sum(t.tax for t in self._trades)

        return {
            'initial_cash': round(self.initial_cash, 2),
            'total_assets': round(total_assets, 2),
            'cash': round(self.cash, 2),
            'market_value': round(total_market_value, 2),
            'total_profit': round(total_profit, 2),
            'total_profit_pct': round(total_profit_pct, 2),
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_commission': round(total_commission, 2),
            'total_tax': round(total_tax, 2)
        }

    def get_trades(self) -> List[dict]:
        """获取交易记录"""
        return [t.to_dict() for t in self._trades]

    def update_prices(self, prices: Dict[str, float]):
        """
        更新持仓价格

        参数:
            prices: {stock_code: price}
        """
        for stock_code, price in prices.items():
            if stock_code in self._positions:
                pos = self._positions[stock_code]
                pos.current_price = price
                pos.market_value = price * pos.size
                pos.profit = (price - pos.avg_cost) * pos.size
                pos.profit_pct = (price / pos.avg_cost - 1) * 100

    def take_snapshot(self, datetime_str: str = None):
        """
        保存组合快照

        参数:
            datetime_str: 快照时间
        """
        total_market_value = sum(pos.market_value for pos in self._positions.values())
        total_assets = self.cash + total_market_value
        total_profit = total_assets - self.initial_cash
        total_profit_pct = (total_assets / self.initial_cash - 1) * 100

        snapshot = PortfolioSnapshot(
            datetime=datetime_str or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_assets=total_assets,
            cash=self.cash,
            market_value=total_market_value,
            total_profit=total_profit,
            total_profit_pct=total_profit_pct
        )
        self._snapshots.append(snapshot)

    def get_snapshots(self) -> List[dict]:
        """获取组合快照"""
        return [s.to_dict() for s in self._snapshots]


# 便捷函数
def create_simulator(initial_cash: float = 1000000) -> TradingSimulator:
    """
    创建交易模拟器

    参数:
        initial_cash: 初始资金

    返回:
        TradingSimulator 实例
    """
    return TradingSimulator(initial_cash=initial_cash)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("交易模拟器测试")
    print("=" * 60)

    # 创建模拟器
    simulator = TradingSimulator(initial_cash=1000000)

    # 测试买入
    print("\n1. 买入测试:")
    simulator.buy("000001", "平安银行", 10.5, 1000)
    simulator.buy("600519", "贵州茅台", 1800.0, 100)

    # 测试持仓
    print("\n2. 持仓信息:")
    portfolio = simulator.get_portfolio()
    print(f"   现金: {portfolio['cash']:,.2f}")
    print(f"   持仓市值: {portfolio['market_value']:,.2f}")
    print(f"   总资产: {portfolio['total_assets']:,.2f}")

    # 测试卖出
    print("\n3. 卖出测试:")
    simulator.sell("000001", 11.0, 500)

    # 测试业绩
    print("\n4. 业绩信息:")
    performance = simulator.get_performance()
    print(f"   总收益: {performance['total_profit']:,.2f}")
    print(f"   收益率: {performance['total_profit_pct']:.2f}%")

    # 测试交易记录
    print("\n5. 交易记录:")
    trades = simulator.get_trades()
    for trade in trades:
        print(f"   {trade['datetime']}: {trade['direction']} {trade['stock_name']} {trade['size']}股 @ {trade['price']}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
