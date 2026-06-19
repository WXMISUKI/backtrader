# 归档文档：Phase 5 智能体与编排器共享路由

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 5 智能体与编排器共享路由归档报告 |
| 版本 | v1.0 |
| 完成日期 | 2026-06-18 |
| 状态 | ✅ 已完成 |

---

## 1. 本阶段目标

让智能体客户端与 StockOrchestrator 复用同一份意图解析逻辑，避免路由规则在不同入口分叉。

---

## 2. 完成内容

### 2.1 新增规格

- `specs/SDD_PHASE5_SHARED_ROUTING.md`

### 2.2 新增/更新实现

- `core/agent/routing.py`
- `core/agent/client.py`
- `core/agent/runtime.py`
- `core/orchestrator.py`

### 2.3 新增知识库沉淀

- `docs/knowledge-base/QUANT_AGENT_LEARNING_MAP.md`

---

## 3. 已实现能力

- 客户端和编排器复用同一份解析规则
- 可提取股票代码和风险偏好
- 可输出结构化 route 结果
- 编排器结果中可附带 route 元信息

---

## 4. 验证结果

轻量验证已通过：

- `py_compile` 通过
- `parse_intent("市场大盘怎么样")` 在运行时和编排器中一致
- `StockOrchestrator().route("帮我做回测 000001")` 返回 `backtest`

---

## 5. 结论

共享路由把“智能体入口”和“编排器入口”统一成同一套规则，后续新增意图时只需要改一处。

这会显著降低后续维护成本，也更利于审计和解释。

---

## 6. 下一阶段建议

1. 做复合意图优先级优化
2. 增加路由审计日志
3. 再推进多智能体协作草案

