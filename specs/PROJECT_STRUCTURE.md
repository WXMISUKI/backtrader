# StockQuantAdvisor 项目结构图

## 整体架构

```
StockQuantAdvisor/
│
├── 📁 specs/                          # 项目规格文档
│   ├── DEVELOPMENT_SPEC.md            # 开发规格书
│   └── PROJECT_STRUCTURE.md           # 项目结构图 (本文件)
│
├── 📁 skills/                         # Skill 模块目录
│   │
│   ├── 📁 stock-advisor/              # ⭐ 核心Skill: 个股买卖建议
│   │   ├── __init__.py
│   │   ├── skill.py                   # Skill 主入口
│   │   ├── config.py                  # 配置管理
│   │   ├── analyzer.py                # 股票分析器
│   │   ├── signal_generator.py        # 信号生成器
│   │   └── report_builder.py          # 报告构建器
│   │
│   ├── 📁 stock-monitor/              # 实时监控 (待开发)
│   │   ├── __init__.py
│   │   ├── skill.py
│   │   └── monitor.py
│   │
│   ├── 📁 stock-backtest/             # 策略回测 (待开发)
│   │   ├── __init__.py
│   │   ├── skill.py
│   │   └── engine.py
│   │
│   └── 📁 stock-selector/             # 智能选股 (待开发)
│       ├── __init__.py
│       ├── skill.py
│       └── screener.py
│
├── 📁 core/                           # 核心模块
│   │
│   ├── 📁 data/                       # 数据层
│   │   ├── __init__.py
│   │   ├── eastmoney_api.py           # 东方财富API (已完成)
│   │   ├── akshare_api.py             # akshare数据源
│   │   └── data_processor.py          # 数据预处理
│   │
│   ├── 📁 indicators/                 # 技术指标
│   │   ├── __init__.py
│   │   ├── trend.py                   # 趋势指标 (MA/MACD/BOLL)
│   │   ├── oscillator.py              # 震荡指标 (RSI/KDJ/CCI)
│   │   └── volume.py                  # 量价指标 (OBV/VOL)
│   │
│   ├── 📁 signals/                    # 信号系统
│   │   ├── __init__.py
│   │   ├── buy_signals.py             # 买入信号
│   │   ├── sell_signals.py            # 卖出信号
│   │   └── signal_strength.py         # 信号强度计算
│   │
│   └── 📁 risk/                       # 风险控制
│       ├── __init__.py
│       ├── risk_profiles.py           # 风险偏好配置
│       └── position_sizer.py          # 仓位管理
│
├── 📁 strategies/                     # 交易策略
│   ├── __init__.py
│   ├── dual_ma.py                     # 双均线策略
│   ├── macd_strategy.py               # MACD策略
│   └── composite_strategy.py          # 综合策略
│
├── 📁 backtest/                       # 回测模块
│   ├── __init__.py
│   ├── engine.py                      # 回测引擎
│   └── analyzer.py                    # 结果分析
│
├── 📁 utils/                          # 工具函数
│   ├── __init__.py
│   ├── logger.py                      # 日志工具
│   ├── decorators.py                  # 装饰器
│   └── validators.py                  # 数据验证
│
├── 📁 examples/                       # 示例代码
│   ├── backtest_demo.py               # 回测示例 (已完成)
│   ├── backtest_simple.py             # 简化回测 (已完成)
│   └── advisor_demo.py                # 顾问示例 (待开发)
│
├── 📁 tests/                          # 测试代码
│   ├── test_indicators.py
│   ├── test_signals.py
│   └── test_advisor.py
│
├── 📁 docs/                           # 文档
│   ├── README.md                      # 项目说明
│   ├── USAGE.md                       # 使用指南
│   └── API.md                         # API文档
│
├── 📁 config/                         # 配置文件
│   ├── settings.py                    # 全局设置
│   └── risk_profiles.json             # 风险偏好配置
│
├── eastmoney_config.py                # 东方财富API配置 (已完成)
├── requirements.txt                   # 依赖列表
├── setup.py                           # 安装脚本
└── README.md                          # 项目主文档
```

