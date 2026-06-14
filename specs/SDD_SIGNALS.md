# 软件设计规格说明 (SDD)
# 信号系统模块

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 信号系统模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述信号系统模块的设计规格，为开发人员提供明确的实现指导，确保代码质量和功能一致性。

### 1.2 范围

本模块负责生成股票买卖信号，包括：
- 买入信号检测
- 卖出信号检测
- 信号强度计算
- 信号聚合和决策

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| 金叉 | 短期均线上穿长期均线 |
| 死叉 | 短期均线下穿长期均线 |
| 超买 | RSI > 70，价格可能回调 |
| 超卖 | RSI < 30，价格可能反弹 |
| 信号强度 | 多个指标综合判断的买入/卖出信心 (0-1) |

### 1.4 参考文档

- `SDD_INDICATORS.md` - 技术指标模块规格
- `DEVELOPMENT_SPEC.md` - 开发规格书

---

## 2. 系统概述

### 2.1 模块位置

```
core/
└── signals/
    ├── __init__.py         # 模块初始化
    ├── buy_signals.py      # 买入信号
    ├── sell_signals.py     # 卖出信号
    └── signal_strength.py  # 信号强度计算
```

### 2.2 依赖关系

```
┌─────────────────────────────────────────┐
│           signals 信号模块              │
├─────────────────────────────────────────┤
│ 依赖:                                   │
│   - core.indicators (技术指标)          │
│   - core.risk (风险配置)                │
│   - pandas (数据处理)                   │
│                                         │
│ 被依赖:                                 │
│   - skills.stock-advisor (个股分析)     │
└─────────────────────────────────────────┘
```

---

## 3. 设计决策

### 3.1 设计原则

1. **可配置性**: 信号阈值可通过风险配置调整
2. **可扩展性**: 易于添加新的信号规则
3. **独立性**: 每个信号规则独立，互不影响
4. **量化输出**: 所有信号输出数值化的强度值

### 3.2 信号规则设计

每个信号规则是一个独立的函数，接收指标数据，返回信号值：
- 返回 1: 买入信号
- 返回 -1: 卖出信号
- 返回 0: 无信号

### 3.3 信号强度计算

```
总信号强度 = Σ(各信号权重 × 信号值) / Σ(权重)
```

---

## 4. 模块详细设计

### 4.1 买入信号模块 (buy_signals.py)

#### 4.1.1 信号规则清单

| 规则ID | 规则名称 | 权重 | 说明 |
|--------|---------|------|------|
| B1 | MA金叉 | 0.20 | MA5 上穿 MA20 |
| B2 | MACD金叉 | 0.25 | DIF 上穿 DEA |
| B3 | RSI超卖反弹 | 0.15 | RSI < 30 后回升 |
| B4 | KDJ金叉 | 0.15 | K 上穿 D |
| B5 | BOLL下轨支撑 | 0.10 | 价格触及下轨后反弹 |
| B6 | 放量突破 | 0.15 | 成交量 > 5日均量 * 1.5 |

#### 4.1.2 信号规则函数

