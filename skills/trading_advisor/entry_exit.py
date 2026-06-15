"""
入场出场时机判断
使用多指标共振确认信号
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class EntrySignal:
    """入场信号"""
    can_enter: bool          # 是否可以入场
    strength: float          # 信号强度 0-1
    signals: List[str]       # 触发的信号列表
    confidence: float = 0.0  # 置信度


@dataclass
class ExitSignal:
    """出场信号"""
    should_exit: bool        # 是否应该出场
    reasons: List[str]       # 出场原因
    urgency: int             # 紧急度 1-5
    profit_loss: float = 0.0 # 当前盈亏


class EntryExitTiming:
    """
    入场出场时机判断
    使用多指标共振确认信号
    """

    def __init__(self):
        # 入场信号权重
        self.entry_weights = {
            'macd_golden_cross': 0.20,
            'rsi_bounce': 0.15,
            'kdj_golden_cross': 0.15,
            'volume_breakout': 0.15,
            'resistance_break': 0.15,
            'ma_support': 0.20
        }

        # 出场信号权重
        self.exit_weights = {
            'stop_loss': 0.30,
            'take_profit': 0.20,
            'macd_death_cross': 0.15,
            'rsi_overbought': 0.10,
            'trend_reversal': 0.15,
            'support_break': 0.10
        }

    def check_entry(self, df: pd.DataFrame, trend_type: str = 'RANGING') -> EntrySignal:
        """
        检查入场时机

        入场条件（需满足至少3个）：
        1. MACD 金叉
        2. RSI 从超卖区回升
        3. KDJ 金叉
        4. 成交量放大
        5. 价格突破关键阻力位
        6. 均线支撑有效

        Args:
            df: OHLCV 数据
            trend_type: 趋势类型

        Returns:
            EntrySignal
        """
        if len(df) < 60:
            return EntrySignal(False, 0, [], 0)

        signals = []
        signal_strengths = {}

        # 1. MACD 金叉
        macd_signal = self._check_macd_golden_cross(df)
        if macd_signal['triggered']:
            signals.append('MACD金叉')
            signal_strengths['macd_golden_cross'] = macd_signal['strength']

        # 2. RSI 超卖回升
        rsi_signal = self._check_rsi_bounce(df)
        if rsi_signal['triggered']:
            signals.append('RSI超卖回升')
            signal_strengths['rsi_bounce'] = rsi_signal['strength']

        # 3. KDJ 金叉
        kdj_signal = self._check_kdj_golden_cross(df)
        if kdj_signal['triggered']:
            signals.append('KDJ金叉')
            signal_strengths['kdj_golden_cross'] = kdj_signal['strength']

        # 4. 成交量放大
        volume_signal = self._check_volume_breakout(df)
        if volume_signal['triggered']:
            signals.append('放量上涨')
            signal_strengths['volume_breakout'] = volume_signal['strength']

        # 5. 突破阻力位
        resistance_signal = self._check_resistance_break(df)
        if resistance_signal['triggered']:
            signals.append('突破阻力')
            signal_strengths['resistance_break'] = resistance_signal['strength']

        # 6. 均线支撑
        ma_signal = self._check_ma_support(df)
        if ma_signal['triggered']:
            signals.append('均线支撑')
            signal_strengths['ma_support'] = ma_signal['strength']

        # 计算综合强度
        total_strength = 0
        for signal_name, strength in signal_strengths.items():
            weight = self.entry_weights.get(signal_name, 0.1)
            total_strength += strength * weight

        # 信号数量加成
        signal_count_bonus = min(1.0, len(signals) / 4)
        total_strength = total_strength * 0.7 + signal_count_bonus * 0.3

        # 趋势加成
        trend_bonus = {
            'BULL': 0.15,
            'RANGING': 0.0,
            'BEAR': -0.10
        }.get(trend_type, 0)

        total_strength = min(1.0, total_strength + trend_bonus)

        # 决定是否入场（至少2个信号，且强度>=0.3）
        can_enter = len(signals) >= 2 and total_strength >= 0.3

        return EntrySignal(
            can_enter=can_enter,
            strength=total_strength,
            signals=signals,
            confidence=total_strength
        )

    def check_exit(self, df: pd.DataFrame, buy_price: float,
                   trend_type: str = 'RANGING') -> ExitSignal:
        """
        检查出场时机

        出场条件（满足任一）：
        1. 止损触发
        2. 止盈触发
        3. MACD 死叉
        4. RSI 超买
        5. 趋势反转
        6. 跌破关键支撑

        Args:
            df: OHLCV 数据
            buy_price: 买入价格
            trend_type: 趋势类型

        Returns:
            ExitSignal
        """
        if len(df) < 20:
            return ExitSignal(False, [], 0, 0)

        reasons = []
        current_price = df['close'].iloc[-1]
        profit_loss = (current_price - buy_price) / buy_price

        # 1. 固定止损
        stop_loss_pct = {
            'BULL': -0.08,
            'RANGING': -0.05,
            'BEAR': -0.03
        }.get(trend_type, -0.05)

        if profit_loss <= stop_loss_pct:
            reasons.append(f'止损触发: {profit_loss:.1%} (阈值: {stop_loss_pct:.1%})')

        # 2. 移动止盈
        if profit_loss > 0.05:  # 盈利超过5%才启动移动止盈
            max_price = df['close'].iloc[-20:].max()
            drawdown = (current_price - max_price) / max_price
            if drawdown < -0.05:  # 从高点回撤超过5%
                reasons.append(f'移动止盈: 从高点回撤 {drawdown:.1%}')

        # 3. MACD 死叉
        if self._check_macd_death_cross(df):
            reasons.append('MACD死叉')

        # 4. RSI 超买
        rsi = self._calc_rsi(df)
        if rsi > 70:
            reasons.append(f'RSI超买: {rsi:.1f}')

        # 5. 趋势反转
        if trend_type == 'BEAR':
            # 检查趋势是否加速恶化
            ma20 = df['close'].rolling(20).mean()
            if ma20.iloc[-1] < ma20.iloc[-5] * 0.97:  # MA20 下降超过3%
                reasons.append('趋势转熊加速')

        # 6. 跌破支撑
        if self._check_support_break(df):
            reasons.append('跌破支撑')

        # 计算紧急度
        urgency = min(5, len(reasons))

        return ExitSignal(
            should_exit=len(reasons) > 0,
            reasons=reasons,
            urgency=urgency,
            profit_loss=profit_loss
        )

    # ==================== 内部方法 ====================

    def _check_macd_golden_cross(self, df: pd.DataFrame) -> Dict:
        """检查 MACD 金叉"""
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()

        # 当前 DIF > DEA 且前一日 DIF <= DEA
        if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
            # 计算金叉强度（DIF - DEA 的差值）
            strength = min(1.0, (dif.iloc[-1] - dea.iloc[-1]) / dea.iloc[-1] * 100)
            return {'triggered': True, 'strength': strength}

        return {'triggered': False, 'strength': 0}

    def _check_rsi_bounce(self, df: pd.DataFrame) -> Dict:
        """检查 RSI 超卖回升"""
        rsi = self._calc_rsi(df)

        # 计算前一日的 RSI
        if len(df) > 15:
            rsi_prev = self._calc_rsi(df.iloc[:-1])
        else:
            rsi_prev = rsi

        # RSI 从低于30回升到30以上
        if rsi > 30 and rsi_prev <= 30:
            strength = min(1.0, (30 - rsi_prev) / 30)
            return {'triggered': True, 'strength': strength}

        # RSI 从低于40回升且趋势向上
        if rsi > 40 and rsi_prev < 35:
            strength = min(1.0, (rsi - 30) / 40)
            return {'triggered': True, 'strength': strength}

        return {'triggered': False, 'strength': 0}

    def _check_kdj_golden_cross(self, df: pd.DataFrame) -> Dict:
        """检查 KDJ 金叉"""
        # 计算 KDJ
        low_n = df['low'].rolling(9).min()
        high_n = df['high'].rolling(9).max()
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100

        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d

        # K 上穿 D
        if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2]:
            # 在超卖区金叉更有意义
            if k.iloc[-1] < 50:
                strength = min(1.0, (50 - k.iloc[-1]) / 50)
                return {'triggered': True, 'strength': strength}
            else:
                return {'triggered': True, 'strength': 0.5}

        return {'triggered': False, 'strength': 0}

    def _check_volume_breakout(self, df: pd.DataFrame) -> Dict:
        """检查成交量放大"""
        vol_ma5 = df['volume'].rolling(5).mean()
        vol_ma20 = df['volume'].rolling(20).mean()

        # 最近成交量是20日均量的1.5倍以上
        vol_ratio = df['volume'].iloc[-1] / vol_ma20.iloc[-1]

        # 且价格上涨
        price_change = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1)

        if vol_ratio > 1.5 and price_change > 0.01:
            strength = min(1.0, (vol_ratio - 1) / 2)
            return {'triggered': True, 'strength': strength}

        return {'triggered': False, 'strength': 0}

    def _check_resistance_break(self, df: pd.DataFrame) -> Dict:
        """检查突破阻力位"""
        # 计算阻力位（最近20日最高价）
        resistance = df['high'].tail(20).max()

        # 当前价格突破阻力位
        current_price = df['close'].iloc[-1]
        if current_price > resistance * 1.01:  # 突破1%
            strength = min(1.0, (current_price - resistance) / resistance * 10)
            return {'triggered': True, 'strength': strength}

        return {'triggered': False, 'strength': 0}

    def _check_ma_support(self, df: pd.DataFrame) -> Dict:
        """检查均线支撑"""
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]
        current_price = df['close'].iloc[-1]

        # 价格在均线附近且均线向上
        ma20_slope = (df['close'].rolling(20).mean().iloc[-1] -
                      df['close'].rolling(20).mean().iloc[-5])

        # 价格回踩MA20不破
        if (abs(current_price - ma20) / ma20 < 0.02 and  # 价格接近MA20
            ma20_slope > 0 and  # MA20向上
            current_price > ma60):  # 价格在MA60之上
            return {'triggered': True, 'strength': 0.7}

        return {'triggered': False, 'strength': 0}

    def _check_macd_death_cross(self, df: pd.DataFrame) -> bool:
        """检查 MACD 死叉"""
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()

        # DIF 下穿 DEA
        return dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]

    def _check_support_break(self, df: pd.DataFrame) -> bool:
        """检查跌破支撑"""
        # 支撑位 = 最近20日最低价
        support = df['low'].tail(20).min()
        current_price = df['close'].iloc[-1]

        return current_price < support * 0.99  # 跌破1%

    def _calc_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """计算 RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
