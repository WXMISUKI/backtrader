# StockQuantAdvisor - 股票量化交易智能顾问系统

## 项目简介

基于 Skill 架构的股票量化交易智能体系统，提供个股分析、买卖建议、风险控制等功能。

### 项目定位

这是一个私人私用的股票预测与推荐智能体项目，不以对外售卖为目标，而是以“快速投产、真实测试、持续迭代”为核心方法。

我们的开发原则是：

- 先把主链路跑通，再根据实际测试结果逐步优化
- 优先验证算法、工具和工作流是否真的可用
- 不追求一开始把每个模块都做到极致
- 生产中遇到的新问题，再按需补强和收敛
- 以可用、好用、可持续改进为目标，而不是过度工程化

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 回测引擎 | backtrader | 1.9.78.123 |
| 数据源 | akshare + 东方财富API | 1.18.64 |
| 可视化 | matplotlib | 3.10.9 |
| 环境管理 | conda (quant) | Python 3.10 |

## 项目结构

```
backtrader/
├── specs/                      # 项目规格文档
│   ├── DEVELOPMENT_SPEC.md     # 开发规格书
│   └── PROJECT_STRUCTURE.md    # 项目结构图
│
├── skills/                     # Skill 模块
│   ├── stock-advisor/          # 个股买卖建议 (优先开发)
│   ├── stock-monitor/          # 实时监控 (待开发)
│   ├── stock-backtest/         # 策略回测 (待开发)
│   └── stock-selector/         # 智能选股 (待开发)
│
├── core/                       # 核心模块
│   ├── data/                   # 数据获取
│   ├── indicators/             # 技术指标
│   ├── signals/                # 信号系统
│   └── risk/                   # 风险控制
│
├── strategies/                 # 交易策略
├── backtest/                   # 回测模块
├── utils/                      # 工具函数
├── examples/                   # 示例代码
├── tests/                      # 测试代码
└── config/                     # 配置文件
```

## 快速开始

### 1. 激活环境

```bash
conda activate quant
```

### 2. 启动最小 HTTP API

```bash
python tools/agent-api.py --host 127.0.0.1 --port 8000
```

也可以使用安装后的命令：

```bash
stock-agent-api --host 127.0.0.1 --port 8000
```

默认支持的环境变量：

- `STOCK_AGENT_API_HOST`
- `STOCK_AGENT_API_PORT`

### 3. 运行最小联调用例

```bash
python examples/api_demo.py --host 127.0.0.1 --port 8000
```

如果希望顺带提交反馈，可以加：

```bash
python examples/api_demo.py --host 127.0.0.1 --port 8000 --submit-feedback
```

如果希望同时查看最近反馈统计，可以加：

```bash
python examples/api_demo.py --host 127.0.0.1 --port 8000 --submit-feedback --show-stats
```

如果希望进一步查看反馈洞察，可以加：

```bash
python examples/api_demo.py --host 127.0.0.1 --port 8000 --show-insights
```

如果你想直接生成一份自选股日常决策清单，可以跑：

```bash
python examples/daily_watchlist_decision.py --watchlist config/watchlist.json --output-json logs/daily_watchlist.json
```

如果你想先看这份清单的数据健康情况，可以先跑：

```bash
python examples/watchlist_data_health.py --watchlist config/watchlist.json --output-json logs/watchlist_health.json
```

推荐顺序是先看数据健康，再看日常决策清单。

这两步现在共用同一套健康摘要口径，优先看：

- `status`
- `health_score`
- `history_source`
- `fundamental_source`
- `history_reason`
- `fundamental_reason`

如果你想给最近一次日常结果记一条轻量反馈，可以跑：

```bash
python examples/daily_watchlist_feedback.py --feedback watching --comment "继续观察"
```

如果你想对某只股票单独记反馈，可以加上 `--stock-code`：

```bash
python examples/daily_watchlist_feedback.py --archive-dir logs/daily_watchlist_archive --stock-code 000001 --feedback accepted --comment "这次判断可采纳"
```

如果你想看看最近反馈的统计趋势，可以跑：

```bash
python examples/daily_watchlist_feedback_insights.py
```

如果你想看反馈后续效果和 T+1 / T+3 / T+5 的轻量回看，可以跑：

```bash
python examples/daily_watchlist_feedback_effects.py
```

如果你想把反馈洞察导出成 JSON，可以加上 `--output-json`：

```bash
python examples/daily_watchlist_feedback_insights.py --output-json logs/daily_watchlist_feedback_insights.json
```

如果你想一条命令看最新留档和最近反馈趋势，可以跑：

