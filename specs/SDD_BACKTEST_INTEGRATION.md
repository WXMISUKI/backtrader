# 软件设计规格说明 (SDD)
# 回测集成模块

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 回测集成模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述回测集成模块的设计规格，将自定义策略与 backtrader 回测引擎集成。

### 1.2 范围

本模块负责：
- 回测数据适配器
- 策略适配器
- 回测结果分析器
- 回测报告生成

### 1.3 参考文档

- `SDD_STRATEGY_FRAMEWORK.md` - 策略框架规格
- `SDD_STOCK_ANALYZER.md` - 个股分析模块规格

---

## 2. 系统概述

### 2.1 模块位置

```
backtest/
├── __init__.py          # 模块初始化
├── adapter.py           # 数据和策略适配器
├── engine.py            # 回测引擎封装
├── analyzer.py          # 结果分析器
└── report.py            # 报告生成器
```

### 2.2 依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                    backtest 回测模块                         │
├─────────────────────────────────────────────────────────────┤
│  engine.py (回测引擎)                                       │
│      │                                                       │
│      ├── backtrader (回测框架)                               │
│      ├── strategies (自定义策略)                             │
│      └── core.data (数据获取)                                │
│                                                             │
│  被依赖:                                                    │
│      └── skills.stock-advisor (个股分析)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 设计决策

### 3.1 核心设计原则

1. **适配器模式**: 将自定义策略适配为 backtrader 策略
2. **门面模式**: 提供简洁的回测接口
3. **结果标准化**: 统一的回测结果格式

### 3.2 回测流程

```
用户调用 → BacktestEngine → backtrader → 结果分析 → 报告生成
    │           │               │            │          │
    │           │               │            │          │
    └───────────┴───────────────┴────────────┴──────────┘
                    适配器模式
```

---

## 4. 模块详细设计

### 4.1 数据适配器 (adapter.py)

```python
class StockDataFeed:
    """
    股票数据适配器

    将 StockData 适配为 backtrader 数据源
    """

    @staticmethod
    def from_stock_data(stock_data: StockData) -> bt.feeds.PandasData:
        """
        从 StockData 创建 backtrader 数据源

        参数:
            stock_data: StockData 对象

        返回:
            backtrader PandasData 对象
        """
        pass
```

### 4.2 策略适配器 (adapter.py)

```python
class StrategyAdapter(bt.Strategy):
    """
    策略适配器

    将自定义 Strategy 适配为 backtrader 策略
    """

    params = (
        ('strategy_name', 'ma_cross'),
        ('config', {}),
    )

    def __init__(self):
        """初始化"""
        # 创建自定义策略实例
        self.custom_strategy = StrategyRegistry.create(
            self.params.strategy_name,
            self.params.config
        )

    def next(self):
        """处理每根 K 线"""
        # 创建 Bar 对象
        bar = self._create_bar()

        # 调用自定义策略
        signal = self.custom_strategy.on_bar(bar)

        # 执行交易
        if signal.is_buy and not self.position:
            self.buy()
        elif signal.is_sell and self.position:
            self.sell()
```

### 4.3 回测引擎 (engine.py)

```python
class BacktestEngine:
    """
    回测引擎

    封装 backtrader，提供简洁的回测接口
    """

    def __init__(self, initial_cash: float = 100000):
        """
        初始化

        参数:
            initial_cash: 初始资金
        """
        self.initial_cash = initial_cash

    def run(
        self,
        stock_code: str,
        strategy_name: str,
        config: dict = None,
        start_date: str = "20260101",
        end_date: str = "20260614"
    ) -> BacktestResult:
        """
        运行回测

        参数:
            stock_code: 股票代码
            strategy_name: 策略名称
            config: 策略配置
            start_date: 开始日期
            end_date: 结束日期

        返回:
            BacktestResult 回测结果
        """
        pass
```

### 4.4 结果分析器 (analyzer.py)

```python
class BacktestResult:
    """
    回测结果
    """
    initial_cash: float         # 初始资金
    final_value: float          # 最终资金
    total_return: float         # 总收益率
    annual_return: float        # 年化收益率
    max_drawdown: float         # 最大回撤
    sharpe_ratio: float         # 夏普比率
    win_rate: float             # 胜率
    total_trades: int           # 总交易次数
    trades: list                # 交易记录

    def summary(self) -> str:
        """生成摘要"""
        pass
```

### 4.5 报告生成器 (report.py)

```python
class ReportGenerator:
    """
    报告生成器
    """

    @staticmethod
    def generate_text_report(result: BacktestResult) -> str:
        """生成文本报告"""
        pass

    @staticmethod
    def generate_json_report(result: BacktestResult) -> dict:
        """生成 JSON 报告"""
        pass
```

---

## 5. 接口设计

### 5.1 简单接口

```python
from backtest import run_backtest

# 一行代码完成回测
result = run_backtest(
    stock_code="000001",
    strategy_name="ma_cross",
    config={'fast_period': 5, 'slow_period': 20}
)

print(result.summary())
```

### 5.2 高级接口

```python
from backtest import BacktestEngine

engine = BacktestEngine(initial_cash=100000)
result = engine.run(
    stock_code="000001",
    strategy_name="macd",
    config={'fast_period': 12, 'slow_period': 26},
    start_date="20260101",
    end_date="20260614"
)
```

---

## 6. 实现检查清单

### 6.1 功能完整性

- [ ] 实现 StockDataFeed 适配器
- [ ] 实现 StrategyAdapter 适配器
- [ ] 实现 BacktestEngine 引擎
- [ ] 实现 BacktestResult 结果类
- [ ] 实现 ReportGenerator 报告生成器
- [ ] 实现 run_backtest 便捷函数

### 6.2 测试覆盖

- [ ] 数据适配器测试
- [ ] 策略适配器测试
- [ ] 回测引擎测试
- [ ] 结果分析器测试

---

## 7. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 数据适配器 | backtest/adapter.py | ⬜ |
| 回测引擎 | backtest/engine.py | ⬜ |
| 结果分析器 | backtest/analyzer.py | ⬜ |
| 报告生成器 | backtest/report.py | ⬜ |
| 模块初始化 | backtest/__init__.py | ⬜ |
| 单元测试 | tests/test_backtest.py | ⬜ |

---

## 8. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
