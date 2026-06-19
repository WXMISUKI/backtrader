# 软件设计规格说明 (SDD)
# Phase 9: 决策会话与用户反馈闭环

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 9 决策会话与用户反馈闭环 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-19 |
| 状态 | 草案 |

---

## 1. 背景

当前项目已经具备：

- 统一任务协议
- 任务回放与学习统计
- 统一输出字段契约
- 工作流模板与协作执行

但这些能力仍然以“单次执行结果”为中心，缺少一个更适合产品化和持续优化的上层对象。

如果要真正做成一个决策工作台，系统必须能记录：

- 这次请求是一次什么样的决策
- 这次决策最终用了什么执行链路
- 用户是否采纳了这个结论
- 如果没有采纳，原因是什么

因此 Phase 9 的重点是引入“决策会话”和“用户反馈”闭环。

---

## 2. 目标

### 2.1 总目标

把一次分析或推荐行为抽象成一个可追踪、可反馈、可复盘的决策会话。

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 会话化 | 每次请求都能落到一个 `session_id` |
| 可反馈 | 用户可以对一次决策明确表示采纳或不采纳 |
| 可追踪 | 会话和 `workflow_id`、`task_protocol` 关联 |
| 可复盘 | 会话能回看路线、结果、反馈和修正 |
| 可学习 | 反馈能反哺路由、模板和统计 |

---

## 3. 核心对象

### 3.1 决策会话 DecisionSession

一次完整的业务决策容器。

建议字段：

- `session_id`
- `decision_id`
- `workflow_id`
- `scenario`
- `objective`
- `route`
- `task_protocol`
- `summary`
- `status`
- `created_at`
- `updated_at`
- `meta`

### 3.2 用户反馈 DecisionFeedback

用户对某次决策结果的显式反馈。

建议字段：

- `feedback_id`
- `session_id`
- `workflow_id`
- `accepted`
- `rating`
- `reason`
- `correction`
- `comment`
- `created_at`
- `meta`

### 3.3 会话统计 SessionStats

轻量统计对象，用于看闭环效果。

建议字段：

- `total_sessions`
- `accepted_count`
- `rejected_count`
- `partial_count`
- `unknown_count`
- `accept_rate`
- `scenario_counts`
- `recent_sessions`
- `recent_feedback`

---

## 4. 生命周期

### 4.1 会话生命周期

`created -> routed -> planned -> executed -> reviewed -> archived`

### 4.2 反馈生命周期

`submitted -> recorded -> aggregated`

---

## 5. 数据来源

本阶段允许使用轻量 JSONL 或内存聚合。

建议路径：

- `logs/decision_sessions.jsonl`
- `logs/decision_feedback.jsonl`

---

## 6. 功能要求

### 6.1 会话创建

当用户发起分析、推荐、回测或报告请求时，应可创建一个 `session_id`，并绑定：

- 路由结果
- 任务协议
- workflow_id
- 场景类型

### 6.2 会话回看

会话应该能回看：

- 初始请求
- 路由结果
- 任务协议
- 工作流结果
- 用户反馈

### 6.3 用户反馈

应支持最小反馈动作：

- 采纳
- 不采纳
- 部分采纳
- 待复核

### 6.4 统计回收

应支持对会话和反馈做轻量统计，并输出可继续消费的统一结构。

---

## 7. 输出要求

### 7.1 会话输出

会话输出应包含：

- `session_id`
- `workflow_id`
- `scenario`
- `summary`
- `task_protocol`
- `feedback`

### 7.2 反馈输出

反馈输出应包含：

- `accepted`
- `rating`
- `reason`
- `correction`
- `comment`

---

## 8. 验收标准

- 可以创建并回看决策会话
- 可以提交用户反馈
- 会话与 workflow_id 能关联
- 反馈能进入统计和复盘
- 输出字段稳定可消费

---

## 9. 归档要求

当以下内容完成后，可将本规格归档：

1. 会话与反馈的数据结构实现完成
2. 工具层可创建和提交反馈
3. 轻量验证通过
4. 形成归档文档

---

## 10. 与已有规格的关系

- `SDD_PHASE6_TASK_PROTOCOL.md` 负责任务语义统一
- `SDD_PHASE7_REPLAY_LEARNING.md` 负责回放与统计
- `SDD_PHASE8_UNIFIED_OUTPUT_CONTRACT.md` 负责统一输出契约
- 本规格负责把这些能力组织成决策会话与反馈闭环

