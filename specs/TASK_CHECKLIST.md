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

### Sprint 7: 回测集成 (本周)

**SDD规格文档**: `specs/SDD_BACKTEST_INTEGRATION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 7.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_BACKTEST_INTEGRATION.md |
| 7.1 | 实现回测数据适配器 | P0 | ✅ | - | adapter.py |
| 7.2 | 实现策略适配器 | P0 | ✅ | - | adapter.py |
| 7.3 | 实现回测结果分析器 | P0 | ✅ | - | engine.py |
| 7.4 | 实现回测引擎 | P0 | ✅ | - | engine.py |
| 7.5 | 实现回测报告生成 | P1 | ✅ | - | BacktestResult.summary() |
| 7.6 | 编写回测测试 | P1 | ✅ | - | test_backtest.py (6 tests passed) |

## Phase 3: 高级功能 (当前)

**SDD规格文档**: `specs/SDD_PHASE3_ADVANCED.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 6.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE3_ADVANCED.md |
| 6.1 | 实现智能选股 Skill | P2 | ✅ | - | stock-selector |
| 6.2 | 实现报告生成 Skill | P3 | ✅ | - | stock-report |
| 6.3 | 实现模拟交易 Skill | P3 | ✅ | - | stock-simulator |
| 6.4 | 编写测试 | P1 | ✅ | - | test_advanced.py (21 tests passed) |

## Phase 4: 智能投顾系统 (待开发)

**SDD规格文档**: `specs/SDD_PHASE4_ADVISOR.md` ✅ 已完成

### Sprint 8: 基本面和市场分析 (本周)

**SDD规格文档**: `specs/SDD_PHASE4_ADVISOR.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 8.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE4_ADVISOR.md |
| 8.1 | 实现基本面分析器 | P0 | ✅ | - | stock-fundamental/analyzer.py |
| 8.2 | 实现市场分析器 | P0 | ✅ | - | stock-market/analyzer.py |
| 8.3 | 实现股票推荐器 | P0 | ✅ | - | stock-recommender/recommender.py |
| 8.4 | 编写测试 | P1 | ✅ | - | test_phase4.py (29 tests passed) |

### Sprint 9: 长短线策略 (待开发)

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 9.1 | 实现长线策略 | P0 | ⬜ | - | stock-strategy/long_term.py |
| 9.2 | 实现短线策略 | P0 | ⬜ | - | stock-strategy/short_term.py |
| 9.3 | 策略回测验证 | P1 | ⬜ | - | |
| 9.4 | 编写测试 | P1 | ⬜ | - | |

## Phase 13: 最小 CLI 启动脚本 (当前)

**SDD规格文档**: `specs/SDD_PHASE13_MINIMAL_CLI_STARTUP.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 13.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE13_MINIMAL_CLI_STARTUP.md |
| 13.1 | 实现 CLI 启动入口 | P0 | ✅ | - | core/cli.py |
| 13.2 | 增加脚本执行入口 | P0 | ✅ | - | tools/agent-api.py |
| 13.3 | 注册安装后命令 | P0 | ✅ | - | stock-agent-api |
| 13.4 | 轻量验证 | P1 | ⬜ | - | 待执行 |

## Phase 14: 最小 API 联调用例 (当前)

**SDD规格文档**: `specs/SDD_PHASE14_MINIMAL_API_EXAMPLE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 14.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE14_MINIMAL_API_EXAMPLE.md |
| 14.1 | 实现联调用例脚本 | P0 | ✅ | - | examples/api_demo.py |
| 14.2 | 覆盖健康检查 | P0 | ✅ | - | /health |
| 14.3 | 覆盖决策调用 | P0 | ✅ | - | /decision |
| 14.4 | 可选反馈调用 | P1 | ✅ | - | /feedback |
| 14.5 | 轻量验证 | P1 | ⬜ | - | 待执行 |

## Phase 15: 最小运行说明 (当前)

**SDD规格文档**: `specs/SDD_PHASE15_MINIMAL_RUNBOOK.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 15.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE15_MINIMAL_RUNBOOK.md |
| 15.1 | 更新运行说明 | P0 | ✅ | - | README_QUANT.md |
| 15.2 | 轻量验证 | P1 | ⬜ | - | 待执行 |

## Phase 16: 最小 curl 使用示例 (当前)

**SDD规格文档**: `specs/SDD_PHASE16_CURL_USAGE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 16.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE16_CURL_USAGE.md |
| 16.1 | 更新 README curl 示例 | P0 | ✅ | - | README_QUANT.md |
| 16.2 | 轻量验证 | P1 | ⬜ | - | 待执行 |

## Phase 17: 东方财富真实联调脚本 (当前)

**SDD规格文档**: `specs/SDD_PHASE17_EASTMONEY_LIVE_CHECK.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 17.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE17_EASTMONEY_LIVE_CHECK.md |
| 17.1 | 实现真实联调脚本 | P0 | ✅ | - | examples/eastmoney_live_check.py |
| 17.2 | 支持 cookie 注入 | P0 | ✅ | - | `--cookie` / `--cookie-file` / `EASTMONEY_COOKIE` |
| 17.3 | 历史行情验证 | P0 | ✅ | - | get_stock_hist / fetch_stock_hist_governed |
| 17.4 | 实时行情验证 | P0 | ✅ | - | get_realtime_quotes |
| 17.5 | 用户本机验证 | P1 | ✅ | - | 已验证通过 |

## Phase 18: 智能体能力目录与自动路由升级 (当前)

