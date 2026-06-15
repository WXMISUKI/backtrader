"""
智能交易决策引擎
综合多维度分析，给出买入/卖出/持有的决策建议
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import List, Dict, Optional
from datetime import datetime

from .trend_detector import TrendDetector, TrendInfo
from .entry_exit import EntryExitTiming, EntrySignal, ExitSignal
from .position_manager import PositionManager, PositionInfo
from .risk_controller import RiskController, RiskMetrics


@dataclass
class TradeDecision:
    """交易决策"""
    action: str                           # 'BUY', 'SELL', 'HOLD'
    confidence: float                     # 置信度 0-1
    reasons: List[str]                    # 决策原因
    position_size: int = 0                # 仓位大小（股数）
    stop_loss: float = 0                  # 止损价
    take_profit: float = 0                # 止盈价
    trend: Optional[TrendInfo] = None     # 趋势信息
    entry_signal: Optional[EntrySignal] = None
    exit_signal: Optional[ExitSignal] = None
    risk_metrics: Optional[RiskMetrics] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def summary(self) -> str:
        """生成决策摘要"""
        lines = [
            f"{'='*50}",
            f"交易决策 - {self.timestamp}",
            f"{'='*50}",
            f"操作: {self.action}",
            f"置信度: {self.confidence:.1%}",
            f"仓位: {self.position_size}股",
            f"止损价: ¥{self.stop_loss:.2f}",
            f"止盈价: ¥{self.take_profit:.2f}",
            f"{'='*50}",
        ]

        if self.trend:
            lines.extend([
                f"趋势: {self.trend.trend_type} (强度: {self.trend.strength:.1%})",
                f"均线排列: {self.trend.ma_arrangement}",
                f"支撑位: ¥{self.trend.support_level:.2f}",
                f"阻力位: ¥{self.trend.resistance_level:.2f}",
            ])

        if self.reasons:
            lines.append(f"{'='*50}")
            lines.append("决策原因:")
            for reason in self.reasons:
                lines.append(f"  • {reason}")

        if self.risk_metrics:
            lines.extend([
                f"{'='*50}",
                f"盈亏比: {self.risk_metrics.risk_reward_ratio:.2f}",
                f"最大亏损: {self.risk_metrics.max_loss_pct:.1%}",
                f"预期盈利: {self.risk_metrics.expected_profit_pct:.1%}",
            ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """转换为字典，便于智能体工具输出。"""
        def _nested(value):
            if value is None:
                return None
            if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
                try:
                    return value.to_dict()
                except Exception:
                    pass
            if is_dataclass(value):
                return asdict(value)
            return str(value)

        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "position_size": self.position_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trend": _nested(self.trend),
            "entry_signal": _nested(self.entry_signal),
            "exit_signal": _nested(self.exit_signal),
            "risk_metrics": _nested(self.risk_metrics),
            "timestamp": self.timestamp,
        }


class TradingAdvisor:
    """
    智能交易决策引擎

    综合多维度分析，给出买入/卖出/持有的决策建议

    决策流程：
    1. 趋势判断 - 确定市场环境
    2. 技术分析 - 多指标共振确认
    3. 入场出场 - 择时判断
    4. 仓位管理 - 控制风险
    5. 止损止盈 - 保护利润
    """

    def __init__(self, risk_profile: str = 'moderate'):
        """
        初始化

        Args:
            risk_profile: 风险偏好 ('conservative', 'moderate', 'aggressive')
        """
        self.risk_profile = risk_profile
        self.trend_detector = TrendDetector()
        self.entry_exit = EntryExitTiming()
        self.position_manager = PositionManager(risk_profile)
        self.risk_controller = RiskController(risk_profile)

    def analyze(self, df: pd.DataFrame, stock_code: str = "",
                buy_price: float = 0, capital: float = 100000,
                current_positions: int = 0) -> TradeDecision:
        """
        综合分析，给出交易决策

        Args:
            df: OHLCV 数据
            stock_code: 股票代码
            buy_price: 买入价格（已持仓时提供）
            capital: 可用资金
            current_positions: 当前持仓数量

        Returns:
            TradeDecision
        """
        if len(df) < 60:
            return TradeDecision(
                action='HOLD',
                confidence=0,
                reasons=['数据不足，无法分析']
            )

        current_price = df['close'].iloc[-1]

        # 1. 趋势判断
        trend = self.trend_detector.detect(df)

        # 2. 判断是入场还是出场
        if buy_price > 0:
            # 已持仓，检查出场信号
            return self._analyze_exit(df, buy_price, trend, stock_code)
        else:
            # 未持仓，检查入场信号
            return self._analyze_entry(df, trend, stock_code, capital, current_positions)

    def _analyze_entry(self, df: pd.DataFrame, trend: TrendInfo,
                       stock_code: str, capital: float,
                       current_positions: int) -> TradeDecision:
        """分析入场时机"""
        current_price = df['close'].iloc[-1]

        # 检查入场信号
        entry_signal = self.entry_exit.check_entry(df, trend.trend_type)

        if not entry_signal.can_enter:
            return TradeDecision(
                action='HOLD',
                confidence=0,
                reasons=['入场条件不满足', f'信号强度: {entry_signal.strength:.1%}'],
                trend=trend,
                entry_signal=entry_signal
            )

        # 计算仓位
        position_info = self.position_manager.calc_position(
            capital, current_price, entry_signal.confidence,
            trend.trend_type, current_positions
        )

        # 计算止损止盈
        stop_loss = self.risk_controller.calc_stop_loss(
            current_price, trend.trend_type, trend.support_level
        )
        take_profit = self.risk_controller.calc_take_profit(
            current_price, trend.trend_type, entry_signal.confidence,
            trend.resistance_level
        )

        # 计算风险指标
        risk_metrics = self.risk_controller.calc_risk_metrics(
            current_price, current_price, stop_loss, take_profit
        )

        # 检查盈亏比是否合理
        if risk_metrics.risk_reward_ratio < 1.5:
            return TradeDecision(
                action='HOLD',
                confidence=entry_signal.confidence,
                reasons=[f'盈亏比不足: {risk_metrics.risk_reward_ratio:.2f} < 1.5'],
                trend=trend,
                entry_signal=entry_signal,
                risk_metrics=risk_metrics
            )

        # 生成决策
        reasons = [
            f'趋势: {trend.trend_type}',
            f'入场信号: {", ".join(entry_signal.signals)}',
            f'信号强度: {entry_signal.strength:.1%}',
            f'盈亏比: {risk_metrics.risk_reward_ratio:.2f}'
        ]

        return TradeDecision(
            action='BUY',
            confidence=entry_signal.confidence,
            reasons=reasons,
            position_size=position_info.shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trend=trend,
            entry_signal=entry_signal,
            risk_metrics=risk_metrics
        )

    def _analyze_exit(self, df: pd.DataFrame, buy_price: float,
                      trend: TrendInfo, stock_code: str) -> TradeDecision:
        """分析出场时机"""
        # 检查出场信号
        exit_signal = self.entry_exit.check_exit(df, buy_price, trend.trend_type)

        if not exit_signal.should_exit:
            # 计算当前盈亏
            current_price = df['close'].iloc[-1]
            profit_loss = (current_price - buy_price) / buy_price

            return TradeDecision(
                action='HOLD',
                confidence=0.5,
                reasons=[f'继续持有，当前盈亏: {profit_loss:.1%}'],
                trend=trend,
                exit_signal=exit_signal
            )

        # 生成卖出决策
        return TradeDecision(
            action='SELL',
            confidence=0.8,
            reasons=exit_signal.reasons,
            trend=trend,
            exit_signal=exit_signal
        )

    def analyze_with_signals(self, df: pd.DataFrame,
                             buy_price: float = 0) -> Dict:
        """
        详细分析，返回所有信号信息

        Args:
            df: OHLCV 数据
            buy_price: 买入价格

        Returns:
            详细分析结果字典
        """
        # 趋势分析
        trend = self.trend_detector.detect(df)

        # 入场信号
        entry_signal = self.entry_exit.check_entry(df, trend.trend_type)

        # 出场信号（如果有持仓）
        exit_signal = None
        if buy_price > 0:
            exit_signal = self.entry_exit.check_exit(df, buy_price, trend.trend_type)

        # 计算止损止盈
        current_price = df['close'].iloc[-1]
        stop_loss = self.risk_controller.calc_stop_loss(
            current_price, trend.trend_type, trend.support_level
        )
        take_profit = self.risk_controller.calc_take_profit(
            current_price, trend.trend_type, entry_signal.confidence,
            trend.resistance_level
        )

        # 风险指标
        risk_metrics = self.risk_controller.calc_risk_metrics(
            current_price, current_price, stop_loss, take_profit
        )

        return {
            'current_price': current_price,
            'trend': {
                'type': trend.trend_type,
                'strength': trend.strength,
                'ma_arrangement': trend.ma_arrangement,
                'support': trend.support_level,
                'resistance': trend.resistance_level
            },
            'entry': {
                'can_enter': entry_signal.can_enter,
                'strength': entry_signal.strength,
                'signals': entry_signal.signals
            },
            'exit': {
                'should_exit': exit_signal.should_exit if exit_signal else False,
                'reasons': exit_signal.reasons if exit_signal else []
            },
            'risk': {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': risk_metrics.risk_reward_ratio,
                'max_loss': risk_metrics.max_loss_pct
            }
        }


# 便捷函数
def create_advisor(risk_profile: str = 'moderate') -> TradingAdvisor:
    """创建交易顾问"""
    return TradingAdvisor(risk_profile)


def analyze_stock(df: pd.DataFrame, stock_code: str = "",
                  risk_profile: str = 'moderate') -> TradeDecision:
    """快速分析股票"""
    advisor = create_advisor(risk_profile)
    return advisor.analyze(df, stock_code)
