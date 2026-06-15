"""
趋势检测器
判断市场处于牛市、熊市还是震荡市
"""

import numpy as np
import pandas as pd
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TrendType(Enum):
    """趋势类型"""
    BULL = 'BULL'       # 牛市
    BEAR = 'BEAR'       # 熊市
    RANGING = 'RANGING' # 震荡市


@dataclass
class TrendInfo:
    """趋势信息"""
    trend_type: str          # 'BULL', 'BEAR', 'RANGING'
    strength: float          # 趋势强度 0-1
    duration: int            # 持续天数
    ma_arrangement: str      # 均线排列: 'BULL', 'BEAR', 'MIXED'
    macd_trend: str          # MACD趋势: 'UP', 'DOWN', 'FLAT'
    support_level: float     # 支撑位
    resistance_level: float  # 阻力位
    slope: float             # 趋势斜率


class TrendDetector:
    """
    趋势检测器
    使用多维度分析判断市场趋势
    """

    def __init__(self):
        # 趋势判断权重
        self.weights = {
            'ma_arrangement': 0.25,   # 均线排列
            'macd_trend': 0.20,       # MACD趋势
            'price_trend': 0.25,      # 价格趋势
            'volume_trend': 0.15,     # 成交量趋势
            'momentum': 0.15          # 动量指标
        }

    def detect(self, df: pd.DataFrame) -> TrendInfo:
        """
        检测趋势

        Args:
            df: OHLCV 数据

        Returns:
            TrendInfo: 趋势信息
        """
        if len(df) < 60:
            return self._default_trend()

        # 1. 均线排列分析
        ma_arrangement = self._check_ma_arrangement(df)

        # 2. MACD 趋势分析
        macd_trend = self._check_macd_trend(df)

        # 3. 价格趋势分析 (线性回归)
        price_trend, slope = self._check_price_trend(df)

        # 4. 成交量趋势分析
        volume_trend = self._check_volume_trend(df)

        # 5. 动量分析
        momentum = self._check_momentum(df)

        # 综合评分
        scores = {
            'BULL': 0,
            'BEAR': 0,
            'RANGING': 0
        }

        # 均线排列评分
        if ma_arrangement == 'BULL':
            scores['BULL'] += self.weights['ma_arrangement']
        elif ma_arrangement == 'BEAR':
            scores['BEAR'] += self.weights['ma_arrangement']
        else:
            scores['RANGING'] += self.weights['ma_arrangement']

        # MACD 趋势评分
        if macd_trend == 'UP':
            scores['BULL'] += self.weights['macd_trend']
        elif macd_trend == 'DOWN':
            scores['BEAR'] += self.weights['macd_trend']
        else:
            scores['RANGING'] += self.weights['macd_trend']

        # 价格趋势评分
        if price_trend == 'BULL':
            scores['BULL'] += self.weights['price_trend']
        elif price_trend == 'BEAR':
            scores['BEAR'] += self.weights['price_trend']
        else:
            scores['RANGING'] += self.weights['price_trend']

        # 成交量趋势评分
        if volume_trend == 'BULL':
            scores['BULL'] += self.weights['volume_trend']
        elif volume_trend == 'BEAR':
            scores['BEAR'] += self.weights['volume_trend']
        else:
            scores['RANGING'] += self.weights['volume_trend']

        # 动量评分
        if momentum == 'BULL':
            scores['BULL'] += self.weights['momentum']
        elif momentum == 'BEAR':
            scores['BEAR'] += self.weights['momentum']
        else:
            scores['RANGING'] += self.weights['momentum']

        # 确定趋势类型
        trend_type = max(scores, key=scores.get)
        strength = scores[trend_type]

        # 计算支撑阻力位
        support_level = self._calc_support(df)
        resistance_level = self._calc_resistance(df)

        # 计算持续天数
        duration = self._calc_trend_duration(df, trend_type)

        return TrendInfo(
            trend_type=trend_type,
            strength=strength,
            duration=duration,
            ma_arrangement=ma_arrangement,
            macd_trend=macd_trend,
            support_level=support_level,
            resistance_level=resistance_level,
            slope=slope
        )

    def _check_ma_arrangement(self, df: pd.DataFrame) -> str:
        """
        检查均线排列

        多头排列: MA5 > MA10 > MA20 > MA60
        空头排列: MA5 < MA10 < MA20 < MA60
        """
        ma5 = df['close'].rolling(5).mean().iloc[-1]
        ma10 = df['close'].rolling(10).mean().iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]

        # 多头排列
        if ma5 > ma10 > ma20 > ma60:
            return 'BULL'
        # 空头排列
        elif ma5 < ma10 < ma20 < ma60:
            return 'BEAR'
        # 部分多头
        elif ma5 > ma10 > ma20:
            return 'BULL'
        # 部分空头
        elif ma5 < ma10 < ma20:
            return 'BEAR'
        else:
            return 'MIXED'

    def _check_macd_trend(self, df: pd.DataFrame) -> str:
        """
        检查 MACD 趋势

        - DIF > DEA 且 MACD柱增长: 上升趋势
        - DIF < DEA 且 MACD柱减少: 下降趋势
        """
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_hist = 2 * (dif - dea)

        # 最近的 DIF 和 DEA
        dif_last = dif.iloc[-1]
        dea_last = dea.iloc[-1]
        hist_last = macd_hist.iloc[-1]
        hist_prev = macd_hist.iloc[-2]

        # DIF > DEA 且 MACD柱增长
        if dif_last > dea_last and hist_last > hist_prev:
            return 'UP'
        # DIF < DEA 且 MACD柱减少
        elif dif_last < dea_last and hist_last < hist_prev:
            return 'DOWN'
        else:
            return 'FLAT'

    def _check_price_trend(self, df: pd.DataFrame, period: int = 60) -> tuple:
        """
        使用线性回归检测价格趋势

        Returns:
            (trend_type, slope)
        """
        prices = df['close'].tail(period).values
        x = np.arange(len(prices))

        # 线性回归
        slope, intercept = np.polyfit(x, prices, 1)

        # 标准化斜率
        mean_price = prices.mean()
        normalized_slope = slope / mean_price * 100

        if normalized_slope > 0.3:
            return 'BULL', slope
        elif normalized_slope < -0.3:
            return 'BEAR', slope
        else:
            return 'RANGING', slope

    def _check_volume_trend(self, df: pd.DataFrame) -> str:
        """
        检查成交量趋势

        - 量增价涨: 牛市
        - 量增价跌: 熊市
        - 量缩: 震荡
        """
        # 计算成交量均线
        vol_ma5 = df['volume'].rolling(5).mean()
        vol_ma20 = df['volume'].rolling(20).mean()

        # 最近5天的成交量
        recent_vol = df['volume'].tail(5)
        recent_close = df['close'].tail(5)

        # 量能变化
        vol_change = recent_vol.mean() / vol_ma20.iloc[-1] - 1

        # 价格变化
        price_change = (recent_close.iloc[-1] / recent_close.iloc[0] - 1)

        if vol_change > 0.2 and price_change > 0.02:
            return 'BULL'
        elif vol_change > 0.2 and price_change < -0.02:
            return 'BEAR'
        else:
            return 'RANGING'

    def _check_momentum(self, df: pd.DataFrame) -> str:
        """
        检查动量

        使用 RSI 和 ROC (Rate of Change)
        """
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_last = rsi.iloc[-1]

        # ROC (10日变化率)
        roc = (df['close'].iloc[-1] / df['close'].iloc[-10] - 1) * 100

        if rsi_last > 50 and roc > 2:
            return 'BULL'
        elif rsi_last < 50 and roc < -2:
            return 'BEAR'
        else:
            return 'RANGING'

    def _calc_support(self, df: pd.DataFrame) -> float:
        """计算支撑位 (最近20日最低价)"""
        return df['low'].tail(20).min()

    def _calc_resistance(self, df: pd.DataFrame) -> float:
        """计算阻力位 (最近20日最高价)"""
        return df['high'].tail(20).max()

    def _calc_trend_duration(self, df: pd.DataFrame, trend_type: str) -> int:
        """计算趋势持续天数"""
        # 简单实现：从最近的 MA20 方向变化开始计算
        ma20 = df['close'].rolling(20).mean()
        duration = 0

        for i in range(len(ma20) - 1, 0, -1):
            if trend_type == 'BULL' and ma20.iloc[i] > ma20.iloc[i-1]:
                duration += 1
            elif trend_type == 'BEAR' and ma20.iloc[i] < ma20.iloc[i-1]:
                duration += 1
            else:
                break

        return duration

    def _default_trend(self) -> TrendInfo:
        """默认趋势（数据不足时）"""
        return TrendInfo(
            trend_type='RANGING',
            strength=0.5,
            duration=0,
            ma_arrangement='MIXED',
            macd_trend='FLAT',
            support_level=0,
            resistance_level=0,
            slope=0
        )
