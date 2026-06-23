# 下一阶段开发方向路线图

## 1. 背景

当前项目已经从单点量化功能，逐步收敛到自选股日常投产流程：

- 默认日常流程：`examples/daily_watchlist_flow.py`
- 数据健康检查：`examples/watchlist_data_health.py`
- 日常决策清单：`examples/daily_watchlist_decision.py`
- 投产验收：`examples/daily_watchlist_acceptance.py`
- 留档回看：`examples/daily_watchlist_archive_viewer.py`
- 诊断收口包：`examples/daily_watchlist_diagnosis_bundle.py`

Phase 40 到 Phase 59 已经完成了大量“入口收口、诊断展示、验收对齐、反馈归档”工作。下一阶段不应继续堆更多入口和更多报告，而应把现有主链路升级为更稳定、更可信、更适合每天使用的投产闭环。

Phase 60、Phase 61、Phase 62、Phase 63、Phase 64、Phase 65、Phase 66 也已经按顺序收口，当前主线已经从“看结果”推进到“先门禁，再行动”，再到“行动提示更清楚”“样本归因更清楚”和“运行节奏更稳定”。

## 2. 总体判断

下一阶段最值得推进的主线是：

> 日常投产质量门禁与真实决策闭环。

目标不是让系统输出更多内容，而是让系统每天跑完以后能回答三个问题：

1. 今天这份结果能不能用于参考？
2. 哪些股票可以进入行动清单，哪些只能观察或跳过？
3. 最近一段时间的建议效果是否值得继续信任？

## 3. 优先级排序

| 优先级 | 方向 | 价值判断 | 是否建议作为下一阶段 |
|---|---|---|---|
| P0 | 投产质量门禁 | 直接解决“今天结果能不能用”的问题，是最快提升投产可靠性的方向 | 是 |
| P0 | 真实数据稳定性增强 | 防止数据降级时产生误导性建议，是量化系统的基础保障 | 是 |
| P1 | 反馈效果闭环 | 从记录反馈升级到评估建议效果，为后续优化规则和模型提供依据 | 是 |
| P1 | 决策输出行动化 | 把报告进一步压缩成每日可执行清单，提高日常使用效率 | 是 |
| P2 | 策略和模型增强 | 有价值，但应等数据可信度和反馈评估稳定后再推进 | 暂缓 |
| P2 | 前端仪表盘和自动调度 | 能提升体验，但当前命令行和归档链路已经能支撑私人投产验证 | 暂缓 |
| P3 | 自动交易 | 当前仍应坚持建议优先、执行保守，不进入自动交易 | 暂不推进 |

## 4. 推荐阶段拆分

### 阶段 A：投产质量门禁

目标：每天跑完默认流程后，系统明确输出 `pass / warn / block`，告诉用户今天结果是否适合用于决策参考。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| A.1 | 编写 Phase 60 SDD | P0 | 明确质量门禁输入、输出、规则、智能体协作边界 |
| A.2 | 定义 `production_gate` 输出结构 | P0 | 至少包含 `status`、`reason`、`allowed_actions`、`blocked_actions`、`evidence` |
| A.3 | 汇总现有健康、诊断、验收材料 | P0 | 复用 `daily_summary`、`diagnosis_evidence`、`acceptance`、`health_score` |
| A.4 | 接入默认日常流程 | P0 | 在 `daily_watchlist_flow.py` 输出中加入门禁结果 |
| A.5 | 接入诊断收口包 | P0 | 在 `daily_watchlist_diagnosis_bundle.py` 中展示最终门禁状态 |
| A.6 | 更新 README 使用说明 | P1 | 明确每天优先看 `production_gate` |

验收标准：

- 默认日常流程输出中有 `production_gate`。
- 门禁结果能区分 `pass / warn / block`。
- 数据明显降级时不会给出强行动建议。
- 规则保持轻量，不引入数据库、不重写业务链路。

### 阶段 B：真实数据稳定性增强

