# 软件设计规格说明 (SDD)
# Phase 5: 统一工作流 Schema

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 5 统一工作流 Schema SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-19 |
| 状态 | 草案 |

---

## 1. 背景

当前项目已经有：

- 统一工具信封
- 路由审计信封
- 协作计划结构

但协作执行层还需要一份统一 schema，确保：

- 规划、执行、审计、回放都说同一种语言
- 前端、调试、日志、知识库能消费同样的结果
- 后续新增 workflow 时不会再造一套结构

---

## 2. 目标

### 2.1 总目标

将协作执行结果标准化为统一工作流 schema。

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 统一输入 | 工作流入口可接受自然语言或已生成计划 |
| 统一过程 | 节点字段、状态、依赖一致 |
| 统一输出 | 结果结构稳定，便于二次消费 |
| 统一审计 | 规划、执行、失败原因可追踪 |
| 统一归档 | 便于知识库和后续工作复用 |

---

## 3. 核心 schema

### 3.1 工作流计划

建议字段：

- `objective`
- `mode`
- `primary_intent`
- `primary_tool`
- `primary_reason`
- `tasks`
- `execution_order`
- `roles`
- `fallback`
- `candidates`
- `matched_terms`
- `route`
- `meta`

### 3.2 工作流节点

建议字段：

- `id`
- `intent`
- `tool`
- `role`
- `description`
- `arguments`
- `depends_on`
- `status`
- `summary`
- `data_source`
- `ok`
- `error`

### 3.3 工作流结果

建议字段：

- `workflow_id`
- `ok`
- `tool`
- `category`
- `data_source`
- `summary`
- `data`
- `meta`

其中 `data` 需要包含：

- `plan`
- `steps`
- `execution_order`
- `is_degraded`
- `route_audit_id`

---

## 4. 输出原则

### 4.1 兼容统一工具信封

工作流结果仍然应当沿用项目现有的统一输出结构，避免上层多套消费逻辑。

### 4.2 过程优先结构化

执行过程必须比最终摘要更结构化，方便追踪和复盘。

### 4.3 支持降级标识

工作流执行中出现任何支持节点失败，都必须显式标识。

---

## 5. 验收标准

- 协作计划和工作流结果字段稳定
- 工具输出和工作流输出可以共存
- 审计日志能够直接消费工作流 schema
- 后续新增 workflow 时不需要再定义新格式

---

## 6. 归档要求

当以下内容完成后，可将本规格归档：

1. 工作流执行结果统一化完成
2. 路由审计可消费工作流 schema
3. 轻量验证通过
4. 形成归档文档

