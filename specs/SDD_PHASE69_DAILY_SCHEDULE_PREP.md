# 软件设计规格说明 (SDD)
# Phase 69: 自选股轻量调度准备

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 69 自选股轻量调度准备 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-21 |
| 状态 | 已完成 |

---

## 1. 背景

Phase 66 到 Phase 68 已经把日常主链路收得比较完整：

- `run_cadence` 说明今天跑到了哪一步
- `prompt_context` 说明这些材料怎么喂给智能体和 Skill
- `review_brief` 说明回看时先看什么

但系统仍缺少一层很薄的“运行就绪提示”，让默认运行、工作流和留档查看都能快速判断：

- 当前结果是否适合继续自动推进
- 下一次运行应该进入自动、人工复核还是暂停
- `degraded` 是业务降级，还是脚本真正失败

Phase 69 的目标，就是把这些信息收成一份统一的 `schedule_hint`，只做运行准备判断，不新增真正的调度系统。

---

## 2. 总目标

建立一个最小可复用的运行就绪层，让系统在每天跑完以后直接回答：

- 下一次是否可以继续自动运行
- 需要人工复核还是先暂停
- 当前状态是可运行、谨慎运行，还是阻断

---

## 3. 核心原则

### 3.1 `schedule_hint` 不是调度系统

它不是 cron、队列、守护进程或重试编排，只是对当前运行状态的轻量提示。

### 3.2 业务降级不等于脚本失败

`degraded` 表示业务结果需要谨慎看待，但只要流程正常跑完，脚本退出码不应等同于失败。

### 3.3 先门禁，再节奏，再回看

运行就绪判断应优先读取：

1. `production_gate`
2. `run_cadence`
3. `review_brief`
4. `prompt_context`

### 3.4 保持薄层

本阶段不新增模型、不新增评分、不新增调度服务，只收紧运行准备语境。

---

## 4. 范围

### 4.1 纳入范围

- 新增 `schedule_hint` 构建能力
- 在日常运行状态中写入 `schedule_hint`
- 在默认工作流和留档查看中展示 `schedule_hint`
- 在投产验收中检查 `schedule_hint`
- 更新 README、任务清单和路线图

### 4.2 不纳入范围

- 新 cron 服务
- 新任务队列
- 新守护进程
- 自动重试平台
- 告警通知系统
- 前端调度看板

---

## 5. 调度准备定义

建议把 `schedule_hint` 拆成以下内容：

| 字段 | 含义 |
|---|---|
| `status` | `ready / caution / blocked` |
| `summary_text` | 面向终端的简短运行就绪提示 |
| `next_step` | 下一次动作前先看什么 |
| `next_run_mode` | 建议进入的运行模式，例如 `daily_auto` / `manual_review` / `pause` |
| `next_run_window` | 下一次运行窗口提示 |
| `read_order` | 推荐阅读顺序 |
| `rules` | 运行就绪提示的约束 |
| `evidence` | 这份提示来自哪些现有材料 |

---

## 6. 规则约定

### 6.1 `blocked`

当满足以下任一条件：

- 默认运行失败
- 投产门禁为 `block`
- 回看或运行结果说明核心链路不可继续

则 `schedule_hint.status` 应为 `blocked`。

### 6.2 `caution`

当满足以下任一条件：

- 默认运行降级
- 投产门禁为 `warn`
- 回看摘要提示需要谨慎复核

则 `schedule_hint.status` 应为 `caution`。

### 6.3 `ready`

当默认运行成功，门禁稳定，回看不提示额外阻断时：

- `schedule_hint.status` 为 `ready`
- 可以按固定节奏继续下一次运行

---

## 7. 输出契约

建议在 JSON 中新增：

```json
{
  "schedule_hint": {
    "status": "caution",
    "summary_text": "调度准备可继续，但存在降级，建议先复核后再进入下一次自动运行。",
    "next_step": "先复核门禁、回看摘要和运行节奏，再决定是否继续自动推进。",
    "next_run_mode": "manual_review",
    "next_run_window": "下次自动运行前",
    "read_order": [
      "production_gate",
      "run_cadence",
      "review_brief",
      "prompt_context"
    ],
    "rules": [],
    "evidence": {}
  }
}
```

---

## 8. 任务拆分

### 8.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 69.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 8.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|------|
| 69.1 | 实现共享 `schedule_hint` 构建 | P0 | ✅ | `examples/watchlist_shared.py` |
| 69.2 | 在日常运行状态中写入 `schedule_hint` | P0 | ✅ | `examples/daily_watchlist_daily_run.py` |
| 69.3 | 在默认工作流和留档查看中展示 `schedule_hint` | P0 | ✅ | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| 69.4 | 在投产验收中检查 `schedule_hint` | P1 | ✅ | `examples/daily_watchlist_acceptance.py` |

### 8.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 69.5 | 编写归档文档 | P1 | ✅ | `specs/ARCHIVE_PHASE69_DAILY_SCHEDULE_PREP.md` |
| 69.6 | 更新知识库与任务清单 | P1 | ✅ | Phase 69 收口 |

---

## 9. 验收标准

- `schedule_hint` 能从默认运行、默认工作流和留档查看里读到
- `schedule_hint` 只负责运行就绪提示，不新增真正的调度系统
- `degraded` 仍然保留在业务状态中，但不会被误判成脚本失败
- 默认运行、工作流和验收的输出契约保持轻量且一致

---

## 10. 后续建议

Phase 69 完成后，继续保持：

1. 摘要短、正文全
2. 运行就绪提示薄而稳定
3. 只在真正需要时再考虑更完整的调度系统