```python
def check_ma_cross(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """
    检测 MA 金叉信号

    参数:
        fast_ma: 短期均线
        slow_ma: 长期均线

    返回:
        pd.Series: 信号值 (1: 金叉, 0: 无信号)

    算法:
        金叉: fast_ma > slow_ma 且 前一日 fast_ma <= slow_ma
    """
    pass


def check_macd_cross(dif: pd.Series, dea: pd.Series) -> pd.Series:
    """
    检测 MACD 金叉信号

    参数:
        dif: DIF 线
        dea: DEA 线

    返回:
        pd.Series: 信号值 (1: 金叉, 0: 无信号)

    算法:
        金叉: dif > dea 且 前一日 dif <= dea
    """
    pass


def check_rsi_oversold(rsi: pd.Series, threshold: int = 30) -> pd.Series:
    """
    检测 RSI 超卖反弹信号

    参数:
        rsi: RSI 值序列
        threshold: 超卖阈值，默认 30

    返回:
        pd.Series: 信号值 (1: 超卖反弹, 0: 无信号)

    算法:
        超卖反弹: rsi > threshold 且 前一日 rsi <= threshold
    """
    pass


def check_kdj_cross(k: pd.Series, d: pd.Series) -> pd.Series:
    """
    检测 KDJ 金叉信号

    参数:
        k: K 值
        d: D 值

    返回:
        pd.Series: 信号值 (1: 金叉, 0: 无信号)

    算法:
        金叉: k > d 且 前一日 k <= d
    """
    pass


def check_boll_support(
    close: pd.Series,
    lower: pd.Series,
    prev_close: pd.Series = None
) -> pd.Series:
    """
    检测 BOLL 下轨支撑信号

    参数:
        close: 收盘价
        lower: BOLL 下轨

    返回:
        pd.Series: 信号值 (1: 支撑反弹, 0: 无信号)

    算法:
        支撑反弹: close > lower 且 前一日 close <= lower
    """
    pass


def check_volume_breakout(
    volume: pd.Series,
    vol_ma: pd.Series,
    ratio: float = 1.5
) -> pd.Series:
    """
    检测放量突破信号

    参数:
        volume: 成交量
        vol_ma: 成交量均线
        ratio: 放量倍数，默认 1.5

    返回:
        pd.Series: 信号值 (1: 放量, 0: 无信号)

    算法:
        放量: volume > vol_ma * ratio
    """
    pass
```

#### 4.1.3 买入信号聚合

```python
def get_buy_signals(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    indicators: pd.DataFrame,
    risk_profile: str = "moderate"
) -> pd.DataFrame:
    """
    获取所有买入信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        indicators: 指标数据 (来自 IndicatorCalculator)
        risk_profile: 风险配置

    返回:
        pd.DataFrame: 包含所有买入信号的 DataFrame
            - signal_xxx: 各个信号
            - signal_count: 信号数量
            - signal_strength: 信号强度
    """
    pass
```

---

### 4.2 卖出信号模块 (sell_signals.py)

#### 4.2.1 信号规则清单

| 规则ID | 规则名称 | 权重 | 说明 |
|--------|---------|------|------|
| S1 | MA死叉 | 0.20 | MA5 下穿 MA20 |
| S2 | MACD死叉 | 0.25 | DIF 下穿 DEA |
| S3 | RSI超买 | 0.15 | RSI > 70 |
| S4 | KDJ死叉 | 0.15 | K 下穿 D |
| S5 | BOLL上轨压力 | 0.10 | 价格触及上轨后回落 |
| S6 | 止损触发 | 0.15 | 亏损超过止损阈值 |

#### 4.2.2 信号规则函数

```python
def check_ma_death_cross(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """
    检测 MA 死叉信号

    参数:
        fast_ma: 短期均线
        slow_ma: 长期均线

    返回:
        pd.Series: 信号值 (1: 死叉, 0: 无信号)

    算法:
        死叉: fast_ma < slow_ma 且 前一日 fast_ma >= slow_ma
    """
    pass


def check_macd_death_cross(dif: pd.Series, dea: pd.Series) -> pd.Series:
    """
    检测 MACD 死叉信号

    参数:
        dif: DIF 线
        dea: DEA 线

    返回:
        pd.Series: 信号值 (1: 死叉, 0: 无信号)
    """
    pass


def check_rsi_overbought(rsi: pd.Series, threshold: int = 70) -> pd.Series:
    """
    检测 RSI 超买信号

    参数:
        rsi: RSI 值序列
        threshold: 超买阈值，默认 70

    返回:
        pd.Series: 信号值 (1: 超买, 0: 无信号)

    算法:
        超买: rsi > threshold
    """
    pass


def check_kdj_death_cross(k: pd.Series, d: pd.Series) -> pd.Series:
    """
    检测 KDJ 死叉信号

    参数:
        k: K 值
        d: D 值

    返回:
        pd.Series: 信号值 (1: 死叉, 0: 无信号)
    """
    pass


def check_boll_pressure(
    close: pd.Series,
    upper: pd.Series
) -> pd.Series:
    """
    检测 BOLL 上轨压力信号

    参数:
        close: 收盘价
        upper: BOLL 上轨

    返回:
        pd.Series: 信号值 (1: 压力回落, 0: 无信号)

    算法:
        压力回落: close < upper 且 前一日 close >= upper
    """
    pass


def check_stop_loss(
    current_price: float,
    buy_price: float,
    stop_loss_pct: float = 0.05
) -> bool:
    """
    检测止损信号

    参数:
        current_price: 当前价格
        buy_price: 买入价格
        stop_loss_pct: 止损百分比，默认 5%

    返回:
        bool: 是否触发止损

    算法:
        止损: (buy_price - current_price) / buy_price > stop_loss_pct
    """
    pass
```