```bash
python examples/daily_watchlist_review.py
```

这个入口现在会先给你一段 `review_brief`，把今天的门禁、行动、节奏、提示语境和反馈效果压成一眼能读完的摘要。

如果你还想把 JSON 细节一起看出来，可以加上 `--show-json`：

```bash
python examples/daily_watchlist_review.py --show-json
```

如果你想做一次日常投产验收，可以跑：

```bash
python examples/daily_watchlist_acceptance.py
```

如果你想把验收结果导出成 JSON，可以加上 `--output-json`：

```bash
python examples/daily_watchlist_acceptance.py --output-json logs/daily_watchlist_acceptance.json
```

如果你想直接一条命令把日常运行、回看和验收串起来，可以跑：

```bash
python examples/daily_watchlist_flow.py --watchlist config/watchlist.json --portfolio config/portfolio.json --archive-dir logs/daily_watchlist_archive --output-json logs/daily_watchlist_flow.json
```

默认工作流现在会同时输出 `production_gate` 和 `action_list`，也就是先看今天能不能参考，再看今天先做什么。

当前的 `action_list` 还会带更明确的 `action_hint`，方便你直接看“今天先怎么处理”。

当前的诊断证据还会带 `sample_attribution`，方便你快速看懂样本主要归到哪几类问题上。

`daily_watchlist_daily_run.py` 现在还会输出 `run_cadence`，把今天跑了哪几步、下一步该先看什么说清楚。

现在它也会输出 `prompt_context`，把 `production_gate`、`action_list` 和 `run_cadence` 收成一段可以直接喂给智能体提示词或技能复用的协作语境。

它还会输出 `schedule_hint`，把“今天跑完后下一次是否适合继续自动推进”说得更清楚。这里的重点不是新调度系统，而是一个很薄的运行就绪提示。

现在它也会输出 `daily_collaboration_pack`，把门禁、行动、节奏、提示语境、回看摘要和运行就绪提示一起收成一份更适合智能体和 Skill 直接消费的总包。

现在它也会输出 `feedback_effect_brief`，把最近反馈效果收成一份更稳定的简报，方便和 `daily_execution_brief` 一起看。

留档查看入口同样会先展示 `review_brief`，让你先看摘要，再看正文和证据。

如果你只想先跳过回看或验收，也可以分别加：

```bash
python examples/daily_watchlist_flow.py --skip-review
python examples/daily_watchlist_flow.py --skip-acceptance
```

默认工作流会先执行 `daily_run`，再执行 `review`，最后执行 `acceptance`。如果你只想看 JSON 结果，可以加 `--show-json`。

如果你还想把持仓上下文一起带进去，可以这样跑：

```bash
python examples/daily_watchlist_decision.py --watchlist config/watchlist.json --portfolio config/portfolio.json --output-json logs/daily_watchlist.json
```

现在更推荐的顺序是：

1. 先看数据健康
2. 再看带持仓上下文的日常决策清单
3. 最后再回看原始分析或导出结果

如果你想一步到位跑完整个日常流程，可以直接用统一入口：

```bash
python examples/daily_watchlist_pipeline.py --watchlist config/watchlist.json --portfolio config/portfolio.json --output-json logs/daily_watchlist_pipeline.json
```

如果你想在日常结果里顺手看出“为什么会降级”，可以重点看健康摘要里的 `diagnosis`，默认工作流 JSON 里的 `diagnosis_counts`，以及总览里的降级原因统计。

日常总览现在由公共摘要模板统一生成，`daily_watchlist_pipeline.py` 只是把健康分组和决策分组喂进去。

投产验收现在还能直接消费一个 `diagnosis_evidence` 视图，用来快速确认今天主要的降级原因和样例项。

留档查看入口也会展示同一份 `diagnosis_evidence`，方便回看时和验收入口对齐。

默认日常流程现在还会输出统一的 `production_gate`，你每天优先看它就行：`pass` 表示可以参考，`warn` 表示谨慎参考，`block` 表示先别拿来做交易判断。

如果你想进一步看明白为什么会被降级，还可以看日常摘要里的可信度分布和平均可信度，它会把 `data_confidence`、低可信样本和主要降级原因一起收进来。

如果你想一条命令把日常摘要、诊断证据和验收状态收成一个收口包，可以跑：

```bash
python examples/daily_watchlist_diagnosis_bundle.py --show-json
```

如果你想快速看懂这条诊断链路，推荐顺序是：

1. `daily_watchlist_flow.py`
2. `daily_watchlist_acceptance.py`
3. `daily_watchlist_archive_viewer.py`
4. `daily_watchlist_diagnosis_bundle.py`

