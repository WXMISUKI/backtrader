# 软件设计规格说明 (SDD)
# Phase 8: 统一输出字段枚举与消费契约

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 8 统一输出字段枚举与消费契约 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-19 |
| 状态 | 草案 |

---

## 1. 背景

当前项目已经具备：

- 统一工具输出信封
- 统一任务协议
- 任务回放与学习统计
- 路由审计和运行监控

但实际消费时，上层仍可能依赖“隐式字段理解”，例如：

- 前端猜测 `meta` 里有哪些关键字段
- 调试工具猜测 `data` 里有哪些嵌套结构
- 智能体消息里对 `summary`、`data_source`、`task_protocol` 的使用不完全一致

如果不收口，系统会出现“接口看似统一，消费方式仍然分裂”的问题。

因此 Phase 8 的重点是把项目对外输出字段枚举和消费契约固定下来。

---

## 2. 目标

### 2.1 总目标

构建一套统一输出字段规范，让工具、编排器、智能体客户端和回放统计都遵循同一套对外契约。

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 字段统一 | 固定核心输出字段 |
| 结构统一 | `ok/tool/category/data_source/summary/data/meta` 保持一致 |
| 契约统一 | 下游只消费稳定字段，不依赖隐式结构 |
| 可扩展 | 新字段只能增加在约定位置 |
| 可审计 | 输出契约变化可追踪 |

---

## 3. 核心字段

### 3.1 工具输出字段

建议所有工具输出都使用：

- `ok`
- `tool`
- `category`
- `data_source`
- `summary`
- `data`
- `meta`

### 3.2 任务协议字段

建议统一任务协议在对外返回时保留：

- `task_protocol`
- `workflow_id`
- `plan_audit_id`
- `route_audit_id`
- `result_audit_id`

### 3.3 运行治理字段

建议统一运行治理补充：

- `governance`
- `is_degraded`
- `cache_hit`
- `overall_ok`

---

## 4. 消费契约

### 4.1 智能体客户端

智能体客户端应优先消费：

- `summary`
- `data_source`
- `task_protocol`
- `governance`

### 4.2 编排器

编排器应优先消费：

- `ok`
- `tool`
- `data`
- `meta`
- `governance`

### 4.3 回放与统计

回放与统计应优先消费：

- `workflow_id`
- `event_type`
- `phase`
- `template_id`
- `template_hit`

---

## 5. 设计原则

### 5.1 显式优先

字段必须显式暴露，不鼓励上层再去深挖内部对象结构。

### 5.2 位置固定

核心字段只能出现在约定层级，避免上层四处找字段。

### 5.3 兼容优先

新增字段可以扩展，但不能破坏已有字段。

---

## 6. 适用范围

- `core/agent/serialization.py`
- `core/agent/tools.py`
- `core/agent/client.py`
- `core/orchestrator.py`
- `core/agent/task_protocol.py`
- `core/agent/replay.py`

---

## 7. 验收标准

- 工具输出字段稳定
- 任务协议字段稳定
- 编排器和客户端都按统一契约返回
- 回放与统计工具的输出位置稳定
- 后续新增工具不会引入新的返回风格

---

## 8. 归档要求

当以下内容完成后，可将本规格归档：

1. 输出字段常量或约束实现完成
2. 工具和编排层完成收口
3. 轻量验证通过
4. 形成归档文档

---

## 9. 与已有规格的关系

- `SDD_PHASE6_TASK_PROTOCOL.md` 负责任务语义统一
- `SDD_PHASE7_REPLAY_LEARNING.md` 负责回放与学习统计
- 本规格负责统一对外输出字段与消费契约

