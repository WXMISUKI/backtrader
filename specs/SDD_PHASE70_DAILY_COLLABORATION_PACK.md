# 软件设计规格说明 (SDD)
# Phase 70: 自选股日常协作总包收束

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 70 自选股日常协作总包收束 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-21 |
| 状态 | 已完成 |

---

## 1. 背景

Phase 60 到 Phase 69 已经把日常主链路逐步收紧：

- `production_gate` 解决今天能不能参考
- `action_list` 解决今天先做什么
- `run_cadence` 解决今天跑到了哪一步
- `prompt_context` 解决这些材料怎么喂给智能体和 Skill
- `review_brief` 解决回看时先看什么
- `schedule_hint` 解决下一次是否适合继续自动推进

但这些内容仍然分散在多个 JSON 片段中。对于智能体和 Skill 来说，最省心的不是再读六份材料，而是读一份统一的协作总包。

Phase 70 的目标，就是把这些现有材料收成一份统一的 `daily_collaboration_pack`。

---

## 2. 总目标

建立一个最小可复用的日常协作总包，让系统在每天跑完后直接回答：

- 今天的协作语境应该怎么读
- 智能体和 Skill 应该先看哪一层
- 如果只看一份总包，应该看到什么

---

## 3. 核心原则

### 3.1 总包不是新分析

`daily_collaboration_pack` 不做新的判断，不重算模型，不新增评分。

它只是把已有材料再收一层。

### 3.2 先门禁，再行动，再节奏，再摘要，再就绪提示

推荐阅读顺序为：

1. `production_gate`
2. `action_list`
3. `run_cadence`
4. `prompt_context`
5. `review_brief`
6. `schedule_hint`

### 3.3 保持薄层

本阶段不新增调度平台，不新增前端，不新增分析模型。

### 3.4 统一给智能体和 Skill 用

总包的设计目标不是单纯为了终端显示，而是为了让智能体、Skill、CLI 和后续 API 都能直接消费同一份语境。

---

## 4. 范围

### 4.1 纳入范围

- 新增 `daily_collaboration_pack` 构建能力
- 在默认日常运行中写入协作总包
- 在默认工作流和留档查看中展示协作总包
- 在投产验收和智能体提示词中识别协作总包
- 更新 README、任务清单和路线图

### 4.2 不纳入范围

- 新调度系统
- 新模型
- 新评分器
- 新前端
- 新告警系统
- 新策略开发

---

## 5. 协作总包定义

建议把 `daily_collaboration_pack` 拆成以下内容：

| 字段 | 含义 |
|---|---|
| `status` | `ready / caution / blocked / unknown` |
| `summary_text` | 面向终端和智能体的简短总览 |
| `prompt_text` | 面向提示词和 Skill 的可直接消费语境 |
| `read_order` | 推荐阅读顺序 |
| `rules` | 协作总包的约束 |
| `evidence` | 协作总包来自哪些现有材料 |

---

## 6. 规则约定

### 6.1 `blocked`

当门禁或协作总包任一核心层显式阻断时：

- 只能输出诊断、修复或等待建议
- 不能输出强行动建议

### 6.2 `caution`

当存在降级、复核或谨慎语境时：

- 可以继续查看
- 但不应把降级当成完全放行

### 6.3 `ready`

当门禁、行动、节奏和回看都稳定时：

- 可以按日常节奏继续
- 协作总包可作为默认提示入口

---

## 7. 输出契约

建议在 JSON 中新增：

```json
{
  "daily_collaboration_pack": {
    "status": "caution",
    "summary_text": "协作总包已收拢：门禁 warn；行动 wait；节奏 degraded；提示语境 warn；回看 warn；调度准备 caution。",
    "prompt_text": "日常协作总包：...",
    "read_order": [
      "production_gate",
      "action_list",
      "run_cadence",
      "prompt_context",
      "review_brief",
      "schedule_hint"
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
| 70.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 8.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 70.1 | 实现共享协作总包构建 | P0 | ✅ | `examples/watchlist_shared.py` |
| 70.2 | 在日常运行状态中写入协作总包 | P0 | ✅ | `examples/daily_watchlist_daily_run.py` |
| 70.3 | 在默认工作流和留档查看中展示协作总包 | P0 | ✅ | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| 70.4 | 在投产验收和智能体提示词中识别协作总包 | P1 | ✅ | `examples/daily_watchlist_acceptance.py` / `core/agent/client.py` |

### 8.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 70.5 | 编写归档文档 | P1 | ✅ | `specs/ARCHIVE_PHASE70_DAILY_COLLABORATION_PACK.md` |
| 70.6 | 更新知识库与任务清单 | P1 | ✅ | Phase 70 收口 |

---

## 9. 验收标准

- `daily_collaboration_pack` 能从默认运行、默认工作流和留档查看里读到
- 智能体提示词能优先识别协作总包，再按内置顺序回退
- 它只做总包收束，不新增新的分析模型或调度平台
- `schedule_hint` 继续作为其中一层存在，但不再承担全部协作职责

---

## 10. 后续建议

Phase 70 完成后，后续如果还要继续增强，优先顺序应当是：

1. 继续观察协作总包是否稳定
2. 只在真正需要时再考虑更完整的调度系统
3. 保持入口少、摘要短、正文全

