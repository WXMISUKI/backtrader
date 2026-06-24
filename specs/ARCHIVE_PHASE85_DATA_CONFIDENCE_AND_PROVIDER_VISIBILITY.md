# Phase 85 归档：真实数据稳定性增强与 provider 可见性收紧

## 1. 背景

Phase 84 已经统一了 `latest.json` 主契约，但真实数据稳定性和 provider 可见性仍然需要继续收紧，避免“契约完整但来源不可见”。

Phase 85 的重点是把 provider 视图和数据可信度稳定下沉到健康预检、流水线、验收和基线入口。

## 2. 本次完成内容

- 健康预检已可稳定输出 `history_selected_provider`、`history_provider_attempts`、`history_provider_summary`
- 流水线和验收继续消费同一套数据可信度与 provider 语义
- 基线入口继续把 provider 可见性列为高优先级证据
- 补充 Phase 85 的规格和归档文档

## 3. 结果

这一阶段的核心变化是：

- 数据可信度和 provider 可见性成为日常入口的主语义
- 降级不再只是一个总状态，而是可追踪、可解释的结果
- 入口之间对同一份数据真相的消费更一致

## 4. 验收口径

- `history_selected_provider` 能在主要入口里稳定看到
- `provider_attempts` 和 `fallback_strategy` 不再只停留在底层
- 低可信数据更倾向于观察或跳过，不被误当作强信号
- 字段缺失不再与真实降级混淆

## 5. 后续建议

Phase 85 完成后，可以继续观察是否还需要把 provider 语义进一步压缩进更短的第一屏摘要，但不建议先扩新模块。
