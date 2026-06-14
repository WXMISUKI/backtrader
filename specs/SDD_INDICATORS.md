# 软件设计规格说明 (SDD)
# 技术指标计算模块

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 技术指标计算模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述技术指标计算模块的设计规格，为开发人员提供明确的实现指导，确保代码质量和功能一致性。

### 1.2 范围

本模块负责计算股票技术分析所需的各种指标，包括：
- 趋势指标：MA、EMA、MACD、BOLL
- 震荡指标：RSI、KDJ、CCI
- 量价指标：VOL MA、OBV、换手率

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| SMA | Simple Moving Average，简单移动平均 |
| EMA | Exponential Moving Average，指数移动平均 |
| MACD | Moving Average Convergence Divergence，移动平均收敛发散 |
| RSI | Relative Strength Index，相对强弱指数 |
| KDJ | 随机指标 |
| BOLL | Bollinger Bands，布林带 |
| OBV | On Balance Volume，能量潮 |

### 1.4 参考文档

- `DEVELOPMENT_SPEC.md` - 开发规格书
- `PROJECT_STRUCTURE.md` - 项目结构图

---

## 2. 系统概述

### 2.1 模块位置

```
core/
└── indicators/
    ├── __init__.py      # 模块初始化
    ├── trend.py         # 趋势指标
    ├── oscillator.py    # 震荡指标
    └── volume.py        # 量价指标
```

### 2.2 依赖关系

```
┌─────────────────────────────────────┐
│         indicators 模块             │
├─────────────────────────────────────┤
│ 依赖:                               │
│   - pandas (数据处理)               │
│   - numpy (数值计算)                │
│   - core.data (数据获取)            │
│                                     │
│ 被依赖:                             │
│   - core.signals (信号生成)         │
│   - skills.stock-advisor (个股分析) │
└─────────────────────────────────────┘
```

---

## 3. 设计决策

### 3.1 设计原则

1. **单一职责**: 每个函数只计算一个指标
2. **无状态**: 函数不保存状态，便于测试和复用
3. **向量化**: 使用 pandas/numpy 向量化操作，提高性能
4. **类型提示**: 使用 Python 类型提示，提高代码可读性
5. **文档完整**: 每个函数都有完整的 docstring

### 3.2 技术选型

| 需求 | 选型 | 理由 |
|------|------|------|
| 数据结构 | pandas.Series/DataFrame | 与 backtrader 兼容 |
| 数值计算 | numpy | 性能优化 |
| 类型检查 | typing | 代码质量 |

### 3.3 输入输出规范

**输入**:
- `data`: pandas.Series 或 pandas.DataFrame
- `period`: int，指标周期参数

**输出**:
- pandas.Series 或 pandas.DataFrame，索引与输入一致

---

## 4. 模块详细设计

### 4.1 趋势指标模块 (trend.py)

#### 4.1.1 SMA - 简单移动平均

```python
def calc_sma(data: pd.Series, period: int) -> pd.Series:
    """
    计算简单移动平均线

    参数:
        data: 价格序列 (通常是收盘价)
        period: 计算周期 (如 5, 10, 20, 60)

    返回:
        pd.Series: SMA 值序列

    示例:
        >>> sma5 = calc_sma(df['close'], 5)
        >>> sma20 = calc_sma(df['close'], 20)

    算法:
        SMA(N) = (C1 + C2 + ... + CN) / N
        其中 C 为收盘价，N 为周期

    注意:
        - 前 N-1 个值为 NaN
        - 数据长度必须大于 period
    """
    pass
```

#### 4.1.2 EMA - 指数移动平均

```python
def calc_ema(data: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线

    参数:
        data: 价格序列
        period: 计算周期

    返回:
        pd.Series: EMA 值序列

    算法:
        EMA(N) = C * K + EMA(yesterday) * (1 - K)
        其中 K = 2 / (N + 1)

    特点:
        - 对近期价格赋予更高权重
        - 比 SMA 更灵敏
    """
    pass
```

#### 4.1.3 MACD - 移动平均收敛发散

```python
def calc_macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """
    计算 MACD 指标

    参数:
        data: 价格序列
        fast_period: 快线周期，默认 12
        slow_period: 慢线周期，默认 26
        signal_period: 信号线周期，默认 9

    返回:
        pd.DataFrame: 包含以下列
            - dif: 快线与慢线的差值
            - dea: DIF 的 EMA (信号线)
            - macd: (DIF - DEA) * 2 (柱状图)

    算法:
        DIF = EMA(fast) - EMA(slow)
        DEA = EMA(DIF, signal)
        MACD = (DIF - DEA) * 2

    应用:
        - DIF 上穿 DEA: 买入信号 (金叉)
        - DIF 下穿 DEA: 卖出信号 (死叉)
        - MACD 柱状图: 动量强弱
    """
    pass
```

#### 4.1.4 BOLL - 布林带

