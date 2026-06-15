# SDD: 智能交易决策系统

## 1. 概述

### 1.1 目标
创建一个智能交易决策系统，结合多维度分析（技术面、基本面、市场情绪、趋势判断），使用AI综合决策，提供精准的买入/卖出时机建议。

### 1.2 背景
当前系统问题：
- 策略只使用单一指标，容易产生假信号
- 止损机制没有正确触发
- 没有趋势过滤，下跌市场中也买入
- 缺少仓位管理和资金管理
- 技术面和基本面分析分离

### 1.3 设计理念
借鉴专业交易员的决策流程：
1. **先看大势** - 市场趋势判断（牛市/熊市/震荡）
2. **再选个股** - 基本面筛选（盈利能力、估值、成长性）
3. **择时入场** - 技术面确认（多指标共振）
4. **仓位管理** - 根据信号强度和风险调整仓位
5. **严格止损** - 动态止损保护利润

## 2. 架构设计

### 2.1 模块结构

```
skills/trading_advisor/
├── __init__.py
├── advisor.py          # 核心决策引擎
├── trend_detector.py   # 趋势检测器
├── entry_exit.py       # 入场出场时机
├── position_manager.py # 仓位管理
├── risk_controller.py  # 风险控制
└── decision_logger.py  # 决策日志
```

### 2.2 核心类

#### TradingAdvisor (交易顾问)

```python
class TradingAdvisor:
    """
    智能交易决策引擎
    综合多维度分析，给出买入/卖出/持有的决策建议
    """

    def __init__(self, risk_profile='moderate'):
        self.trend_detector = TrendDetector()
        self.entry_exit = EntryExitTiming()
        self.position_manager = PositionManager(risk_profile)
        self.risk_controller = RiskController(risk_profile)
        self.decision_logger = DecisionLogger()

    def analyze(self, stock_code: str, df: pd.DataFrame) -> TradeDecision:
        """
        综合分析，给出交易决策

        Args:
            stock_code: 股票代码
            df: OHLCV 数据

        Returns:
            TradeDecision: 包含 action, confidence, reasons, position_size, stop_loss, take_profit
        """
        # 1. 趋势判断
        trend = self.trend_detector.detect(df)

        # 2. 技术信号
        technical_signals = self._analyze_technical(df)

        # 3. 基本面评分
        fundamental_score = self._analyze_fundamental(stock_code)

        # 4. 综合决策
        decision = self._make_decision(trend, technical_signals, fundamental_score)

        # 5. 仓位计算
        decision.position_size = self.position_manager.calc_position(
            decision.confidence, trend, df['close'].iloc[-1]
        )

        # 6. 止损止盈
        decision.stop_loss = self.risk_controller.calc_stop_loss(
            df['close'].iloc[-1], trend
        )
        decision.take_profit = self.risk_controller.calc_take_profit(
            df['close'].iloc[-1], trend, decision.confidence
        )

        # 7. 记录决策
        self.decision_logger.log(decision)

        return decision
```

#### TrendDetector (趋势检测器)

```python
class TrendDetector:
    """
    趋势检测器
    判断市场处于牛市、熊市还是震荡市
    """

    def detect(self, df: pd.DataFrame) -> TrendInfo:
        """
        检测趋势

        Returns:
            TrendInfo: trend_type (BULL/BEAR/RANGING), strength, duration
        """
        # 多周期趋势判断
        short_trend = self._detect_period_trend(df, period=20)   # 短期
        mid_trend = self._detect_period_trend(df, period=60)     # 中期
        long_trend = self._detect_period_trend(df, period=120)   # 长期

        # 均线排列判断
        ma_arrangement = self._check_ma_arrangement(df)

        # MACD 趋势确认
        macd_trend = self._check_macd_trend(df)

        # 综合判断
        return self._combine_trends(short_trend, mid_trend, long_trend,
                                     ma_arrangement, macd_trend)

    def _detect_period_trend(self, df, period):
        """使用线性回归检测趋势"""
        prices = df['close'].tail(period).values
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)

        # 斜率标准化
        normalized_slope = slope / prices.mean() * 100

        if normalized_slope > 0.5:
            return TrendType.BULL
        elif normalized_slope < -0.5:
            return TrendType.BEAR
        else:
            return TrendType.RANGING

    def _check_ma_arrangement(self, df):
        """检查均线排列"""
        ma5 = df['close'].rolling(5).mean().iloc[-1]
        ma10 = df['close'].rolling(10).mean().iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]

        # 多头排列: MA5 > MA10 > MA20 > MA60
        if ma5 > ma10 > ma20 > ma60:
            return 'BULL'
        # 空头排列: MA5 < MA10 < MA20 < MA60
        elif ma5 < ma10 < ma20 < ma60:
            return 'BEAR'
        else:
            return 'RANGING'
```

#### EntryExitTiming (入场出场时机)

