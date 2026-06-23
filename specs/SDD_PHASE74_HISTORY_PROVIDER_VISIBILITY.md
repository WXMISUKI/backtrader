# 软件设计规格说明 (SDD)
# Phase 74: 历史行情 provider 可见性下沉

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 74 历史行情 provider 可见性下沉 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-23 |
| 状态 | 已完成 |

---

## 1. 背景

Phase 73 已经把历史行情做成了多源路由和 cookie 刷新助手，并且在底层治理快照里记录了 `selected_provider / provider_attempts`。

但当前日常使用里，还有一个实际问题：

- 底层已经知道今天用了哪个 provider
- 但 `watchlist_data_health.py` 和 `daily_watchlist_pipeline.py` 还没有把这个结果完整下沉到可见输出里

这会让“多源路由已经生效”只停留在技术层，而不是日常决策层。

因此，本阶段只做一件事：把 provider 可见性补进日常入口、摘要和验收，不再扩展新的数据源逻辑。

---

## 2. 目标

### 2.1 总目标

让日常健康预检和统一流水线直接看见历史行情今天最终走了哪个 provider，以及尝试过哪些 provider。

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 可见性下沉 | provider 信息进入健康预检和日常流水线输出 |
| 诊断更快 | 一眼能看出今天是东财、AKShare 还是离线兜底 |
| 兼容现状 | 不改变 Phase 73 的路由行为 |
| 轻量修改 | 只改输出展示和归档，不重写路由器 |
| 可验证 | 新增最小回归测试，固定展示语义 |

---

## 3. 范围

### 3.1 纳入范围

- `build_data_health_summary` 的 provider 字段透传
- `watchlist_data_health.py` 的 provider 展示
- `daily_watchlist_pipeline.py` 的 provider 展示
- `daily_watchlist_acceptance.py` 的 provider 视图检查
- 运行说明补充
- 归档和任务清单更新

### 3.2 不纳入范围

- 新增 provider
- 修改路由优先级
- 修改 cookie 刷新 helper 的行为
- 修改 AKShare / 东财具体请求逻辑

---

## 4. 设计原则

### 4.1 不重复造路由

provider 选择已经在 Phase 73 完成，本阶段只负责把结果展示出来。

### 4.2 日常输出优先

历史行情 provider 的第一消费方是日常健康预检和统一流水线，而不是底层 debug 工具。

### 4.3 保持简洁

输出里只保留足够判断“今天谁在工作、谁失败了”的信息，不堆更多噪声字段。

---

## 5. 输出约定

### 5.1 健康摘要新增字段

建议让 `build_data_health_summary()` 输出并由上层消费：

- `history_selected_provider`
- `history_provider_attempts`

### 5.2 日常预检展示

建议在每个股票条目中补充：

- `历史 provider`
- `provider 尝试次数`
- `provider 尝试摘要`

### 5.3 流水线展示

建议在统一日报或 JSON 里补充：

- `history_selected_provider`
- `history_provider_attempts`
- `history_provider_summary`

---

## 6. 验收标准

- `watchlist_data_health.py` 能看见 provider
- `daily_watchlist_pipeline.py` 的条目和 JSON 能看见 provider
- `daily_watchlist_acceptance.py` 能检查 provider 字段存在
- 现有门禁、反馈和回看链路不受影响

---

## 7. 任务拆分

### 7.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 74.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 7.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 74.1 | 透传历史 provider 到健康摘要 | P0 | ✅ | `examples/watchlist_shared.py` |
| 74.2 | 在健康预检中展示 provider | P0 | ✅ | `examples/watchlist_data_health.py` |
| 74.3 | 在日常流水线中展示 provider | P0 | ✅ | `examples/daily_watchlist_pipeline.py` |
| 74.4 | 在投产验收中检查 provider | P1 | ✅ | `examples/daily_watchlist_acceptance.py` |
| 74.5 | 增加最小回归测试 | P0 | ✅ | `tests/test_history_provider_visibility.py` |
| 74.6 | 更新运行说明 | P1 | ✅ | `README_QUANT.md` |

### 7.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 74.7 | 编写归档文档 | P1 | ✅ | 记录 provider 可见性结果 |
| 74.8 | 更新路线图与任务清单 | P1 | ✅ | 固化 provider 可见性语义 |

---

## 8. 下一步建议

1. 先把 provider 透传到健康摘要
2. 再把预检和统一流水线的输出补齐
3. 最后用最小回归测试固定这层可见性