这几步共享同一套 `daily_summary / diagnosis_evidence / acceptance` 语义。

如果你想做一次更完整的默认日常检查，推荐直接跑默认工作流，再看验收入口：

```bash
python examples/daily_watchlist_flow.py --watchlist config/watchlist.json --portfolio config/portfolio.json --archive-dir logs/daily_watchlist_archive --output-json logs/daily_watchlist_flow.json
python examples/daily_watchlist_acceptance.py
```

如果你想把今天的结果和上一份日报做对比，可以加上 `--compare-with`：

```bash
python examples/daily_watchlist_pipeline.py --watchlist config/watchlist.json --portfolio config/portfolio.json --compare-with logs/daily_watchlist_phase33.json --output-json logs/daily_watchlist_pipeline.json
```

如果你想把多份日报收成周报模板，可以加上 `--weekly-reports`：

```bash
python examples/daily_watchlist_pipeline.py --watchlist config/watchlist.json --portfolio config/portfolio.json --weekly-reports logs/daily_watchlist_phase33.json,logs/daily_watchlist_phase34.json --output-json logs/daily_watchlist_pipeline.json
```

如果你想把多份周报或日报收成阶段报告模板，可以加上 `--stage-reports`：

```bash
python examples/daily_watchlist_pipeline.py --watchlist config/watchlist.json --portfolio config/portfolio.json --stage-reports logs/daily_watchlist_phase35.json,logs/daily_watchlist_phase34.json --output-json logs/daily_watchlist_pipeline.json
```

如果你想把当前日报、对比、周报和阶段报告一起打成留档包，可以加上 `--archive-package`：

```bash
python examples/daily_watchlist_pipeline.py --watchlist config/watchlist.json --portfolio config/portfolio.json --archive-package --archive-name "月度复盘包" --output-json logs/daily_watchlist_pipeline.json
```

如果你想把当天结果按日期目录自动留档，并顺手导出 Markdown，可以这样跑：

```bash
python examples/daily_watchlist_pipeline.py --watchlist config/watchlist.json --portfolio config/portfolio.json --archive-package --export-markdown --write-latest --output-json logs/daily_watchlist_pipeline.json
```

默认会把结果写到 `logs/daily_watchlist_archive/YYYYMMDD/`，并在启用 `--write-latest` 时更新：

- `logs/daily_watchlist_archive/latest.json`
- `logs/daily_watchlist_archive/latest.md`

如果你想直接查看最近一次留档结果，可以跑：

```bash
python examples/daily_watchlist_archive_viewer.py --archive-dir logs/daily_watchlist_archive
```

如果你想看完整 Markdown 或 JSON，可以分别加上 `--show-markdown` 或 `--show-json`。

如果你想直接做一次“预检 -> 执行 -> 留档 -> 查看”的日常运行，可以跑：

```bash
python examples/daily_watchlist_daily_run.py --watchlist config/watchlist.json --portfolio config/portfolio.json --archive-dir logs/daily_watchlist_archive
```

这个命令会先做数据健康预检，再执行统一日常流程，最后自动归档并打开最近一次留档查看结果。

如果你想先确认东方财富 cookie 是从哪里读到的，可以跑：

```bash
python examples/eastmoney_live_check.py --cookie-file .\\eastmoney.cookie --skip-realtime
```

联调脚本会输出 `cookie_source`、`cookie_loaded`、`has_jsessionid` 等诊断信息，方便先确认配置，再看接口结果。

如果你想把浏览器里导出的 cookie 先标准化、再写回项目本地配置，并顺手做一次历史行情验证，可以跑：

```bash
python examples/eastmoney_cookie_refresh.py --cookie-file .\\eastmoney.cookie --persist --smoke-test
```

如果你要联调 AKShare 相关的历史行情备选源，请切到专门的 `akshare-bt` 环境再跑：

```bash
conda run -n akshare-bt python -c "import akshare as ak; print(ak.__version__)"
```

当前多源路由会优先尝试东方财富，再尝试 AKShare，最后才落到离线兜底；你可以通过 `selected_provider` 和 `provider_attempts` 判断今天最终走的是哪条路。

当前东财会话默认会继承运行环境里的代理设置；如果你需要显式关闭这层继承，可以设置 `EASTMONEY_TRUST_ENV=0`。这次历史行情修复的重点，就是避免把这层环境路由写死成不可用的默认值。

如果历史行情仍然失败，联调脚本还会给出 `failure_kind`、`failure_stage`、`failure_code`、`fallback_strategy` 和 `fallback_reason`，帮助区分请求异常、响应异常、质量异常，以及当前到底用了哪种回退策略。

