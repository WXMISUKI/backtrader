# 软件设计规格说明 (SDD)
# 内置策略模块

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 内置策略模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述内置策略模块的设计规格，实现常用的交易策略供用户直接使用。

### 1.2 范围

本模块负责实现以下策略：
- MACD 策略
- RSI 策略
- 布林带策略
- 综合策略

### 1.3 参考文档

- `SDD_STRATEGY_FRAMEWORK.md` - 策略框架规格
- `SDD_INDICATORS.md` - 技术指标模块规格

---

## 2. 系统概述

### 2.1 模块位置

```
strategies/
├── __init__.py          # 模块初始化
├── base.py              # 策略基类 (已完成)
├── registry.py          # 策略注册表 (已完成)
├── ma_cross.py          # 双均线策略 (已完成)
├── macd_strategy.py     # MACD 策略 (待实现)
├── rsi_strategy.py      # RSI 策略 (待实现)
├── boll_strategy.py     # 布林带策略 (待实现)
└── composite.py         # 综合策略 (待实现)
```

---

## 3. 设计决策

### 3.1 策略设计原则

1. **继承 Strategy 基类**: 所有策略必须继承 `Strategy` 基类
2. **实现 on_bar 方法**: 核心逻辑在 `on_bar` 方法中实现
3. **注册到 StrategyRegistry**: 使用装饰器注册策略
4. **配置驱动**: 所有参数通过 config 字典传入
5. **信号标准化**: 返回 `Signal` 对象，包含类型、置信度、原因

### 3.2 信号生成规则

| 策略 | 买入条件 | 卖出条件 |
|------|---------|---------|
| MACD | DIF 上穿 DEA (金叉) | DIF 下穿 DEA (死叉) |
| RSI | RSI < 30 后回升 | RSI > 70 |
| BOLL | 价格触及下轨后反弹 | 价格触及上轨后回落 |
| 综合 | 多指标确认 | 多指标确认 |

---

## 4. 模块详细设计

### 4.1 MACD 策略 (macd_strategy.py)

```python
@StrategyRegistry.register("macd")
class MACDStrategy(Strategy):
    """
    MACD 策略

    - DIF 上穿 DEA：买入 (金叉)
    - DIF 下穿 DEA：卖出 (死叉)

    参数:
        fast_period: 快线周期 (默认 12)
        slow_period: 慢线周期 (默认 26)
        signal_period: 信号线周期 (默认 9)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)
    """

    def on_bar(self, bar: Bar) -> Signal:
        """处理 K 线"""
        # 计算 MACD
        # 检测金叉/死叉
        # 生成信号
        pass
```

### 4.2 RSI 策略 (rsi_strategy.py)

```python
@StrategyRegistry.register("rsi")
class RSIStrategy(Strategy):
    """
    RSI 策略

    - RSI < oversold 后回升：买入
    - RSI > overbought：卖出

    参数:
        period: RSI 周期 (默认 14)
        overbought: 超买阈值 (默认 70)
        oversold: 超卖阈值 (默认 30)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)
    """

    def on_bar(self, bar: Bar) -> Signal:
        """处理 K 线"""
        # 计算 RSI
        # 检测超买超卖
        # 生成信号
        pass
```

### 4.3 布林带策略 (boll_strategy.py)

```python
@StrategyRegistry.register("boll")
class BollStrategy(Strategy):
    """
    布林带策略

    - 价格触及下轨后反弹：买入
    - 价格触及上轨后回落：卖出

    参数:
        period: 布林带周期 (默认 20)
        std_dev: 标准差倍数 (默认 2.0)
        stop_loss: 止损比例 (默认 0.05)
        take_profit: 止盈比例 (默认 0.15)
    """

    def on_bar(self, bar: Bar) -> Signal:
        """处理 K 线"""
        # 计算布林带
        # 检测突破/回落
        # 生成信号
        pass
```

### 4.4 综合策略 (composite.py)

```python
@StrategyRegistry.register("composite")
class CompositeStrategy(Strategy):
    """
    综合策略

    综合多个指标进行判断，提高信号可靠性

    参数:
        strategies: 子策略列表
        min_agreement: 最少同意策略数 (默认 2)
    """

    def on_bar(self, bar: Bar) -> Signal:
        """处理 K 线"""
        # 收集子策略信号
        # 统计共识
        # 生成最终信号
        pass
```

---

## 5. 测试设计

### 5.1 单元测试

```python
class TestMACDStrategy:
    """MACD 策略测试"""
    def test_initialization(self):
        pass
    def test_on_bar(self):
        pass
    def test_backtest(self):
        pass

class TestRSIStrategy:
    """RSI 策略测试"""
    def test_initialization(self):
        pass
    def test_on_bar(self):
        pass

class TestBollStrategy:
    """布林带策略测试"""
    def test_initialization(self):
        pass
    def test_on_bar(self):
        pass

class TestCompositeStrategy:
    """综合策略测试"""
    def test_initialization(self):
        pass
    def test_on_bar(self):
        pass
```

---

## 6. 实现检查清单

### 6.1 功能完整性

- [ ] 实现 MACDStrategy
- [ ] 实现 RSIStrategy
- [ ] 实现 BollStrategy
- [ ] 实现 CompositeStrategy
- [ ] 更新 __init__.py
- [ ] 编写测试

---

## 7. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| MACD 策略 | strategies/macd_strategy.py | ⬜ |
| RSI 策略 | strategies/rsi_strategy.py | ⬜ |
| 布林带策略 | strategies/boll_strategy.py | ⬜ |
| 综合策略 | strategies/composite.py | ⬜ |
| 单元测试 | tests/test_strategies.py | ⬜ |

---

## 8. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