**SDD规格文档**: `specs/SDD_PHASE18_AGENT_CAPABILITY_DIRECTORY.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 18.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE18_AGENT_CAPABILITY_DIRECTORY.md |
| 18.1 | 实现能力目录数据结构 | P0 | ✅ | - | `core/agent/capability_directory.py` |
| 18.2 | 注册能力目录工具入口 | P0 | ✅ | - | `list_project_capabilities` |
| 18.3 | 扩展意图路由规则 | P0 | ✅ | - | 能力目录类意图 |
| 18.4 | 扩展客户端与编排器入口 | P0 | ✅ | - | `ArkAgentClient` / `StockOrchestrator` / `StockAgentRuntime` |
| 18.5 | 统一输出与分类标记 | P1 | ✅ | - | `knowledge_base` / `workflow` |
| 18.6 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE18_AGENT_CAPABILITY_DIRECTORY.md |
| 18.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 19: 盘前概览标准工作流 (当前)

**SDD规格文档**: `specs/SDD_PHASE19_PRE_MARKET_OVERVIEW.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 19.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE19_PRE_MARKET_OVERVIEW.md |
| 19.1 | 新增盘前概览模板 | P0 | ✅ | - | `core/agent/workflow_templates.py` |
| 19.2 | 扩展协作规划支持盘前健康检查 | P0 | ✅ | - | `core/agent/collaboration.py` |
| 19.3 | 扩展意图路由识别盘前概览 | P0 | ✅ | - | `core/agent/routing.py` |
| 19.4 | 扩展能力目录推荐路径 | P1 | ✅ | - | `core/agent/capability_directory.py` |
| 19.5 | 确认统一输出与审计字段 | P1 | ✅ | - | 复用现有 schema |
| 19.6 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE19_PRE_MARKET_OVERVIEW.md |
| 19.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 20: 组合体检标准工作流 (当前)

**SDD规格文档**: `specs/SDD_PHASE20_PORTFOLIO_HEALTH_CHECK.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 20.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE20_PORTFOLIO_HEALTH_CHECK.md |
| 20.1 | 新增组合体检模板 | P0 | ✅ | - | `core/agent/workflow_templates.py` |
| 20.2 | 扩展协作规划支持体检验证 | P0 | ✅ | - | `core/agent/collaboration.py` |
| 20.3 | 扩展意图路由识别组合体检 | P0 | ✅ | - | `core/agent/routing.py` |
| 20.4 | 扩展能力目录推荐路径 | P1 | ✅ | - | `core/agent/capability_directory.py` |
| 20.5 | 确认统一输出与审计字段 | P1 | ✅ | - | 复用现有 schema |
| 20.6 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE20_PORTFOLIO_HEALTH_CHECK.md |
| 20.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 21: 复盘报告标准工作流 (当前)

**SDD规格文档**: `specs/SDD_PHASE21_REVIEW_REPORT.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 21.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE21_REVIEW_REPORT.md |
| 21.1 | 新增复盘报告模板 | P0 | ✅ | - | `core/agent/workflow_templates.py` |
| 21.2 | 扩展协作规划支持复盘回放 | P0 | ✅ | - | `core/agent/collaboration.py` |
| 21.3 | 扩展意图路由识别复盘报告 | P0 | ✅ | - | `core/agent/routing.py` |
| 21.4 | 扩展能力目录推荐路径 | P1 | ✅ | - | `core/agent/capability_directory.py` |
| 21.5 | 确认统一输出与审计字段 | P1 | ✅ | - | 复用现有 schema |
| 21.6 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE21_REVIEW_REPORT.md |
| 21.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 22: 标准工作流总入口与统一输出收口 (当前)

**SDD规格文档**: `specs/SDD_PHASE22_STANDARD_WORKFLOW_PORTAL.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 22.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE22_STANDARD_WORKFLOW_PORTAL.md |
| 22.1 | 扩展路由识别标准工作流总入口 | P0 | ✅ | - | `core/agent/routing.py` |
| 22.2 | 扩展编排器支持统一决策入口路由 | P0 | ✅ | - | `core/orchestrator.py` |
| 22.3 | 扩展运行时与客户端入口推荐 | P1 | ✅ | - | `core/agent/client.py` / `core/agent/runtime.py` |
| 22.4 | 修正统一输出分类语义 | P1 | ✅ | - | `core/agent/serialization.py` / `core/agent/tools.py` |
| 22.5 | 扩展能力目录推荐路径 | P1 | ✅ | - | `core/agent/capability_directory.py` |
| 22.6 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE22_STANDARD_WORKFLOW_PORTAL.md |
| 22.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 23: 最小反馈闭环入口 (当前)

**SDD规格文档**: `specs/SDD_PHASE23_MINIMAL_FEEDBACK_LOOP.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 23.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE23_MINIMAL_FEEDBACK_LOOP.md |
| 23.1 | 允许反馈入口回推 workflow_id | P0 | ✅ | - | `core/agent/session.py` |
| 23.2 | 扩展编排器反馈方法 | P0 | ✅ | - | `core/orchestrator.py` |
| 23.3 | 扩展 HTTP API 反馈请求 | P0 | ✅ | - | `core/api_server.py` |
| 23.4 | 扩展运行时与工具入口 | P1 | ✅ | - | `core/agent/runtime.py` / `core/agent/tools.py` |
| 23.5 | 更新反馈联调用例 | P1 | ✅ | - | `examples/api_demo.py` |
| 23.6 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE23_MINIMAL_FEEDBACK_LOOP.md |
| 23.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 24: 最小反馈统计入口 (当前)

