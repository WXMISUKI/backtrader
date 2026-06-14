# 归档文档：信号系统模块

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 信号系统模块归档报告 |
| 版本 | v1.0 |
| 完成日期 | 2026-06-14 |
| 状态 | ✅ 已完成 |

---

## 1. 任务完成情况

### 1.1 规格阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| SDD_SIGNALS.md | ✅ | 信号系统设计规格说明 |

### 1.2 实现阶段

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 买入信号 | core/signals/buy_signals.py | ✅ | 6种买入信号规则 |
| 卖出信号 | core/signals/sell_signals.py | ✅ | 6种卖出信号规则 |
| 信号强度 | core/signals/signal_strength.py | ✅ | 强度计算/方向判断/综合信号 |
| 模块初始化 | core/signals/__init__.py | ✅ | 统一接口和 SignalGenerator 类 |

### 1.3 归档阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 单元测试 | ✅ | 21 个测试全部通过 |
| 归档文档 | ✅ | 本文件 |

---

## 2. 实现的功能清单

### 2.1 买入信号规则

| 函数名 | 功能 | 权重 | 返回值 |
|--------|------|------|--------|
| `check_ma_cross` | MA 金叉 | 0.20 | Series (0/1) |
| `check_macd_cross` | MACD 金叉 | 0.25 | Series (0/1) |
| `check_rsi_oversold` | RSI 超卖反弹 | 0.15 | Series (0/1) |
| `check_kdj_cross` | KDJ 金叉 | 0.15 | Series (0/1) |
| `check_boll_support` | BOLL 下轨支撑 | 0.10 | Series (0/1) |
| `check_volume_breakout` | 放量突破 | 0.15 | Series (0/1) |

### 2.2 卖出信号规则

| 函数名 | 功能 | 权重 | 返回值 |
|--------|------|------|--------|
| `check_ma_death_cross` | MA 死叉 | 0.20 | Series (0/1) |
| `check_macd_death_cross` | MACD 死叉 | 0.25 | Series (0/1) |
| `check_rsi_overbought` | RSI 超买 | 0.15 | Series (0/1) |
| `check_kdj_death_cross` | KDJ 死叉 | 0.15 | Series (0/1) |
| `check_boll_pressure` | BOLL 上轨压力 | 0.10 | Series (0/1) |
| `check_stop_loss` | 止损触发 | 0.15 | bool |

### 2.3 信号强度和决策

| 函数名 | 功能 | 返回值 |
|--------|------|--------|
| `calc_signal_strength` | 计算信号强度 | Series (0-1) |
| `get_trade_direction` | 判断交易方向 | Series (1/-1/0) |
| `get_confidence` | 计算置信度 | Series (0-1) |
| `generate_signal` | 生成综合信号 | DataFrame |
| `get_latest_signal` | 获取最新信号 | dict |

### 2.4 SignalGenerator 类

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `generate` | 生成所有信号 | DataFrame |
| `get_latest_signal` | 获取最新信号 | dict |
| `get_buy_signals` | 获取买入信号 | DataFrame |
| `get_sell_signals` | 获取卖出信号 | DataFrame |
| `set_risk_profile` | 设置风险配置 | None |

---

## 3. 测试结果

### 3.1 测试统计

```
============================= test session starts =============================
platform win32 -- Python 3.10.20, pytest-9.1.0
collected 21 items

tests/test_signals.py::TestMACross::test_golden_cross PASSED
tests/test_signals.py::TestMACross::test_no_cross PASSED
tests/test_signals.py::TestMACDCross::test_golden_cross PASSED
tests/test_signals.py::TestRSIOversold::test_oversold_bounce PASSED
tests/test_signals.py::TestRSIOversold::test_no_signal_in_normal PASSED
tests/test_signals.py::TestKDJCross::test_golden_cross PASSED
tests/test_signals.py::TestBollSupport::test_support_bounce PASSED
tests/test_signals.py::TestVolumeBreakout::test_breakout PASSED
tests/test_signals.py::TestMADeathCross::test_death_cross PASSED
tests/test_signals.py::TestRSIOverbought::test_overbought PASSED
tests/test_signals.py::TestStopLoss::test_stop_loss_triggered PASSED
tests/test_signals.py::TestStopLoss::test_stop_loss_edge_cases PASSED
tests/test_signals.py::TestSignalStrength::test_strength_calculation PASSED
tests/test_signals.py::TestSignalStrength::test_empty_signals PASSED
tests/test_signals.py::TestTradeDirection::test_buy_direction PASSED
tests/test_signals.py::TestTradeDirection::test_hold_when_weak PASSED
tests/test_signals.py::TestConfidence::test_confidence_calculation PASSED
tests/test_signals.py::TestSignalGenerator::test_initialization PASSED
tests/test_signals.py::TestSignalGenerator::test_invalid_profile PASSED
tests/test_signals.py::TestSignalGenerator::test_generate_signals PASSED
tests/test_signals.py::TestSignalGenerator::test_get_latest_signal PASSED

============================= 21 passed in 0.76s ==============================
```

