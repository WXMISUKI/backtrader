# StockQuantAdvisor - 股票量化交易智能顾问系统

## 项目简介

基于 Skill 架构的股票量化交易智能体系统，提供个股分析、买卖建议、风险控制等功能。

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

联调用例会依次检查：

- `GET /health`
- `POST /decision`
- 可选 `POST /feedback`

### 4. 运行回测示例

```bash
python examples/backtest_simple.py
```

### 5. 使用风险管理器

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

### 6. 使用智能体接入层

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