**SDD规格文档**: `specs/SDD_PHASE24_MINIMAL_FEEDBACK_STATS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 24.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE24_MINIMAL_FEEDBACK_STATS.md |
| 24.1 | 扩展编排器反馈统计入口 | P0 | ✅ | - | `core/orchestrator.py` |
| 24.2 | 扩展 HTTP API 统计接口 | P0 | ✅ | - | `core/api_server.py` |
| 24.3 | 扩展联调用例支持统计查看 | P1 | ✅ | - | `examples/api_demo.py` |
| 24.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 24.5 | 编写归档文档 | P1 | ✅ | - | ARCHIVE_PHASE24_MINIMAL_FEEDBACK_STATS.md |
| 24.6 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 25: 最小反馈洞察入口 (当前)

**SDD规格文档**: `specs/SDD_PHASE25_FEEDBACK_INSIGHTS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 25.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE25_FEEDBACK_INSIGHTS.md |
| 25.1 | 扩展会话存储洞察方法 | P0 | ✅ | - | `core/agent/session.py` |
| 25.2 | 扩展编排器洞察入口 | P0 | ✅ | - | `core/orchestrator.py` |
| 25.3 | 扩展 HTTP API 洞察接口 | P0 | ✅ | - | `core/api_server.py` |
| 25.4 | 扩展运行时和工具入口 | P1 | ✅ | - | `core/agent/runtime.py` / `core/agent/tools.py` |
| 25.5 | 更新联调用例 | P1 | ✅ | - | `examples/api_demo.py` |
| 25.6 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 25.7 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE25_FEEDBACK_INSIGHTS.md` |
| 25.8 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 26: 统一决策摘要收紧 (当前)

**SDD规格文档**: `specs/SDD_PHASE26_DECISION_OUTPUT_SHARPENING.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 26.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE26_DECISION_OUTPUT_SHARPENING.md |
| 26.1 | 强化统一决策返回摘要 | P0 | ✅ | - | `core/orchestrator.py` |
| 26.2 | 暴露简化摘要运行时入口 | P0 | ✅ | - | `core/agent/runtime.py` |
| 26.3 | 收紧智能体输出提示 | P1 | ✅ | - | `core/agent/client.py` |
| 26.4 | 更新联调用例展示 | P1 | ✅ | - | `examples/api_demo.py` |
| 26.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 26.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE26_DECISION_OUTPUT_SHARPENING.md` |
| 26.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 27: 统计与洞察摘要标准化 (当前)

**SDD规格文档**: `specs/SDD_PHASE27_INSIGHT_SUMMARY_STANDARDIZATION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 27.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE27_INSIGHT_SUMMARY_STANDARDIZATION.md |
| 27.1 | 扩展统计摘要卡片 | P0 | ✅ | - | `core/agent/session.py` |
| 27.2 | 扩展洞察摘要卡片 | P0 | ✅ | - | `core/agent/session.py` |
| 27.3 | 更新联调用例展示 | P1 | ✅ | - | `examples/api_demo.py` |
| 27.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 27.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE27_INSIGHT_SUMMARY_STANDARDIZATION.md` |
| 27.6 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 28: 自选股日常决策清单 MVP (当前)

**SDD规格文档**: `specs/SDD_PHASE28_DAILY_WATCHLIST_DECISION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 28.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE28_DAILY_WATCHLIST_DECISION.md |
| 28.1 | 新增 watchlist 配置样例 | P0 | ✅ | - | `config/watchlist.json` |
| 28.2 | 实现批量决策脚本 | P0 | ✅ | - | `examples/daily_watchlist_decision.py` |
| 28.3 | 复用现有个股分析编排 | P0 | ✅ | - | `core/orchestrator.py` |
| 28.4 | 增加分组与摘要输出 | P0 | ✅ | - | `examples/daily_watchlist_decision.py` |
| 28.5 | 增加可选 JSON 导出 | P1 | ✅ | - | `examples/daily_watchlist_decision.py` |
| 28.6 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 28.7 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE28_DAILY_WATCHLIST_DECISION.md` |
| 28.8 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 29: 自选股数据健康透明化 (当前)

**SDD规格文档**: `specs/SDD_PHASE29_WATCHLIST_DATA_HEALTH.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 29.0 | 编写 SDD 规格文档 | P0 | ✅ | - | SDD_PHASE29_WATCHLIST_DATA_HEALTH.md |
| 29.1 | 实现 watchlist 数据健康脚本 | P0 | ✅ | - | `examples/watchlist_data_health.py` |
| 29.2 | 复用行情治理入口 | P0 | ✅ | - | `core/data/eastmoney_api.py` |
| 29.3 | 复用基本面治理入口 | P0 | ✅ | - | `core/data/real_provider.py` |
| 29.4 | 增加分级输出与 JSON 导出 | P1 | ✅ | - | `examples/watchlist_data_health.py` |
| 29.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 29.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE29_WATCHLIST_DATA_HEALTH.md` |
| 29.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 30: 自选股持仓上下文接入 (当前)

**SDD规格文档**: `specs/SDD_PHASE30_WATCHLIST_PORTFOLIO_CONTEXT.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 30.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE30_WATCHLIST_PORTFOLIO_CONTEXT.md` |
| 30.1 | 新增持仓配置样例 | P0 | ✅ | - | `config/portfolio.json` |
| 30.2 | 扩展日常清单脚本读取持仓 | P0 | ✅ | - | `examples/daily_watchlist_decision.py` |
| 30.3 | 增加持仓摘要与仓位占用 | P0 | ✅ | - | `examples/daily_watchlist_decision.py` |
| 30.4 | 增加持仓相关运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 30.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE30_WATCHLIST_PORTFOLIO_CONTEXT.md` |
| 30.6 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 31: 自选股日常流程统一入口 (当前)