如果你只是想快速判断数据源是不是正常，先看统一健康摘要里的 `status`，再看 `history_source` 和 `fundamental_source`，最后再看原因字段；如果历史链路降级，再顺手看 `history_failure_stage` 和 `history_failure_code`，就能更快定位是请求层、响应层还是质量层的问题。

如果你想跑一个最小的回归测试，确认历史行情失败时会稳定标记为 `request`，可以跑：

```bash
python -m pytest tests/test_eastmoney_history_resilience.py -q
```

如果你想验证历史行情多源路由、cookie 解析和最终 provider 记录，可以跑：

```bash
python -m pytest tests/test_history_multisource_routing.py tests/test_eastmoney_history_resilience.py -q
```

如果你想确认健康预检、统一流水线和投产验收都能看见 `history_selected_provider`，可以跑：

```bash
python -m pytest tests/test_history_provider_visibility.py -q
```

留档包现在会按固定结构输出：

1. 复盘总览
2. 当日日报
3. 日报对比
4. 周报模板
5. 阶段报告
6. 持仓语境

周报和阶段报告的标题也会保持更平整的表达，不再递归引用上一层标题。

统一入口会依次输出：

1. 日更报告
2. 数据健康预检
3. 持仓上下文
4. 最终日常决策清单

如果提供了对比基线，还会额外输出日报对比摘要。
如果提供了周报输入，还会额外输出周报模板。
如果提供了阶段输入，还会额外输出阶段报告模板。
如果启用留档包，还会额外输出复盘留档包。

联调用例会依次检查：

- `GET /health`
- `POST /decision`
- `decision_summary` 四段式摘要
- 可选 `POST /feedback`
- 可选 `GET /decision/stats`，优先展示 `stats_summary`
- 可选 `GET /decision/insights`，优先展示 `insights_summary`

统一摘要字段建议优先阅读：

- `结论` / `conclusion`
- `依据` / `basis`
- `风险` / `risk`
- `下一步动作` / `next_action`

`decision_summary`、`stats_summary` 和 `insights_summary` 都遵循这套四段式模板；需要排查细节时，再继续查看原始 `data` 明细。

### 4. 运行回测示例

```bash
python examples/backtest_simple.py
```

### 5. 最小 `curl` 调试示例

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/decision ^
  -H "Content-Type: application/json" ^
  -d "{\"user_input\":\"请分析 000001，并给出买入/卖出建议和持仓建议。\",\"risk_profile\":\"moderate\"}"
```

```bash
curl -X POST http://127.0.0.1:8000/feedback ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"your-session-id\",\"workflow_id\":\"your-workflow-id\",\"accepted\":true,\"rating\":5,\"reason\":\"\",\"correction\":\"\",\"comment\":\"示例反馈\"}"
```

```bash
curl "http://127.0.0.1:8000/decision/stats?limit=20"
```

```bash
curl "http://127.0.0.1:8000/decision/insights?limit=20&min_samples=2"
```

### 6. 使用风险管理器

```python
from core.risk.risk_profiles import RiskManager

# 创建风险管理器 (默认稳健型)
rm = RiskManager()

# 切换风险等级
rm.set_profile("conservative")  # 保守型
rm.set_profile("moderate")      # 稳健型
rm.set_profile("aggressive")    # 激进型

# 计算止损止盈
stop_loss = rm.calc_stop_loss_price(10.0)  # 买入价10元
take_profit = rm.calc_take_profit_price(10.0)

