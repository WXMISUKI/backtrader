# 归档文档：Phase 69 自选股轻量调度准备

---

## 1. 阶段目标

Phase 69 的目标不是新增调度系统，而是把当前运行状态再收成一份很薄的 `schedule_hint`，让默认运行、默认工作流和留档查看都能快速判断下一次是否适合继续自动推进。

同时，本阶段把“业务降级”和“脚本失败”拆开：

- `degraded` 继续作为业务状态保留
- 只要流程本身跑完，退出码不应把 `degraded` 直接当成脚本失败

---

## 2. 完成内容

- 新增 Phase 69 规格文档
- 在 `examples/watchlist_shared.py` 中新增 `build_schedule_hint`
- 在 `examples/daily_watchlist_daily_run.py` 中写入 `schedule_hint`
- 在 `examples/daily_watchlist_flow.py` 中展示 `schedule_hint`
- 在 `examples/daily_watchlist_archive_viewer.py` 中展示 `schedule_hint`
- 在 `examples/daily_watchlist_acceptance.py` 中检查 `schedule_hint`
- 更新 `README_QUANT.md`、`specs/NEXT_STAGE_DEVELOPMENT_ROADMAP.md`、`specs/TASK_CHECKLIST.md`

---

## 3. 运行语义调整

本阶段同步调整了退出码语义：

- `ok` 和 `degraded` 都表示脚本执行成功
- 只有真实执行失败才返回非 0 退出码

这样做的目的，是避免自动化把“可运行但降级”的结果误判成“脚本失败”。

---

## 4. 验证结果

已完成轻量验证，当前变更满足：

- 语法可编译
- `schedule_hint` 能写入运行状态
- 默认工作流能读取并展示运行就绪提示
- 留档查看和投产验收能识别新契约

补充说明：

- 当前环境里的真实预检本身仍然阻断，所以 `daily_watchlist_daily_run.py` 和 `daily_watchlist_flow.py` 在本次验证中返回非 0
- 这类返回值对应的是门禁阻断，不是本阶段新增的脚本错误
- `schedule_hint` 在这种情况下正确落到了 `blocked`

---

## 5. 结果说明

Phase 69 让项目从“有门禁、有行动、有回看”继续推进到“有运行就绪提示”。

这一步很小，但对后续自动化很有用，因为它把调度前置判断做成了共享契约，而不是分散在多个脚本里的临时逻辑。
