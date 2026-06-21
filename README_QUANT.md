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
