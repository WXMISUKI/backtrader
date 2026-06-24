# 软件设计规格说明 (SDD)
# Phase 84: 投产产物契约统一与 `latest.json` 写入修复

---

## 1. 背景

Phase 78 到 Phase 83 已经把日常投产入口收成了薄基线、修复优先级和关键门禁透传。

但当前仍存在一个结构性问题：运行链路里已经算出来的关键产物，没有稳定收进 `latest.json` 这一个最终消费契约，导致基线和验收还会把“字段没写进去”误读成“门禁失败”。

Phase 84 只做一件事：统一投产产物契约，让 `latest.json` 成为关键日常产物的单一事实来源。

---

## 2. 总目标

把日常链路从“算出了很多摘要”推进到“最终消费端稳定读到同一份产物契约”。

本阶段要保证：

- `latest.json` 稳定包含关键门禁与简报
- `daily_run` 与 `acceptance` 优先消费 `latest.json`
- 字段缺失与真实数据降级不再混淆

---

## 3. 设计原则

### 3.1 只统一契约

不新增分析层，不新增模型，不新增调度系统，只统一写盘和读取的最终契约。

### 3.2 以 `latest.json` 为准

`latest.json` 是最终给基线、验收和回看的主产物。

### 3.3 保持薄层

允许 `run_status` 作为兜底，但不能反向把兜底当主契约。

### 3.4 可验证

必须能通过最小测试验证关键字段存在/缺失两种场景。

---

## 4. 范围

### 4.1 纳入范围

- `latest.json` 投产契约统一
- `pipeline` 关键产物写入
- `daily_run` 读取优先级收紧
- `acceptance` 契约校验收紧
- 最小回归测试
- 归档与路线图同步

### 4.2 不纳入范围

- 新策略
- 新指标
- 新 UI
- 新调度平台

---

## 5. 目标契约

`latest.json` 至少应稳定包含：

- `production_gate`
- `daily_execution_brief`
- `review_brief`
- `schedule_hint`
- `daily_collaboration_pack`
- `run_cadence`
- `prompt_context`
- `feedback_effect_brief`
- `history_selected_provider` 相关健康信息

---

## 6. 规则约定

### 6.1 `pipeline`

`examples/daily_watchlist_pipeline.py` 负责生成并写入关键契约字段。

### 6.2 `daily_run`

`examples/daily_watchlist_daily_run.py` 优先读取 `pipeline` 的契约字段，不再重复造同一层数据。

### 6.3 `acceptance`

`examples/daily_watchlist_acceptance.py` 优先检查 `latest.json`，`run_status` 仅作兜底。

### 6.4 验收语义

如果关键契约字段缺失，应视为结构性问题；如果字段存在但数据降级，应继续保留 `caution` 或 `failed` 语义。

---

## 7. 任务拆分

### 7.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 84.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 7.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 84.1 | 在 pipeline 中写入关键契约字段 | P0 | ⬜ | `latest.json` 主契约 |
| 84.2 | 收紧 daily_run 读取优先级 | P0 | ⬜ | 优先消费 `latest.json` |
| 84.3 | 收紧 acceptance 契约检查 | P0 | ⬜ | 优先读取 `latest.json` |
| 84.4 | 增加最小回归测试 | P1 | ⬜ | 字段存在/缺失两种场景 |

### 7.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 84.5 | 编写归档文档 | P1 | ⬜ | 记录产物契约统一闭环 |
| 84.6 | 更新路线图与任务清单 | P1 | ⬜ | 固化 `latest.json` 口径 |

---

## 8. 验收标准

- `latest.json` 能稳定读到关键门禁与简报字段
- `daily_run` 不再依赖重算来弥补契约缺失
- `acceptance` 优先以 `latest.json` 为准
- 基线失败时能明确区分“字段缺失”和“数据降级”
- 不破坏 `ready / caution / failed / blocked` 语义