#### 4.2.3 卖出信号聚合

```python
def get_sell_signals(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    indicators: pd.DataFrame,
    risk_profile: str = "moderate"
) -> pd.DataFrame:
    """
    获取所有卖出信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        indicators: 指标数据
        risk_profile: 风险配置

    返回:
        pd.DataFrame: 包含所有卖出信号的 DataFrame
    """
    pass
```

---

### 4.3 信号强度模块 (signal_strength.py)

#### 4.3.1 信号强度计算

```python
def calc_signal_strength(
    signals: pd.DataFrame,
    weights: dict
) -> pd.Series:
    """
    计算信号强度

    参数:
        signals: 信号 DataFrame (每列是一个信号)
        weights: 权重字典 {信号名: 权重}

    返回:
        pd.Series: 信号强度 (0-1)

    算法:
        强度 = Σ(信号值 × 权重) / Σ(权重)
    """
    pass
```

#### 4.3.2 交易方向判断

```python
def get_trade_direction(
    buy_strength: pd.Series,
    sell_strength: pd.Series,
    min_strength: float = 0.5
) -> pd.Series:
    """
    判断交易方向

    参数:
        buy_strength: 买入信号强度
        sell_strength: 卖出信号强度
        min_strength: 最小信号强度阈值

    返回:
        pd.Series: 交易方向
            - 1: 买入
            - -1: 卖出
            - 0: 观望

    算法:
        如果 buy_strength >= min_strength 且 buy_strength > sell_strength: 买入
        如果 sell_strength >= min_strength 且 sell_strength > buy_strength: 卖出
        否则: 观望
    """
    pass
```

#### 4.3.3 综合信号生成

```python
def generate_signal(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    risk_profile: str = "moderate"
) -> pd.DataFrame:
    """
    生成综合交易信号

    参数:
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        risk_profile: 风险配置

    返回:
        pd.DataFrame: 包含以下列
            - buy_strength: 买入信号强度
            - sell_strength: 卖出信号强度
            - direction: 交易方向 (1/-1/0)
            - confidence: 置信度
    """
    pass
```

---

## 5. 接口设计

### 5.1 统一接口

```python
class SignalGenerator:
    """信号生成器"""

    def __init__(self, risk_profile: str = "moderate"):
        """
        初始化信号生成器

        参数:
            risk_profile: 风险配置名称
        """
        pass

    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号

        参数:
            data: 包含 OHLCV 的 DataFrame

        返回:
            包含信号的 DataFrame
        """
        pass

    def get_latest_signal(self, data: pd.DataFrame) -> dict:
        """
        获取最新信号

        参数:
            data: 包含 OHLCV 的 DataFrame

        返回:
            最新信号信息
        """
        pass
```

---

## 6. 错误处理

### 6.1 异常类型