目标：减少“结果看起来正常，但数据其实不可用或已降级”的风险。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| B.1 | 统一降级原因枚举 | P0 | 固定 `history_unavailable`、`fundamental_unavailable`、`quality_missing_columns`、`empty_payload`、`external_api_error`、`cache_fallback` 等 |
| B.2 | 增强每只股票的数据可信度 | P0 | 增加 `data_confidence`，区分行情可信度和基本面可信度 |
| B.3 | 优化健康摘要 | P0 | 在 `build_data_health_summary` 中输出更稳定的诊断字段 |
| B.4 | 决策前置数据门禁 | P0 | 低可信股票不能进入强行动分组 |
| B.5 | 在诊断包展示主要数据源问题 | P1 | 显示今天主要降级来自行情、基本面、缓存还是外部接口 |

验收标准：

- 每只股票都有明确的数据可信度。
- 数据低可信时进入 `数据不足` 或观察类分组。
- 诊断输出能直接定位主要数据问题。

### 阶段 C：反馈效果闭环

目标：从“记录反馈”升级为“评估建议是否有效”。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| C.1 | 记录建议基准价格 | P0 | 每日归档保存建议动作、价格、置信度、数据可信度 |
| C.2 | 增加 T+1 / T+3 / T+5 回看 | P0 | 先做轻量涨跌幅验证，不做复杂归因 |
| C.3 | 生成建议命中率摘要 | P1 | 输出重点关注样本数、正向样本数、平均涨跌幅、排除样本数 |
| C.4 | 排除低可信样本 | P1 | 数据不足或明显降级样本不纳入建议效果评估 |
| C.5 | 接入诊断收口包 | P1 | 让日常入口能看到最近建议效果趋势 |

验收标准：

- 可以基于历史归档生成最近 N 天建议效果。
- 能区分有效样本和数据不足样本。
- 不训练模型，只做可解释的轻量评估。

### 阶段 D：日常执行清单行动化

目标：把长报告压缩成当天可读、可执行的行动清单。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| D.1 | 新增 `action_list` | P0 | 输出 `review_now`、`hold_watch`、`wait`、`skip_due_to_data` |
| D.2 | 强化持仓上下文 | P0 | 已持仓股票优先显示仓位、成本、风险提示 |
| D.3 | 生成终端短摘要 | P1 | 每天跑完直接看到 3 到 5 条最重要行动 |
| D.4 | JSON 保留完整证据 | P1 | 终端短，JSON 完整，便于回溯 |

验收标准：

- 默认流程终端输出可直接指导当天查看顺序。
- 每条行动都有简短原因和证据来源。
- 门禁为 `block` 时不输出强行动建议。

### 阶段 E：提示语境联动

目标：把 `production_gate`、`action_list` 和 `run_cadence` 再收成一份统一的 `prompt_context`，让提示词、Skill 和日常入口共用同一套语境。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| E.1 | 编写 Phase 67 SDD | P0 | 明确提示语境输入、输出、规则和协作边界 |
| E.2 | 定义 `prompt_context` 输出结构 | P0 | 至少包含 `summary_text`、`prompt_text`、`read_order`、`rules` |
| E.3 | 接入默认日常流程 | P0 | 在 `daily_watchlist_daily_run.py`、`daily_watchlist_flow.py` 和留档查看里写入并展示提示语境 |
| E.4 | 接入诊断收口包和验收 | P1 | 让 `daily_watchlist_diagnosis_bundle.py` 和 `daily_watchlist_acceptance.py` 也能读取同一份提示语境 |
| E.5 | 更新智能体默认提示词 | P1 | 让 `core/agent/client.py` 明确识别日常语境协议 |
| E.6 | 更新 README 与任务清单 | P1 | 把新的阅读顺序写入日常使用说明 |

验收标准：

- `prompt_context` 能从统一流程、默认工作流和留档查看里读到。
- 提示词/Skill 可以直接按 `production_gate -> action_list -> run_cadence` 的顺序消费。
- `block` 门禁下不会冒出强行动建议。
- 规则保持轻量，不引入新的编排平台。

