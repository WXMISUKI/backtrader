# 软件设计规格说明 (SDD)
# Phase 67: 自选股日常提示语境联动

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 67 自选股日常提示语境联动 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-21 |
| 状态 | 已完成 |

---

## 1. 背景

Phase 60 到 Phase 66 已经把自选股日常链路收得比较完整：

- `production_gate` 回答今天能不能参考
- `action_list` 回答今天先做什么
- `run_cadence` 回答今天跑到了哪一步

但在实际协作里，用户和智能体仍然要自己把这些产物重新拼起来，才能形成当天的真正执行语境。

Phase 67 的目标，就是把这些已有结果继续收拢成一份统一的 `prompt_context`，让日常脚本、提示词和 Skill 入口都能读取同一套协作语境，而不是各自解释一遍。

---

## 2. 总目标

建立一个最小可复用的日常提示语境层，让系统在每次运行后能直接回答：

- 今天应该先看什么
- 今天哪些动作允许
- 今天哪些动作必须压掉
- 这份语境如何喂给智能体提示词和 Skill

---

## 3. 核心原则

### 3.1 语境先于单点字段

`prompt_context` 不是新的评分，也不是新的判断器。

它只是把已有门禁、行动清单和运行节奏串成一段可直接复用的上下文。

### 3.2 先门禁，再语境，再建议

任何提示词或 Skill 在输出建议前，都应先读取：

1. `production_gate`
2. `action_list`
3. `run_cadence`

当 `production_gate = block` 时，只能给出诊断、修复数据或等待建议，不能输出强行动建议。

### 3.3 保持薄层

本阶段不新增模型，不做自动修复，不做复杂编排，只补一个共享的提示语境块。

### 3.4 人和智能体共用

同一份 `prompt_context` 应同时适用于：

- 终端查看
- 归档查看
- 投产验收
- 智能体提示词
- 后续 Skill / 工具协作

---

## 4. 范围

### 4.1 纳入范围

- 新增 `prompt_context` 构建能力
- 把 `production_gate / action_list / run_cadence` 收成统一提示语境
- 在默认日常流程和留档查看中展示提示语境
- 在诊断收口包中保留提示语境
- 在投产验收中检查提示语境存在
- 更新智能体默认提示词
- 更新 README、任务清单和归档

### 4.2 不纳入范围

- 新调度平台
- 自动交易
- 新前端
- 复杂提示词编排器
- 新模型训练

---

## 5. 提示语境定义

建议把提示语境拆成以下内容：

| 字段 | 含义 |
|---|---|
| `summary_text` | 面向终端的简短语境摘要 |
| `prompt_text` | 可直接喂给智能体或 Skill 的上下文文本 |
| `read_order` | 推荐阅读顺序 |
| `rules` | 明确的协作约束 |
| `top_actions` | 今日优先行动样本 |
| `evidence` | 这份语境来自哪些门禁/行动/节奏材料 |

---

## 6. 规则约定

### 6.1 `block` 语境

当 `production_gate` 为 `block`：

- 语境必须显式说明只做诊断
- 不能输出买入、加仓、强执行建议
- `action_list` 中的强动作必须被压掉

### 6.2 `warn` 语境

当 `production_gate` 为 `warn`：

- 语境必须强调谨慎
- 只能输出观察、复核、等待类建议
- 不能把降级数据包装成强信号

### 6.3 `pass` 语境

当 `production_gate` 为 `pass`：

- 可以正常说明重点关注和观察建议
- 仍然要保留风险提示
- 继续按照 `production_gate -> action_list -> run_cadence` 的顺序阅读

---

## 7. 输出契约

建议在 JSON 中新增：

```json
{
  "prompt_context": {
    "status": "warn",
    "summary_text": "提示语境已收拢：先看投产门禁，再看行动清单，再看运行节奏。",
    "prompt_text": "日常协作语境：...",
    "read_order": [
      "production_gate",
      "action_list",
      "run_cadence",
      "diagnosis_evidence"
    ],
    "rules": [
      "先看 production_gate，再看 action_list，再看 run_cadence。",
      "production_gate 为 block 时，只能给出诊断、修复数据或等待建议，不给强行动建议。"
    ],
    "top_actions": [],
    "evidence": {
      "production_gate": {},
      "action_list": {},
      "run_cadence": {},
      "diagnosis_evidence": {}
    }
  }
}
```

---

## 8. 任务拆分

### 8.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 67.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 8.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 67.1 | 实现共享提示语境构建 | P0 | ✅ | `examples/watchlist_shared.py` |
| 67.2 | 在日常运行状态中写入提示语境 | P0 | ✅ | `examples/daily_watchlist_daily_run.py` |
| 67.3 | 在默认工作流和留档查看中展示提示语境 | P0 | ✅ | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| 67.4 | 在诊断收口包中展示提示语境 | P1 | ✅ | `examples/daily_watchlist_diagnosis_bundle.py` |
| 67.5 | 更新智能体默认提示词 | P1 | ✅ | `core/agent/client.py` |
| 67.6 | 在投产验收中检查提示语境 | P1 | ✅ | `examples/daily_watchlist_acceptance.py` |

### 8.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 67.7 | 编写归档文档 | P1 | ✅ | `specs/ARCHIVE_PHASE67_DAILY_PROMPT_CONTEXT_LINKAGE.md` |
| 67.8 | 更新知识库与任务清单 | P1 | ✅ | Phase 67 收口 |

---

## 9. 验收标准

- `run_status` 中包含 `prompt_context`
- 默认工作流和留档查看能看到提示语境摘要
- 诊断收口包能展示同一份提示语境
- 投产验收能检查提示语境存在
- 智能体默认提示词明确知道 `production_gate -> action_list -> run_cadence` 的阅读顺序

---

## 10. 后续建议

Phase 67 完成后，再往下优先：

1. 更细的回看呈现
2. 更轻的调度准备

下一阶段继续保持“入口少、语境稳、协作协议统一”的方向。
