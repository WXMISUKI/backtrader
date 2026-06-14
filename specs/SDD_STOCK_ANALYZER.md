# 软件设计规格说明 (SDD)
# 个股分析模块 (StockAnalyzer)

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | 个股分析模块 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述个股分析模块的设计规格，整合技术指标和信号系统，提供完整的股票分析能力。

### 1.2 范围

本模块负责整合所有子模块，提供：
- 股票数据获取和封装
- 技术指标计算
- 买卖信号生成
- 风险评估
- 分析报告输出

### 1.3 设计灵感来源

本设计借鉴了以下优秀开源项目的设计思路：

| 项目 | 借鉴内容 |
|------|---------|
| **finquant** | EventBus 事件驱动、二级缓存、配置驱动风控 |
| **QUANTAXIS** | 统一数据结构、分层数据获取、因子分析 |
| **vectorbt** | Pandas Accessor、指标工厂、配置系统 |

### 1.4 参考文档

- `SDD_INDICATORS.md` - 技术指标模块规格
- `SDD_SIGNALS.md` - 信号系统模块规格
- `DEVELOPMENT_SPEC.md` - 开发规格书

---

## 2. 系统概述

### 2.1 模块位置

```
skills/
└── stock-advisor/
    ├── __init__.py          # 模块初始化
    ├── skill.py             # Skill 主入口
    ├── analyzer.py          # 股票分析器 (核心)
    ├── stock_data.py        # 股票数据封装
    └── report_builder.py    # 报告构建器
```

### 2.2 依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                 stock-advisor Skill                          │
├─────────────────────────────────────────────────────────────┤
│  analyzer.py (核心分析器)                                   │
│      │                                                       │
│      ├── core.data.eastmoney_api (数据获取)                 │
│      ├── core.indicators (技术指标)                          │
│      ├── core.signals (信号生成)                             │
│      └── core.risk (风险控制)                                │
│                                                             │
│  被依赖:                                                    │
│      └── 用户调用 / 其他 Skill                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 设计决策

### 3.1 核心设计原则

借鉴三个项目的优秀设计，我们采用以下原则：

**1. 统一数据结构 (借鉴 QUANTAXIS 的 QADataStruct)**

```python
class StockData:
    """股票数据统一封装"""
    def __init__(self, code, name, df):
        self.code = code          # 股票代码
        self.name = name          # 股票名称
        self.df = df              # OHLCV DataFrame
        self._indicators = None   # 懒计算缓存
        self._signals = None      # 懒计算缓存

    @property
    def indicators(self):
        """懒计算技术指标"""
        if self._indicators is None:
            self._indicators = self._calc_indicators()
        return self._indicators

    @property
    def signals(self):
        """懒计算信号"""
        if self._signals is None:
            self._signals = self._calc_signals()
        return self._signals
```

**2. 配置驱动 (借鉴 vectorbt 的嵌套配置)**

```python
@dataclass
class AnalysisConfig:
    """分析配置"""
    # 数据配置
    start_date: str = "20260101"
    end_date: str = "20260614"
    adjust: str = "qfq"

    # 指标参数
    ma_periods: list = field(default_factory=lambda: [5, 10, 20, 60])
    rsi_period: int = 14
    macd_params: tuple = (12, 26, 9)

    # 风险配置
    risk_profile: str = "moderate"

    # 输出配置
    output_format: str = "dict"  # dict/json/dataframe
```

**3. 渐进式 API (借鉴 finquant 的便捷函数)**

```python
# 简单用法
result = analyze("000001")

# 高级用法
config = AnalysisConfig(risk_profile="aggressive")
analyzer = StockAnalyzer(config)
result = analyzer.analyze("000001")
```

### 3.2 懒计算模式 (借鉴 vectorbt 的 @property 缓存)

所有计算密集型操作采用懒计算模式：
- 首次访问时计算并缓存
- 后续访问直接返回缓存结果
- 通过 `@property` 装饰器实现透明调用

---

## 4. 模块详细设计

### 4.1 StockData 类 (stock_data.py)

