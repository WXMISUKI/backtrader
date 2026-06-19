# Phase 10 统一决策入口与最小生产闭环归档

---

## 1. 归档结论

Phase 10 已完成最小投产闭环：项目对外已有一个统一决策入口，可以直接承接分析、推荐、回测、报告、风控和工作流场景，并返回更适合私用测试迭代的标准业务决策结果。

---

## 2. 已完成内容

- 新增 Phase 10 规格草案
- 新增统一决策入口 `StockOrchestrator.answer_decision_request()`
- 新增业务决策摘要构造，支持四段式输出
- `StockAgentRuntime` 可直接调用统一决策入口
- 会话创建与统一输出可以在单入口中完成

---

## 3. 当前收口边界

本阶段以“快速投产、真实测试、持续迭代”为目标，不额外引入新的内部层次。

项目定位是私人私用的股票预测与推荐智能体，目标不是对外售卖，而是先把算法、工具和工作流跑通，再根据真实使用效果逐步优化。

统一入口优先返回四段式决策摘要：

- `结论`
- `依据`
- `风险`
- `下一步动作`

同时保留兼容字段：

- `ok`
- `scenario`
- `action`
- `tool`
- `summary`
- `decision`
- `data_source`
- `session_id`
- `workflow_id`
- `route_audit_id`
- `task_protocol`
- `governance`

---

## 4. 轻量验证要求

建议验证：

1. `StockOrchestrator.answer_decision_request()` 可返回完整结果
2. `StockAgentRuntime.answer_decision_request()` 可直接调用
3. 编译验证通过

---

## 5. 后续建议

下一阶段如果继续推进，优先方向应是：

1. 简单结果展示页或 API 适配
2. 最小采纳/不采纳反馈入口
3. 在真实用户流中验证统一入口
