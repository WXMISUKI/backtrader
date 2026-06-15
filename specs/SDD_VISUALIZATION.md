# SDD: 可视化图表模块

## 1. 概述

### 1.1 目标
为量化交易系统添加完整的可视化能力，包括 K 线图、技术指标图、信号标注、回测曲线、推荐结果展示等。

### 1.2 背景
当前系统问题：
- skills 模块没有任何可视化代码
- 报告都是纯文本格式
- 无法直观展示分析结果
- 缺少交互式图表

### 1.3 设计来源
- mplfinance (专业 K 线图库)
- plotly (交互式图表)
- backtrader 内置绘图模块

## 2. 架构设计

### 2.1 模块结构

```
skills/stock_visual/
├── __init__.py
├── charts.py          # 核心图表类
├── kline.py           # K 线图
├── indicators.py      # 指标图
├── signals.py         # 信号标注图
├── backtest.py        # 回测结果图
├── dashboard.py       # 仪表盘
└── themes.py          # 主题样式
```

### 2.2 核心类

#### StockChart (股票图表基类)

```python
class StockChart:
    """股票图表基类"""

    def __init__(self, theme='dark'):
        self.theme = THEMES[theme]
        self.fig = None
        self.ax = None

    def create_figure(self, nrows=1, figsize=(14, 10)):
        """创建图表"""
        self.fig, self.axes = plt.subplots(
            nrows=nrows, figsize=figsize,
            gridspec_kw={'height_ratios': self._get_ratios(nrows)}
        )
        return self

    def save(self, path, dpi=150):
        """保存图表"""
        self.fig.savefig(path, dpi=dpi, bbox_inches='tight')

    def show(self):
        """显示图表"""
        plt.show()
```

#### KLineChart (K 线图)

```python
class KLineChart(StockChart):
    """K 线图"""

    def plot(self, df, title=None):
        """
        绘制 K 线图

        Args:
            df: DataFrame with columns [date, open, high, low, close, volume]
            title: 图表标题
        """
        # 使用 mplfinance 或手动绘制
        mpf.plot(df, type='candle', style=self.theme,
                 volume=True, ax=self.ax)

    def add_ma(self, periods=[5, 10, 20]):
        """添加均线"""
        for period in periods:
            ma = self.df['close'].rolling(period).mean()
            self.ax.plot(ma, label=f'MA{period}')

    def add_boll(self, period=20, std=2):
        """添加布林带"""
        ma = self.df['close'].rolling(period).mean()
        std = self.df['close'].rolling(period).std()
        self.ax.fill_between(ma - std*2, ma + std*2, alpha=0.2)

    def add_signals(self, signals):
        """添加买卖信号"""
        buy_signals = signals[signals['type'] == 'BUY']
        sell_signals = signals[signals['type'] == 'SELL']
        self.ax.scatter(buy_signals.index, buy_signals['price'],
                       marker='^', color='red', label='买入')
        self.ax.scatter(sell_signals.index, sell_signals['price'],
                       marker='v', color='green', label='卖出')
```

#### IndicatorChart (指标图)

```python
class IndicatorChart(StockChart):
    """技术指标图"""

    def plot_macd(self, df):
        """绘制 MACD"""
        # DIF, DEA, MACD柱

    def plot_rsi(self, df, period=14):
        """绘制 RSI"""
        # 超买超卖线

    def plot_kdj(self, df):
        """绘制 KDJ"""
        # K, D, J 线

    def plot_volume(self, df):
        """绘制成交量"""
        # 成交量柱状图
```

#### BacktestChart (回测结果图)

```python
class BacktestChart(StockChart):
    """回测结果图"""

    def plot_equity_curve(self, equity_series):
        """绘制资金曲线"""
        self.ax.plot(equity_series, label='策略资金')
        self.ax.fill_between(equity_series.index, equity_series, alpha=0.3)

    def plot_drawdown(self, equity_series):
        """绘制回撤曲线"""
        drawdown = (equity_series / equity_series.cummax() - 1) * 100
        self.ax.fill_between(drawdown.index, drawdown, color='red', alpha=0.3)

    def plot_monthly_returns(self, returns):
        """绘制月度收益热力图"""
        # 月份 x 年份 热力图

    def plot_trade_distribution(self, trades):
        """绘制交易分布"""
        # 盈亏分布直方图
```

#### Dashboard (仪表盘)

