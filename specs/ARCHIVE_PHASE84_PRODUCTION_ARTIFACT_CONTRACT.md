# Phase 84 归档：投产产物契约统一与 `latest.json` 写入修复

## 1. 背景

Phase 83 解决了关键门禁与关键简报的薄层透传，但最终消费端仍然可能因为 `latest.json` 契约不完整而误判结构失败。

Phase 84 的目标是把关键产物统一写入 `latest.json`，让基线、验收和回看都以同一份契约为准。

## 2. 本次完成内容

- `examples/daily_watchlist_pipeline.py` 现在会写入关键门禁与简报产物
- `examples/daily_watchlist_daily_run.py` 现在优先消费 pipeline 产物，不再重复造同一层数据
- `examples/daily_watchlist_acceptance.py` 现在优先检查 `latest.json` 契约
- 补充了 Phase 84 的规格与归档文档

## 3. 结果

这一阶段的核心变化是：

- `latest.json` 成为主消费契约
- 结构字段缺失和真实数据降级的边界更清楚
- 日常链路继续保持薄层，不向外扩编排

## 4. 验收口径

- `latest.json` 稳定包含关键门禁与简报
- `daily_run` 和 `acceptance` 优先消费 `latest.json`
- 字段缺失不再被误读成数据降级
- 数据降级仍然可以继续给出 `caution`

## 5. 后续建议

Phase 84 之后，可以继续观察 `history_selected_provider` 的稳定性，但不建议在这个阶段之前再扩展新的分析层。
