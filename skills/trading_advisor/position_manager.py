"""
仓位管理器
根据信号强度、趋势、风险控制仓位
"""

from dataclasses import dataclass


@dataclass
class PositionInfo:
    """仓位信息"""
    shares: int           # 股数
    position_ratio: float # 仓位比例
    capital_used: float   # 使用资金
    risk_level: str       # 风险等级


class PositionManager:
    """
    仓位管理器
    根据信号强度、趋势、风险控制仓位
    """

    def __init__(self, risk_profile: str = 'moderate'):
        """
        初始化

        Args:
            risk_profile: 风险偏好 ('conservative', 'moderate', 'aggressive')
        """
        self.risk_profile = risk_profile

        # 最大仓位比例
        self.max_position_ratio = {
            'conservative': 0.30,  # 最多30%仓位
            'moderate': 0.50,      # 最多50%仓位
            'aggressive': 0.80     # 最多80%仓位
        }[risk_profile]

        # 最小开仓比例
        self.min_position_ratio = 0.10  # 至少10%仓位

        # 单只股票最大仓位
        self.max_single_stock = {
            'conservative': 0.15,  # 单只最多15%
            'moderate': 0.25,      # 单只最多25%
            'aggressive': 0.40     # 单只最多40%
        }[risk_profile]

    def calc_position(self, capital: float, price: float,
                      confidence: float, trend_type: str,
                      current_positions: int = 0) -> PositionInfo:
        """
        计算仓位大小

        Args:
            capital: 可用资金
            price: 当前价格
            confidence: 信号置信度 (0-1)
            trend_type: 趋势类型
            current_positions: 当前持仓数量

        Returns:
            PositionInfo
        """
        # 基础仓位 = 可用资金 * 最大仓位比例
        base_capital = capital * self.max_position_ratio

        # 根据信号强度调整
        confidence_factor = self._calc_confidence_factor(confidence)

        # 根据趋势调整
        trend_factor = self._calc_trend_factor(trend_type)

        # 根据持仓数量调整（分散风险）
        position_factor = self._calc_position_factor(current_positions)

        # 计算实际可用资金
        adjusted_capital = base_capital * confidence_factor * trend_factor * position_factor

        # 计算股数（100的整数倍）
        shares = int(adjusted_capital / price / 100) * 100

        # 确保最少1手
        shares = max(100, shares)

        # 确保不超过单只股票最大仓位
        max_shares = int(capital * self.max_single_stock / price / 100) * 100
        shares = min(shares, max_shares)

        # 计算实际使用资金
        capital_used = shares * price
        position_ratio = capital_used / capital

        # 确定风险等级
        risk_level = self._assess_risk_level(position_ratio, confidence, trend_type)

        return PositionInfo(
            shares=shares,
            position_ratio=position_ratio,
            capital_used=capital_used,
            risk_level=risk_level
        )

    def should_add_position(self, current_profit: float,
                            trend_type: str, confidence: float) -> bool:
        """
        是否加仓

        加仓条件：
        1. 当前盈利 > 5%
        2. 趋势为牛市
        3. 信号置信度 > 0.7
        """
        return (current_profit > 0.05 and
                trend_type == 'BULL' and
                confidence > 0.7)

    def calc_add_position(self, capital: float, price: float,
                          current_shares: int, current_profit: float) -> PositionInfo:
        """
        计算加仓数量

        加仓策略：
        - 盈利 5-10%: 加仓 10%
        - 盈利 10-20%: 加仓 15%
        - 盈利 > 20%: 加仓 20%
        """
        if current_profit < 0.05:
            return PositionInfo(0, 0, 0, 'NONE')

        # 确定加仓比例
        if current_profit < 0.10:
            add_ratio = 0.10
        elif current_profit < 0.20:
            add_ratio = 0.15
        else:
            add_ratio = 0.20

        # 计算加仓资金
        add_capital = capital * add_ratio
        add_shares = int(add_capital / price / 100) * 100

        return PositionInfo(
            shares=add_shares,
            position_ratio=add_ratio,
            capital_used=add_shares * price,
            risk_level='LOW'
        )

    def _calc_confidence_factor(self, confidence: float) -> float:
        """
        根据置信度调整仓位

        置信度越高，仓位越大
        """
        if confidence >= 0.8:
            return 1.0
        elif confidence >= 0.6:
            return 0.8
        elif confidence >= 0.5:
            return 0.6
        else:
            return 0.4

    def _calc_trend_factor(self, trend_type: str) -> float:
        """
        根据趋势调整仓位

        牛市满仓，熊市轻仓
        """
        return {
            'BULL': 1.0,      # 牛市: 100%
            'RANGING': 0.6,   # 震荡市: 60%
            'BEAR': 0.3       # 熊市: 30%
        }.get(trend_type, 0.5)

    def _calc_position_factor(self, current_positions: int) -> float:
        """
        根据持仓数量调整仓位

        持仓越多，新仓位越小（分散风险）
        """
        if current_positions == 0:
            return 1.0
        elif current_positions == 1:
            return 0.8
        elif current_positions == 2:
            return 0.6
        elif current_positions == 3:
            return 0.4
        else:
            return 0.2

    def _assess_risk_level(self, position_ratio: float,
                           confidence: float, trend_type: str) -> str:
        """评估风险等级"""
        risk_score = 0

        # 仓位风险
        if position_ratio > 0.5:
            risk_score += 3
        elif position_ratio > 0.3:
            risk_score += 2
        else:
            risk_score += 1

        # 置信度风险
        if confidence < 0.5:
            risk_score += 2
        elif confidence < 0.7:
            risk_score += 1

        # 趋势风险
        if trend_type == 'BEAR':
            risk_score += 2
        elif trend_type == 'RANGING':
            risk_score += 1

        # 风险等级
        if risk_score >= 5:
            return 'HIGH'
        elif risk_score >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'