```python
class StockData:
    """
    股票数据统一封装

    借鉴 QUANTAXIS 的 QADataStruct 设计
    """

    def __init__(self, code: str, name: str, df: pd.DataFrame):
        """
        初始化

        参数:
            code: 股票代码 (如 "000001")
            name: 股票名称 (如 "平安银行")
            df: OHLCV DataFrame，必须包含 open/high/low/close/volume 列
        """
        self.code = code
        self.name = name
        self.df = df
        self._indicators = None
        self._signals = None

    @property
    def close(self) -> pd.Series:
        """收盘价"""
        return self.df['close']

    @property
    def open(self) -> pd.Series:
        """开盘价"""
        return self.df['open']

    @property
    def high(self) -> pd.Series:
        """最高价"""
        return self.df['high']

    @property
    def low(self) -> pd.Series:
        """最低价"""
        return self.df['low']

    @property
    def volume(self) -> pd.Series:
        """成交量"""
        return self.df['volume']

    @property
    def latest_price(self) -> float:
        """最新价格"""
        return float(self.close.iloc[-1])

    @property
    def indicators(self) -> pd.DataFrame:
        """
        技术指标 (懒计算)

        返回:
            包含所有技术指标的 DataFrame
        """
        if self._indicators is None:
            from core.indicators import IndicatorCalculator
            calc = IndicatorCalculator()
            self._indicators = calc.calc_all(
                self.high, self.low, self.close, self.volume
            )
        return self._indicators

    @property
    def signals(self) -> pd.DataFrame:
        """
        交易信号 (懒计算)

        返回:
            包含买卖信号的 DataFrame
        """
        if self._signals is None:
            from core.signals import SignalGenerator
            gen = SignalGenerator()
            self._signals = gen.generate(
                self.close, self.high, self.low,
                self.volume, self.indicators
            )
        return self._signals

    def get_latest_signal(self, risk_profile: str = "moderate") -> dict:
        """获取最新信号"""
        from core.signals import SignalGenerator
        gen = SignalGenerator(risk_profile)
        return gen.get_latest_signal(
            self.close, self.high, self.low,
            self.volume, self.indicators
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'latest_price': self.latest_price,
            'data_points': len(self.df),
            'date_range': f"{self.df.index[0]} ~ {self.df.index[-1]}"
        }
```

### 4.2 StockAnalyzer 类 (analyzer.py)

```python
class StockAnalyzer:
    """
    股票分析器

    整合数据获取、指标计算、信号生成、风险评估
    """

    def __init__(self, config: AnalysisConfig = None):
        """初始化"""
        self.config = config or AnalysisConfig()
        self._data_cache = {}  # 数据缓存

    def analyze(self, stock_code: str) -> AnalysisResult:
        """
        分析股票

        参数:
            stock_code: 股票代码

        返回:
            AnalysisResult 分析结果
        """
        # 1. 获取数据
        stock_data = self.get_stock_data(stock_code)

        # 2. 获取最新信号
        signal = stock_data.get_latest_signal(self.config.risk_profile)

        # 3. 评估风险
        risk = self._assess_risk(stock_data)

        # 4. 生成建议
        recommendation = self._generate_recommendation(signal, risk)

        # 5. 构建结果
        return AnalysisResult(
            stock_data=stock_data,
            signal=signal,
            risk=risk,
            recommendation=recommendation
        )

    def get_stock_data(self, stock_code: str) -> StockData:
        """获取股票数据 (带缓存)"""
        if stock_code in self._data_cache:
            return self._data_cache[stock_code]

        from core.data.eastmoney_api import get_stock_hist
        from eastmoney_config import EASTMONEY_COOKIES, EASTMONEY_HEADERS

        df = get_stock_hist(
            stock_code,
            self.config.start_date,
            self.config.end_date
        )

        # 获取股票名称
        name = self._get_stock_name(stock_code)

        stock_data = StockData(stock_code, name, df)
        self._data_cache[stock_code] = stock_data

        return stock_data

    def _assess_risk(self, stock_data: StockData) -> RiskAssessment:
        """评估风险"""
        from core.risk import RiskManager

        rm = RiskManager(self.config.risk_profile)

        # 获取最新价格
        current_price = stock_data.latest_price

        # 计算波动率
        returns = stock_data.close.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波动率

        # 计算最大回撤
        cumulative = (1 + returns).cumprod()
        max_drawdown = (cumulative / cumulative.cummax() - 1).min()

        return RiskAssessment(
            volatility=volatility,
            max_drawdown=max_drawdown,
            stop_loss_price=rm.calc_stop_loss_price(current_price),
            take_profit_price=rm.calc_take_profit_price(current_price),
            max_position=rm.get_max_position()
        )

    def _generate_recommendation(self, signal: dict, risk: RiskAssessment) -> Recommendation:
        """生成投资建议"""
        direction = signal['direction']
        confidence = signal['confidence']

        # 根据信号强度和风险调整建议
        if direction == 'BUY' and confidence >= 0.5:
            action = 'BUY'
            reason = f"买入信号强度 {confidence:.1%}，建议适量买入"
        elif direction == 'SELL' and confidence >= 0.5:
            action = 'SELL'
            reason = f"卖出信号强度 {confidence:.1%}，建议考虑卖出"
        else:
            action = 'HOLD'
            reason = "信号不明确，建议观望"

        return Recommendation(
            action=action,
            confidence=confidence,
            reason=reason,
            target_price=risk.take_profit_price,
            stop_loss=risk.stop_loss_price,
            position_ratio=risk.max_position
        )
```