```python
class Dashboard:
    """综合仪表盘"""

    def __init__(self):
        self.charts = []

    def add_chart(self, chart, position):
        """添加图表到仪表盘"""
        self.charts.append((chart, position))

    def create_stock_dashboard(self, stock_data, analysis_result):
        """创建股票分析仪表盘"""
        # K 线图 + 指标 + 信号 + 风险

    def create_backtest_dashboard(self, backtest_result):
        """创建回测结果仪表盘"""
        # 资金曲线 + 回撤 + 交易统计

    def create_recommendation_dashboard(self, recommendations):
        """创建推荐结果仪表盘"""
        # 推荐列表 + 评分 + 风险
```

## 3. 功能设计

### 3.1 K 线图

| 功能 | 描述 |
|------|------|
| 基础 K 线 | 标准 OHLC K 线图 |
| 均线叠加 | MA5/10/20/60 |
| 布林带 | 上中下轨 |
| 成交量 | 底部成交量柱状图 |
| 信号标注 | 买卖点标记 |

### 3.2 指标图

| 功能 | 描述 |
|------|------|
| MACD | DIF/DEA 线 + MACD 柱 |
| RSI | RSI 线 + 超买超卖区间 |
| KDJ | K/D/J 三线 |
| 成交量 | 量能分析 |

### 3.3 回测图

| 功能 | 描述 |
|------|------|
| 资金曲线 | 策略资金变化 |
| 回撤曲线 | 最大回撤展示 |
| 月度收益 | 月度收益热力图 |
| 交易分布 | 盈亏分布直方图 |

### 3.4 仪表盘

| 功能 | 描述 |
|------|------|
| 股票分析盘 | 综合分析展示 |
| 回测结果盘 | 回测结果展示 |
| 推荐结果盘 | 推荐列表展示 |

## 4. 接口设计

### 4.1 快捷函数

```python
from skills.stock_visual import (
    plot_kline,
    plot_indicators,
    plot_backtest,
    create_stock_dashboard
)

# K 线图
plot_kline(df, title='平安银行', save_path='kline.png')

# 指标图
plot_indicators(df, indicators=['macd', 'rsi', 'kdj'])

# 回测图
plot_backtest(result, save_path='backtest.png')

# 仪表盘
dashboard = create_stock_dashboard(stock_data, analysis)
dashboard.save('dashboard.png')
```

### 4.2 类接口

```python
from skills.stock_visual import KLineChart, IndicatorChart, BacktestChart

# K 线图
chart = KLineChart(theme='dark')
chart.create_figure(nrows=2)
chart.plot(df)
chart.add_ma([5, 10, 20])
chart.add_signals(signals)
chart.save('kline.png')

# 指标图
indicator = IndicatorChart()
indicator.create_figure(nrows=3)
indicator.plot_macd(df)
indicator.plot_rsi(df)
indicator.plot_kdj(df)
indicator.save('indicators.png')
```

## 5. 主题设计

### 5.1 暗色主题

```python
DARK_THEME = {
    'background': '#1a1a2e',
    'grid': '#16213e',
    'text': '#e6e6e6',
    'up_color': '#ff4757',      # 涨 - 红色
    'down_color': '#2ed573',    # 跌 - 绿色
    'volume_up': '#ff6b81',
    'volume_down': '#7bed9f',
    'ma_colors': ['#f0932b', '#eb4d4b', '#6ab04c', '#22a6b3'],
}
```

### 5.2 亮色主题

```python
LIGHT_THEME = {
    'background': '#ffffff',
    'grid': '#f0f0f0',
    'text': '#333333',
    'up_color': '#ff4757',
    'down_color': '#2ed573',
    'volume_up': '#ff6b81',
    'volume_down': '#7bed9f',
    'ma_colors': ['#f0932b', '#eb4d4b', '#6ab04c', '#22a6b3'],
}
```

## 6. 数据流

```
原始数据 (DataFrame)
    │
    ▼
┌─────────────────┐
│  数据预处理     │
│  计算指标       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  创建图表       │
│  设置主题       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  绘制内容       │
│  K线/指标/信号  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  保存/显示      │
└─────────────────┘
```

## 7. 测试计划

### 7.1 单元测试

| 测试项 | 描述 |
|--------|------|
| test_kline_chart | 测试 K 线图绘制 |
| test_indicator_chart | 测试指标图绘制 |
| test_backtest_chart | 测试回测图绘制 |
| test_theme_switch | 测试主题切换 |
| test_save_formats | 测试保存格式 |

### 7.2 集成测试

| 测试项 | 描述 |
|--------|------|
| test_stock_dashboard | 测试股票分析仪表盘 |
| test_backtest_dashboard | 测试回测结果仪表盘 |

## 8. 依赖

- matplotlib (已有)
- mplfinance (需安装)
- pandas (已有)
- numpy (已有)

## 9. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 性能问题 | 限制数据点数量 |
| 中文显示 | 配置字体 |
| 兼容性 | 降级到 matplotlib |
