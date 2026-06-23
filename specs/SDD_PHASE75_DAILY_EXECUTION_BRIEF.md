# 软件设计规格说明 (SDD)
# Phase 75: 自选股日常执行简报与质量门禁闭环

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 75 自选股日常执行简报与质量门禁闭环 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-23 |
| 状态 | 草案 |

---

## 1. 背景

Phase 60 到 Phase 70 已经把日常链路收得比较完整：

- `production_gate` 解决今天能不能参考
- `action_list` 解决今天先做什么
- `run_cadence` 解决今天跑到了哪一步
- `prompt_context` 解决这些材料怎么喂给智能体和 Skill
- `review_brief` 解决回看时先看什么
- `schedule_hint` 解决下一次是否适合继续自动推进
- `daily_collaboration_pack` 解决智能体和 Skill 读取一份统一总包

Phase 71 到 Phase 74 又把历史行情链路补稳：

- 会话路由修正
- 历史失败分层
- 多源路由与 cookie 刷新自动化
- provider 可见性下沉

现在项目的主要矛盾不再是“数据有没有”和“结果有没有”，而是：

> 日常使用时，能不能在第一屏快速看懂今天到底该做什么、先看什么、哪些地方要停一下。

因此，下一阶段不建议继续扩散入口，也不建议继续加更多平行摘要，而是要把现有产物再收成一层更薄、更直接的 **日常执行简报**。

---

## 2. 总目标

建立一个最小可复用的日常执行简报层，让默认流程、工作流、留档查看和验收入口都能先给出一屏级结论：

- 今天结果是否可用
- 今天优先做什么
- 今天哪些动作应被禁止
- 回看和调度应该怎么衔接

这层简报只负责把已有结果组织得更快读，不新增模型，不重算判断，不替代现有门禁和行动清单。

---

## 3. 设计原则

### 3.1 不重复造轮子

Phase 75 不是再做一个新的门禁，也不是再做一个新的行动清单。

它只是把已存在的 `production_gate`、`action_list`、`run_cadence`、`review_brief`、`schedule_hint` 和 `daily_collaboration_pack` 再向上收成一层“第一眼可读”的执行简报。

### 3.2 先门禁，再行动，再回看，再就绪

推荐阅读顺序保持为：

1. `production_gate`
2. `action_list`
3. `run_cadence`
4. `review_brief`
5. `schedule_hint`
6. `daily_collaboration_pack`

### 3.3 第一屏优先

默认工作流和留档查看的终端输出要更像一个执行入口，而不是长报告目录。

### 3.4 轻量但一致

简报层应与既有 JSON 结构、提示词层和 Skill 层保持一致，避免不同入口口径不统一。

---

## 4. 范围

### 4.1 纳入范围

- 新增 `daily_execution_brief` 构建能力
- 在默认日常运行中写入执行简报
- 在默认工作流和留档查看中展示执行简报
- 在投产验收中检查执行简报可用性
- 在智能体提示词中优先识别执行简报
- 更新 README、路线图和任务清单

### 4.2 不纳入范围

- 新调度系统
- 新前端看板
- 新模型
- 新策略开发
- 新数据源

---

## 5. 执行简报定义

建议把 `daily_execution_brief` 拆成以下内容：

| 字段 | 含义 |
|---|---|
| `status` | `ready / caution / blocked / unknown` |
| `summary_text` | 面向终端的一段简短执行结论 |
| `headline` | 第一眼看到的标题式结论 |
| `primary_action` | 今天最优先看的动作 |
| `read_order` | 推荐阅读顺序 |
| `rules` | 执行简报的约束 |
| `evidence` | 这份简报来自哪些现有材料 |

---

## 6. 规则约定

### 6.1 `blocked`

当 `production_gate` 为 `block`，或者 `daily_collaboration_pack` 为 `blocked` 时：

- 执行简报必须明确提示先处理阻断
- 只能输出诊断、修复数据或等待建议
- 不能输出强行动建议

### 6.2 `caution`

当 `production_gate` 为 `warn`、`schedule_hint` 为 `caution`，或者存在明显降级时：

- 执行简报必须强调谨慎复核
- 可以看行动，但不能把降级当放行
- 简报应优先标出今天的观察顺序

### 6.3 `ready`

当门禁、行动、节奏和回看都稳定时：

- 执行简报可以作为第一屏默认入口
- 仍然保留门禁与回看顺序
- 允许日常按固定节奏继续推进

---

## 7. 输出契约

建议在 JSON 中新增：

```json
{
  "daily_execution_brief": {
    "status": "caution",
    "headline": "今日执行简报：需要谨慎复核，先看门禁和行动。",
    "summary_text": "门禁 warn，行动以 review_now / hold_watch 为主，先复核再动作。",
    "primary_action": "先看 production_gate，再看 action_list。",
    "read_order": [
      "production_gate",
      "action_list",
      "run_cadence",
      "review_brief",
      "schedule_hint",
      "daily_collaboration_pack"
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
| 75.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 8.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 75.1 | 实现共享执行简报构建 | P0 | ⬜ | `examples/watchlist_shared.py` |
| 75.2 | 在日常运行状态中写入执行简报 | P0 | ⬜ | `examples/daily_watchlist_daily_run.py` |
| 75.3 | 在默认工作流中展示执行简报 | P0 | ⬜ | `examples/daily_watchlist_flow.py` |
| 75.4 | 在留档查看入口展示执行简报 | P0 | ⬜ | `examples/daily_watchlist_archive_viewer.py` |
| 75.5 | 在回看入口展示执行简报 | P1 | ⬜ | `examples/daily_watchlist_review.py` |
| 75.6 | 在投产验收中检查执行简报 | P1 | ⬜ | `examples/daily_watchlist_acceptance.py` |
| 75.7 | 在智能体提示词中优先识别执行简报 | P1 | ⬜ | `core/agent/client.py` |

### 8.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 75.8 | 编写归档文档 | P1 | ⬜ | 记录执行简报收口 |
| 75.9 | 更新路线图与任务清单 | P1 | ⬜ | 固化 Phase 75 语义 |

---

## 9. 验收标准

- 默认日常运行 JSON 中包含 `daily_execution_brief`
- 默认工作流、留档查看和回看入口都能读到同一份简报
- 简报在 `block / caution / ready` 场景下都保持一致的约束语义
- 智能体提示词优先读取执行简报，再回退到 `daily_collaboration_pack`
- 简报不替代门禁和行动清单，只负责让第一屏更好读

---

## 10. 后续建议

Phase 75 完成后，后续优先顺序建议为：

1. 观察执行简报在真实日常中的稳定性
2. 如果仍需要更强压缩，再考虑更细的第一屏聚合
3. 继续保持入口少、摘要短、正文全