### 阶段 F：回看呈现收紧

目标：把 `production_gate`、`action_list`、`run_cadence`、`prompt_context` 和反馈效果收成一份统一的 `review_brief`，让回看入口先给摘要，再给正文。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| F.1 | 编写 Phase 68 SDD | P0 | 明确回看摘要输入、输出、规则和协作边界 |
| F.2 | 定义 `review_brief` 输出结构 | P0 | 至少包含 `summary_text`、`next_step`、`risk_note`、`read_order`、`key_points` |
| F.3 | 接入日常回看入口 | P0 | 在 `daily_watchlist_review.py` 里先输出回看摘要 |
| F.4 | 接入留档查看入口 | P0 | 在 `daily_watchlist_archive_viewer.py` 里先输出回看摘要 |
| F.5 | 接入投产验收 | P1 | 让 `daily_watchlist_acceptance.py` 检查回看摘要是否可用 |
| F.6 | 更新 README 与任务清单 | P1 | 把回看时的推荐阅读顺序写清楚 |

验收标准：

- 日常回看入口能先看到 `review_brief`。
- 留档查看入口能先看到 `review_brief`。
- 回看摘要能区分 `pass / warn / block`。
- 反馈效果仍保留在正文里，不被摘要替代。

### 阶段 G：轻量调度准备

目标：把 `production_gate`、`run_cadence`、`prompt_context` 和 `review_brief` 再收成一份很薄的 `schedule_hint`，让默认运行、工作流和留档查看都能判断下一次是否适合继续自动推进。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| G.1 | 编写 Phase 69 SDD | P0 | 明确调度准备输入、输出、规则和协作边界 |
| G.2 | 定义 `schedule_hint` 输出结构 | P0 | 至少包含 `status`、`summary_text`、`next_step`、`next_run_mode`、`next_run_window`、`read_order`、`rules` |
| G.3 | 接入默认日常运行 | P0 | 在 `daily_watchlist_daily_run.py` 输出并写入调度准备 |
| G.4 | 接入默认工作流和留档查看 | P0 | 在 `daily_watchlist_flow.py` 和 `daily_watchlist_archive_viewer.py` 展示调度准备 |
| G.5 | 接入投产验收 | P1 | 让 `daily_watchlist_acceptance.py` 检查调度准备是否可用 |
| G.6 | 更新 README 与任务清单 | P1 | 把“运行就绪提示”的阅读顺序写清楚 |

验收标准：

- `schedule_hint` 能从默认运行、默认工作流和留档查看里读到。
- `schedule_hint` 只负责运行就绪提示，不新增真正的调度系统。
- `degraded` 仍可视为运行成功，但会明确标成 `caution`，避免误伤脚本退出码。
- 规则保持轻量，不引入新的编排平台。

### 阶段 H：日常协作总包收束

目标：把 `production_gate`、`action_list`、`run_cadence`、`prompt_context`、`review_brief` 和 `schedule_hint` 再收成一份统一的 `daily_collaboration_pack`，让智能体和 Skill 直接消费一份完整的日常协作总包。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| H.1 | 编写 Phase 70 SDD | P0 | 明确协作总包输入、输出、规则和协作边界 |
| H.2 | 定义 `daily_collaboration_pack` 输出结构 | P0 | 至少包含 `summary_text`、`prompt_text`、`read_order`、`rules`、`evidence` |
| H.3 | 接入默认日常运行 | P0 | 在 `daily_watchlist_daily_run.py` 输出并写入协作总包 |
| H.4 | 接入默认工作流和留档查看 | P0 | 在 `daily_watchlist_flow.py` 和 `daily_watchlist_archive_viewer.py` 展示协作总包 |
| H.5 | 接入投产验收和智能体提示词 | P1 | 让 `daily_watchlist_acceptance.py` 和 `core/agent/client.py` 优先读取协作总包 |
| H.6 | 更新 README 与任务清单 | P1 | 把协作总包的阅读顺序写清楚 |

验收标准：

