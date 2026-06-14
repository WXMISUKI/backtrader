# 归档文档：策略框架模块

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 策略框架模块归档报告 |
| 版本 | v1.0 |
| 完成日期 | 2026-06-14 |
| 状态 | ✅ 已完成 |

---

## 1. 任务完成情况

### 1.1 规格阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| SDD_STRATEGY_FRAMEWORK.md | ✅ | 策略框架设计规格 |

### 1.2 实现阶段

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 策略基类 | strategies/base.py | ✅ | Signal/Bar/Strategy |
| 策略注册表 | strategies/registry.py | ✅ | StrategyRegistry |
| 双均线策略 | strategies/ma_cross.py | ✅ | MACrossStrategy |
| 模块初始化 | strategies/__init__.py | ✅ | 统一接口 |

### 1.3 归档阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 单元测试 | ✅ | 31 个测试全部通过 |
| 归档文档 | ✅ | 本文件 |

---

## 2. 实现的功能清单

### 2.1 Signal 类

| 方法/属性 | 功能 | 返回值 |
|----------|------|--------|
| `type` | 信号类型 | SignalType |
| `confidence` | 置信度 | float |
| `reason` | 原因说明 | str |
| `price` | 建议价格 | float |
| `stop_loss` | 止损价 | float |
| `take_profit` | 止盈价 | float |
| `is_buy` | 是否买入 | bool |
| `is_sell` | 是否卖出 | bool |
| `is_hold` | 是否观望 | bool |
| `to_dict()` | 转换为字典 | dict |

### 2.2 Bar 类

| 方法/属性 | 功能 | 返回值 |
|----------|------|--------|
| `open` | 开盘价 | float |
| `high` | 最高价 | float |
| `low` | 最低价 | float |
| `close` | 收盘价 | float |
| `volume` | 成交量 | float |
| `datetime` | 日期时间 | datetime |
| `index` | 当前索引 | int |
| `history(field, period)` | 历史数据 | Series |
| `sma(period)` | 简单移动平均 | float |
| `ema(period)` | 指数移动平均 | float |
| `rsi(period)` | RSI 指标 | float |

### 2.3 Strategy 基类

| 方法/属性 | 功能 | 返回值 |
|----------|------|--------|
| `config` | 配置参数 | dict |
| `position` | 当前持仓 | int |
| `buy_price` | 买入价格 | float |
| `has_position` | 是否有持仓 | bool |
| `trades` | 交易记录 | list |
| `on_bar(bar)` | 处理K线 (抽象) | Signal |
| `buy(price, size)` | 买入 | - |
| `sell(price, size)` | 卖出 | - |
| `reset()` | 重置状态 | - |

### 2.4 StrategyRegistry 类

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `register(name)` | 注册装饰器 | decorator |
| `get(name)` | 获取策略类 | Type[Strategy] |
| `create(name, config)` | 创建实例 | Strategy |
| `list()` | 列出策略 | List[str] |
| `exists(name)` | 是否存在 | bool |
| `clear()` | 清除注册 | - |
| `get_info(name)` | 获取信息 | dict |

### 2.5 MACrossStrategy 策略

| 配置参数 | 默认值 | 说明 |
|---------|--------|------|
| `fast_period` | 5 | 短期均线周期 |
| `slow_period` | 20 | 长期均线周期 |
| `stop_loss` | 0.05 | 止损比例 |
| `take_profit` | 0.15 | 止盈比例 |

---

## 3. 测试结果

### 3.1 测试统计

```
============================= test session starts =============================
platform win32 -- Python 3.10.20, pytest-9.1.0
collected 31 items

tests/test_strategies.py::TestSignal::test_buy_signal PASSED
tests/test_strategies.py::TestSignal::test_sell_signal PASSED
tests/test_strategies.py::TestSignal::test_hold_signal PASSED
tests/test_strategies.py::TestSignal::test_to_dict PASSED
tests/test_strategies.py::TestSignal::test_str PASSED
tests/test_strategies.py::TestBar::test_properties PASSED
tests/test_strategies.py::TestBar::test_datetime PASSED
tests/test_strategies.py::TestBar::test_index PASSED
tests/test_strategies.py::TestBar::test_history PASSED
tests/test_strategies.py::TestBar::test_sma PASSED
tests/test_strategies.py::TestBar::test_ema PASSED
tests/test_strategies.py::TestBar::test_rsi PASSED
tests/test_strategies.py::TestBar::test_str PASSED
tests/test_strategies.py::TestStrategy::test_abstract PASSED
tests/test_strategies.py::TestStrategy::test_concrete PASSED
tests/test_strategies.py::TestStrategy::test_position PASSED
tests/test_strategies.py::TestStrategy::test_buy_sell PASSED
tests/test_strategies.py::TestStrategy::test_trades PASSED
tests/test_strategies.py::TestStrategy::test_reset PASSED
tests/test_strategies.py::TestStrategyRegistry::test_register PASSED
tests/test_strategies.py::TestStrategyRegistry::test_get PASSED
tests/test_strategies.py::TestStrategyRegistry::test_create PASSED
tests/test_strategies.py::TestStrategyRegistry::test_list PASSED
tests/test_strategies.py::TestStrategyRegistry::test_exists PASSED
tests/test_strategies.py::TestStrategyRegistry::test_key_error PASSED
tests/test_strategies.py::TestStrategyRegistry::test_type_error PASSED
tests/test_strategies.py::TestMACrossStrategy::test_initialization PASSED
tests/test_strategies.py::TestMACrossStrategy::test_default_params PASSED
tests/test_strategies.py::TestMACrossStrategy::test_on_bar_insufficient_data PASSED
tests/test_strategies.py::TestMACrossStrategy::test_on_bar_normal PASSED
tests/test_strategies.py::TestMACrossStrategy::test_backtest_simulation PASSED

============================= 31 passed in 0.83s ==============================
```