```python
class SignalError(Exception):
    """信号计算异常基类"""
    pass

class InsufficientIndicatorError(SignalError):
    """指标数据不足异常"""
    pass

class InvalidWeightError(SignalError):
    """权重配置错误"""
    pass
```

### 6.2 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| 指标数据不足 | 抛出 InsufficientIndicatorError |
| 权重配置错误 | 抛出 InvalidWeightError |
| 计算异常 | 返回无信号 (0) 并记录警告 |

---

## 7. 测试设计

### 7.1 单元测试用例

```python
class TestBuySignals:
    """买入信号测试"""

    def test_ma_golden_cross(self):
        """测试 MA 金叉信号"""
        pass

    def test_macd_golden_cross(self):
        """测试 MACD 金叉信号"""
        pass

    def test_rsi_oversold(self):
        """测试 RSI 超卖反弹"""
        pass

    def test_kdj_golden_cross(self):
        """测试 KDJ 金叉信号"""
        pass

    def test_boll_support(self):
        """测试 BOLL 下轨支撑"""
        pass

    def test_volume_breakout(self):
        """测试放量突破"""
        pass


class TestSellSignals:
    """卖出信号测试"""

    def test_ma_death_cross(self):
        """测试 MA 死叉信号"""
        pass

    def test_macd_death_cross(self):
        """测试 MACD 死叉信号"""
        pass

    def test_rsi_overbought(self):
        """测试 RSI 超买信号"""
        pass

    def test_stop_loss(self):
        """测试止损信号"""
        pass


class TestSignalStrength:
    """信号强度测试"""

    def test_strength_calculation(self):
        """测试强度计算"""
        pass

    def test_direction_judgment(self):
        """测试方向判断"""
        pass
```

### 7.2 测试数据

```python
# 模拟金叉场景
FAST_MA = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
SLOW_MA = pd.Series([12, 12, 12, 12, 12, 12, 12, 12, 12, 12])
# 第5个点应该产生金叉信号 (14 > 12 且 13 <= 12)

# 模拟死叉场景
FAST_MA_DOWN = pd.Series([20, 19, 18, 17, 16, 15, 14, 13, 12, 11])
SLOW_MA_UP = pd.Series([12, 12, 12, 12, 12, 12, 12, 12, 12, 12])
# 第5个点应该产生死叉信号 (16 < 12 且 17 >= 12) - 注意这个例子不合适
```

---

## 8. 实现检查清单

### 8.1 代码规范

- [ ] 所有函数都有类型提示
- [ ] 所有函数都有 docstring
- [ ] 代码行长度不超过 100 字符

### 8.2 功能完整性

- [ ] 实现 check_ma_cross (MA金叉)
- [ ] 实现 check_macd_cross (MACD金叉)
- [ ] 实现 check_rsi_oversold (RSI超卖反弹)
- [ ] 实现 check_kdj_cross (KDJ金叉)
- [ ] 实现 check_boll_support (BOLL下轨支撑)
- [ ] 实现 check_volume_breakout (放量突破)
- [ ] 实现 check_ma_death_cross (MA死叉)
- [ ] 实现 check_macd_death_cross (MACD死叉)
- [ ] 实现 check_rsi_overbought (RSI超买)
- [ ] 实现 check_stop_loss (止损)
- [ ] 实现 calc_signal_strength (信号强度)
- [ ] 实现 get_trade_direction (方向判断)
- [ ] 实现 SignalGenerator 类

### 8.3 测试覆盖

- [ ] 单元测试覆盖所有信号规则
- [ ] 集成测试覆盖信号聚合
- [ ] 边界条件测试

---

## 9. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 买入信号模块 | core/signals/buy_signals.py | ⬜ |
| 卖出信号模块 | core/signals/sell_signals.py | ⬜ |
| 信号强度模块 | core/signals/signal_strength.py | ⬜ |
| 模块初始化 | core/signals/__init__.py | ⬜ |
| 单元测试 | tests/test_signals.py | ⬜ |

---

## 10. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
