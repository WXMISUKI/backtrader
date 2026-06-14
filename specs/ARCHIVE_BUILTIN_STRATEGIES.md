# 归档文档：内置策略模块

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 内置策略模块归档报告 |
| 版本 | v1.0 |
| 完成日期 | 2026-06-14 |
| 状态 | ✅ 已完成 |

---

## 1. 任务完成情况

### 1.1 规格阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| SDD_BUILTIN_STRATEGIES.md | ✅ | 内置策略设计规格 |

### 1.2 实现阶段

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| MACD 策略 | strategies/macd_strategy.py | ✅ | MACDStrategy |
| RSI 策略 | strategies/rsi_strategy.py | ✅ | RSIStrategy |
| 布林带策略 | strategies/boll_strategy.py | ✅ | BollStrategy |
| 综合策略 | strategies/composite.py | ✅ | CompositeStrategy |

### 1.3 归档阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 单元测试 | ✅ | 47 个测试全部通过 |
| 归档文档 | ✅ | 本文件 |

---

## 2. 实现的功能清单

### 2.1 内置策略

| 策略 | 注册名 | 买入条件 | 卖出条件 |
|------|--------|---------|---------|
| 双均线策略 | ma_cross | MA5 上穿 MA20 | MA5 下穿 MA20 |
| MACD 策略 | macd | DIF 上穿 DEA | DIF 下穿 DEA |
| RSI 策略 | rsi | RSI < 30 后回升 | RSI > 70 |
| 布林带策略 | boll | 价格触及下轨后反弹 | 价格触及上轨后回落 |
| 综合策略 | composite | 多数子策略同意买入 | 多数子策略同意卖出 |

### 2.2 策略参数

| 策略 | 参数 | 默认值 | 说明 |
|------|------|--------|------|
| MACDStrategy | fast_period | 12 | 快线周期 |
| | slow_period | 26 | 慢线周期 |
| | signal_period | 9 | 信号线周期 |
| | stop_loss | 0.05 | 止损比例 |
| | take_profit | 0.15 | 止盈比例 |
| RSIStrategy | period | 14 | RSI 周期 |
| | overbought | 70 | 超买阈值 |
| | oversold | 30 | 超卖阈值 |
| | stop_loss | 0.05 | 止损比例 |
| | take_profit | 0.15 | 止盈比例 |
| BollStrategy | period | 20 | 布林带周期 |
| | std_dev | 2.0 | 标准差倍数 |
| | stop_loss | 0.05 | 止损比例 |
| | take_profit | 0.15 | 止盈比例 |
| CompositeStrategy | strategies | ['ma_cross', 'macd', 'rsi'] | 子策略列表 |
| | min_agreement | 2 | 最少同意数 |

---

## 3. 测试结果

### 3.1 测试统计

```
============================= test session starts =============================
platform win32 -- Python 3.10.20, pytest-9.1.0
collected 47 items

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
tests/test_strategies.py::TestMACDStrategy::test_initialization PASSED
tests/test_strategies.py::TestMACDStrategy::test_default_params PASSED
tests/test_strategies.py::TestMACDStrategy::test_on_bar PASSED
tests/test_strategies.py::TestMACDStrategy::test_backtest PASSED
tests/test_strategies.py::TestRSIStrategy::test_initialization PASSED
tests/test_strategies.py::TestRSIStrategy::test_default_params PASSED
tests/test_strategies.py::TestRSIStrategy::test_on_bar PASSED
tests/test_strategies.py::TestRSIStrategy::test_backtest PASSED
tests/test_strategies.py::TestBollStrategy::test_initialization PASSED
tests/test_strategies.py::TestBollStrategy::test_default_params PASSED
tests/test_strategies.py::TestBollStrategy::test_on_bar PASSED
tests/test_strategies.py::TestBollStrategy::test_backtest PASSED
tests/test_strategies.py::TestCompositeStrategy::test_initialization PASSED
tests/test_strategies.py::TestCompositeStrategy::test_on_bar PASSED
tests/test_strategies.py::TestCompositeStrategy::test_backtest PASSED
tests/test_strategies.py::TestCompositeStrategy::test_reset PASSED

============================= 47 passed in 1.28s ==============================
```

### 3.2 测试覆盖

| 测试类别 | 测试数量 | 通过 | 失败 |
|---------|---------|------|------|
| Signal 测试 | 5 | 5 | 0 |
| Bar 测试 | 8 | 8 | 0 |
| Strategy 测试 | 6 | 6 | 0 |
| StrategyRegistry 测试 | 7 | 7 | 0 |
| MACrossStrategy 测试 | 5 | 5 | 0 |
| MACDStrategy 测试 | 4 | 4 | 0 |
| RSIStrategy 测试 | 4 | 4 | 0 |
| BollStrategy 测试 | 4 | 4 | 0 |
| CompositeStrategy 测试 | 4 | 4 | 0 |
| **总计** | **47** | **47** | **0** |

---

## 4. 使用示例

### 4.1 使用 MACD 策略

```python
from strategies import get_strategy

strategy = get_strategy("macd", {
    'fast_period': 12,
    'slow_period': 26,
    'signal_period': 9
})

# 处理 K 线
bar = Bar(df, index=99)
signal = strategy.on_bar(bar)

if signal.is_buy:
    print(f"买入: {signal.reason}")
elif signal.is_sell:
    print(f"卖出: {signal.reason}")
```

### 4.2 使用 RSI 策略

```python
from strategies import get_strategy

strategy = get_strategy("rsi", {
    'period': 14,
    'overbought': 70,
    'oversold': 30
})
```

### 4.3 使用综合策略

```python
from strategies import get_strategy

strategy = get_strategy("composite", {
    'strategies': ['ma_cross', 'macd', 'rsi'],
    'min_agreement': 2,
    'configs': {
        'ma_cross': {'fast_period': 5, 'slow_period': 20},
        'macd': {'fast_period': 12},
        'rsi': {'period': 14}
    }
})
```

### 4.4 列出所有策略

```python
from strategies import list_strategies

print(list_strategies())
# 输出: ['ma_cross', 'macd', 'rsi', 'boll', 'composite']
```

---

## 5. 文件清单

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| strategies/__init__.py | 模块初始化 | ~70 |
| strategies/base.py | 策略基类 | ~300 |
| strategies/registry.py | 策略注册表 | ~180 |
| strategies/ma_cross.py | 双均线策略 | ~200 |
| strategies/macd_strategy.py | MACD 策略 | ~220 |
| strategies/rsi_strategy.py | RSI 策略 | ~220 |
| strategies/boll_strategy.py | 布林带策略 | ~200 |
| strategies/composite.py | 综合策略 | ~200 |
| tests/test_strategies.py | 单元测试 | ~450 |

---

## 6. 已知问题和改进方向

### 6.1 已知问题

无

### 6.2 改进方向

1. **更多策略**: 可以添加 KDJ、CCI、OBV 等策略
2. **参数优化**: 可以添加网格搜索和贝叶斯优化
3. **策略组合**: 可以支持更复杂的组合逻辑
4. **回测集成**: 可以与 backtrader 深度集成

---

## 7. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