### 3.2 测试覆盖

| 测试类别 | 测试数量 | 通过 | 失败 |
|---------|---------|------|------|
| Signal 测试 | 5 | 5 | 0 |
| Bar 测试 | 8 | 8 | 0 |
| Strategy 测试 | 6 | 6 | 0 |
| StrategyRegistry 测试 | 6 | 6 | 0 |
| MACrossStrategy 测试 | 6 | 6 | 0 |
| **总计** | **31** | **31** | **0** |

---

## 4. 使用示例

### 4.1 使用策略注册表

```python
from strategies import StrategyRegistry

# 列出所有策略
print(StrategyRegistry.list())
# 输出: ['ma_cross']

# 创建策略实例
strategy = StrategyRegistry.create("ma_cross", {
    'fast_period': 5,
    'slow_period': 20
})

print(strategy.name)
print(strategy.description)
```

### 4.2 使用便捷函数

```python
from strategies import get_strategy, list_strategies

# 列出策略
print(list_strategies())

# 获取策略
strategy = get_strategy("ma_cross", {'fast_period': 5})
```

### 4.3 自定义策略

```python
from strategies import Strategy, Bar, Signal, SignalType, StrategyRegistry

@StrategyRegistry.register("my_strategy")
class MyStrategy(Strategy):
    """我的自定义策略"""

    def __init__(self, config=None):
        super().__init__(config)
        self.threshold = self.config.get('threshold', 0.5)

    def on_bar(self, bar: Bar) -> Signal:
        # 计算指标
        sma20 = bar.sma(20)
        rsi = bar.rsi(14)

        # 买入条件
        if bar.close > sma20 and rsi < 30:
            return Signal(
                type=SignalType.BUY,
                confidence=0.7,
                reason="价格高于均线且RSI超卖"
            )

        # 卖出条件
        if bar.close < sma20 and rsi > 70:
            return Signal(
                type=SignalType.SELL,
                confidence=0.6,
                reason="价格低于均线且RSI超买"
            )

        return Signal(SignalType.HOLD)
```

### 4.4 回测模拟

```python
from strategies import Bar, MACrossStrategy
import pandas as pd

# 加载数据
df = pd.read_csv("stock_data.csv", index_col='date', parse_dates=True)

# 创建策略
strategy = MACrossStrategy({'fast_period': 5, 'slow_period': 20})

# 模拟回测
for i in range(len(df)):
    bar = Bar(df, index=i)
    signal = strategy.on_bar(bar)

    if signal.is_buy:
        strategy.buy(bar.close)
        print(f"买入: {bar.datetime} @ {bar.close}")
    elif signal.is_sell:
        strategy.sell(bar.close)
        print(f"卖出: {bar.datetime} @ {bar.close}")
```

---

## 5. 设计亮点

### 5.1 借鉴的优秀设计

| 设计来源 | 借鉴内容 | 应用位置 |
|---------|---------|---------|
| finquant | Signal/Bar/Strategy 三件套 | base.py |
| finquant | bar.history() 历史查询 | Bar 类 |
| vectorbt | 策略注册表模式 | StrategyRegistry |
| QUANTAXIS | 统一数据结构 | Bar 封装 |

### 5.2 核心特性

1. **策略与引擎解耦**: 策略只关心 on_bar 方法，不关心数据来源
2. **Bar 封装**: 提供简洁的历史数据查询接口
3. **注册表模式**: 支持动态注册和实例化策略
4. **配置驱动**: 所有参数通过 config 字典传入

---

## 6. 文件清单

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| strategies/__init__.py | 模块初始化 | ~60 |
| strategies/base.py | 策略基类 | ~300 |
| strategies/registry.py | 策略注册表 | ~180 |
| strategies/ma_cross.py | 双均线策略 | ~200 |
| tests/test_strategies.py | 单元测试 | ~300 |

---

## 7. 已知问题和改进方向

### 7.1 已知问题

无

### 7.2 改进方向

1. **更多策略**: 可以添加 MACD、RSI、布林带等策略
2. **参数优化**: 可以添加网格搜索和贝叶斯优化
3. **组合策略**: 可以支持多策略组合
4. **回测集成**: 可以与 backtrader 深度集成

---

## 8. 依赖的外部资源

| 资源 | 版本 | 用途 |
|------|------|------|
| pandas | 2.3.3 | 数据处理 |
| numpy | 2.2.6 | 数值计算 |
| pytest | 9.1.0 | 单元测试 |

---

## 9. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本，借鉴 finquant/QUANTAXIS/vectorbt | - |