```python
class EntryExitTiming:
    """
    入场出场时机判断
    使用多指标共振确认信号
    """

    def check_entry(self, df: pd.DataFrame, trend: TrendInfo) -> EntrySignal:
        """
        检查入场时机

        入场条件（需满足至少3个）：
        1. MACD 金叉
        2. RSI 从超卖区回升
        3. KDJ 金叉
        4. 成交量放大
        5. 价格突破关键阻力位
        6. 均线多头排列
        """
        signals = []

        # 1. MACD 金叉
        if self._check_macd_golden_cross(df):
            signals.append('MACD金叉')

        # 2. RSI 超卖回升
        if self._check_rsi_bounce(df):
            signals.append('RSI超卖回升')

        # 3. KDJ 金叉
        if self._check_kdj_golden_cross(df):
            signals.append('KDJ金叉')

        # 4. 成交量放大
        if self._check_volume_breakout(df):
            signals.append('放量上涨')

        # 5. 突破阻力位
        if self._check_resistance_break(df):
            signals.append('突破阻力')

        # 6. 均线多头排列
        if trend.ma_arrangement == 'BULL':
            signals.append('均线多头')

        # 信号强度
        strength = len(signals) / 6

        return EntrySignal(
            can_enter=len(signals) >= 3,
            strength=strength,
            signals=signals
        )

    def check_exit(self, df: pd.DataFrame, buy_price: float,
                   trend: TrendInfo) -> ExitSignal:
        """
        检查出场时机

        出场条件（满足任一）：
        1. 止损触发
        2. 止盈触发
        3. MACD 死叉
        4. RSI 超买
        5. 趋势反转
        6. 跌破关键支撑
        """
        reasons = []
        current_price = df['close'].iloc[-1]
        profit_pct = (current_price - buy_price) / buy_price

        # 1. 固定止损
        if profit_pct <= -0.05:
            reasons.append(f'止损触发: {profit_pct:.1%}')

        # 2. 移动止盈
        max_price = df['close'].iloc[-20:].max()
        drawdown = (current_price - max_price) / max_price
        if profit_pct > 0.1 and drawdown < -0.05:
            reasons.append(f'移动止盈: 从高点回撤 {drawdown:.1%}')

        # 3. MACD 死叉
        if self._check_macd_death_cross(df):
            reasons.append('MACD死叉')

        # 4. RSI 超买
        rsi = self._calc_rsi(df)
        if rsi > 70:
            reasons.append(f'RSI超买: {rsi:.1f}')

        # 5. 趋势反转
        if trend.trend_type == 'BEAR' and trend.strength > 0.7:
            reasons.append('趋势转熊')

        # 6. 跌破支撑
        if self._check_support_break(df):
            reasons.append('跌破支撑')

        return ExitSignal(
            should_exit=len(reasons) > 0,
            reasons=reasons,
            urgency=max(1, len(reasons))  # 紧急度 1-5
        )
```

#### PositionManager (仓位管理)

```python
class PositionManager:
    """
    仓位管理器
    根据信号强度、趋势、风险控制仓位
    """

    def __init__(self, risk_profile='moderate'):
        self.risk_profile = risk_profile
        self.max_position = {
            'conservative': 0.3,
            'moderate': 0.5,
            'aggressive': 0.8
        }[risk_profile]

    def calc_position(self, confidence: float, trend: TrendInfo,
                      price: float, capital: float) -> int:
        """
        计算仓位大小

        Args:
            confidence: 信号置信度 (0-1)
            trend: 趋势信息
            price: 当前价格
            capital: 可用资金

        Returns:
            买入股数（100的整数倍）
        """
        # 基础仓位 = 可用资金 * 最大仓位比例
        base_capital = capital * self.max_position

        # 根据信号强度调整
        signal_factor = confidence

        # 根据趋势调整
        trend_factor = {
            'BULL': 1.0,      # 牛市满仓
            'RANGING': 0.6,   # 震荡市6成仓
            'BEAR': 0.3       # 熊市3成仓
        }[trend.trend_type]

        # 计算实际可用资金
        adjusted_capital = base_capital * signal_factor * trend_factor

        # 计算股数（100的整数倍）
        shares = int(adjusted_capital / price / 100) * 100

        return max(100, shares)  # 最少1手

    def should_add_position(self, current_profit: float,
                            trend: TrendInfo) -> bool:
        """
        是否加仓

        加仓条件：
        1. 当前盈利 > 5%
        2. 趋势为牛市
        3. 信号强度 > 0.7
        """
        return (current_profit > 0.05 and
                trend.trend_type == 'BULL' and
                trend.strength > 0.7)
```

#### RiskController (风险控制)

