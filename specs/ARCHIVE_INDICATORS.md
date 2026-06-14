# 归档文档：技术指标计算模块

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 技术指标计算模块归档报告 |
| 版本 | v1.0 |
| 完成日期 | 2026-06-14 |
| 状态 | ✅ 已完成 |

---

## 1. 任务完成情况

### 1.1 规格阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| SDD_INDICATORS.md | ✅ | 软件设计规格说明 |

### 1.2 实现阶段

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 趋势指标 | core/indicators/trend.py | ✅ | SMA, EMA, MACD, BOLL |
| 震荡指标 | core/indicators/oscillator.py | ✅ | RSI, KDJ, CCI, Williams %R |
| 量价指标 | core/indicators/volume.py | ✅ | VOL MA, OBV, VWAP, 量比, 换手率 |
| 模块初始化 | core/indicators/__init__.py | ✅ | 统一接口和 IndicatorCalculator 类 |

### 1.3 归档阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 单元测试 | ✅ | 27 个测试全部通过 |
| 归档文档 | ✅ | 本文件 |

---

## 2. 实现的指标清单

### 2.1 趋势指标

| 函数名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `calc_sma` | 简单移动平均 | data, period | Series |
| `calc_ema` | 指数移动平均 | data, period | Series |
| `calc_macd` | MACD | data, fast, slow, signal | DataFrame (dif, dea, macd) |
| `calc_boll` | 布林带 | data, period, std_dev | DataFrame (upper, middle, lower, bandwidth) |
| `calc_all_trend` | 批量计算趋势指标 | close, ma_periods, macd_params, boll_params | DataFrame |

### 2.2 震荡指标

| 函数名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `calc_rsi` | RSI | data, period | Series (0-100) |
| `calc_kdj` | KDJ | high, low, close, n, m1, m2 | DataFrame (k, d, j) |
| `calc_cci` | CCI | high, low, close, period | Series |
| `calc_williams_r` | Williams %R | high, low, close, period | Series (-100~0) |
| `calc_all_oscillator` | 批量计算震荡指标 | high, low, close | DataFrame |

### 2.3 量价指标

| 函数名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `calc_vol_ma` | 成交量移动平均 | volume, period | Series |
| `calc_obv` | OBV 能量潮 | close, volume | Series |
| `calc_vwap` | VWAP | high, low, close, volume, period | Series |
| `calc_turnover_rate` | 换手率 | volume, total_shares | Series |
| `calc_volume_ratio` | 量比 | volume, period | Series |
| `calc_all_volume` | 批量计算量价指标 | high, low, close, volume | DataFrame |

---

## 3. 测试结果

### 3.1 测试统计

```
============================= test session starts =============================
platform win32 -- Python 3.10.20, pytest-9.1.0
collected 27 items

tests/test_indicators.py::TestSMA::test_basic_sma PASSED
tests/test_indicators.py::TestSMA::test_sma_nan_values PASSED
tests/test_indicators.py::TestSMA::test_sma_insufficient_data PASSED
tests/test_indicators.py::TestSMA::test_sma_invalid_period PASSED
tests/test_indicators.py::TestSMA::test_sma_type_error PASSED
tests/test_indicators.py::TestEMA::test_basic_ema PASSED
tests/test_indicators.py::TestEMA::test_ema_more_responsive PASSED
tests/test_indicators.py::TestMACD::test_basic_macd PASSED
tests/test_indicators.py::TestMACD::test_macd_custom_params PASSED
tests/test_indicators.py::TestMACD::test_macd_invalid_params PASSED
tests/test_indicators.py::TestBOLL::test_basic_boll PASSED
tests/test_indicators.py::TestBOLL::test_boll_relationship PASSED
tests/test_indicators.py::TestRSI::test_basic_rsi PASSED
tests/test_indicators.py::TestRSI::test_rsi_default_period PASSED
tests/test_indicators.py::TestKDJ::test_basic_kdj PASSED
tests/test_indicators.py::TestKDJ::test_kdj_custom_params PASSED
tests/test_indicators.py::TestCCI::test_basic_cci PASSED
tests/test_indicators.py::TestWilliamsR::test_basic_williams_r PASSED
tests/test_indicators.py::TestVOLMA::test_basic_vol_ma PASSED
tests/test_indicators.py::TestOBV::test_basic_obv PASSED
tests/test_indicators.py::TestVWAP::test_basic_vwap PASSED
tests/test_indicators.py::TestTurnoverRate::test_basic_turnover PASSED
tests/test_indicators.py::TestVolumeRatio::test_basic_volume_ratio PASSED
tests/test_indicators.py::TestIndicatorCalculator::test_calculator_initialization PASSED
tests/test_indicators.py::TestIndicatorCalculator::test_calculator_all_indicators PASSED
tests/test_indicators.py::TestIndicatorCalculator::test_calculator_rsi PASSED
tests/test_indicators.py::TestIndicatorCalculator::test_calculator_macd PASSED

============================= 27 passed in 3.09s ==============================
```

