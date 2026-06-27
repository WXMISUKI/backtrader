# Phase 88 归档：自动回归门禁默认化与修复闭环

## 1. 背景

Phase 87 已经把关键回归步骤串成一键门禁，但它仍需要进入日常主入口，成为默认可消费的协议。

Phase 88 的目标是把 `regression_gate` 下沉到 `daily_run`、`acceptance` 和 `baseline`，让它不再只是独立入口。

## 2. 本次完成内容

- `examples/watchlist_shared.py` 新增 `build_regression_gate`
- `daily_run` 写入 `regression_gate`
- `acceptance` 读取并校验 `regression_gate`
- `baseline` 读取并展示 `regression_gate`
- 新增 Phase 88 规格与归档文档

## 3. 结果

这一阶段的核心变化是：

- 自动回归门禁从独立脚本推进到默认消费层
- 日常运行、验收和基线开始围绕同一份回归门禁视图协同
- `block` 时更直接地进入修复提示，而不是继续扩摘要

## 4. 验收口径

- `regression_gate` 在主入口里可见
- `acceptance` 和 `baseline` 能稳定消费同一份回归门禁
- 出现阻断时能优先定位修复项
- 仍然保持原有业务门禁语义

## 5. 后续建议

Phase 88 之后，若要继续收口，优先观察是否需要把 `regression_gate` 和 `repair_priority` 进一步合并成一个更短的修复视图，但不建议先扩仪表盘或调度系统。
