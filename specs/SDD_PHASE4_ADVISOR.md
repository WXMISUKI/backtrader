# 软件设计规格说明 (SDD)
# Phase 4: 智能投顾系统

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Phase 4 智能投顾系统 SDD |
| 版本 | v1.0 |
| 创建日期 | 2026-06-14 |
| 状态 | 待实现 |

---

## 1. 引言

### 1.1 目的

本文档详细描述智能投顾系统的设计规格，补充长线/短线策略、股票推荐、基本面分析等功能。

### 1.2 范围

本阶段负责：
- 长线投资策略
- 短线交易策略
- 基本面分析模块
- 股票推荐系统
- 市场分析模块

### 1.3 设计灵感来源

| 项目 | 借鉴内容 |
|------|---------|
| QUANTAXIS | 因子研究框架、数据结构 |
| FinRL | 强化学习思路、多策略集成 |
| akshare | 基本面数据接口 |
| PyPortfolioOpt | 投资组合优化 |

---

## 2. 系统概述

### 2.1 模块位置

```
skills/
├── stock-advisor/          # 个股分析 (已有)
├── stock-selector/         # 智能选股 (已有)
├── stock-report/           # 报告生成 (已有)
├── stock-simulator/        # 模拟交易 (已有)
├── stock-fundamental/      # 基本面分析 (新增)
│   ├── __init__.py
│   └── analyzer.py
├── stock-market/           # 市场分析 (新增)
│   ├── __init__.py
│   └── analyzer.py
├── stock-recommender/      # 股票推荐 (新增)
│   ├── __init__.py
│   └── recommender.py
└── stock-strategy/         # 策略库 (新增)
    ├── __init__.py
    ├── long_term.py        # 长线策略
    └── short_term.py       # 短线策略
```

---

## 3. 基本面分析模块设计

### 3.1 功能概述

分析股票的基本面数据，包括财务指标、估值指标、成长性指标等。

### 3.2 核心指标

| 类别 | 指标 | 说明 | 优质标准 |
|------|------|------|---------|
| 估值 | PE 市盈率 | 股价/每股收益 | < 20 |
| | PB 市净率 | 股价/每股净资产 | < 3 |
| | PS 市销率 | 股价/每股营收 | < 5 |
| 盈利 | ROE 净资产收益率 | 净利润/净资产 | > 15% |
| | ROA 总资产收益率 | 净利润/总资产 | > 5% |
| | 毛利率 | (营收-成本)/营收 | > 30% |
| 成长 | 营收增长率 | 同比增长率 | > 10% |
| | 净利润增长率 | 同比增长率 | > 10% |
| 安全 | 资产负债率 | 总负债/总资产 | < 60% |
| | 流动比率 | 流动资产/流动负债 | > 1.5 |

### 3.3 核心接口

```python
class FundamentalAnalyzer:
    """基本面分析器"""

    def analyze(self, stock_code: str) -> FundamentalResult:
        """分析股票基本面"""
        pass

    def get_valuation(self, stock_code: str) -> dict:
        """获取估值指标"""
        pass

    def get_profitability(self, stock_code: str) -> dict:
        """获取盈利指标"""
        pass

    def get_growth(self, stock_code: str) -> dict:
        """获取成长指标"""
        pass
```

---

## 4. 市场分析模块设计

### 4.1 功能概述

分析大盘走势、板块轮动、市场情绪等。

### 4.2 分析维度

| 维度 | 指标 | 说明 |
|------|------|------|
| 大盘 | 上证指数 | A股整体走势 |
| | 深证成指 | 深圳市场走势 |
| | 创业板指 | 创业板走势 |
| 板块 | 行业板块 | 各行业涨跌幅 |
| | 概念板块 | 热门概念 |
| 情绪 | 涨跌比 | 上涨/下跌股票数量 |
| | 成交量 | 市场活跃度 |
| | 北向资金 | 外资流向 |

### 4.3 核心接口

```python
class MarketAnalyzer:
    """市场分析器"""

    def get_market_overview(self) -> dict:
        """获取市场概览"""
        pass

    def get_sector_performance(self) -> pd.DataFrame:
        """获取板块表现"""
        pass

    def get_market_sentiment(self) -> dict:
        """获取市场情绪"""
        pass
```

