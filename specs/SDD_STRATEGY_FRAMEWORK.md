# 软件设计规格说明 (SDD)
# 策略框架模块

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 策略框架模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述策略框架模块的设计规格，建立可扩展的策略体系，支持多策略组合和回测。

### 1.2 范围

本模块负责：
- 策略基类定义
- 信号和 Bar 数据封装
- 策略注册和管理
- 内置策略实现

### 1.3 设灵灵感来源

| 项目 | 借鉴内容 |
|------|---------|
| **finquant** | Strategy/Signal/Bar 设计、事件驱动 |
| **QUANTAXIS** | 事件引擎架构、统一数据结构 |
| **vectorbt** | 指标工厂模式、配置驱动 |

### 1.4 参考文档

- `SDD_INDICATORS.md` - 技术指标模块规格
- `SDD_SIGNALS.md` - 信号系统模块规格
- `SDD_STOCK_ANALYZER.md` - 个股分析模块规格

---

## 2. 系统概述

### 2.1 模块位置

```
strategies/
├── __init__.py          # 模块初始化
├── base.py              # 策略基类、Signal、Bar
├── registry.py          # 策略注册表
├── ma_cross.py          # 双均线策略
├── macd_strategy.py     # MACD 策略
├── rsi_strategy.py      # RSI 策略
├── boll_strategy.py     # 布林带策略
└── composite.py         # 综合策略
```

### 2.2 依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                    strategies 策略模块                       │
├─────────────────────────────────────────────────────────────┤
│  base.py (策略基类)                                         │
│      │                                                       │
│      ├── core.indicators (技术指标)                          │
│      ├── core.signals (信号系统)                             │
│      └── core.risk (风险控制)                                │
│                                                             │
│  被依赖:                                                    │
│      ├── backtest (回测模块)                                 │
│      └── skills.stock-advisor (个股分析)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 设计决策

### 3.1 核心设计原则

**1. 策略与引擎解耦 (借鉴 finquant)**

策略只需实现 `on_bar(bar) -> Signal` 方法，无需关心数据来源和引擎细节。这使得策略可以独立进行单元测试。

**2. Bar 封装与历史注入 (借鉴 finquant)**

```python
class Bar:
    """K线数据封装"""
    def __init__(self, data, index):
        self._data = data
        self._index = index
        self._history_data = None

    def history(self, field: str, period: int) -> pd.Series:
        """获取历史数据"""
        return self._history_data[field].iloc[self._index-period+1:self._index+1]
```

**3. 指标工厂模式 (借鉴 vectorbt)**

用声明式方式定义策略，自动生成参数扫描和缓存能力。

**4. 配置驱动 (借鉴 vectorbt)**

```python
@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    params: dict
    risk_profile: str = "moderate"
```

---

## 4. 模块详细设计

### 4.1 Signal 类 (base.py)

```python
from enum import Enum
from dataclasses import dataclass

class SignalType(Enum):
    """信号类型枚举"""
    BUY = 1         # 买入
    SELL = -1       # 卖出
    HOLD = 0        # 观望

@dataclass
class Signal:
    """
    交易信号

    借鉴 finquant 的 Signal 设计
    """
    type: SignalType        # 信号类型
    confidence: float       # 置信度 (0-1)
    reason: str             # 原因说明
    price: float = None     # 建议价格
    stop_loss: float = None # 止损价
    take_profit: float = None # 止盈价

    @property
    def is_buy(self) -> bool:
        """是否是买入信号"""
        return self.type == SignalType.BUY

    @property
    def is_sell(self) -> bool:
        """是否是卖出信号"""
        return self.type == SignalType.SELL

    @property
    def is_hold(self) -> bool:
        """是否是观望信号"""
        return self.type == SignalType.HOLD

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'type': self.type.name,
            'confidence': self.confidence,
            'reason': self.reason,
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
        }
```

### 4.2 Bar 类 (base.py)

