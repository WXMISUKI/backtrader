# 归档文档：个股分析模块 (StockAnalyzer)

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 个股分析模块归档报告 |
| 版本 | v1.0 |
| 完成日期 | 2026-06-14 |
| 状态 | ✅ 已完成 |

---

## 1. 任务完成情况

### 1.1 规格阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| SDD_STOCK_ANALYZER.md | ✅ | 个股分析模块设计规格 |

### 1.2 实现阶段

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 股票数据封装 | skills/stock_advisor/stock_data.py | ✅ | StockData 类 |
| 股票分析器 | skills/stock_advisor/analyzer.py | ✅ | StockAnalyzer 类 |
| 模块初始化 | skills/stock_advisor/__init__.py | ✅ | 统一接口 |

### 1.3 归档阶段

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 单元测试 | ✅ | 18 个测试全部通过 |
| 归档文档 | ✅ | 本文件 |

---

## 2. 实现的功能清单

### 2.1 StockData 类

| 方法/属性 | 功能 | 返回值 |
|----------|------|--------|
| `code` | 股票代码 | str |
| `name` | 股票名称 | str |
| `close` | 收盘价序列 | Series |
| `open` | 开盘价序列 | Series |
| `high` | 最高价序列 | Series |
| `low` | 最低价序列 | Series |
| `volume` | 成交量序列 | Series |
| `latest_price` | 最新价格 | float |
| `data_points` | 数据点数量 | int |
| `date_range` | 日期范围 | tuple |
| `indicators` | 技术指标 (懒计算) | DataFrame |
| `signals` | 交易信号 (懒计算) | DataFrame |
| `get_latest_signal()` | 获取最新信号 | dict |
| `get_returns()` | 计算收益率 | Series |
| `get_volatility()` | 计算波动率 | float |
| `get_max_drawdown()` | 计算最大回撤 | float |
| `get_sharpe_ratio()` | 计算夏普比率 | float |
| `to_dict()` | 转换为字典 | dict |
| `summary()` | 生成摘要 | str |

### 2.2 StockAnalyzer 类

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `__init__(config)` | 初始化分析器 | - |
| `analyze(stock_code)` | 分析股票 | AnalysisResult |
| `get_stock_data(stock_code)` | 获取股票数据 | StockData |
| `clear_cache()` | 清除缓存 | - |

### 2.3 配置和结果类

| 类 | 功能 |
|---|------|
| `AnalysisConfig` | 分析配置 (日期/指标参数/风险配置) |
| `RiskAssessment` | 风险评估 (波动率/回撤/止损止盈) |
| `Recommendation` | 投资建议 (操作/置信度/原因) |
| `AnalysisResult` | 分析结果 (整合所有信息) |

### 2.4 便捷函数

| 函数 | 功能 | 返回值 |
|------|------|--------|
| `analyze(code, risk_profile)` | 分析单只股票 | AnalysisResult |
| `batch_analyze(codes, risk_profile)` | 批量分析股票 | List[AnalysisResult] |

---

## 3. 测试结果

### 3.1 测试统计

```
============================= test session starts =============================
platform win32 -- Python 3.10.20, pytest-9.1.0
collected 18 items

tests/test_stock_analyzer.py::TestStockData::test_initialization PASSED
tests/test_stock_analyzer.py::TestStockData::test_properties PASSED
tests/test_stock_analyzer.py::TestStockData::test_date_range PASSED
tests/test_stock_analyzer.py::TestStockData::test_statistics PASSED
tests/test_stock_analyzer.py::TestStockData::test_lazy_indicators PASSED
tests/test_stock_analyzer.py::TestStockData::test_lazy_signals PASSED
tests/test_stock_analyzer.py::TestStockData::test_to_dict PASSED
tests/test_stock_analyzer.py::TestStockData::test_summary PASSED
tests/test_stock_analyzer.py::TestStockData::test_invalid_dataframe PASSED
tests/test_stock_analyzer.py::TestAnalysisConfig::test_default_config PASSED
tests/test_stock_analyzer.py::TestAnalysisConfig::test_custom_config PASSED
tests/test_stock_analyzer.py::TestAnalysisConfig::test_to_dict PASSED
tests/test_stock_analyzer.py::TestStockAnalyzer::test_initialization PASSED
tests/test_stock_analyzer.py::TestStockAnalyzer::test_custom_config PASSED
tests/test_stock_analyzer.py::TestStockAnalyzer::test_cache PASSED
tests/test_stock_analyzer.py::TestStockAnalyzer::test_clear_cache PASSED
tests/test_stock_analyzer.py::TestDataClasses::test_risk_assessment PASSED
tests/test_stock_analyzer.py::TestDataClasses::test_recommendation PASSED

============================= 18 passed in 0.75s ==============================
```