- `daily_collaboration_pack` 能从默认运行、默认工作流和留档查看里读到。
- 智能体提示词能优先识别协作总包，再按其内置顺序回退。
- 它只做总包收束，不新增新的分析模型或调度平台。
- `schedule_hint` 继续作为其中一层，不被替代，但也不再单独承担所有协作职责。

### 阶段 I：东方财富历史行情数据源韧性与回退策略

目标：把东财历史行情失败从“只知道降级了”升级成“知道哪一层失败、失败编码是什么、回退策略是什么”，让日常健康摘要和联调脚本直接消费统一语义。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| I.1 | 编写 Phase 72 SDD | P0 | 明确失败分层、失败编码和回退策略 |
| I.2 | 定义结构化失败语义 | P0 | 至少包含 `failure_kind`、`failure_stage`、`failure_code`、`fallback_strategy` |
| I.3 | 接入默认历史治理快照 | P0 | 在 `core/data/eastmoney_api.py` 里补齐元数据 |
| I.4 | 接入联调和健康摘要 | P1 | 在 `examples/eastmoney_live_check.py` 和 `examples/watchlist_shared.py` 展示新字段 |
| I.5 | 编写回归测试 | P0 | 固定远端断开和质量失败两类语义 |
| I.6 | 更新运行说明与归档 | P1 | `README_QUANT.md` / `specs/ARCHIVE_PHASE72_EASTMONEY_HISTORY_RESILIENCE.md` |

验收标准：

- 历史行情失败时能稳定看到分层后的失败语义。
- 联调脚本和健康摘要不再只依赖泛化的 `mock` 和 `fallback_reason`。
- 当前回退仍然是 mock，但回退原因和策略更清楚。
- 这一步不引入新的数据源，只把现有失败说清楚、锁住。

### 阶段 J：历史行情多源路由与 cookie 刷新自动化

目标：在 Phase 72 的失败分层基础上，把真实历史行情从“可解释失败”推进到“可绕行恢复”，并把 cookie 刷新收束成可复用的本地自动化步骤。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|---|---|---|
| J.1 | 编写 Phase 73 SDD | P0 | 明确 provider 契约、多源路由和 cookie 自动化边界 |
| J.2 | 定义 provider 路由契约 | P0 | 统一历史行情 provider 输出结构 |
| J.3 | 接入 AKShare 备选源 | P0 | 把 `akshare_hist` 作为稳定备选候选 |
| J.4 | 预留同花顺候选 | P1 | 先做最小探测与可用性标记 |
| J.5 | 实现 cookie 刷新 helper | P0 | 把手工抓 cookie 的流程收成本地自动化 |
| J.6 | 写入治理快照与健康摘要 | P1 | 记录 `selected_provider` 与 `provider_attempts` |
| J.7 | 增加回归测试 | P0 | 覆盖主源失败、备源接管和最终兜底 |
| J.8 | 更新运行说明与归档 | P1 | 把新路由和 helper 的日常用法写清楚 |

验收标准：

- 东财失败后系统可以尝试 AKShare 等备选源。
- 最终使用了哪个 provider 在治理快照里可见。
- cookie 刷新不再完全依赖手工拼接。
- mock 仍然保留，但只作为最后兜底。

### 阶段 K：历史行情 provider 可见性下沉

目标：把 Phase 73 的多源路由结果显性化到日常健康摘要、统一流水线和验收入口，让最终 provider 和尝试链一眼可见，避免“路由已生效但使用侧看不见”的断层。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| K.1 | 编写 Phase 74 SDD | P0 | 明确 provider 可见性下沉边界 |
| K.2 | 透传历史 provider 到健康摘要 | P0 | 在 `examples/watchlist_shared.py` 输出 provider 视图 |
| K.3 | 在健康预检中展示 provider | P0 | `examples/watchlist_data_health.py` 直接可读 |
| K.4 | 在日常流水线中展示 provider | P0 | `examples/daily_watchlist_pipeline.py` 条目可见 |
| K.5 | 在投产验收中检查 provider | P1 | `examples/daily_watchlist_acceptance.py` 作为门禁项 |
| K.6 | 增加最小回归测试 | P0 | 固定 provider 透传语义 |
| K.7 | 更新运行说明 | P1 | `README_QUANT.md` |
| K.8 | 编写归档文档并更新清单 | P1 | 记录完成态并固化任务状态 |

