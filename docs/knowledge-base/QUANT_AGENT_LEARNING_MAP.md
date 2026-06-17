# 量化智能体知识库

## 1. 我们现在该怎么理解项目

这个项目已经不是单纯的“量化算法集合”，而是一个可以被智能体调用的量化能力平台。

核心判断：

- 智能体负责编排和解释
- 算法工具负责计算和验证
- 数据层负责稳定、降级和追踪
- 回测层负责复验，不能只靠模型口头判断

---

## 2. 最值得借鉴的开源项目

### 2.1 Qlib

来源：

- [Qlib](https://github.com/microsoft/qlib)
- [Qlib-Server](https://github.com/microsoft/qlib-server)

值得学的地方：

- 研究流程到生产流程的分层
- 数据集、特征和实验的标准化
- 离线研究和在线服务的分离

适合我们落地到：

- 数据提供器抽象
- 缓存与数据版本管理
- 特征和实验记录

### 2.2 vn.py

来源：

- [vn.py](https://github.com/vnpy/vnpy)

值得学的地方：

- 框架边界清晰
- Gateway / Engine / Strategy 分层明确
- 适合扩展到实盘接口

适合我们落地到：

- 交易通道抽象
- 策略执行引擎
- 实盘扩展预留接口

### 2.3 TradingAgents

来源：

- [TradingAgents](https://github.com/TauricResearch/TradingAgents)

值得学的地方：

- 多角色分工
- 把复杂交易决策拆成研究、观点、风控和结论
- 强调这是研究框架，不是自动投资承诺

适合我们落地到：

- 多智能体编排
- 让 agent 做“选择工具”和“组织结论”
- 风控和结论分离输出

### 2.4 FinRobot

来源：

- [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot)
- [FinRobot Equity Research Module](https://github.com/AI4Finance-Foundation/FinRobot/blob/master/finrobot_equity/README.md)

值得学的地方：

- 金融场景下的多模型统一编排
- 研究、报告、风控的整体化
- 面向股票研究的完整工作流

适合我们落地到：

- 统一分析报告生成
- 模型 + 规则 + 风控的组合
- 报告可追溯

---

## 3. 我们项目里可以直接复用的能力

### 3.1 已经适合给智能体调用的工具

- `analyze_stock`
- `recommend_by_risk`
- `get_market_overview`
- `get_risk_profile`
- `run_backtest`
- `generate_stock_report`

### 3.2 已经适合继续增强的工具

- `recommend_long_term`
- `recommend_short_term`
- `screen_stocks`
- `analyze_trading_decision`
- `get_financial_indicators`

### 3.3 已经具备的工程基础

- 东方财富数据源与降级路径
- 回测引擎
- 风险管理
- 个股分析
- 基本面分析
- 市场分析
- 推荐器

---

## 4. 现在不建议走的方向

- 不建议把每个指标都直接暴露给智能体
- 不建议让模型自己拼接原始数据后直接下结论
- 不建议把所有能力都做成平级工具
- 不建议再新建一批重复的“长线/短线/稳健/保守”碎工具

原因：

- 工具太碎，模型容易乱路由
- 输出太散，不利于后续审计和回测
- 业务级工具比原子工具更稳定

---

## 5. 推荐的下一阶段方向

### 5.1 先做统一编排层

目标：

- 一个入口串起分析、推荐、回测、报告、风控

候选模块：

- `StockOrchestrator`
- `DataQualityChecker`
- `CacheManager`
- `AuditLogger`

### 5.2 再做统一输出格式

建议固定字段：

- `ok`
- `tool`
- `category`
- `data_source`
- `summary`
- `data`
- `meta`

### 5.3 再做模型和规则共存

建议策略：

- 规则负责解释性
- ML 负责排序和补充
- 风控负责约束
- 智能体负责组织表达

---

## 6. 推荐的技能生态使用方式

当前更适合复用的不是“金融特化 skill 大包”，而是通用能力：

- 规划类 skill
- 文档类 skill
- 代码审查类 skill
- 测试类 skill

金融特化 skill 可以作为参考，但不建议盲目作为主依赖，因为成熟度和安装量差异很大。

我们现在更应该优先把自己的知识库和工具边界做稳。

---

## 7. Phase 5 的开发原则

1. 先收口，再扩展
2. 先统一，再丰富
3. 先可回溯，再自动化
4. 先业务级工具，再原子工具
5. 先真实数据，真实不可用时明确降级

---

## 8. 结论

这个项目后续最好的方向不是“继续堆算法”，而是：

- 用智能体把现有能力串起来
- 用知识库把经验沉淀下来
- 用统一输出把结果规范起来
- 用回测和审计把系统稳定下来

这样才会越来越像一个可持续演进的量化智能体平台。

