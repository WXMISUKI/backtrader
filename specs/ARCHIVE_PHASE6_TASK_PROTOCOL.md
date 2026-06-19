# Phase 6 统一任务协议与学习闭环归档

---

## 1. 归档结论

Phase 6 已完成第一阶段闭环：统一任务协议已建立，协作计划与工作流结果已可转换为同一套任务语义，后续智能体能力可以围绕这套协议继续扩展。

---

## 2. 已完成内容

- 新增统一任务协议模块 `core/agent/task_protocol.py`
- 协作计划可导出为 `TaskPlan`
- 工作流结果可导出为 `TaskResult`
- 智能体客户端与编排器输出增加 `task_protocol`
- Phase 6 规格草案已新增

---

## 3. 当前收口边界

当前项目仍然保留以下旧结构作为兼容层：

- `CollaborationPlan`
- `WorkflowExecutionResult`
- `WorkflowStepResult`

但对外推荐消费：

- `TaskPlan`
- `TaskStep`
- `TaskResult`

---

## 4. 轻量验证要求

建议验证以下能力：

1. `build_collaboration_plan(...).to_task_plan()`
2. `WorkflowExecutionResult.to_task_result()`
3. `StockOrchestrator.plan_collaboration()` 返回 `task_protocol`
4. `StockOrchestrator.execute_workflow()` 返回 `task_protocol`

---

## 5. 后续建议

下一阶段不建议继续扩很多碎工具，而是优先推进：

1. 任务回放与学习统计
2. 标准输出在前端和日志中的统一消费
3. 模板选择与任务协议的更深绑定
4. 智能体工具自动路由的可解释增强

