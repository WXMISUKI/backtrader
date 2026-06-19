# 归档文档：Phase 23 最小反馈闭环入口

---

## 1. 归档结论

Phase 23 已完成最小反馈闭环入口。

现在用户在私用测试中，只要保留 `session_id`，就可以把一次决策的采纳或不采纳反馈快速记录下来；如果同时提供 `workflow_id` 也可以直接透传，不会破坏原有链路。

---

## 2. 已完成内容

- 新增 Phase 23 规格草案
- `DecisionSessionStore.submit_feedback()` 支持从 `session_id` 回推 `workflow_id`，并允许 `workflow_id` 为空
- `StockOrchestrator.submit_decision_feedback()` 补齐编排层反馈入口
- HTTP API 的 `/feedback` 允许只传 `session_id`
- 工具入口与运行时反馈签名已放宽
- `examples/api_demo.py` 已支持只传 `session_id` 提交反馈

---

## 3. 验证结果

轻量验证目标是：

- `POST /feedback` 最少只需 `session_id`
- 已存在会话时可自动回推 `workflow_id`
- 反馈可继续写入 JSONL 并进入回放统计
- 不影响 `POST /decision` 的原有路径

---

## 4. 当前收口边界

本阶段不新增复杂反馈模型，不做多轮反馈协议，也不做独立反馈工作台。

目标只是让你在真实使用时能更轻松地记录采纳情况，然后继续根据反馈迭代算法、工具和工作流。

---

## 5. 本阶段结论

最小反馈闭环的价值在于：

- 真实可用
- 记录成本低
- 和会话、工作流、复盘天然联动
- 很适合私人私用场景下的边用边改

---

## 6. 后续建议

1. 先在真实使用中多记录几次采纳/不采纳
2. 再看是否需要更细的反馈分类
3. 如果后续迭代频繁，再考虑把反馈统计单独做一个轻量查询入口