```python
class Bar:
    """
    K线数据封装

    借鉴 finquant 的 Bar 设计，支持历史数据查询
    """

    def __init__(self, data: pd.DataFrame, index: int):
        """
        初始化

        参数:
            data: 完整的 OHLCV DataFrame
            index: 当前 K 线的索引位置
        """
        self._data = data
        self._index = index
        self._history_data = None

    @property
    def open(self) -> float:
        """开盘价"""
        return float(self._data['open'].iloc[self._index])

    @property
    def high(self) -> float:
        """最高价"""
        return float(self._data['high'].iloc[self._index])

    @property
    def low(self) -> float:
        """最低价"""
        return float(self._data['low'].iloc[self._index])

    @property
    def close(self) -> float:
        """收盘价"""
        return float(self._data['close'].iloc[self._index])

    @property
    def volume(self) -> float:
        """成交量"""
        return float(self._data['volume'].iloc[self._index])

    @property
    def datetime(self):
        """日期时间"""
        return self._data.index[self._index]

    def history(self, field: str, period: int) -> pd.Series:
        """
        获取历史数据

        参数:
            field: 字段名 (open/high/low/close/volume)
            period: 周期数

        返回:
            历史数据序列

        示例:
            >>> bar.history('close', 20)  # 获取最近20根K线的收盘价
        """
        start = max(0, self._index - period + 1)
        end = self._index + 1
        return self._data[field].iloc[start:end]

    def sma(self, period: int) -> float:
        """计算简单移动平均"""
        return float(self.history('close', period).mean())

    def ema(self, period: int) -> float:
        """计算指数移动平均"""
        return float(self.history('close', period).ewm(span=period).mean().iloc[-1])

    def rsi(self, period: int = 14) -> float:
        """计算 RSI"""
        from core.indicators import calc_rsi
        close = self.history('close', period + 1)
        rsi = calc_rsi(close, period)
        return float(rsi.iloc[-1])
```

### 4.3 Strategy 基类 (base.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class Strategy(ABC):
    """
    策略基类

    借鉴 finquant 的 Strategy 设计
    所有策略必须继承此类并实现 on_bar 方法
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化

        参数:
            config: 策略配置参数
        """
        self.config = config or {}
        self._position = 0  # 当前持仓
        self._buy_price = None  # 买入价格

    @abstractmethod
    def on_bar(self, bar: Bar) -> Signal:
        """
        处理 K 线数据 (必须实现)

        参数:
            bar: K 线数据

        返回:
            交易信号
        """
        pass

    def on_init(self):
        """策略初始化回调"""
        pass

    def on_start(self):
        """策略启动回调"""
        pass

    def on_stop(self):
        """策略停止回调"""
        pass

    def on_order(self, order):
        """订单回调"""
        pass

    @property
    def position(self) -> int:
        """当前持仓"""
        return self._position

    @position.setter
    def position(self, value: int):
        """设置持仓"""
        self._position = value

    @property
    def buy_price(self) -> Optional[float]:
        """买入价格"""
        return self._buy_price

    @buy_price.setter
    def buy_price(self, value: float):
        """设置买入价格"""
        self._buy_price = value

    @property
    def has_position(self) -> bool:
        """是否有持仓"""
        return self._position > 0

    def buy(self, price: float, size: int = 100):
        """买入"""
        self._position += size
        self._buy_price = price

    def sell(self, price: float, size: int = None):
        """卖出"""
        if size is None:
            size = self._position
        self._position = max(0, self._position - size)
        if self._position == 0:
            self._buy_price = None

    @property
    def name(self) -> str:
        """策略名称"""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """策略描述"""
        return self.__doc__ or ""
```

### 4.4 策略注册表 (registry.py)

```python
from typing import Dict, Type, List
from .base import Strategy

class StrategyRegistry:
    """
    策略注册表

    借鉴 vectorbt 的指标工厂模式
    支持策略注册、查询、实例化
    """

    _strategies: Dict[str, Type[Strategy]] = {}

    @classmethod
    def register(cls, name: str = None):
        """
        注册策略装饰器

        参数:
            name: 策略名称，默认使用类名

        示例:
            @StrategyRegistry.register("ma_cross")
            class MACrossStrategy(Strategy):
                pass
        """
        def decorator(strategy_cls):
            strategy_name = name or strategy_cls.__name__
            cls._strategies[strategy_name] = strategy_cls
            return strategy_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> Type[Strategy]:
        """
        获取策略类

        参数:
            name: 策略名称

        返回:
            策略类
        """
        if name not in cls._strategies:
            raise KeyError(f"未找到策略: {name}，可用策略: {cls.list()}")
        return cls._strategies[name]

    @classmethod
    def create(cls, name: str, config: Dict = None) -> Strategy:
        """
        创建策略实例

        参数:
            name: 策略名称
            config: 策略配置

        返回:
            策略实例
        """
        strategy_cls = cls.get(name)
        return strategy_cls(config)

    @classmethod
    def list(cls) -> List[str]:
        """列出所有已注册的策略"""
        return list(cls._strategies.keys())

    @classmethod
    def clear(cls):
        """清除所有注册"""
        cls._strategies.clear()