**SDD规格文档**: `specs/SDD_PHASE31_DAILY_FLOW_UNIFICATION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 31.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE31_DAILY_FLOW_UNIFICATION.md` |
| 31.1 | 提炼自选股共享工具 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 31.2 | 实现统一日常入口脚本 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 31.3 | 复用健康预检和持仓上下文 | P0 | ✅ | - | `examples/watchlist_data_health.py` / `examples/daily_watchlist_decision.py` |
| 31.4 | 增加统一运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 31.5 | 编写归档文档 | P1 | ⬜ | - | 记录统一入口结果 |
| 31.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀统一入口模板 |

## Phase 32: 自选股日更摘要压缩 (当前)

**SDD规格文档**: `specs/SDD_PHASE32_DAILY_SUMMARY_COMPRESSION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 32.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE32_DAILY_SUMMARY_COMPRESSION.md` |
| 32.1 | 增加日更摘要构建逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 32.2 | 增加首屏摘要输出 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 32.3 | 增加摘要 JSON 字段 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 32.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 32.5 | 编写归档文档 | P1 | ⬜ | - | 记录摘要压缩结果 |
| 32.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀摘要模板 |

## Phase 33: 自选股日更报告格式化 (当前)

**SDD规格文档**: `specs/SDD_PHASE33_DAILY_REPORT_FORMAT.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 33.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE33_DAILY_REPORT_FORMAT.md` |
| 33.1 | 增加日更报告构建逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 33.2 | 增加报告文本输出 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 33.3 | 增加报告 JSON 字段 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 33.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 33.5 | 编写归档文档 | P1 | ⬜ | - | 记录报告格式化结果 |
| 33.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀报告模板 |

## Phase 34: 自选股日更报告对比 (当前)

**SDD规格文档**: `specs/SDD_PHASE34_DAILY_REPORT_COMPARISON.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 34.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE34_DAILY_REPORT_COMPARISON.md` |
| 34.1 | 增加日报对比输入参数 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 34.2 | 增加对比构建逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 34.3 | 增加对比输出与 JSON 字段 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 34.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 34.5 | 编写归档文档 | P1 | ⬜ | - | 记录日报对比结果 |
| 34.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀对比模板 |

## Phase 35: 自选股周报模板 (当前)

**SDD规格文档**: `specs/SDD_PHASE35_WEEKLY_REPORT_TEMPLATE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 35.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE35_WEEKLY_REPORT_TEMPLATE.md` |
| 35.1 | 增加周报聚合输入参数 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 35.2 | 增加周报构建逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 35.3 | 增加周报输出与 JSON 字段 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 35.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 35.5 | 编写归档文档 | P1 | ⬜ | - | 记录周报模板结果 |
| 35.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀周报模板 |

## Phase 36: 自选股阶段报告模板 (当前)

**SDD规格文档**: `specs/SDD_PHASE36_STAGE_REPORT_TEMPLATE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 36.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE36_STAGE_REPORT_TEMPLATE.md` |
| 36.1 | 增加阶段报告输入参数 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 36.2 | 增加阶段报告构建逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 36.3 | 增加阶段报告输出与 JSON 字段 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 36.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 36.5 | 编写归档文档 | P1 | ⬜ | - | 记录阶段报告模板结果 |
| 36.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀阶段报告模板 |

## Phase 37: 自选股复盘留档包 (当前)

**SDD规格文档**: `specs/SDD_PHASE37_REVIEW_ARCHIVE_PACKAGE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 37.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE37_REVIEW_ARCHIVE_PACKAGE.md` |
| 37.1 | 增加留档包输入参数 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 37.2 | 增加留档包构建逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 37.3 | 增加留档包输出与 JSON 字段 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 37.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 37.5 | 编写归档文档 | P1 | ⬜ | - | 记录留档包结果 |
| 37.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀留档包模板 |

## Phase 38: 复盘留档包结构清理 (当前)

**SDD规格文档**: `specs/SDD_PHASE38_ARCHIVE_PACKAGE_CLEANUP.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 38.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE38_ARCHIVE_PACKAGE_CLEANUP.md` |
| 38.1 | 清理留档包标题层级 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 38.2 | 统一留档包字段命名 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 38.3 | 重构留档包输出结构 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 38.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 38.5 | 编写归档文档 | P1 | ⬜ | - | 记录结构清理结果 |
| 38.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀统一结构 |

## Phase 39: 报告标题与摘要归一化 (当前)

**SDD规格文档**: `specs/SDD_PHASE39_REPORT_TITLE_NORMALIZATION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 39.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE39_REPORT_TITLE_NORMALIZATION.md` |
| 39.1 | 统一周报标题表达 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 39.2 | 统一阶段报告标题表达 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 39.3 | 统一留档包总览表达 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 39.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 39.5 | 编写归档文档 | P1 | ⬜ | - | 记录标题归一化结果 |
| 39.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀统一命名 |

## Phase 40: 自选股日常运行固化与自动留档 (当前)

**SDD规格文档**: `specs/SDD_PHASE40_DAILY_RUN_ARTIFACTS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 40.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE40_DAILY_RUN_ARTIFACTS.md` |
| 40.1 | 增加日常归档目录参数 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 40.2 | 增加 Markdown 导出逻辑 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 40.3 | 增加 latest 指针更新逻辑 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 40.4 | 保留 JSON 与日常目录并存 | P1 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 40.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 40.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE40_DAILY_RUN_ARTIFACTS.md` |
| 40.7 | 更新知识库与任务清单 | P1 | ✅ | - | 沉淀日常留档规范 |

## Phase 41: 自选股日常留档查看入口 (当前)

**SDD规格文档**: `specs/SDD_PHASE41_DAILY_ARCHIVE_VIEWER.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 41.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE41_DAILY_ARCHIVE_VIEWER.md` |
| 41.1 | 增加日常留档查看脚本 | P0 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 41.2 | 增加 latest 回退读取逻辑 | P0 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 41.3 | 增加 Markdown/JSON 可选展示 | P1 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 41.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 41.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE41_DAILY_ARCHIVE_VIEWER.md` |
| 41.6 | 更新知识库与任务清单 | P1 | ✅ | - | 沉淀查看入口规范 |