### 3.2 测试覆盖

| 测试类别 | 测试数量 | 通过 | 失败 |
|---------|---------|------|------|
| MA 信号测试 | 3 | 3 | 0 |
| MACD 信号测试 | 1 | 1 | 0 |
| RSI 信号测试 | 3 | 3 | 0 |
| KDJ 信号测试 | 1 | 1 | 0 |
| BOLL 信号测试 | 1 | 1 | 0 |
| 成交量信号测试 | 1 | 1 | 0 |
| 止损测试 | 2 | 2 | 0 |
| 信号强度测试 | 2 | 2 | 0 |
| 交易方向测试 | 2 | 2 | 0 |
| 置信度测试 | 1 | 1 | 0 |
| 集成测试 | 4 | 4 | 0 |
| **总计** | **21** | **21** | **0** |

---

## 4. 使用示例

### 4.1 基本使用

```python
from core.signals import SignalGenerator
from core.indicators import IndicatorCalculator

# 创建计算器和信号生成器
calc = IndicatorCalculator()
generator = SignalGenerator(risk_profile="moderate")

# 计算指标
indicators = calc.calc_all(high, low, close, volume)

# 生成信号
signals = generator.generate(close, high, low, volume, indicators)

# 获取最新信号
latest = generator.get_latest_signal(close, high, low, volume, indicators)
print(latest)
# 输出: {'direction': 'BUY', 'confidence': 0.65, 'buy_strength': 0.65, ...}
```

### 4.2 不同风险配置

```python
# 保守型
generator = SignalGenerator(risk_profile="conservative")
# RSI 阈值: 超卖 < 35, 超买 > 65
# 止损: 3%

# 稳健型 (默认)
generator = SignalGenerator(risk_profile="moderate")
# RSI 阈值: 超卖 < 30, 超买 > 70
# 止损: 5%

# 激进型
generator = SignalGenerator(risk_profile="aggressive")
# RSI 阈值: 超卖 < 20, 超买 > 80
# 止损: 8%
```

### 4.3 信号解读

```python
latest = generator.get_latest_signal(close, high, low, volume, indicators)

if latest['direction'] == 'BUY':
    print(f"建议买入，置信度: {latest['confidence']*100:.1f}%")
    print(f"买入强度: {latest['buy_strength']:.2f}")
elif latest['direction'] == 'SELL':
    print(f"建议卖出，置信度: {latest['confidence']*100:.1f}%")
    print(f"卖出强度: {latest['sell_strength']:.2f}")
else:
    print("建议观望")
```

---

## 5. 文件清单

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| core/signals/__init__.py | 模块初始化 | ~180 |
| core/signals/buy_signals.py | 买入信号 | ~250 |
| core/signals/sell_signals.py | 卖出信号 | ~250 |
| core/signals/signal_strength.py | 信号强度 | ~300 |
| tests/test_signals.py | 单元测试 | ~300 |

---

## 6. 信号权重配置

### 6.1 买入信号权重

| 信号 | 权重 | 说明 |
|------|------|------|
| MA 金叉 | 0.20 | 趋势确认 |
| MACD 金叉 | 0.25 | 动量确认 |
| RSI 超卖反弹 | 0.15 | 超卖反弹 |
| KDJ 金叉 | 0.15 | 短期动量 |
| BOLL 下轨支撑 | 0.10 | 支撑确认 |
| 放量突破 | 0.15 | 量价配合 |

### 6.2 卖出信号权重

| 信号 | 权重 | 说明 |
|------|------|------|
| MA 死叉 | 0.20 | 趋势反转 |
| MACD 死叉 | 0.25 | 动量减弱 |
| RSI 超买 | 0.15 | 超买风险 |
| KDJ 死叉 | 0.15 | 短期动量 |
| BOLL 上轨压力 | 0.10 | 压力确认 |
| 止损触发 | 0.15 | 风险控制 |

---

## 7. 已知问题和改进方向

### 7.1 已知问题

无

### 7.2 改进方向

1. **信号优化**: 可以根据回测结果调整信号权重
2. **新增信号**: 可以添加更多信号规则，如成交量背离等
3. **机器学习**: 可以使用机器学习优化信号权重

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
| v1.0 | 2026-06-14 | 初始版本 | - |
