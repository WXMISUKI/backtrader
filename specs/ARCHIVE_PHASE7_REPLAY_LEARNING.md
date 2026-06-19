# Phase 7 任务回放与学习统计归档

---

## 1. 归档结论

Phase 7 已完成最小闭环：任务可以按 `workflow_id` 回放，模板命中与审计链路可以被轻量统计，项目开始具备“可复盘、可观察、可持续优化”的基础。

---

## 2. 已完成内容

- 新增 Phase 7 规格草案
- 新增任务回放模块 `core/agent/replay.py`
- 新增 `get_workflow_replay`
- 新增 `get_workflow_learning_stats`
- 工具注册表已暴露回放和统计工具

---

## 3. 当前收口边界

本阶段只做轻量回放与统计，不引入新数据库或训练系统。

推荐继续使用：

- `RouteAuditLogger`
- `TemplateMetricsStore`
- `TaskPlan`
- `TaskResult`

---

## 4. 轻量验证要求

建议验证：

1. `get_workflow_replay(workflow_id)` 可返回审计片段
2. `get_workflow_learning_stats()` 可返回统计汇总
3. 工具注册表可暴露新工具
4. 编译验证通过

---

## 5. 后续建议

下一阶段最值得继续推进的是：

1. 将回放结果接入调试或前端展示
2. 把更多路由样本纳入统计
3. 用统计结果反哺模板和路由规则
4. 再考虑更严格的统一输出字段枚举