### 4.3 AnalysisResult 类

```python
@dataclass
class AnalysisResult:
    """分析结果"""
    stock_data: StockData
    signal: dict
    risk: RiskAssessment
    recommendation: Recommendation

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'stock': self.stock_data.to_dict(),
            'signal': self.signal,
            'risk': {
                'volatility': round(self.risk.volatility, 4),
                'max_drawdown': round(self.risk.max_drawdown, 4),
                'stop_loss_price': round(self.risk.stop_loss_price, 2),
                'take_profit_price': round(self.risk.take_profit_price, 2),
            },
            'recommendation': {
                'action': self.recommendation.action,
                'confidence': round(self.recommendation.confidence, 4),
                'reason': self.recommendation.reason,
                'target_price': round(self.recommendation.target_price, 2),
                'stop_loss': round(self.recommendation.stop_loss, 2),
                'position_ratio': round(self.recommendation.position_ratio, 2),
            }
        }

    def summary(self) -> str:
        """生成摘要"""
        r = self.recommendation
        return (
            f"【{self.stock_data.name}({self.stock_data.code})】\n"
            f"当前价格: {self.stock_data.latest_price:.2f}\n"
            f"操作建议: {r.action}\n"
            f"置信度: {r.confidence:.1%}\n"
            f"原因: {r.reason}\n"
            f"目标价: {r.target_price:.2f}\n"
            f"止损价: {r.stop_loss:.2f}\n"
            f"建议仓位: {r.position_ratio:.0%}"
        )
```

### 4.4 便捷函数 (skill.py)

```python
def analyze(stock_code: str, risk_profile: str = "moderate") -> AnalysisResult:
    """
    分析股票 (便捷函数)

    参数:
        stock_code: 股票代码
        risk_profile: 风险配置 (conservative/moderate/aggressive)

    返回:
        AnalysisResult 分析结果

    示例:
        >>> from skills.stock_advisor import analyze
        >>> result = analyze("000001", "moderate")
        >>> print(result.summary())
    """
    config = AnalysisConfig(risk_profile=risk_profile)
    analyzer = StockAnalyzer(config)
    return analyzer.analyze(stock_code)


def batch_analyze(stock_codes: list, risk_profile: str = "moderate") -> list:
    """
    批量分析股票

    参数:
        stock_codes: 股票代码列表
        risk_profile: 风险配置

    返回:
        AnalysisResult 列表
    """
    config = AnalysisConfig(risk_profile=risk_profile)
    analyzer = StockAnalyzer(config)
    return [analyzer.analyze(code) for code in stock_codes]
```