### 3.2 测试覆盖

| 测试类别 | 测试数量 | 通过 | 失败 |
|---------|---------|------|------|
| SMA 测试 | 5 | 5 | 0 |
| EMA 测试 | 2 | 2 | 0 |
| MACD 测试 | 3 | 3 | 0 |
| BOLL 测试 | 2 | 2 | 0 |
| RSI 测试 | 2 | 2 | 0 |
| KDJ 测试 | 2 | 2 | 0 |
| CCI 测试 | 1 | 1 | 0 |
| Williams %R 测试 | 1 | 1 | 0 |
| VOL MA 测试 | 1 | 1 | 0 |
| OBV 测试 | 1 | 1 | 0 |
| VWAP 测试 | 1 | 1 | 0 |
| 换手率测试 | 1 | 1 | 0 |
| 量比测试 | 1 | 1 | 0 |
| 集成测试 | 4 | 4 | 0 |
| **总计** | **27** | **27** | **0** |

---

## 4. 使用示例

### 4.1 基本使用

```python
from core.indicators import IndicatorCalculator

# 创建计算器
calc = IndicatorCalculator()

# 计算单个指标
rsi = calc.calc_rsi(close, period=14)
macd = calc.calc_macd(close)
sma5 = calc.calc_sma(close, 5)

# 批量计算所有指标
all_indicators = calc.calc_all(high, low, close, volume)
```

### 4.2 信号判断示例

```python
from core.indicators import calc_rsi, calc_macd, calc_kdj

# 计算指标
rsi = calc_rsi(close, 14)
macd = calc_macd(close)
kdj = calc_kdj(high, low, close)

# RSI 超买超卖
overbought = rsi > 70
oversold = rsi < 30

# MACD 金叉死叉
golden_cross = (macd['dif'] > macd['dea']) & (macd['dif'].shift(1) <= macd['dea'].shift(1))
death_cross = (macd['dif'] < macd['dea']) & (macd['dif'].shift(1) >= macd['dea'].shift(1))

# KDJ 金叉死叉
kdj_golden = (kdj['k'] > kdj['d']) & (kdj['k'].shift(1) <= kdj['d'].shift(1))
kdj_death = (kdj['k'] < kdj['d']) & (kdj['k'].shift(1) >= kdj['d'].shift(1))
```

---

## 5. 文件清单

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| core/indicators/__init__.py | 模块初始化 | ~150 |
| core/indicators/trend.py | 趋势指标 | ~300 |
| core/indicators/oscillator.py | 震荡指标 | ~350 |
| core/indicators/volume.py | 量价指标 | ~300 |
| tests/test_indicators.py | 单元测试 | ~300 |

---

## 6. 已知问题和改进方向

### 6.1 已知问题

无

### 6.2 改进方向

1. **性能优化**: 可以使用 numba 或 cython 优化计算性能
2. **指标扩展**: 可以添加更多指标，如 ATR、ADX 等
3. **向量化计算**: 部分计算可以进一步向量化

---

## 7. 依赖的外部资源

| 资源 | 版本 | 用途 |
|------|------|------|
| pandas | 2.3.3 | 数据处理 |
| numpy | 2.2.6 | 数值计算 |
| pytest | 9.1.0 | 单元测试 |

---

## 8. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
