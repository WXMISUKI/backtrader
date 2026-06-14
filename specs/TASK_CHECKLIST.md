# 开发任务清单

## 当前迭代: Phase 1 - 核心基础

### 任务状态说明
- ⬜ 待开始
- 🔄 进行中
- ✅ 已完成
- ❌ 已取消

---

## Sprint 1: Skill 框架搭建 (本周)

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 1.1 | 创建 Skill 目录结构 | P0 | ✅ | - | 已完成 |
| 1.2 | 实现 Skill 基类 | P0 | ⬜ | - | |
| 1.3 | 实现 Skill 注册机制 | P0 | ⬜ | - | |
| 1.4 | 实现 Skill 加载器 | P1 | ⬜ | - | |
| 1.5 | 编写框架测试 | P1 | ⬜ | - | |

## Sprint 2: 技术指标模块 (本周)

**SDD规格文档**: `specs/SDD_INDICATORS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 2.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_INDICATORS.md |
| 2.1 | 实现 MA 指标 (SMA/EMA) | P0 | ✅ | - | trend.py |
| 2.2 | 实现 MACD 指标 | P0 | ✅ | - | trend.py |
| 2.3 | 实现 RSI 指标 | P0 | ✅ | - | oscillator.py |
| 2.4 | 实现 KDJ 指标 | P0 | ✅ | - | oscillator.py |
| 2.5 | 实现 BOLL 指标 | P1 | ✅ | - | trend.py |
| 2.6 | 实现成交量指标 | P1 | ✅ | - | volume.py |
| 2.7 | 编写指标测试 | P1 | ✅ | - | test_indicators.py (27 tests passed) |

## Sprint 3: 信号系统 (本周)

**SDD规格文档**: `specs/SDD_SIGNALS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 3.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_SIGNALS.md |
| 3.1 | 实现买入信号规则 | P0 | ✅ | - | buy_signals.py |
| 3.2 | 实现卖出信号规则 | P0 | ✅ | - | sell_signals.py |
| 3.3 | 实现信号强度计算 | P0 | ✅ | - | signal_strength.py |
| 3.4 | 实现信号聚合器 | P1 | ✅ | - | SignalGenerator 类 |
| 3.5 | 编写信号测试 | P1 | ✅ | - | test_signals.py (21 tests passed) |

## Sprint 4: 个股分析功能 (本周)

**SDD规格文档**: `specs/SDD_STOCK_ANALYZER.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 4.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_STOCK_ANALYZER.md |
| 4.1 | 实现 StockData 类 | P0 | ✅ | - | stock_data.py |
| 4.2 | 实现 StockAnalyzer 类 | P0 | ✅ | - | analyzer.py |
| 4.3 | 集成数据获取 | P0 | ✅ | - | 东方财富API |
| 4.4 | 集成指标计算 | P0 | ✅ | - | core.indicators |
| 4.5 | 集成信号生成 | P0 | ✅ | - | core.signals |
| 4.6 | 集成风险控制 | P0 | ✅ | - | core.risk |
| 4.7 | 实现 stock-advisor Skill | P0 | ✅ | - | __init__.py |
| 4.8 | 编写集成测试 | P1 | ✅ | - | test_stock_analyzer.py (18 tests passed) |

---

## Phase 2: 策略增强 (当前)

### Sprint 5: 策略框架 (本周)

**SDD规格文档**: `specs/SDD_STRATEGY_FRAMEWORK.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 5.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_STRATEGY_FRAMEWORK.md |
| 5.1 | 实现 Signal 类 | P0 | ✅ | - | base.py |
| 5.2 | 实现 Bar 类 | P0 | ✅ | - | base.py |
| 5.3 | 实现 Strategy 基类 | P0 | ✅ | - | base.py |
| 5.4 | 实现 StrategyRegistry | P0 | ✅ | - | registry.py |
| 5.5 | 实现双均线策略 | P0 | ✅ | - | ma_cross.py |
| 5.6 | 编写框架测试 | P1 | ✅ | - | test_strategies.py (31 tests passed) |

