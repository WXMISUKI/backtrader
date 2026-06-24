# 软件设计规格说明 (SDD)
# Phase 85: 真实数据稳定性增强与 provider 可见性收紧

---

## 1. 背景

Phase 84 已经把 `latest.json` 统一成主契约。

但当前仍需要把真实数据稳定性进一步收紧，确保上层入口能稳定看见：

- `history_selected_provider`
- `provider_attempts`
- `fallback_strategy`
- `data_confidence`
- `confidence_level`

本阶段不再扩展新的分析层，而是把既有数据可信度和 provider 可见性稳定下沉到日常入口。

---

## 2. 总目标

把“数据是否可信”和“最终用了哪个 provider”变成所有主要入口都能稳定读到的主语义。

要求达到：

- 数据降级时，入口能清楚说明降级原因
- provider 回退时，入口能清楚说明回退链路
- 基线、验收、健康预检、流水线都共享同一套语义

---

## 3. 设计原则

### 3.1 真实优先

优先暴露真实来源和真实降级，不用更宽松的口径掩盖问题。

### 3.2 不重复造概念

`data_confidence`、`confidence_level`、`history_selected_provider`、`provider_attempts`、`fallback_strategy` 已经存在，本阶段只统一下沉和消费。

### 3.3 保持薄层

不新建编排层，不做复杂路由，只把当前链路的结果稳定写出来、读出来。

### 3.4 可验

必须能通过最小测试验证主源成功、备源接管、最终兜底三种场景。

---

## 4. 范围

### 4.1 纳入范围

- 数据可信度统一口径
- provider 可见性下沉
- 降级语义收紧
- 最小回归测试
- 归档与路线图同步

### 4.2 不纳入范围

- 新数据源
- 新模型
- 新前端
- 新调度系统

---

## 5. 目标输出

所有主要日常入口应稳定可读：

- `history_selected_provider`
- `history_provider_attempts`
- `history_provider_summary`
- `data_confidence`
- `confidence_level`
- `history_fallback_strategy`

---

## 6. 规则约定

### 6.1 健康预检

健康预检要直接输出 provider 视图和数据可信度，不只输出健康分。

### 6.2 日常流水线

流水线要在健康项、决策项、日报和最终 payload 中保持同一套语义。

### 6.3 投产验收

验收要能确认 provider 视图没有在下游丢失。

### 6.4 基线入口

基线要把 provider 可见性和数据可信度摆在前面，避免只剩一个总状态。

---

## 7. 任务拆分

### 7.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 85.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 7.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 85.1 | 在健康预检中稳定输出 provider 视图 | P0 | ⬜ | `examples/watchlist_data_health.py` |
| 85.2 | 在流水线中稳定透传 provider 与可信度 | P0 | ⬜ | `examples/daily_watchlist_pipeline.py` |
| 85.3 | 在投产验收中稳定检查 provider 视图 | P0 | ⬜ | `examples/daily_watchlist_acceptance.py` |
| 85.4 | 在基线入口中突出 provider 和可信度 | P0 | ⬜ | `examples/daily_watchlist_production_baseline.py` |
| 85.5 | 保持门禁语义不变 | P0 | ⬜ | 不改 `ready / caution / failed / blocked` |
| 85.6 | 补最小回归测试 | P1 | ⬜ | 主源 / 备源 / 兜底 |

### 7.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 85.7 | 编写归档文档 | P1 | ⬜ | 记录 provider 可见性闭环 |
| 85.8 | 更新路线图与任务清单 | P1 | ⬜ | 固化数据可信度口径 |

---

## 8. 验收标准

- 健康预检能清楚看见 provider 视图
- 流水线和验收能稳定读到 provider 相关字段
- 数据降级与结构缺失能清晰区分
- 低可信数据会更倾向于观察或跳过，而不是强行动
- 不破坏 `ready / caution / failed / blocked` 语义