---

## 5. 股票推荐系统设计

### 5.1 功能概述

综合技术面、基本面、市场面，推荐买入/卖出股票。

### 5.2 推荐策略

| 类型 | 策略 | 权重 | 说明 |
|------|------|------|------|
| **长线** | 基本面优质 | 40% | PE低、ROE高、成长好 |
| | 技术面支撑 | 30% | 均线多头、趋势向上 |
| | 市场面配合 | 30% | 板块轮动、资金流入 |
| **短线** | 技术面强势 | 50% | 金叉、突破、放量 |
| | 市场面热点 | 30% | 热门板块、资金关注 |
| | 基本面安全 | 20% | 无重大风险 |

### 5.3 核心接口

```python
class StockRecommender:
    """股票推荐器"""

    def recommend_long_term(self, top_n: int = 10) -> list:
        """长线推荐"""
        pass

    def recommend_short_term(self, top_n: int = 10) -> list:
        """短线推荐"""
        pass

    def recommend_by_risk(self, risk_level: str) -> list:
        """按风险偏好推荐"""
        pass
```

---

## 6. 长线策略设计

### 6.1 策略特点

| 特点 | 说明 |
|------|------|
| 投资周期 | 3个月以上 |
| 核心逻辑 | 基本面驱动 |
| 止损设置 | 较宽 (10-15%) |
| 止盈设置 | 较高 (30-50%) |
| 仓位管理 | 分批建仓 |

### 6.2 选股条件

```python
LONG_TERM_CONDITIONS = {
    # 估值条件
    'pe_max': 20,           # PE < 20
    'pb_max': 3,            # PB < 3

    # 盈利条件
    'roe_min': 15,          # ROE > 15%
    'gross_margin_min': 30, # 毛利率 > 30%

    # 成长条件
    'revenue_growth_min': 10,  # 营收增长 > 10%
    'profit_growth_min': 10,   # 利润增长 > 10%

    # 安全条件
    'debt_ratio_max': 60,   # 资产负债率 < 60%
}
```

---

## 7. 短线策略设计

### 7.1 策略特点

| 特点 | 说明 |
|------|------|
| 投资周期 | 1-10天 |
| 核心逻辑 | 技术面驱动 |
| 止损设置 | 较紧 (3-5%) |
| 止盈设置 | 适中 (10-15%) |
| 仓位管理 | 一次性建仓 |

### 7.2 选股条件

```python
SHORT_TERM_CONDITIONS = {
    # 技术条件
    'ma_cross': True,       # MA金叉
    'macd_cross': True,     # MACD金叉
    'rsi_oversold': True,   # RSI超卖反弹

    # 量能条件
    'volume_ratio_min': 1.5,  # 放量

    # 趋势条件
    'price_above_ma20': True, # 价格在MA20上方
}
```

---

## 8. 实现检查清单

### 8.1 基本面分析

- [ ] 实现 FundamentalAnalyzer
- [ ] 实现估值指标计算
- [ ] 实现盈利指标计算
- [ ] 实现成长指标计算

### 8.2 市场分析

- [ ] 实现 MarketAnalyzer
- [ ] 实现大盘分析
- [ ] 实现板块分析
- [ ] 实现市场情绪分析

### 8.3 股票推荐

- [ ] 实现 StockRecommender
- [ ] 实现长线推荐
- [ ] 实现短线推荐
- [ ] 实现风险匹配推荐

### 8.4 长短线策略

- [ ] 实现长线策略
- [ ] 实现短线策略
- [ ] 编写测试

---

## 9. 交付物清单

| 交付物 | 文件路径 | 状态 |
|--------|---------|------|
| 基本面分析器 | skills/stock-fundamental/analyzer.py | ⬜ |
| 市场分析器 | skills/stock-market/analyzer.py | ⬜ |
| 股票推荐器 | skills/stock-recommender/recommender.py | ⬜ |
| 长线策略 | skills/stock-strategy/long_term.py | ⬜ |
| 短线策略 | skills/stock-strategy/short_term.py | ⬜ |
| 单元测试 | tests/test_phase4.py | ⬜ |

---

## 10. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-06-14 | 初始版本 | - |