---

## 5. 接口设计

### 5.1 简单接口

```python
# 最简单的用法
from skills.stock_advisor import analyze

result = analyze("000001")
print(result.summary())
```

### 5.2 高级接口

```python
# 高级用法
from skills.stock_advisor import StockAnalyzer, AnalysisConfig

config = AnalysisConfig(
    start_date="20260101",
    end_date="20260614",
    risk_profile="aggressive",
    ma_periods=[5, 10, 20, 60]
)

analyzer = StockAnalyzer(config)
result = analyzer.analyze("000001")

# 访问详细数据
print(result.signal)
print(result.risk)
print(result.recommendation)
```

### 5.3 批量接口

```python
# 批量分析
from skills.stock_advisor import batch_analyze

codes = ["000001", "600519", "000858"]
results = batch_analyze(codes, "moderate")

for r in results:
    print(r.summary())
    print("---")
```

---

## 6. 输出格式规范

### 6.1 分析结果字典

```json
{
    "stock": {
        "code": "000001",
        "name": "平安银行",
        "latest_price": 11.24,
        "data_points": 120,
        "date_range": "2026-01-02 ~ 2026-06-12"
    },
    "signal": {
        "buy_strength": 0.65,
        "sell_strength": 0.20,
        "direction": "BUY",
        "confidence": 0.65
    },
    "risk": {
        "volatility": 0.25,
        "max_drawdown": -0.15,
        "stop_loss_price": 10.68,
        "take_profit_price": 12.93
    },
    "recommendation": {
        "action": "BUY",
        "confidence": 0.65,
        "reason": "买入信号强度 65%，建议适量买入",
        "target_price": 12.93,
        "stop_loss": 10.68,
        "position_ratio": 0.50
    }
}
```

### 6.2 摘要格式

```
【平安银行(000001)】
当前价格: 11.24
操作建议: BUY
置信度: 65%
原因: 买入信号强度 65%，建议适量买入
目标价: 12.93
止损价: 10.68
建议仓位: 50%
```

---

## 7. 测试设计

### 7.1 单元测试

```python
class TestStockData:
    """StockData 测试"""

    def test_initialization(self):
        """测试初始化"""
        pass

    def test_lazy_indicators(self):
        """测试指标懒计算"""
        pass

    def test_lazy_signals(self):
        """测试信号懒计算"""
        pass


class TestStockAnalyzer:
    """StockAnalyzer 测试"""

    def test_analyze(self):
        """测试分析功能"""
        pass

    def test_cache(self):
        """测试数据缓存"""
        pass

    def test_batch_analyze(self):
        """测试批量分析"""
        pass
```

---

## 8. 实现检查清单

### 8.1 功能完整性

- [ ] 实现 StockData 类
- [ ] 实现 StockAnalyzer 类
- [ ] 实现 AnalysisResult 类
- [ ] 实现 RiskAssessment 类
- [ ] 实现 Recommendation 类
- [ ] 实现 AnalysisConfig 类
- [ ] 实现 analyze() 便捷函数
- [ ] 实现 batch_analyze() 批量函数

### 8.2 集成测试

- [ ] 测试数据获取
- [ ] 测试指标计算
- [ ] 测试信号生成
- [ ] 测试风险评估
- [ ] 测试完整流程

---

## 9. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 股票数据封装 | skills/stock_advisor/stock_data.py | ⬜ |
| 股票分析器 | skills/stock_advisor/analyzer.py | ⬜ |
| 报告构建器 | skills/stock_advisor/report_builder.py | ⬜ |
| Skill 入口 | skills/stock_advisor/skill.py | ⬜ |
| 模块初始化 | skills/stock_advisor/__init__.py | ⬜ |
| 单元测试 | tests/test_stock_analyzer.py | ⬜ |

---

## 10. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本，借鉴 finquant/QUANTAXIS/vectorbt | - |
