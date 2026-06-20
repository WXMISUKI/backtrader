# 归档文档：Phase 27 统计与洞察摘要标准化

---

## 1. 归档结论

Phase 27 已完成统计与洞察摘要标准化。

本阶段没有新增接口、数据库或复杂报表，而是把 `/decision/stats` 与 `/decision/insights` 的阅读方式统一到四段式摘要模板，让决策、统计、洞察三类结果都能先看结论，再看细节。

---

## 2. 已完成内容

- 新增 Phase 27 规格文档
- `DecisionSessionStore.get_stats()` 增加 `stats_summary`
- `DecisionSessionStore.get_feedback_insights()` 增加 `insights_summary`
- 统计与洞察结果顶层暴露 `结论 / 依据 / 风险 / 下一步动作`
- 统计与洞察结果同步暴露英文兼容字段 `conclusion / basis / risk / next_action`
- `examples/api_demo.py` 在 JSON 明细前优先打印摘要卡片
- `README_QUANT.md` 补充统一摘要字段说明
- `specs/TASK_CHECKLIST.md` 记录 Phase 27 完成状态

---

## 3. 验证目标

轻量验证的目标是确认摘要标准化不破坏原有调用：

- `/decision/stats` 仍然保留原始统计明细
- `/decision/insights` 仍然保留原始洞察明细
- `stats_summary` 可直接读取四段式摘要
- `insights_summary` 可直接读取四段式摘要
- 联调用例会优先展示摘要，再展示 JSON 明细

---

## 4. 当前收口边界

本阶段只做表达标准化，不做新的推理能力，也不增加新的聚合接口。

统计与洞察里的样本量提示只作为使用提醒，避免在反馈较少时过度解读结果。

---

## 5. 本阶段结论

统计与洞察摘要标准化的价值在于，它把反馈闭环从“有数据可查”推进到“第一眼就知道该怎么用”。

后续继续迭代时，默认优先保持 `decision_summary`、`stats_summary`、`insights_summary` 三类摘要的一致性。

---

## 6. 后续建议

1. 真实联调时优先观察三类摘要是否足够直接
2. 如果继续增强反馈闭环，优先优化摘要表达，而不是新增入口
3. 当反馈样本足够多后，再考虑增加趋势对比或时间窗口维度