```python
class RiskController:
    """
    风险控制器
    动态止损止盈
    """

    def __init__(self, risk_profile='moderate'):
        self.risk_profile = risk_profile

    def calc_stop_loss(self, buy_price: float, trend: TrendInfo) -> float:
        """
        计算止损价

        动态止损策略：
        1. 牛市：宽松止损 (-8%)
        2. 震荡市：标准止损 (-5%)
        3. 熊市：严格止损 (-3%)
        """
        stop_loss_pct = {
            'BULL': 0.08,
            'RANGING': 0.05,
            'BEAR': 0.03
        }[trend.trend_type]

        return buy_price * (1 - stop_loss_pct)

    def calc_take_profit(self, buy_price: float, trend: TrendInfo,
                         confidence: float) -> float:
        """
        计算止盈价

        动态止盈策略：
        - 基础止盈 = 买入价 * (1 + 基础比例)
        - 趋势加成 = 牛市 +10%, 震荡 +5%, 熊市 +0%
        - 信心加成 = (confidence - 0.5) * 20%
        """
        base_pct = 0.15  # 基础15%
        trend_bonus = {
            'BULL': 0.10,
            'RANGING': 0.05,
            'BEAR': 0.00
        }[trend.trend_type]
        confidence_bonus = (confidence - 0.5) * 0.2

        total_pct = base_pct + trend_bonus + confidence_bonus
        return buy_price * (1 + total_pct)

    def check_daily_loss(self, daily_pnl: float) -> bool:
        """检查日内亏损限制"""
        max_daily_loss = {
            'conservative': 0.02,
            'moderate': 0.03,
            'aggressive': 0.05
        }[self.risk_profile]

        return daily_pnl < -max_daily_loss
```

## 3. 数据结构

### 3.1 TradeDecision

```python
@dataclass
class TradeDecision:
    """交易决策"""
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 置信度 0-1
    reasons: List[str]  # 决策原因
    position_size: int  # 仓位大小（股数）
    stop_loss: float  # 止损价
    take_profit: float  # 止盈价
    trend: TrendInfo  # 趋势信息
    technical_signals: Dict  # 技术信号
    fundamental_score: float  # 基本面评分
    timestamp: str  # 决策时间
```

### 3.2 TrendInfo

```python
@dataclass
class TrendInfo:
    """趋势信息"""
    trend_type: str  # 'BULL', 'BEAR', 'RANGING'
    strength: float  # 趋势强度 0-1
    duration: int  # 持续天数
    ma_arrangement: str  # 均线排列
    macd_trend: str  # MACD趋势
    support_level: float  # 支撑位
    resistance_level: float  # 阻力位
```

### 3.3 EntrySignal / ExitSignal

```python
@dataclass
class EntrySignal:
    """入场信号"""
    can_enter: bool
    strength: float
    signals: List[str]

@dataclass
class ExitSignal:
    """出场信号"""
    should_exit: bool
    reasons: List[str]
    urgency: int  # 1-5
```

## 4. 决策流程

```
┌─────────────────────────────────────────────────────────────┐
│                    智能交易决策流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入: 股票代码 + OHLCV数据                                  │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────┐                                        │
│  │  1. 趋势判断    │  ← MA排列 + MACD + 线性回归             │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  2. 技术分析    │  ← MACD/RSI/KDJ/BOLL/成交量            │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  3. 基本面评估  │  ← PE/PB/ROE/营收增长                  │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  4. 综合决策    │  ← 加权评分 + 规则判断                  │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  5. 仓位计算    │  ← 信号强度 + 趋势 + 风险偏好           │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  6. 止损止盈    │  ← 动态调整                            │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  输出: TradeDecision                                        │
│  {action, confidence, position_size, stop_loss, take_profit}│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 5. 测试计划

### 5.1 单元测试

| 测试项 | 描述 |
|--------|------|
| test_trend_detection | 测试趋势检测 |
| test_entry_signal | 测试入场信号 |
| test_exit_signal | 测试出场信号 |
| test_position_calc | 测试仓位计算 |
| test_stop_loss | 测试止损计算 |
| test_take_profit | 测试止盈计算 |

### 5.2 集成测试

| 测试项 | 描述 |
|--------|------|
| test_full_decision_flow | 测试完整决策流程 |
| test_backtest_with_advisor | 测试带顾问的回测 |

## 6. 依赖

- pandas (已有)
- numpy (已有)
- core/indicators (已有)
- core/signals (已有)
- skills/stock_fundamental (已有)

## 7. 预期效果

### 7.1 改进点

1. **趋势过滤**: 熊市不买入，避免下跌趋势中的亏损
2. **多指标确认**: 至少3个信号共振才入场，减少假信号
3. **动态止损**: 根据趋势调整止损幅度，牛市宽止损，熊市严止损
4. **仓位管理**: 根据信号强度和趋势调整仓位，控制风险
5. **移动止盈**: 保护利润，让利润奔跑

### 7.2 预期收益提升

- 胜率: 30-40% → 50-60%
- 盈亏比: 1:1 → 2:1
- 最大回撤: -15% → -8%