## Phase 42: 自选股日常生产运行守门与一键执行 (当前)

**SDD规格文档**: `specs/SDD_PHASE42_DAILY_PRODUCTION_RUNNER.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 42.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE42_DAILY_PRODUCTION_RUNNER.md` |
| 42.1 | 增加一键运行脚本 | P0 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 42.2 | 增加预检与状态判定 | P0 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 42.3 | 增加自动执行与留档编排 | P0 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 42.4 | 增加 run_status 输出 | P1 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 42.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 42.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE42_DAILY_PRODUCTION_RUNNER.md` |
| 42.7 | 更新知识库与任务清单 | P1 | ✅ | - | 沉淀生产运行守门规范 |

## Phase 43: 东方财富 Cookie 配置一致性收口 (当前)

**SDD规格文档**: `specs/SDD_PHASE43_EASTMONEY_COOKIE_CONSISTENCY.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 43.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE43_EASTMONEY_COOKIE_CONSISTENCY.md` |
| 43.1 | 统一东方财富 cookie 读取路径 | P0 | ✅ | - | `eastmoney_config.py` |
| 43.2 | 增加 cookie 来源诊断 | P0 | ✅ | - | `examples/eastmoney_live_check.py` |
| 43.3 | 更新日常运行的 cookie 提示 | P1 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 43.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 43.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE43_EASTMONEY_COOKIE_CONSISTENCY.md` |
| 43.6 | 更新知识库与任务清单 | P1 | ✅ | - | 沉淀 cookie 默认路径 |

## Phase 44: 东方财富历史行情失败诊断与回退可读化 (当前)

**SDD规格文档**: `specs/SDD_PHASE44_EASTMONEY_HISTORY_DIAGNOSIS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 44.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE44_EASTMONEY_HISTORY_DIAGNOSIS.md` |
| 44.1 | 增强历史行情失败分类 | P0 | ✅ | - | `core/data/eastmoney_api.py` |
| 44.2 | 增强治理快照诊断信息 | P0 | ✅ | - | `core/data/eastmoney_api.py` |
| 44.3 | 增强联调脚本输出 | P1 | ✅ | - | `examples/eastmoney_live_check.py` |
| 44.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 44.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE44_EASTMONEY_HISTORY_DIAGNOSIS.md` |
| 44.6 | 更新知识库与任务清单 | P1 | ✅ | - | 沉淀失败诊断规则 |

## Phase 45: 东方财富历史行情失败回归测试固定 (当前)

**SDD规格文档**: `specs/SDD_PHASE45_EASTMONEY_HISTORY_REGRESSION_TEST.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 45.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE45_EASTMONEY_HISTORY_REGRESSION_TEST.md` |
| 45.1 | 增加历史行情失败回归测试 | P0 | ✅ | - | `tests/test_eastmoney_history_diagnosis.py` |
| 45.2 | 验证 request 失败语义 | P0 | ✅ | - | `tests/test_eastmoney_history_diagnosis.py` |
| 45.3 | 验证 fallback 输出 | P1 | ✅ | - | `tests/test_eastmoney_history_diagnosis.py` |
| 45.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 45.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE45_EASTMONEY_HISTORY_REGRESSION_TEST.md` |
| 45.6 | 更新知识库与任务清单 | P1 | ✅ | - | 沉淀失败诊断回归 |

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
| 0.12 | 回测集成模块 | 2026-06-14 | BacktestEngine/Adapter/Result (6 tests passed) |
| 0.13 | 智能选股模块 | 2026-06-14 | StockScreener/screen_stocks |
| 0.14 | 报告生成模块 | 2026-06-14 | ReportGenerator |
| 0.15 | 模拟交易模块 | 2026-06-14 | TradingSimulator (21 tests passed) |
| 0.16 | 基本面分析模块 | 2026-06-14 | FundamentalAnalyzer (29 tests passed) |
| 0.17 | 市场分析模块 | 2026-06-14 | MarketAnalyzer |
| 0.18 | 股票推荐模块 | 2026-06-14 | StockRecommender (长线/短线/风险匹配) |
| 0.19 | 数据源健康摘要统一展示 | 2026-06-21 | 统一 watchlist 预检与日常流程健康口径 |

## Phase 46: 数据源健康摘要统一展示 (当前)

**SDD规格文档**: `specs/SDD_PHASE46_DATA_SOURCE_HEALTH_SUMMARY.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 46.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE46_DATA_SOURCE_HEALTH_SUMMARY.md` |
| 46.1 | 提取统一数据源健康摘要函数 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 46.2 | 复用健康摘要到数据健康预检 | P0 | ✅ | - | `examples/watchlist_data_health.py` |
| 46.3 | 复用健康摘要到日常统一流程 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 46.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 46.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE46_DATA_SOURCE_HEALTH_SUMMARY.md` |
| 46.6 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 47: 自选股日常决策反馈闭环 (当前)

**SDD规格文档**: `specs/SDD_PHASE47_DAILY_DECISION_FEEDBACK_LOOP.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 47.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE47_DAILY_DECISION_FEEDBACK_LOOP.md` |
| 47.1 | 新增日常反馈脚本 | P0 | ✅ | - | `examples/daily_watchlist_feedback.py` |
| 47.2 | 支持 latest 留档定位 | P0 | ✅ | - | `examples/daily_watchlist_feedback.py` |
| 47.3 | 支持 JSONL 追加写入 | P0 | ✅ | - | `examples/daily_watchlist_feedback.py` |
| 47.4 | 查看器展示反馈摘要 | P1 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 47.5 | 日常运行状态带反馈计数 | P1 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 47.6 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 47.7 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE47_DAILY_DECISION_FEEDBACK_LOOP.md` |
| 47.8 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 48: 自选股日常反馈统计洞察 (当前)