验收标准：

- 健康预检能看见 `history_selected_provider` 与尝试链。
- 日常流水线条目和 JSON 都能看见 provider 结果。
- 投产验收能确认 provider 视图没有在下游丢失。
- 不修改路由优先级，只补日常可见性。

### 阶段 L：日常执行简报与质量门禁闭环

目标：把 `production_gate`、`action_list`、`run_cadence`、`review_brief`、`schedule_hint` 和 `daily_collaboration_pack` 再往上收成一层 `daily_execution_brief`，让默认工作流、留档查看和回看入口第一屏就能看懂今天该做什么。

任务拆分：

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| L.1 | 编写 Phase 75 SDD | P0 | 明确执行简报边界 |
| L.2 | 构建共享执行简报 | P0 | 在 `examples/watchlist_shared.py` 中实现 |
| L.3 | 在日常运行状态中写入执行简报 | P0 | `examples/daily_watchlist_daily_run.py` |
| L.4 | 在默认工作流和留档查看中展示执行简报 | P0 | `examples/daily_watchlist_flow.py` / `examples/daily_watchlist_archive_viewer.py` |
| L.5 | 在回看入口和投产验收中检查执行简报 | P1 | `examples/daily_watchlist_review.py` / `examples/daily_watchlist_acceptance.py` |
| L.6 | 在智能体提示词中优先识别执行简报 | P1 | `core/agent/client.py` |
| L.7 | 更新 README 与任务清单 | P1 | 固化第一屏阅读顺序 |
| L.8 | 编写归档文档 | P1 | 记录 Phase 75 收口 |

验收标准：

- 日常运行、工作流、留档查看和回看入口都能读到 `daily_execution_brief`。
- 简报不替代 `production_gate` 和 `action_list`，而是把它们压成第一屏。
- `block / caution / ready` 约束和现有门禁保持一致。
- 智能体和 Skill 能优先按简报阅读，再回退到 `daily_collaboration_pack`。

## 5. 统一质量门禁的协作边界

统一质量门禁不是某一个单一评分规则，也不是简单的 `if health_score < 60` 判断。

它应该是一套由多个层次共同协作的机制：

| 层次 | 职责 |
|---|---|
| 数据治理层 | 提供真实数据、缓存、降级、质量检查和来源追踪 |
| 日常工作流层 | 汇总健康检查、决策结果、验收结果和归档产物 |
| Skill / 工具层 | 暴露稳定工具入口，避免智能体直接拼接底层字段 |
| 智能体提示词层 | 约束智能体在输出建议前必须读取门禁结果，门禁不足时只能给观察或诊断建议 |
| 输出契约层 | 把门禁结论写入统一 JSON，方便 CLI、API、智能体和后续界面共同消费 |

因此，质量门禁的定位是“生产决策前的协作协议”，不是某个孤立函数。

## 6. 推荐下一步

如果还要继续增强，建议从这几个轻量方向往下走：

1. 更细的提示语境联动
2. 更细的回看呈现
3. 更轻的调度准备

这条路线最贴合项目当前状态：投入小、见效快、能真实提升日常投产质量，也避免陷入局部无限优化。

当前建议的 Phase 68 `review_brief` 回看收紧和 Phase 69 `schedule_hint` 轻量调度准备已经落地，下一步再把 `daily_collaboration_pack` 作为统一协作总包。

如果接下来要继续处理日常协作链路，建议优先推进“日常执行简报与质量门禁闭环”这一阶段：把 `production_gate`、`action_list`、`run_cadence`、`review_brief`、`schedule_hint` 和 `daily_collaboration_pack` 再向上压成第一屏简报，避免使用侧每次都得自己拼上下文。
