# 软件设计规格说明 (SDD)
# StockOrchestrator: 统一编排入口

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | StockOrchestrator 统一编排入口 SDD |
| 版本 | v0.1 |
| 创建日期 | 2026-06-17 |
| 状态 | 草案 |

---

## 1. 背景

当前项目已经具备多个可独立调用的能力模块，包括个股分析、推荐、市场概览、风控、回测和报告生成。但这些能力之间还缺少一个稳定的统一编排层。

当用户输入自然语言问题时，如果每个能力都由模型自行推断并直接调用，系统容易出现：

- 工具路由不稳定
- 多轮工具调用收敛差
- 输出格式不统一
- 真实数据与降级数据混用
- 后续审计和回测难以复验

因此需要一个统一编排器，将这些能力组织成稳定、可追踪、可回溯的业务入口。

---

## 2. 目标

### 2.1 总目标

实现一个最小可用但可扩展的 `StockOrchestrator`，用于统一协调项目能力，并输出标准化结果。

### 2.2 具体目标

| 目标 | 说明 |
|------|------|
| 统一入口 | 一个对象承接分析、推荐、市场、风控、回测和报告 |
| 统一输出 | 所有结果使用标准信封 |
| 统一路由 | 根据意图自动选择最合适的工具链 |
| 统一降级 | 工具失败时可回退到受控结果 |
| 统一追踪 | 保留工具名、类别、来源与时间戳 |

### 2.3 当前实现状态

- 已实现 `core/orchestrator.py`
- 已实现 `StockOrchestrator`
- 已实现 `route()` 自然语言路由入口
- 已支持 `analyze / recommend / market_overview / risk_profile / backtest / report`
- 已能提取 6 位股票代码并做默认路由
- 已接入 `CacheManager` 与 `DataQualityChecker`
- 已支持按能力缓存和质量标记
- 已支持缓存命中返回统一结构

---

## 3. 范围

### 3.1 纳入范围

- `analyze_stock`
- `recommend_by_risk`
- `get_market_overview`
- `get_risk_profile`
- `run_backtest`
- `generate_stock_report`

### 3.2 不纳入范围

- 自动下单
- 实盘交易通道
- 模型训练与在线学习
- 复杂策略优化器

---

## 4. 设计原则

### 4.1 以业务级工具为主

编排器不直接依赖底层指标函数，而是依赖现有业务工具。

### 4.2 保留智能体友好性

编排器的输出必须能够被智能体直接解释和总结。

### 4.3 结果可追溯

每次输出必须包含：

- 工具名
- 工具分类
- 数据来源
- 生成时间
- 追踪上下文

### 4.4 降级可见

如果走了 mock 或其他降级路径，必须显式标记。

---

## 5. 核心接口

```python
class StockOrchestrator:
    def analyze(self, stock_code: str, risk_profile: str = "moderate") -> dict:
        """执行个股分析。"""

    def recommend(self, risk_profile: str = "moderate", top_n: int = 5) -> dict:
        """执行统一推荐。"""

    def market_overview(self) -> dict:
        """获取市场概览。"""

    def risk_profile(self, risk_profile: str = "moderate") -> dict:
        """获取风险配置。"""

    def backtest(self, stock_code: str, strategy_name: str, **kwargs) -> dict:
        """执行回测。"""

    def report(self, stock_code: str, risk_profile: str = "moderate") -> dict:
        """生成报告。"""

    def route(self, user_input: str, **kwargs) -> dict:
        """根据自然语言意图路由到最合适的能力。"""
```

---

## 6. 路由规则

### 6.1 推荐

- 未明确说明长线/短线时，默认走 `recommend_by_risk`
- 明确风险偏好时，传入对应 `risk_profile`

### 6.2 分析

- 明确股票代码和“分析/建议/报告”时，走 `analyze_stock`

### 6.3 市场

- 用户提到“市场/大盘/行情”时，走 `get_market_overview`

### 6.4 风控

- 用户提到“风控/仓位/风险”时，走 `get_risk_profile`

### 6.5 回测

- 用户提到“回测”时，走 `run_backtest`

---

## 7. 输出规范

统一输出建议包含：

```json
{
  "ok": true,
  "action": "recommend",
  "tool": "recommend_by_risk",
  "category": "recommendation",
  "data_source": "mock",
  "summary": "已生成风险匹配推荐列表。",
  "data": {},
  "meta": {
    "orchestrator": "StockOrchestrator",
    "payload_version": "1.0",
    "generated_at": "2026-06-17T00:00:00Z"
  }
}
```

---

## 8. 验收标准

- 可直接调用至少 3 个业务场景
- 返回格式统一
- 数据来源明确
- mock 降级明确
- 不影响现有工具直接调用
- 可根据自然语言直接路由到对应能力
- 可自动提取股票代码并兜底默认策略
- 可对重复调用走缓存并返回来源标记
- 可在结果中暴露质量检查结果
- 缓存命中与首轮结果结构一致

---

## 10. 实现归档

### 已完成

- `core/orchestrator.py`
- `examples/orchestrator_demo.py`
- `core/data/governance.py`

### 验证结果

- 推荐路由正常
- 分析路由正常
- 市场路由正常
- 回测路由正常
- 缓存路由正常
- 质量检查正常

---

## 9. 风险

| 风险 | 说明 | 缓解 |
|------|------|------|
| 逻辑重复 | 与现有工具层重叠 | 只做编排，不重做算法 |
| 输出漂移 | 各工具返回不一致 | 统一信封和序列化 |
| 降级隐藏 | 用户误以为是真实数据 | 强制显式标记 data_source |