**SDD规格文档**: `specs/SDD_PHASE48_DAILY_FEEDBACK_INSIGHTS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 48.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE48_DAILY_FEEDBACK_INSIGHTS.md` |
| 48.1 | 新增反馈洞察脚本 | P0 | ✅ | - | `examples/daily_watchlist_feedback_insights.py` |
| 48.2 | 统计动作分布 | P0 | ✅ | - | `examples/daily_watchlist_feedback_insights.py` |
| 48.3 | 统计股票频次 | P0 | ✅ | - | `examples/daily_watchlist_feedback_insights.py` |
| 48.4 | 支持 JSON 导出 | P1 | ✅ | - | `examples/daily_watchlist_feedback_insights.py` |
| 48.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 48.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE48_DAILY_FEEDBACK_INSIGHTS.md` |
| 48.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 49: 自选股日常回看流程收口 (当前)

**SDD规格文档**: `specs/SDD_PHASE49_DAILY_REVIEW_FLOW.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 49.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE49_DAILY_REVIEW_FLOW.md` |
| 49.1 | 新增日常回看脚本 | P0 | ✅ | - | `examples/daily_watchlist_review.py` |
| 49.2 | 串起 latest 留档查看 | P0 | ✅ | - | `examples/daily_watchlist_review.py` |
| 49.3 | 串起反馈洞察查看 | P0 | ✅ | - | `examples/daily_watchlist_review.py` |
| 49.4 | 支持 JSON 细节输出 | P1 | ✅ | - | `examples/daily_watchlist_review.py` |
| 49.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 49.6 | 编写归档文档 | P1 | ⬜ | - | 记录回看流程结果 |
| 49.7 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀回看流程模板 |

## Phase 50: 自选股日常显示层统一 (当前)

**SDD规格文档**: `specs/SDD_PHASE50_DAILY_DISPLAY_UNIFICATION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 50.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE50_DAILY_DISPLAY_UNIFICATION.md` |
| 50.1 | 抽出共享显示辅助工具 | P0 | ✅ | - | `examples/daily_watchlist_display.py` |
| 50.2 | 统一留档查看器摘要 | P0 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 50.3 | 统一反馈洞察摘要 | P0 | ✅ | - | `examples/daily_watchlist_feedback_insights.py` |
| 50.4 | 统一回看流程摘要 | P0 | ✅ | - | `examples/daily_watchlist_review.py` |
| 50.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 50.6 | 编写归档文档 | P1 | ⬜ | - | 记录显示层统一结果 |
| 50.7 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀显示层统一模板 |

## Phase 51: 自选股日常投产验收 (当前)

**SDD规格文档**: `specs/SDD_PHASE51_DAILY_ACCEPTANCE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 51.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE51_DAILY_ACCEPTANCE.md` |
| 51.1 | 新增投产验收脚本 | P0 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 51.2 | 检查关键文件存在 | P0 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 51.3 | 检查关键入口可运行 | P0 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 51.4 | 支持 JSON 导出 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 51.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 51.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE51_DAILY_ACCEPTANCE.md` |
| 51.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 52: 自选股默认日常工作流收口 (当前)

**SDD规格文档**: `specs/SDD_PHASE52_DAILY_WORKFLOW_FLOW.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 52.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE52_DAILY_WORKFLOW_FLOW.md` |
| 52.1 | 新增默认日常工作流脚本 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` |
| 52.2 | 串起 daily_run | P0 | ✅ | - | `examples/daily_watchlist_flow.py` |
| 52.3 | 串起 review | P0 | ✅ | - | `examples/daily_watchlist_flow.py` |
| 52.4 | 串起 acceptance | P0 | ✅ | - | `examples/daily_watchlist_flow.py` |
| 52.5 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 52.6 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE52_DAILY_WORKFLOW_FLOW.md` |
| 52.7 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 53: 自选股日常降级原因分层 (当前)

