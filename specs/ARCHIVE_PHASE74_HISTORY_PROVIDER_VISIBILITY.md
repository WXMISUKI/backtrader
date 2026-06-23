# 归档文档：Phase 74 历史行情 provider 可见性下沉

---

## 1. 归档结论

Phase 74 没有继续修改历史行情路由本身，而是把 Phase 73 已经选出来的 `selected_provider` 和 `provider_attempts` 显性下沉到了日常使用入口。

这一步的核心价值很简单：

- 路由层知道今天是谁在工作
- 日常健康预检也能看见
- 统一流水线的终端和 JSON 都能看见
- 投产验收可以直接确认这条可见性没有丢

它解决的是“路由已经生效，但使用侧看不见”的断层问题。

---

## 2. 已完成内容

- 在 `examples/watchlist_shared.py` 中透传历史 provider 结果
- 在健康摘要里新增 `history_selected_provider`、`history_provider_attempts`、`history_provider_summary`
- 在 `examples/watchlist_data_health.py` 中展示 provider 信息
- 在 `examples/daily_watchlist_pipeline.py` 中展示 provider 信息
- 在 `examples/daily_watchlist_acceptance.py` 中增加 provider 可见性检查
- 新增最小回归测试 `tests/test_history_provider_visibility.py`
- 更新运行说明，补充 provider 与多源路由的查看方式
- 更新路线图与任务清单，固化 Phase 74 的完成态

---

## 3. 验收结果

本阶段回归测试已通过：

```text
10 passed in 3.63s
```

说明 provider 透传、预检展示、流水线展示和验收检查这条链路已经稳定打通。

---

## 4. 关键观察

- 多源路由已经不再只停留在底层治理快照里
- 日常预检和统一流水线现在能直接看见今天最终用了哪个 provider
- `provider_attempts` 的价值主要在诊断，不是做额外路由决策
- 这一阶段依然没有修改路由优先级，只是把结果往上送

---

## 5. 本阶段收口边界

本阶段没有新增 provider，没有修改 cookie 刷新逻辑，没有重写历史行情获取策略。

我们只做了四件事：

1. 把 provider 结果显性化
2. 把展示结果接到日常入口
3. 把验收项补成最小门禁
4. 把阶段状态写回路线图和任务清单

---

## 6. 后续建议

下一步如果继续推进历史行情链路，优先关注两类工作：

1. 让 provider 视图继续进入更多日常诊断入口
2. 继续观察 AKShare 与东财主源在不同环境中的稳定性差异

当前阶段已经足够支撑“先看今天谁在工作，再看今天数据能不能用”的日常节奏。