### 3.2 测试覆盖

| 测试类别 | 测试数量 | 通过 | 失败 |
|---------|---------|------|------|
| StockData 测试 | 9 | 9 | 0 |
| AnalysisConfig 测试 | 3 | 3 | 0 |
| StockAnalyzer 测试 | 4 | 4 | 0 |
| 数据类测试 | 2 | 2 | 0 |
| **总计** | **18** | **18** | **0** |

---

## 4. 使用示例

### 4.1 简单用法

```python
from skills.stock_advisor import analyze

# 分析单只股票
result = analyze("000001")
print(result.summary())
```

输出:
```
==================================================
【平安银行(000001)】分析报告
==================================================
当前价格: 11.24
数据区间: 2026-01-02 ~ 2026-06-12
──────────────────────────────────────────────────
操作建议: 📈 买入
置信度: 65%
原因: 买入信号强度 65%，建议适量买入
──────────────────────────────────────────────────
目标价: 12.93
止损价: 10.68
建议仓位: 50%
──────────────────────────────────────────────────
波动率: 25.00%
最大回撤: -15.00%
==================================================
⚠️ 以上建议仅供参考，投资有风险，入市需谨慎
```

### 4.2 高级用法

```python
from skills.stock_advisor import StockAnalyzer, AnalysisConfig

# 自定义配置
config = AnalysisConfig(
    start_date="20250101",
    end_date="20260614",
    risk_profile="aggressive"
)

# 创建分析器
analyzer = StockAnalyzer(config)

# 分析股票
result = analyzer.analyze("000001")

# 访问详细数据
print(result.signal)
print(result.risk.to_dict())
print(result.recommendation.to_dict())
```

### 4.3 批量分析

```python
from skills.stock_advisor import batch_analyze

# 批量分析
codes = ["000001", "600519", "000858"]
results = batch_analyze(codes, "moderate")

for r in results:
    print(r.summary())
    print("---")
```

### 4.4 不同风险配置

```python
# 保守型
result = analyze("000001", "conservative")
# RSI 阈值更严格，止损更紧

# 稳健型 (默认)
result = analyze("000001", "moderate")
# 平衡风险收益

# 激进型
result = analyze("000001", "aggressive")
# RSI 阈值更宽松，止损更宽
```

---

## 5. 设计亮点

### 5.1 借鉴的优秀设计

| 设计来源 | 借鉴内容 | 应用位置 |
|---------|---------|---------|
| QUANTAXIS | 统一数据结构 | StockData 类 |
| vectorbt | 懒计算模式 | @property 缓存 |
| vectorbt | 配置驱动 | AnalysisConfig |
| finquant | 渐进式 API | analyze() 便捷函数 |

### 5.2 核心特性

1. **懒计算模式**: 技术指标和信号首次访问时计算，后续直接返回缓存
2. **配置驱动**: 所有参数通过 AnalysisConfig 配置，支持不同场景
3. **渐进式 API**: 同时提供简单和高级接口，满足不同用户需求
4. **完整集成**: 整合数据、指标、信号、风险四大模块

---

## 6. 文件清单

| 文件路径 | 说明 | 行数 |
|---------|------|------|
| skills/stock_advisor/__init__.py | 模块初始化 | ~50 |
| skills/stock_advisor/stock_data.py | 股票数据封装 | ~250 |
| skills/stock_advisor/analyzer.py | 股票分析器 | ~350 |
| tests/test_stock_analyzer.py | 单元测试 | ~200 |

---

## 7. 已知问题和改进方向

### 7.1 已知问题

无

### 7.2 改进方向

1. **数据缓存**: 可以借鉴 finquant 的二级缓存策略，添加本地文件缓存
2. **股票名称**: 可以从 API 或数据库获取，而不是硬编码
3. **报告生成**: 可以添加 report_builder.py，支持更多输出格式
4. **可视化**: 可以添加图表生成功能

---

## 8. 依赖的外部资源

| 资源 | 版本 | 用途 |
|------|------|------|
| pandas | 2.3.3 | 数据处理 |
| numpy | 2.2.6 | 数值计算 |
| pytest | 9.1.0 | 单元测试 |
| core.indicators | - | 技术指标 |
| core.signals | - | 信号系统 |
| core.risk | - | 风险控制 |

---

## 9. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本，借鉴 finquant/QUANTAXIS/vectorbt | - |