**SDD规格文档**: `specs/SDD_PHASE53_DAILY_DEGRADATION_DIAGNOSIS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 53.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE53_DAILY_DEGRADATION_DIAGNOSIS.md` |
| 53.1 | 扩展共享健康摘要诊断字段 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 53.2 | 增加降级原因分层规则 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 53.3 | 汇总日常总览降级原因统计 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 53.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 53.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE53_DAILY_DEGRADATION_DIAGNOSIS.md` |
| 53.6 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 54: 自选股日常诊断口径贯通 (当前)

**SDD规格文档**: `specs/SDD_PHASE54_DAILY_DIAGNOSIS_FLOW.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 54.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE54_DAILY_DIAGNOSIS_FLOW.md` |
| 54.1 | 默认工作流输出诊断载荷 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` |
| 54.2 | 投产验收检查诊断摘要 | P0 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 54.3 | 日常统一流程补充诊断行 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 54.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 54.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE54_DAILY_DIAGNOSIS_FLOW.md` |
| 54.6 | 更新知识库与任务清单 | P1 | ✅ | - | 已更新 |

## Phase 55: 自选股日常诊断摘要模板化 (当前)

**SDD规格文档**: `specs/SDD_PHASE55_DAILY_DIAGNOSIS_TEMPLATE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 55.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE55_DAILY_DIAGNOSIS_TEMPLATE.md` |
| 55.1 | 新增日常诊断摘要模板 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 55.2 | 让日常统一流程复用模板 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 55.3 | 更新运行说明 | P1 | ⬜ | - | `README_QUANT.md` |
| 55.4 | 编写归档文档 | P1 | ⬜ | - | 记录摘要模板化结果 |
| 55.5 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀公共模板接口 |

## Phase 56: 自选股日常诊断证据视图 (当前)

**SDD规格文档**: `specs/SDD_PHASE56_DAILY_DIAGNOSIS_EVIDENCE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 56.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE56_DAILY_DIAGNOSIS_EVIDENCE.md` |
| 56.1 | 新增诊断证据视图 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 56.2 | 让投产验收消费证据视图 | P0 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 56.3 | 更新运行说明 | P1 | ⬜ | - | `README_QUANT.md` |
| 56.4 | 编写归档文档 | P1 | ⬜ | - | 记录证据视图收口结果 |
| 56.5 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀验收证据模板 |

## Phase 57: 自选股日常诊断回看对齐 (当前)

**SDD规格文档**: `specs/SDD_PHASE57_DAILY_DIAGNOSIS_REVIEW_ALIGN.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 57.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE57_DAILY_DIAGNOSIS_REVIEW_ALIGN.md` |
| 57.1 | 留档查看入口展示诊断证据 | P0 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 57.2 | 更新运行说明 | P1 | ⬜ | - | `README_QUANT.md` |
| 57.3 | 编写归档文档 | P1 | ⬜ | - | 记录回看对齐结果 |
| 57.4 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀回看对齐模板 |

## Phase 58: 自选股日常诊断收口包 (当前)

**SDD规格文档**: `specs/SDD_PHASE58_DAILY_DIAGNOSIS_BUNDLE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 58.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE58_DAILY_DIAGNOSIS_BUNDLE.md` |
| 58.1 | 新增诊断收口包脚本 | P0 | ✅ | - | `examples/daily_watchlist_diagnosis_bundle.py` |
| 58.2 | 聚合日常摘要与证据视图 | P0 | ✅ | - | `examples/daily_watchlist_diagnosis_bundle.py` |
| 58.3 | 聚合验收状态 | P0 | ✅ | - | `examples/daily_watchlist_diagnosis_bundle.py` |
| 58.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 58.5 | 编写归档文档 | P1 | ⬜ | - | 记录收口包结果 |
| 58.6 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀收口包模板 |

## Phase 59: 自选股日常诊断路径说明 (当前)

**SDD规格文档**: `specs/SDD_PHASE59_DAILY_DIAGNOSIS_PATH.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 59.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE59_DAILY_DIAGNOSIS_PATH.md` |
| 59.1 | 编写诊断路径说明文档 | P0 | ✅ | - | `README_QUANT.md` |
| 59.2 | 更新运行说明指向路径说明 | P1 | ✅ | - | `README_QUANT.md` |
| 59.3 | 编写归档文档 | P1 | ⬜ | - | 记录路径说明结果 |
| 59.4 | 更新知识库与任务清单 | P1 | ⬜ | - | 沉淀路径说明 |

## Phase 60: 自选股日常投产质量门禁 (下一阶段)

**SDD规格文档**: `specs/SDD_PHASE60_DAILY_PRODUCTION_GATE.md` ✅ 已完成

**阶段路线图**: `specs/NEXT_STAGE_DEVELOPMENT_ROADMAP.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 60.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE60_DAILY_PRODUCTION_GATE.md` |
| 60.1 | 写入下一阶段开发路线图 | P0 | ✅ | - | `specs/NEXT_STAGE_DEVELOPMENT_ROADMAP.md` |
| 60.2 | 新增门禁构建函数 | P0 | ✅ | - | 生成 `production_gate` |
| 60.3 | 在默认日常流程接入门禁 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` |
| 60.4 | 在诊断收口包展示门禁 | P0 | ✅ | - | `examples/daily_watchlist_diagnosis_bundle.py` |
| 60.5 | 输出门禁终端摘要 | P1 | ✅ | - | 显示 `pass / warn / block` |
| 60.6 | 更新 README 使用说明 | P1 | ✅ | - | 每天优先查看投产门禁 |
| 60.7 | 轻量验证门禁输出 | P1 | ✅ | - | 已完成语法与分支验证 |
| 60.8 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE60_DAILY_PRODUCTION_GATE.md` |
| 60.9 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 60 已收口 |

## Phase 61: 自选股数据可信度增强 (下一阶段)

**SDD规格文档**: `specs/SDD_PHASE61_DATA_CONFIDENCE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 61.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE61_DATA_CONFIDENCE.md` |
| 61.1 | 实现统一数据可信度计算 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 61.2 | 健康摘要输出可信度字段 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 61.3 | 决策清单接入可信度门槛 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 61.4 | 门禁接入可信度依据 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 61.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE61_DATA_CONFIDENCE.md` |
| 61.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 61 已收口 |

## Phase 62: 自选股反馈效果评估 (下一阶段)

