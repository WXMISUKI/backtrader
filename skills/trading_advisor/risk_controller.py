"""
风险控制器
动态止损止盈
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskMetrics:
    """风险指标"""
    stop_loss_price: float     # 止损价
    take_profit_price: float   # 止盈价
    max_loss_pct: float        # 最大亏损比例
    expected_profit_pct: float # 预期盈利比例
    risk_reward_ratio: float   # 盈亏比


class RiskController:
    """
    风险控制器
    动态止损止盈
    """

    def __init__(self, risk_profile: str = 'moderate'):
        """
        初始化

        Args:
            risk_profile: 风险偏好
        """
        self.risk_profile = risk_profile

        # 基础止损比例
        self.base_stop_loss = {
            'conservative': 0.03,  # 3%
            'moderate': 0.05,      # 5%
            'aggressive': 0.08     # 8%
        }[risk_profile]

        # 基础止盈比例
        self.base_take_profit = {
            'conservative': 0.08,  # 8%
            'moderate': 0.15,      # 15%
            'aggressive': 0.25     # 25%
        }[risk_profile]

        # 日内最大亏损
        self.max_daily_loss = {
            'conservative': 0.02,  # 2%
            'moderate': 0.03,      # 3%
            'aggressive': 0.05     # 5%
        }[risk_profile]

    def calc_stop_loss(self, buy_price: float, trend_type: str,
                       support_level: Optional[float] = None) -> float:
        """
        计算止损价

        动态止损策略：
        1. 基础止损
        2. 趋势调整（熊市更严格）
        3. 支撑位止损

        Args:
            buy_price: 买入价格
            trend_type: 趋势类型
            support_level: 支撑位

        Returns:
            止损价
        """
        # 基础止损
        stop_loss_pct = self.base_stop_loss

        # 趋势调整
        if trend_type == 'BEAR':
            stop_loss_pct *= 0.6  # 熊市止损更严格
        elif trend_type == 'BULL':
            stop_loss_pct *= 1.2  # 牛市止损更宽松

        # 基础止损价
        base_stop_price = buy_price * (1 - stop_loss_pct)

        # 支撑位止损
        if support_level and support_level > 0:
            # 使用支撑位作为止损（如果支撑位在止损范围内）
            support_stop = support_level * 0.99  # 支撑位下方1%
            if support_stop > base_stop_price * 0.95:  # 不低于基础止损的95%
                return support_stop

        return base_stop_price

    def calc_take_profit(self, buy_price: float, trend_type: str,
                         confidence: float,
                         resistance_level: Optional[float] = None) -> float:
        """
        计算止盈价

        动态止盈策略：
        1. 基础止盈
        2. 趋势加成（牛市更高）
        3. 置信度加成
        4. 阻力位止盈

        Args:
            buy_price: 买入价格
            trend_type: 趋势类型
            confidence: 信号置信度
            resistance_level: 阻力位

        Returns:
            止盈价
        """
        # 基础止盈
        base_pct = self.base_take_profit

        # 趋势加成
        trend_bonus = {
            'BULL': 0.10,      # 牛市 +10%
            'RANGING': 0.05,   # 震荡 +5%
            'BEAR': 0.00       # 熊市 +0%
        }.get(trend_type, 0)

        # 置信度加成
        confidence_bonus = (confidence - 0.5) * 0.2  # 置信度每高0.1，加2%

        # 总止盈比例
        total_pct = base_pct + trend_bonus + confidence_bonus

        # 基础止盈价
        base_profit_price = buy_price * (1 + total_pct)

        # 阻力位止盈
        if resistance_level and resistance_level > 0:
            # 使用阻力位作为止盈（如果阻力位在止盈范围内）
            if resistance_level < base_profit_price * 1.1:  # 不超过基础止盈的110%
                return resistance_level

        return base_profit_price

    def calc_risk_metrics(self, buy_price: float, current_price: float,
                          stop_loss: float, take_profit: float) -> RiskMetrics:
        """
        计算风险指标

        Args:
            buy_price: 买入价格
            current_price: 当前价格
            stop_loss: 止损价
            take_profit: 止盈价

        Returns:
            RiskMetrics
        """
        # 最大亏损
        max_loss = (stop_loss - buy_price) / buy_price

        # 预期盈利
        expected_profit = (take_profit - buy_price) / buy_price

        # 盈亏比
        risk_reward = abs(expected_profit / max_loss) if max_loss != 0 else 0

        return RiskMetrics(
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            max_loss_pct=max_loss,
            expected_profit_pct=expected_profit,
            risk_reward_ratio=risk_reward
        )

    def should_trail_stop(self, current_price: float, buy_price: float,
                          highest_price: float) -> bool:
        """
        是否应该移动止损

        移动止损条件：
        1. 当前盈利 > 10%
        2. 从最高点回撤 > 5%
        """
        profit_pct = (current_price - buy_price) / buy_price
        # 计算从最高点的回撤（正数表示回撤）
        drawdown_pct = (highest_price - current_price) / highest_price

        return profit_pct > 0.10 and drawdown_pct > 0.05

    def calc_trail_stop(self, highest_price: float,
                        trail_pct: float = 0.05) -> float:
        """
        计算移动止损价

        Args:
            highest_price: 持仓期间最高价
            trail_pct: 回撤比例

        Returns:
            移动止损价
        """
        return highest_price * (1 - trail_pct)

    def check_daily_loss_limit(self, daily_pnl: float) -> bool:
        """
        检查日内亏损限制

        Args:
            daily_pnl: 日内盈亏比例

        Returns:
            是否触发日内止损
        """
        return daily_pnl < -self.max_daily_loss

    def calc_position_risk(self, position_size: int, price: float,
                           capital: float) -> dict:
        """
        计算仓位风险

        Args:
            position_size: 持仓股数
            price: 当前价格
            capital: 总资金

        Returns:
            风险指标字典
        """
        position_value = position_size * price
        position_ratio = position_value / capital

        # 止损风险
        stop_loss_value = position_value * self.base_stop_loss

        # 风险等级
        if position_ratio > 0.5:
            risk_level = 'HIGH'
        elif position_ratio > 0.3:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        return {
            'position_value': position_value,
            'position_ratio': position_ratio,
            'stop_loss_value': stop_loss_value,
            'risk_level': risk_level
        }