```

### 4.5 双均线策略示例 (ma_cross.py)

```python
from .base import Strategy, Bar, Signal, SignalType
from .registry import StrategyRegistry

@StrategyRegistry.register("ma_cross")
class MACrossStrategy(Strategy):
    """
    双均线交叉策略

    - 短期均线上穿长期均线：买入
    - 短期均线下穿长期均线：卖出
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.fast_period = self.config.get('fast_period', 5)
        self.slow_period = self.config.get('slow_period', 20)

    def on_bar(self, bar: Bar) -> Signal:
        """处理 K 线"""
        # 数据不足时观望
        if bar._index < self.slow_period:
            return Signal(
                type=SignalType.HOLD,
                confidence=0,
                reason="数据不足"
            )

        # 计算均线
        fast_ma = bar.sma(self.fast_period)
        slow_ma = bar.sma(self.slow_period)

        # 计算前一日均线
        fast_ma_prev = bar.history('close', self.fast_period + 1).iloc[:-1].mean()
        slow_ma_prev = bar.history('close', self.slow_period + 1).iloc[:-1].mean()

        # 金叉买入
        if fast_ma > slow_ma and fast_ma_prev <= slow_ma_prev:
            if not self.has_position:
                return Signal(
                    type=SignalType.BUY,
                    confidence=0.7,
                    reason=f"MA{self.fast_period} 上穿 MA{self.slow_period}",
                    price=bar.close,
                    stop_loss=bar.close * 0.95,
                    take_profit=bar.close * 1.15
                )

        # 死叉卖出
        if fast_ma < slow_ma and fast_ma_prev >= slow_ma_prev:
            if self.has_position:
                return Signal(
                    type=SignalType.SELL,
                    confidence=0.7,
                    reason=f"MA{self.fast_period} 下穿 MA{self.slow_period}",
                    price=bar.close
                )

        # 观望
        return Signal(
            type=SignalType.HOLD,
            confidence=0,
            reason="无信号"
        )
```

---

## 5. 接口设计

### 5.1 简单接口

```python
from strategies import StrategyRegistry

# 创建策略
strategy = StrategyRegistry.create("ma_cross", {
    'fast_period': 5,
    'slow_period': 20
})

# 处理 K 线
bar = Bar(df, index=99)
signal = strategy.on_bar(bar)
```

### 5.2 批量回测接口

```python
from strategies import run_backtest

# 运行回测
result = run_backtest(
    strategy_name="ma_cross",
    stock_code="000001",
    start_date="20260101",
    end_date="20260614",
    config={'fast_period': 5, 'slow_period': 20}
)

print(result.summary())
```

---

## 6. 测试设计

### 6.1 单元测试

```python
class TestSignal:
    """Signal 测试"""

    def test_buy_signal(self):
        """测试买入信号"""
        pass

    def test_sell_signal(self):
        """测试卖出信号"""
        pass

    def test_hold_signal(self):
        """测试观望信号"""
        pass


class TestBar:
    """Bar 测试"""

    def test_properties(self):
        """测试基础属性"""
        pass

    def test_history(self):
        """测试历史数据查询"""
        pass

    def test_indicators(self):
        """测试指标计算"""
        pass


class TestStrategy:
    """Strategy 测试"""

    def test_initialization(self):
        """测试初始化"""
        pass

    def test_position(self):
        """测试持仓管理"""
        pass
```

---

## 7. 实现检查清单

### 7.1 功能完整性

- [ ] 实现 Signal 类
- [ ] 实现 Bar 类
- [ ] 实现 Strategy 基类
- [ ] 实现 StrategyRegistry 类
- [ ] 实现 MACrossStrategy
- [ ] 实现 MACDStrategy
- [ ] 实现 RSIStrategy
- [ ] 实现 BollStrategy

### 7.2 测试覆盖

- [ ] Signal 测试
- [ ] Bar 测试
- [ ] Strategy 测试
- [ ] 策略注册表测试
- [ ] 内置策略测试

---

## 8. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 策略基类 | strategies/base.py | ⬜ |
| 策略注册表 | strategies/registry.py | ⬜ |
| 双均线策略 | strategies/ma_cross.py | ⬜ |
| MACD 策略 | strategies/macd_strategy.py | ⬜ |
| RSI 策略 | strategies/rsi_strategy.py | ⬜ |
| 布林带策略 | strategies/boll_strategy.py | ⬜ |
| 模块初始化 | strategies/__init__.py | ⬜ |
| 单元测试 | tests/test_strategies.py | ⬜ |

---

## 9. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本，借鉴 finquant/QUANTAXIS/vectorbt | - |
