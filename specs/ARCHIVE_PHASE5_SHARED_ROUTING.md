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

将智能体客户端与 StockOrchestrator 的自然语言路由统一到同一份共享逻辑。

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

- 智能体与编排器复用同一份意图解析逻辑
- 可提取股票代码和风险偏好
- 可返回结构化 route 计划
- 编排器结果中可看到 route 元信息

---

## 4. 验证结果

轻量验证已通过：

- `py_compile` 通过
- `parse_intent("帮我回测 000001")` 在运行时和编排器中结果一致
- `StockOrchestrator().route("帮我回测 000001")` 能返回 `run_backtest`

---

## 5. 结论

这一步把“智能体路由”和“编排器路由”收口成同一套规则，避免后面规则越写越分叉。

对于后续多智能体协作，这是一块很重要的地基。

---

## 6. 下一阶段建议

1. 给复合意图做更细的优先级
2. 再考虑多智能体协作草案
3. 如果要上更强的解释能力，可以把 route 结果持久化到审计日志

