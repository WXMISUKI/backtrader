#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
风险偏好配置管理
支持保守型、稳健型、激进型三档风险配置
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


class RiskLevel(Enum):
    """风险等级枚举"""
    CONSERVATIVE = "conservative"  # 保守型
    MODERATE = "moderate"          # 稳健型
    AGGRESSIVE = "aggressive"      # 激进型


@dataclass
class RiskProfile:
    """风险偏好配置"""
    name: str                           # 配置名称
    stop_loss: float                    # 止损阈值 (如 0.05 表示 5%)
    take_profit: float                  # 止盈阈值
    max_position: float                 # 最大仓位比例
    rsi_overbought: int                 # RSI 超买阈值
    rsi_oversold: int                   # RSI 超卖阈值
    min_signal_strength: float          # 最小信号强度
    max_daily_trades: int               # 每日最大交易次数
    description: str                    # 配置描述


# 预定义的风险配置
RISK_PROFILES: Dict[str, RiskProfile] = {
    "conservative": RiskProfile(
        name="保守型",
        stop_loss=0.03,
        take_profit=0.08,
        max_position=0.30,
        rsi_overbought=65,
        rsi_oversold=35,
        min_signal_strength=0.7,
        max_daily_trades=2,
        description="追求稳定收益，严格止损止盈，仓位控制严格"
    ),

    "moderate": RiskProfile(
        name="稳健型",
        stop_loss=0.05,
        take_profit=0.15,
        max_position=0.50,
        rsi_overbought=70,
        rsi_oversold=30,
        min_signal_strength=0.5,
        max_daily_trades=5,
        description="平衡风险收益，适中的止损止盈和仓位控制"
    ),

    "aggressive": RiskProfile(
        name="激进型",
        stop_loss=0.08,
        take_profit=0.25,
        max_position=0.80,
        rsi_overbought=80,
        rsi_oversold=20,
        min_signal_strength=0.3,
        max_daily_trades=10,
        description="追求高收益，宽松的止损止盈，允许高仓位"
    )
}


class RiskManager:
    """风险管理器"""

    def __init__(self, default_profile: str = "moderate"):
        """
        初始化风险管理器

        Args:
            default_profile: 默认风险配置名称
        """
        self._profiles = RISK_PROFILES.copy()
        self._current_profile = default_profile

    @property
    def current_profile(self) -> RiskProfile:
        """获取当前风险配置"""
        return self._profiles[self._current_profile]

    @property
    def current_level(self) -> str:
        """获取当前风险等级名称"""
        return self._current_profile

    def set_profile(self, profile_name: str) -> None:
        """
        设置风险配置

        Args:
            profile_name: 风险配置名称 (conservative/moderate/aggressive)

        Raises:
            ValueError: 如果配置名称不存在
        """
        if profile_name not in self._profiles:
            raise ValueError(
                f"未知的风险配置: {profile_name}，"
                f"可选配置: {list(self._profiles.keys())}"
            )
        self._current_profile = profile_name

    def get_stop_loss(self) -> float:
        """获取止损阈值"""
        return self.current_profile.stop_loss

    def get_take_profit(self) -> float:
        """获取止盈阈值"""
        return self.current_profile.take_profit

    def get_max_position(self) -> float:
        """获取最大仓位比例"""
        return self.current_profile.max_position

    def get_rsi_thresholds(self) -> tuple:
        """获取RSI阈值 (超买, 超卖)"""
        return (
            self.current_profile.rsi_overbought,
            self.current_profile.rsi_oversold
        )

    def get_min_signal_strength(self) -> float:
        """获取最小信号强度"""
        return self.current_profile.min_signal_strength

    def calc_position_size(self, capital: float, price: float) -> int:
        """
        计算仓位大小

        Args:
            capital: 可用资金
            price: 当前价格

        Returns:
            可买入的股票数量 (整百)
        """
        max_amount = capital * self.current_profile.max_position
        shares = int(max_amount / price)
        # 取整到100股（A股最小交易单位）
        return (shares // 100) * 100

    def calc_stop_loss_price(self, buy_price: float) -> float:
        """
        计算止损价格

        Args:
            buy_price: 买入价格

        Returns:
            止损价格
        """
        return buy_price * (1 - self.current_profile.stop_loss)

    def calc_take_profit_price(self, buy_price: float) -> float:
        """
        计算止盈价格

        Args:
            buy_price: 买入价格

        Returns:
            止盈价格
        """
        return buy_price * (1 + self.current_profile.take_profit)

    def should_trade(self, signal_strength: float) -> bool:
        """
        判断是否应该交易

        Args:
            signal_strength: 信号强度 (0-1)

        Returns:
            是否应该交易
        """
        return signal_strength >= self.current_profile.min_signal_strength

    def list_profiles(self) -> list:
        """列出所有可用的风险配置"""
        return [
            {
                "key": key,
                "name": profile.name,
                "description": profile.description
            }
            for key, profile in self._profiles.items()
        ]

    def get_profile_summary(self) -> dict:
        """获取当前配置摘要"""
        profile = self.current_profile
        return {
            "risk_level": self._current_profile,
            "name": profile.name,
            "stop_loss": f"{profile.stop_loss*100}%",
            "take_profit": f"{profile.take_profit*100}%",
            "max_position": f"{profile.max_position*100}%",
            "rsi_overbought": profile.rsi_overbought,
            "rsi_oversold": profile.rsi_oversold,
            "description": profile.description
        }


# 便捷函数
def get_risk_manager(profile: str = "moderate") -> RiskManager:
    """
    获取风险管理器实例

    Args:
        profile: 风险配置名称

    Returns:
        RiskManager 实例
    """
    return RiskManager(default_profile=profile)


# 测试代码
if __name__ == "__main__":
    # 测试风险管理器
    rm = RiskManager()

    print("=" * 50)
    print("风险管理器测试")
    print("=" * 50)

    # 列出所有配置
    print("\n可用的风险配置:")
    for p in rm.list_profiles():
        print(f"  - {p['key']}: {p['name']} - {p['description']}")

    # 测试不同配置
    for level in ["conservative", "moderate", "aggressive"]:
        rm.set_profile(level)
        print(f"\n{'='*50}")
        print(f"当前配置: {rm.current_profile.name}")
        print(f"止损阈值: {rm.get_stop_loss()*100}%")
        print(f"止盈阈值: {rm.get_take_profit()*100}%")
        print(f"最大仓位: {rm.get_max_position()*100}%")
        print(f"RSI阈值: 超买>{rm.get_rsi_thresholds()[0]}, 超卖<{rm.get_rsi_thresholds()[1]}")
        print(f"止损价(买入价10元): {rm.calc_stop_loss_price(10):.2f}")
        print(f"止盈价(买入价10元): {rm.calc_take_profit_price(10):.2f}")
        print(f"可买数量(资金10万,股价10元): {rm.calc_position_size(100000, 10)}股")