## 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                        用户交互层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │stock-advisor│  │stock-monitor│  │stock-backtest│  ...    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                        核心业务层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   signals   │  │  indicators │  │    risk     │         │
│  │  信号生成    │  │  技术指标   │  │  风险控制   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据服务层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ eastmoney   │  │   akshare   │  │  backtrader │         │
│  │ 东方财富API  │  │  数据接口   │  │  回测引擎   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 数据流图

```
                    ┌──────────────┐
                    │   用户请求   │
                    │ "分析000001" │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ stock-advisor│
                    │   Skill      │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
     ┌──────────┐   ┌──────────┐   ┌──────────┐
     │ 获取数据  │   │ 计算指标  │   │ 读取配置  │
     │ eastmoney│   │ MA/RSI.. │   │ risk_level│
     └────┬─────┘   └────┬─────┘   └────┬─────┘
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  ┌──────────────┐
                  │  信号分析     │
                  │  买入/卖出   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  生成建议     │
                  │  目标价/止损  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  返回结果     │
                  │  JSON报告    │
                  └──────────────┘
```

## Skill 注册表

| Skill | 入口文件 | 主要类 | 依赖 |
|-------|---------|--------|------|
| stock-advisor | skills/stock-advisor/skill.py | StockAdvisor | core.data, core.indicators, core.signals |
| stock-monitor | skills/stock-monitor/skill.py | StockMonitor | core.data |
| stock-backtest | skills/stock-backtest/skill.py | StockBacktest | backtest, strategies |
| stock-selector | skills/stock-selector/skill.py | StockSelector | core.data, core.indicators |

## 关键类图

```
┌─────────────────────────────────────────────────────────┐
│                    StockAdvisor                          │
├─────────────────────────────────────────────────────────┤
│ - data_fetcher: DataFetcher                             │
│ - indicator_calc: IndicatorCalculator                   │
│ - signal_gen: SignalGenerator                           │
│ - risk_manager: RiskManager                             │
├─────────────────────────────────────────────────────────┤
│ + analyze(stock_code, risk_profile) → AnalysisReport    │
│ + get_recommendation(stock_code) → Recommendation       │
│ + set_risk_profile(profile) → None                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  IndicatorCalculator                     │
├─────────────────────────────────────────────────────────┤
│ + calc_ma(data, period) → Series                        │
│ + calc_macd(data) → DataFrame                           │
│ + calc_rsi(data, period) → Series                       │
│ + calc_kdj(data) → DataFrame                            │
│ + calc_boll(data) → DataFrame                           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   SignalGenerator                        │
├─────────────────────────────────────────────────────────┤
│ - buy_rules: List[BuyRule]                              │
│ - sell_rules: List[SellRule]                            │
├─────────────────────────────────────────────────────────┤
│ + generate_signals(data, indicators) → Signals          │
│ + calc_signal_strength(signals) → float                 │
│ + get_direction(signals) → Direction                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    RiskManager                           │
├─────────────────────────────────────────────────────────┤
│ - profiles: Dict[str, RiskProfile]                      │
│ - current_profile: str                                  │
├─────────────────────────────────────────────────────────┤
│ + set_profile(profile_name) → None                      │
│ + get_stop_loss() → float                               │
│ + get_take_profit() → float                             │
│ + get_max_position() → float                            │
│ + calc_position_size(capital, price) → int              │
└─────────────────────────────────────────────────────────┘
```

## 文件命名规范

- **模块名**: 小写下划线 (snake_case)
- **类名**: 大驼峰 (PascalCase)
- **函数名**: 小写下划线 (snake_case)
- **常量名**: 全大写下划线 (UPPER_SNAKE_CASE)
- **配置文件**: 小写点分隔 (risk_profiles.json)

## 导入路径规范

```python
# 从 core 模块导入
from core.data.eastmoney_api import get_stock_hist
from core.indicators.trend import calc_ma, calc_macd
from core.signals.buy_signals import check_buy_signals

# 从 skills 模块导入
from skills.stock_advisor.analyzer import StockAnalyzer

# 从 utils 模块导入
from utils.logger import get_logger
```
