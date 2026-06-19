# 软件设计规格说明 (SDD)
# Phase 18: 智能体能力目录与自动路由升级

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 18 智能体能力目录与自动路由升级 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-19 |
| 状态 | 草案 |

---

## 1. 背景

当前项目已经具备统一决策、协作工作流、模板选择、回放统计、会话反馈、模型治理和运行监控等能力。

但从智能体接入的角度看，项目的能力仍然分散在多个工具和入口里，缺少一个“先理解项目能做什么，再选择最合适路径”的能力目录。

如果继续只扩展原子工具，容易出现：

- 工具越来越碎，模型路由越来越乱
- 用户不知道该先走哪个入口
- 智能体缺少稳定的推荐顺序
- 新增能力无法形成统一认知

因此，本阶段不再继续扩展底层算法，而是把现有能力整理成面向智能体的能力目录，并将其接入自动路由和统一输出体系。

---

## 2. 目标

### 2.1 总目标

构建一个面向智能体的项目能力目录，让系统能够明确回答：

- 当前项目有哪些高价值能力
- 每个能力适合什么场景
- 默认优先调用什么入口
- 失败或数据不足时如何回退

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 能力可见 | 将现有能力整理成统一目录 |
| 路由可读 | 能解释为什么推荐某个入口 |
| 路径可选 | 能同时给出主路径、辅助路径和回退路径 |
| 输出统一 | 目录也遵守统一输出契约 |
| 接入简单 | 智能体只需一个目录入口即可查看能力 |

---

## 3. 范围

### 3.1 纳入范围

- 统一决策入口
- 协作工作流
- 市场概览
- 风控
- 个股分析
- 推荐
- 回测
- 报告
- 模型治理
- 运行监控
- 会话与反馈
- 工作流模板

### 3.2 不纳入范围

- 新增交易策略算法
- 新增数据源适配
- 新增部署体系
- 复杂多智能体编排平台

---

## 4. 设计原则

### 4.1 先目录，再扩展

先把现有能力收口成目录，再考虑新增能力，避免继续堆碎工具。

### 4.2 先推荐，再执行

目录不仅要列出能力，还要给出推荐顺序和适用场景。

### 4.3 先统一，再细分

对外先保持统一 schema，再在内部区分不同场景。

### 4.4 先薄层，再增强

目录入口只做组织与推荐，不承担复杂业务计算。

---

## 5. 核心设计

### 5.1 能力目录结构

能力目录建议至少包含以下字段：

- `directory_version`
- `focus`
- `capabilities`
- `recommended_path`
- `fallback_path`
- `high_value_paths`
- `next_actions`
- `meta`

### 5.2 能力分组

#### A. 决策类

- `answer_decision_request`
- `plan_collaboration`
- `execute_workflow`

#### B. 分析类

- `analyze_stock`
- `analyze_fundamental`
- `get_market_overview`
- `get_risk_profile`

#### C. 组合类

- `recommend_by_risk`
- `recommend_long_term`
- `recommend_short_term`
- `screen_stocks`

#### D. 验证类

- `run_backtest`
- `generate_stock_report`

#### E. 治理类

- `get_model_governance_status`
- `evaluate_model_release`
- `get_runtime_health`
- `evaluate_runtime_health`

#### F. 复盘类

- `create_decision_session`
- `submit_decision_feedback`
- `get_decision_session_replay`
- `get_decision_session_stats`
- `get_workflow_replay`
- `get_workflow_learning_stats`

#### G. 模板类

- `list_workflow_templates`
- `get_workflow_template_stats`

### 5.3 自动路由原则

当用户询问以下问题时，优先给出能力目录或对应能力入口：

- “项目能做什么”
- “有哪些能力”
- “工具目录”
- “接入能力”
- “能力清单”
- “下一步该做什么”
- “该先用哪个入口”

当用户明确表达业务任务时，继续保持现有路由优先级：

- 回测优先走 `run_backtest`
- 市场优先走 `get_market_overview`
- 风控优先走 `get_risk_profile`
- 推荐优先走 `recommend_by_risk`
- 工作流优先走 `execute_workflow`

---

## 6. 统一输出约定

目录入口也必须使用统一工具信封：

```json
{
  "ok": true,
  "tool": "list_project_capabilities",
  "category": "workflow",
  "data_source": "knowledge_base",
  "summary": "已返回项目能力目录。",
  "data": {},
  "meta": {
    "payload_version": "1.0",
    "generated_at": "2026-06-19T00:00:00Z"
  }
}
```

目录内容中的单条能力建议包含：

- `id`
- `name`
- `category`
- `primary_tool`
- `support_tools`
- `when_to_use`
- `fallback_tools`
- `output_contract`
- `notes`

---

## 7. 验收标准

- 可以返回统一的项目能力目录
- 可以给出面向智能体的推荐路径
- 可以说明每个能力的适用场景
- 可以与现有路由和工具注册表共存
- 可以在本地快速验证，无需新增部署依赖

---

## 8. 任务拆分

### 8.1 规格阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 18.0 | 编写 SDD 规格文档 | P0 | ✅ | 本文件 |

### 8.2 实现阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 18.1 | 实现能力目录数据结构 | P0 | ⬜ | `core/agent/capability_directory.py` |
| 18.2 | 注册能力目录工具入口 | P0 | ⬜ | `list_project_capabilities` |
| 18.3 | 扩展意图路由规则 | P0 | ⬜ | 项目能力/工具目录/能力清单 |
| 18.4 | 扩展客户端与编排器入口 | P0 | ⬜ | 路由、运行时、提示词 |
| 18.5 | 统一输出与分类标记 | P1 | ⬜ | `workflow` / `knowledge_base` |

### 8.3 归档阶段

| # | 任务 | 优先级 | 状态 | 备注 |
|---|------|--------|------|------|
| 18.6 | 编写归档文档 | P1 | ⬜ | 记录验证结果和下一步建议 |
| 18.7 | 更新知识库与任务清单 | P1 | ⬜ | 沉淀能力目录与路由原则 |

---

## 9. 下一步建议

1. 先落 `list_project_capabilities`，让智能体知道项目当前有哪些高价值能力
2. 再把“能力目录”接入路由，处理“项目能做什么/有哪些能力”这类问题
3. 最后把知识库和任务清单同步收口，作为下一阶段默认入口