```python
def calc_boll(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:
    """
    计算布林带

    参数:
        data: 价格序列
        period: 移动平均周期，默认 20
        std_dev: 标准差倍数，默认 2.0

    返回:
        pd.DataFrame: 包含以下列
            - upper: 上轨
            - middle: 中轨 (SMA)
            - lower: 下轨

    算法:
        中轨 = SMA(N)
        标准差 = STD(CLOSE, N)
        上轨 = 中轨 + K * 标准差
        下轨 = 中轨 - K * 标准差

    应用:
        - 价格触及上轨: 可能超买
        - 价格触及下轨: 可能超买
        - 带宽收窄: 可能变盘
    """
    pass
```

---

### 4.2 震荡指标模块 (oscillator.py)

#### 4.2.1 RSI - 相对强弱指数

```python
def calc_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI 指标

    参数:
        data: 价格序列
        period: 计算周期，默认 14

    返回:
        pd.Series: RSI 值序列 (0-100)

    算法:
        1. 计算价格变化: diff = C - C(-1)
        2. 分离涨跌: gain = max(diff, 0), loss = max(-diff, 0)
        3. 计算平均涨跌: avg_gain = SMA(gain, N), avg_loss = SMA(loss, N)
        4. 计算相对强度: RS = avg_gain / avg_loss
        5. 计算 RSI: RSI = 100 - (100 / (1 + RS))

    应用:
        - RSI > 70: 超买区域，可能回调
        - RSI < 30: 超卖区域，可能反弹
        - RSI 背离: 趋势可能反转

    阈值 (可配置):
        - 超买: 70 (激进型: 80)
        - 超卖: 30 (激进型: 20)
    """
    pass
```

#### 4.2.2 KDJ - 随机指标

```python
def calc_kdj(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> pd.DataFrame:
    """
    计算 KDJ 指标

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        n: RSV 周期，默认 9
        m1: K 值平滑周期，默认 3
        m2: D 值平滑周期，默认 3

    返回:
        pd.DataFrame: 包含以下列
            - k: K 值
            - d: D 值
            - j: J 值 (3K - 2D)

    算法:
        1. RSV = (C - Ln) / (Hn - Ln) * 100
        2. K = SMA(RSV, M1)
        3. D = SMA(K, M2)
        4. J = 3 * K - 2 * D

    应用:
        - K 上穿 D: 买入信号 (金叉)
        - K 下穿 D: 卖出信号 (死叉)
        - J > 100: 超买
        - J < 0: 超卖
    """
    pass
```

#### 4.2.3 CCI - 商品通道指数

```python
def calc_cci(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    计算 CCI 指标

    参数:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 计算周期，默认 14

    返回:
        pd.Series: CCI 值序列

    算法:
        1. TP = (H + L + C) / 3 (典型价格)
        2. MA_TP = SMA(TP, N)
        3. MD = mean(abs(TP - MA_TP))
        4. CCI = (TP - MA_TP) / (0.015 * MD)

    应用:
        - CCI > 100: 超买
        - CCI < -100: 超卖
        - CCI 穿越 0: 趋势变化
    """
    pass
```

---

### 4.3 量价指标模块 (volume.py)

#### 4.3.1 VOL MA - 成交量移动平均

```python
def calc_vol_ma(volume: pd.Series, period: int = 5) -> pd.Series:
    """
    计算成交量移动平均

    参数:
        volume: 成交量序列
        period: 计算周期，默认 5

    返回:
        pd.Series: 成交量 MA 值

    应用:
        - 量价齐升: 趋势确认
        - 量价背离: 趋势可能反转
        - 放量突破: 有效突破
    """
    pass
```

#### 4.3.2 OBV - 能量潮

```python
def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算 OBV 指标

    参数:
        close: 收盘价序列
        volume: 成交量序列

    返回:
        pd.Series: OBV 值序列

    算法:
        如果 C > C(-1): OBV = OBV(-1) + V
        如果 C < C(-1): OBV = OBV(-1) - V
        如果 C = C(-1): OBV = OBV(-1)

    应用:
        - OBV 上升: 资金流入
        - OBV 下降: 资金流出
        - OBV 背离: 趋势可能反转
    """
    pass
```

#### 4.3.3 换手率计算

```python
def calc_turnover_rate(
    volume: pd.Series,
    total_shares: float
) -> pd.Series:
    """
    计算换手率

    参数:
        volume: 成交量序列
        total_shares: 总股本

    返回:
        pd.Series: 换手率序列 (百分比)

    算法:
        换手率 = 成交量 / 总股本 * 100%

    应用:
        - 换手率 > 10%: 高度活跃
        - 换手率 < 1%: 低迷
    """
    pass
```

---

## 5. 接口设计

### 5.1 统一接口