**SDD规格文档**: `specs/SDD_PHASE62_FEEDBACK_EFFECT_EVALUATION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 62.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE62_FEEDBACK_EFFECT_EVALUATION.md` |
| 62.1 | 反馈记录补充基线字段 | P0 | ✅ | - | `examples/daily_watchlist_feedback.py` |
| 62.2 | 新增反馈效果评估脚本 | P0 | ✅ | - | `examples/daily_watchlist_feedback_effects.py` |
| 62.3 | 回看入口展示反馈效果 | P0 | ✅ | - | `examples/daily_watchlist_review.py` / `examples/daily_watchlist_archive_viewer.py` |
| 62.4 | 更新运行说明 | P1 | ✅ | - | `README_QUANT.md` |
| 62.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE62_FEEDBACK_EFFECT_EVALUATION.md` |
| 62.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 62 已收口 |

## Phase 63: 自选股日常行动清单收口

**SDD规格文档**: `specs/SDD_PHASE63_DAILY_ACTION_LIST.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 63.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE63_DAILY_ACTION_LIST.md` |
| 63.1 | 实现共享行动清单构建 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 63.2 | 接入统一流程输出行动清单 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 63.3 | 接入默认日常流程和回看入口 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_review.py` / `examples/daily_watchlist_archive_viewer.py` |
| 63.4 | 接入投产验收 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 63.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE63_DAILY_ACTION_LIST.md` |
| 63.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 63 已收口 |

## Phase 64: 自选股日常行动提示语句精炼

**SDD规格文档**: `specs/SDD_PHASE64_DAILY_ACTION_HINTS.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 64.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE64_DAILY_ACTION_HINTS.md` |
| 64.1 | 为 `action_list` 增加行动提示语句 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 64.2 | 让统一流程输出更明确的行动提示 | P0 | ✅ | - | `examples/daily_watchlist_pipeline.py` |
| 64.3 | 让默认流程和留档查看展示新提示 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| 64.4 | 让投产验收检查提示语句 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 64.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE64_DAILY_ACTION_HINTS.md` |
| 64.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 64 已收口 |

## Phase 65: 自选股日常样本归因收口

**SDD规格文档**: `specs/SDD_PHASE65_SAMPLE_ATTRIBUTION.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 65.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE65_SAMPLE_ATTRIBUTION.md` |
| 65.1 | 构建样本归因块 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 65.2 | 让留档查看展示样本归因 | P0 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 65.3 | 让诊断收口包展示样本归因 | P0 | ✅ | - | `examples/daily_watchlist_diagnosis_bundle.py` |
| 65.4 | 让投产验收检查样本归因 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 65.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE65_SAMPLE_ATTRIBUTION.md` |
| 65.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 65 收口 |

## Phase 66: 自选股日常运行节奏稳定化

**SDD规格文档**: `specs/SDD_PHASE66_DAILY_RUN_CADENCE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 66.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE66_DAILY_RUN_CADENCE.md` |
| 66.1 | 构建运行节奏摘要 | P0 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 66.2 | 在运行状态中写入节奏摘要 | P0 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 66.3 | 在默认工作流和留档查看中展示节奏摘要 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| 66.4 | 在投产验收中检查节奏摘要 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 66.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE66_DAILY_RUN_CADENCE.md` |
| 66.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 66 收口 |

## Phase 67: 自选股日常提示语境联动

**SDD规格文档**: `specs/SDD_PHASE67_DAILY_PROMPT_CONTEXT_LINKAGE.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 67.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE67_DAILY_PROMPT_CONTEXT_LINKAGE.md` |
| 67.1 | 实现共享提示语境构建 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 67.2 | 在日常运行状态中写入提示语境 | P0 | ✅ | - | `examples/daily_watchlist_daily_run.py` |
| 67.3 | 在默认工作流和留档查看中展示提示语境 | P0 | ✅ | - | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| 67.4 | 在诊断收口包中展示提示语境 | P1 | ✅ | - | `examples/daily_watchlist_diagnosis_bundle.py` |
| 67.5 | 更新智能体默认提示词 | P1 | ✅ | - | `core/agent/client.py` |
| 67.6 | 在投产验收中检查提示语境 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 67.7 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE67_DAILY_PROMPT_CONTEXT_LINKAGE.md` |
| 67.8 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 67 收口 |

## Phase 68: 自选股日常回看摘要收紧

**SDD规格文档**: `specs/SDD_PHASE68_DAILY_REVIEW_BRIEF.md` ✅ 已完成

| # | 任务 | 优先级 | 状态 | 负责 | 备注 |
|---|------|--------|------|------|------|
| 68.0 | 编写 SDD 规格文档 | P0 | ✅ | - | `specs/SDD_PHASE68_DAILY_REVIEW_BRIEF.md` |
| 68.1 | 实现共享回看摘要构建 | P0 | ✅ | - | `examples/watchlist_shared.py` |
| 68.2 | 在日常回看入口展示回看摘要 | P0 | ✅ | - | `examples/daily_watchlist_review.py` |
| 68.3 | 在留档查看入口展示回看摘要 | P0 | ✅ | - | `examples/daily_watchlist_archive_viewer.py` |
| 68.4 | 在投产验收中检查回看摘要 | P1 | ✅ | - | `examples/daily_watchlist_acceptance.py` |
| 68.5 | 编写归档文档 | P1 | ✅ | - | `specs/ARCHIVE_PHASE68_DAILY_REVIEW_BRIEF.md` |
| 68.6 | 更新知识库与任务清单 | P1 | ✅ | - | Phase 68 收口 |

---

## 下一步行动

1. **当前**: 以 `production_gate` + `action_list` 作为默认日常查看顺序
2. **随后**: 以 `prompt_context` 作为日常提示词和 Skill 的共享语境
3. **再后**: 以 `review_brief` 作为回看的第一眼摘要
4. **持续**: 观察反馈效果评估是否稳定

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