# 计算仓位
position = rm.calc_position_size(100000, 10.0)  # 10万资金，10元股价
```

### 7. 使用智能体接入层

```bash
python examples/agent_demo.py "请分析 000001，并给出建议"
```

智能体会优先调用项目现有工具，例如：
- 个股分析
- 基本面分析
- 市场概览
- 推荐列表
- 回测结果
- 风险配置

注意：
- 需要先在 `.env` 中配置 `ARK_API_KEY`
- 如果真实行情不可用，系统会自动降级到离线模拟数据，并在结果中标记 `mock`
- 如果你要联调东方财富真实数据，Cookie 需要保持有效；过期后请重新从官网浏览器中获取
- 如果你想判断下一步该优先优化什么，先看 `/decision/insights`，再决定是否调整工具或工作流
- 如果你想更快看懂决策、统计和洞察结果，优先看 `decision_summary` / `stats_summary` / `insights_summary` 的四段式输出
- 如果你想每天拿一份自选股清单，优先跑 `examples/daily_watchlist_decision.py`
- 如果你想先判断当天数据靠不靠谱，优先跑 `examples/watchlist_data_health.py`
- 如果你想一次看懂东财数据状态，优先看统一健康摘要里的 `status`
- 如果你想记一条轻量反馈，优先跑 `examples/daily_watchlist_feedback.py`
- 如果你想快速看反馈趋势，优先跑 `examples/daily_watchlist_feedback_insights.py`
- 如果你想看反馈后续效果，优先跑 `examples/daily_watchlist_feedback_effects.py`

## 功能模块

### 已完成 ✅

- [x] conda 环境搭建 (quant, Python 3.10)
- [x] backtrader 安装和配置
- [x] akshare 安装和配置
- [x] 东方财富 API 对接 (需 Cookie)
- [x] 基础回测示例
- [x] 风险偏好配置系统

### 开发中 🚧

- [ ] Skill 框架搭建
- [ ] 技术指标计算模块
- [ ] 信号生成引擎
- [ ] 个股分析功能

### 待开发 📋

- [ ] 多策略支持
- [ ] 实时监控
- [ ] 智能选股
- [ ] 报告生成

## 风险偏好系统

| 风险等级 | 止损 | 止盈 | 最大仓位 | 适用场景 |
|---------|------|------|---------|---------|
| 保守型 | -3% | +8% | 30% | 追求稳定收益 |
| **稳健型** (默认) | -5% | +15% | 50% | 平衡风险收益 |
| 激进型 | -8% | +25% | 80% | 追求高收益 |

## 参考的开源项目

| 项目 | Stars | 用途 |
|------|-------|------|
| [backtrader](https://github.com/mementum/backtrader) | 14k+ | 回测引擎 |
| [akshare](https://github.com/akfamily/akshare) | 9k+ | 数据获取 |
| [vnpy](https://github.com/vnpy/vnpy) | 24k+ | 交易系统架构参考 |
| [qlib](https://github.com/microsoft/qlib) | 15k+ | AI量化框架参考 |
| [easytrader](https://github.com/shidenggui/easytrader) | 8k+ | 自动交易参考 |

## 开发计划

### 当前推荐顺序: 先门禁，再行动

当前日常主线已经收敛为“日常投产质量门禁与真实决策闭环”，详见：

- `specs/NEXT_STAGE_DEVELOPMENT_ROADMAP.md`
- `specs/SDD_PHASE60_DAILY_PRODUCTION_GATE.md`
- `specs/SDD_PHASE63_DAILY_ACTION_LIST.md`
- `specs/SDD_PHASE64_DAILY_ACTION_HINTS.md`
- `specs/SDD_PHASE65_SAMPLE_ATTRIBUTION.md`
- `specs/SDD_PHASE66_DAILY_RUN_CADENCE.md`
- `specs/SDD_PHASE67_DAILY_PROMPT_CONTEXT_LINKAGE.md`
- `specs/SDD_PHASE68_DAILY_REVIEW_BRIEF.md`
- `specs/SDD_PHASE69_DAILY_SCHEDULE_PREP.md`
- `specs/SDD_PHASE70_DAILY_COLLABORATION_PACK.md`

核心目标是让默认日常流程先输出统一的 `production_gate`，明确今天结果属于 `pass / warn / block`，再输出 `action_list`，把今天先看什么、先做什么说清楚。

这里的统一质量门禁不是单一评分规则，而是数据治理、日常工作流、Skill / 工具、智能体提示词和输出契约一起协作出来的生产决策协议。

接下来建议继续沿着 `daily_collaboration_pack` 往上收，把门禁、行动清单、运行节奏、回看摘要和运行就绪提示变成智能体和 Skill 都能直接消费的日常语境；当前更推荐的下一阶段，是把反馈效果再压成稳定闭环信号，让它真正影响回看、执行简报和投产验收，而不是只停留在独立脚本里。

现在这层反馈效果已经收成了 `feedback_effect_brief`，下一步更适合先观察它在真实日常中的稳定性，再决定是否细化样本排除规则。

### Phase 1: 核心基础 (当前)
- Skill 框架搭建
- 技术指标计算
- 信号生成引擎
- 个股分析功能

### Phase 2: 策略增强
- 多策略支持
- 回测集成
- 组合分析

### Phase 3: 高级功能
- 实时监控
- 自动选股
- 报告生成

## 注意事项

1. **Cookie 更新**: 东方财富 API 需要定期更新 Cookie
2. **风险提示**: 所有分析结果仅供参考，投资有风险
3. **数据延迟**: 实时数据可能存在延迟

## 许可证

本项目基于 backtrader 开源项目扩展，遵循 GPLv3+ 许可证。

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
