# 软件设计规格说明 (SDD)
# Phase 78: 自选股日常投产实跑基线与一键验收闭环

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 78 自选股日常投产实跑基线与一键验收闭环 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-24 |
| 状态 | 草案 |

---

## 1. 背景

Phase 60 到 Phase 77 已经把日常投产链路的关键薄层都补出来了：

- `production_gate`
- `action_list`
- `run_cadence`
- `prompt_context`
- `review_brief`
- `schedule_hint`
- `daily_collaboration_pack`
- `daily_execution_brief`
- `feedback_effect_brief`
- `history_selected_provider`

这些层已经足够支撑日常使用，但还缺一个更贴近真实投产的基线入口：

> 今天这条链路到底能不能完整跑通，卡在哪一层，下一步先修什么。

因此本阶段不再继续堆新的语义层，而是把现有产物收成一个最小的日常投产基线与一键验收闭环。

---

## 2. 总目标

建立一个最小的日常投产实跑基线，让系统每天都能快速回答：

- 今天预检、执行、归档、回看、验收是否都完整
- 卡点出现在什么阶段
- 当前结果是否适合人工参考
- 下一步应优先处理什么

本阶段只做基线汇总，不重写业务链路，不新增分析模型。

---

## 3. 设计原则

### 3.1 复用现有入口

直接复用 `daily_watchlist_daily_run.py`、`daily_watchlist_review.py`、`daily_watchlist_acceptance.py`、`daily_watchlist_archive_viewer.py` 的现有 JSON 和摘要，不重复实现主流程。

### 3.2 先结论，再证据

终端先输出一段短结论，再给失败阶段和下一步动作，避免把用户带回多层 JSON 里翻找。

### 3.3 失败要可定位

基线入口要清楚说明卡在：

- 预检
- 执行
- 归档
- 回看
- 验收

### 3.4 保持薄层

不新增数据库，不新增前端，不新增调度系统。

---

## 4. 范围

### 4.1 纳入范围

- 投产基线汇总入口
- 预检、执行、归档、回看、验收状态汇总
- `production_gate` / `daily_execution_brief` / `feedback_effect_brief` / `schedule_hint` / `history_selected_provider` 检查
- 一键验收结论
- README、路线图、任务清单更新

### 4.2 不纳入范围

- 新策略
- 新模型
- 新前端
- 新调度系统
- 新数据源

---

## 5. 建议输出

建议新增一个薄入口，例如 `examples/daily_watchlist_production_baseline.py`，输出结构至少包含：

| 字段 | 含义 |
|---|---|
| `status` | `ready / caution / blocked / failed` |
| `summary_text` | 一句话基线结论 |
| `failed_stage` | 卡点所在阶段 |
| `next_action` | 下一步优先动作 |
| `checks` | 各项检查结果 |
| `evidence` | 对应 JSON / 简报证据 |

---

## 6. 规则约定

### 6.1 `failed`

当预检、执行或验收任一环节失败时：

- 基线入口必须明确指出失败阶段
- 不能只给一个笼统失败态

### 6.2 `blocked`

当 `production_gate`、`daily_execution_brief` 或 `feedback_effect_brief` 明确阻断时：

- 基线入口只能提示修复数据或等待
- 不能输出强行动建议

### 6.3 `caution`

当链路能跑通但存在降级时：

- 基线入口可以继续参考
- 但必须提示先复核再动作

### 6.4 `ready`

当整条链路都完整可用时：

- 可视为日常投产基线通过
- 仍保留人工复核顺序

---

## 7. 任务拆分

### 7.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 78.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 7.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 78.1 | 实现日常投产基线入口 | P0 | ⬜ | `examples/daily_watchlist_production_baseline.py` |
| 78.2 | 汇总预检、执行、回看、验收状态 | P0 | ⬜ | 复用现有 JSON / 摘要 |
| 78.3 | 输出失败阶段与下一步动作 | P0 | ⬜ | 终端短报告 |
| 78.4 | 透传关键证据 | P1 | ⬜ | `production_gate` / `daily_execution_brief` / `feedback_effect_brief` / `schedule_hint` / `history_selected_provider` |
| 78.5 | 在智能体提示词中识别基线入口 | P1 | ⬜ | `core/agent/client.py` |

### 7.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 78.6 | 编写归档文档 | P1 | ⬜ | 记录基线闭环 |
| 78.7 | 更新路线图与任务清单 | P1 | ⬜ | 固化投产基线口径 |

---

## 8. 验收标准

- 能通过一个薄入口判断今天整条链路是否跑通
- 失败时能指出具体卡点
- 能看到关键证据而不是只看一个总状态
- 不引入复杂编排或新模型

---

## 9. 后续建议

Phase 78 完成后，优先观察这个基线入口在真实日常中的稳定性，再决定是否细化失败分层。