### Sprint 6: 内置策略 (本周)

**SDD规格文档**: `specs/SDD_BUILTIN_STRATEGIES.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 6.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_BUILTIN_STRATEGIES.md |
| 6.1 | 实现 MACD 策略 | P0 | ✅ | - | macd_strategy.py |
| 6.2 | 实现 RSI 策略 | P1 | ✅ | - | rsi_strategy.py |
| 6.3 | 实现布林带策略 | P1 | ✅ | - | boll_strategy.py |
| 6.4 | 实现综合策略 | P2 | ✅ | - | composite.py |
| 6.5 | 编写策略测试 | P1 | ✅ | - | test_strategies.py (47 tests passed) |

### Sprint 7: 回测集成 (第三周)

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 7.1 | 实现回测数据适配器 | P0 | ⬜ | - | |
| 7.2 | 实现策略适配器 | P0 | ⬜ | - | |
| 7.3 | 实现回测结果分析器 | P0 | ⬜ | - | |
| 7.4 | 实现参数优化器 | P2 | ⬜ | - | |
| 7.5 | 实现回测报告生成 | P1 | ⬜ | - | |
| 7.6 | 编写回测测试 | P1 | ⬜ | - | |

## Phase 3: 高级功能 (远期)

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 6.1 | 实时监控 Skill | P2 | ⬜ | - | |
| 6.2 | 智能选股 Skill | P2 | ⬜ | - | |
| 6.3 | 报告生成 Skill | P3 | ⬜ | - | |
| 6.4 | 模拟交易 | P3 | ⬜ | - | |

---

## 已完成任务归档

| # | 任务 | 完成日期 | 备注 |
|---|------|---------|------|
| 0.1 | conda 环境搭建 | 2026-06-14 | quant, Python 3.10 |
| 0.2 | backtrader 安装 | 2026-06-14 | v1.9.78.123 |
| 0.3 | akshare 安装 | 2026-06-14 | v1.18.64 |
| 0.4 | 东方财富 API 对接 | 2026-06-14 | 需 Cookie |
| 0.5 | 回测示例 | 2026-06-14 | 双均线策略 |
| 0.6 | 风险偏好配置 | 2026-06-14 | 三档风险等级 |
| 0.7 | 技术指标模块 | 2026-06-14 | 趋势/震荡/量价指标 (27 tests passed) |
| 0.8 | 信号系统模块 | 2026-06-14 | 买卖信号/强度计算/SignalGenerator (21 tests passed) |
| 0.9 | 个股分析模块 | 2026-06-14 | StockData/StockAnalyzer/analyze (18 tests passed) |
| 0.10 | 策略框架模块 | 2026-06-14 | Signal/Bar/Strategy/Registry/MACross (31 tests passed) |
| 0.11 | 内置策略模块 | 2026-06-14 | MACD/RSI/BOLL/Composite (47 tests passed) |

---

## 下一步行动

1. **立即**: 实现技术指标计算模块 (Sprint 2)
2. **本周**: 完成 Skill 框架和信号系统
3. **下周**: 完成个股分析功能
4. **验证**: 运行完整的分析流程

---

## 风险和阻塞项

| 风险/阻塞 | 影响 | 解决方案 |
|----------|------|---------|
| Cookie 过期 | 无法获取数据 | 定期更新 Cookie |
| API 限流 | 请求失败 | 添加重试机制 |
| 指标计算错误 | 信号不准 | 充分测试验证 |

---

## 依赖的外部资源

| 资源 | 用途 | 状态 |
|------|------|------|
| 东方财富 API | 数据获取 | ✅ 可用 |
| akshare | 备用数据源 | ✅ 可用 |
| TA-Lib | 技术指标 | ⬜ 待集成 |