```python
class IndicatorCalculator:
    """技术指标计算器"""

    def calc_indicator(
        self,
        data: pd.DataFrame,
        indicator: str,
        **params
    ) -> pd.Series | pd.DataFrame:
        """
        统一指标计算接口

        参数:
            data: 包含 OHLCV 的 DataFrame
            indicator: 指标名称
            **params: 指标参数

        返回:
            指标计算结果

        示例:
            >>> calc = IndicatorCalculator()
            >>> rsi = calc.calc_indicator(df, 'rsi', period=14)
            >>> macd = calc.calc_indicator(df, 'macd')
        """
        pass
```

### 5.2 指标注册表

```python
INDICATOR_REGISTRY = {
    # 趋势指标
    'sma': {'func': calc_sma, 'category': 'trend'},
    'ema': {'func': calc_ema, 'category': 'trend'},
    'macd': {'func': calc_macd, 'category': 'trend'},
    'boll': {'func': calc_boll, 'category': 'trend'},

    # 震荡指标
    'rsi': {'func': calc_rsi, 'category': 'oscillator'},
    'kdj': {'func': calc_kdj, 'category': 'oscillator'},
    'cci': {'func': calc_cci, 'category': 'oscillator'},

    # 量价指标
    'vol_ma': {'func': calc_vol_ma, 'category': 'volume'},
    'obv': {'func': calc_obv, 'category': 'volume'},
}
```

---

## 6. 错误处理

### 6.1 异常类型

```python
class IndicatorError(Exception):
    """指标计算异常基类"""
    pass

class InsufficientDataError(IndicatorError):
    """数据不足异常"""
    pass

class InvalidParameterError(IndicatorError):
    """参数无效异常"""
    pass
```

### 6.2 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| 数据不足 | 抛出 InsufficientDataError |
| 参数无效 | 抛出 InvalidParameterError |
| 计算异常 | 返回 NaN 序列并记录警告 |

### 6.3 输入验证

```python
def validate_input(data: pd.Series, min_length: int, name: str = "data"):
    """验证输入数据"""
    if not isinstance(data, pd.Series):
        raise TypeError(f"{name} 必须是 pandas.Series 类型")

    if len(data) < min_length:
        raise InsufficientDataError(
            f"{name} 长度不足，需要至少 {min_length} 个数据点，"
            f"实际只有 {len(data)} 个"
        )

    if data.isnull().all():
        raise ValueError(f"{name} 全部为 NaN")
```

---

## 7. 测试设计

### 7.1 单元测试用例

```python
class TestSMA:
    """SMA 测试"""

    def test_basic_sma(self):
        """测试基本 SMA 计算"""
        pass

    def test_sma_with_nan(self):
        """测试包含 NaN 的情况"""
        pass

    def test_sma_period_validation(self):
        """测试周期参数验证"""
        pass

    def test_sma_insufficient_data(self):
        """测试数据不足的情况"""
        pass
```

### 7.2 测试数据

```python
# 标准测试数据
TEST_DATA = pd.Series([
    10.0, 10.5, 10.3, 10.8, 11.0,
    10.9, 11.2, 11.5, 11.3, 11.8
])

# 预期结果 (SMA5)
EXPECTED_SMA5 = pd.Series([
    None, None, None, None, 10.52,
    10.70, 10.84, 11.08, 11.18, 11.34
])
```

### 7.3 性能测试

```python
def test_performance():
    """性能测试: 10万条数据应在 1 秒内完成"""
    import time
    data = pd.Series(np.random.randn(100000))

    start = time.time()
    calc_sma(data, 20)
    elapsed = time.time() - start

    assert elapsed < 1.0, f"SMA 计算耗时 {elapsed:.2f} 秒，超过 1 秒"
```

---

## 8. 实现检查清单

### 8.1 代码规范

- [ ] 所有函数都有类型提示
- [ ] 所有函数都有 docstring
- [ ] 代码行长度不超过 100 字符
- [ ] 使用 4 空格缩进

### 8.2 功能完整性

- [ ] 实现 calc_sma
- [ ] 实现 calc_ema
- [ ] 实现 calc_macd
- [ ] 实现 calc_boll
- [ ] 实现 calc_rsi
- [ ] 实现 calc_kdj
- [ ] 实现 calc_cci
- [ ] 实现 calc_vol_ma
- [ ] 实现 calc_obv
- [ ] 实现 IndicatorCalculator 类

### 8.3 测试覆盖

- [ ] 单元测试覆盖所有函数
- [ ] 边界条件测试
- [ ] 异常情况测试
- [ ] 性能测试

### 8.4 文档完整

- [ ] 模块级 docstring
- [ ] 函数级 docstring
- [ ] 使用示例
- [ ] README 更新

---

## 9. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 趋势指标模块 | core/indicators/trend.py | ⬜ |
| 震荡指标模块 | core/indicators/oscillator.py | ⬜ |
| 量价指标模块 | core/indicators/volume.py | ⬜ |
| 模块初始化 | core/indicators/__init__.py | ⬜ |
| 单元测试 | tests/test_indicators.py | ⬜ |
| 文档更新 | README_QUANT.md | ⬜ |

---

## 10. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
