# 归档: 可视化图表模块

## 1. 完成日期
2026-06-14

## 2. 功能清单

| 功能 | 状态 | 测试覆盖 |
|------|------|---------|
| KLineChart | ✅ | 9 tests |
| IndicatorChart | ✅ | 6 tests |
| BacktestChart | ✅ | 6 tests |
| Dashboard | ✅ | 5 tests |
| 主题系统 | ✅ | 4 tests |
| 集成测试 | ✅ | 2 tests |

## 3. 文件清单

### 3.1 实现文件

| 文件 | 描述 |
|------|------|
| `skills/stock_visual/__init__.py` | 模块初始化 |
| `skills/stock_visual/themes.py` | 主题样式定义 |
| `skills/stock_visual/charts.py` | 图表基类 |
| `skills/stock_visual/kline.py` | K 线图 |
| `skills/stock_visual/indicators.py` | 指标图 |
| `skills/stock_visual/backtest.py` | 回测结果图 |
| `skills/stock_visual/dashboard.py` | 仪表盘 |

### 3.2 测试文件

| 文件 | 测试数 | 状态 |
|------|--------|------|
| `tests/test_visualization.py` | 32 | ✅ 全部通过 |

### 3.3 规格文件

| 文件 | 描述 |
|------|------|
| `specs/SDD_VISUALIZATION.md` | 规格说明 |

## 4. 核心类

### 4.1 StockChart (基类)

所有图表的基类，提供通用功能。

```python
chart = StockChart(theme='dark')
chart.create_figure(nrows=2, figsize=(14, 10))
chart.set_title('标题')
chart.save('output.png')
```

**方法:**
- `create_figure(nrows, ncols, figsize, height_ratios)`: 创建图表
- `get_ax(index)`: 获取指定 axes
- `set_title(title, ax_index)`: 设置标题
- `set_xlabel(label, ax_index)`: 设置 X 轴标签
- `set_ylabel(label, ax_index)`: 设置 Y 轴标签
- `add_legend(ax_index, loc)`: 添加图例
- `save(path, dpi)`: 保存图表

### 4.2 KLineChart

K 线图，支持均线、布林带、信号标注。

```python
chart = KLineChart(theme='dark')
chart.plot(df, title='平安银行', show_volume=True)
chart.add_ma([5, 10, 20])
chart.add_boll()
chart.add_signals(signals)
chart.save('kline.png')
```

**方法:**
- `plot(df, title, show_volume)`: 绘制 K 线图
- `add_ma(periods, ax_index)`: 添加均线
- `add_boll(period, std_dev, ax_index)`: 添加布林带
- `add_signals(signals, ax_index)`: 添加买卖信号
- `add_price_annotations(ax_index)`: 添加价格标注

### 4.3 IndicatorChart

技术指标图。

```python
chart = IndicatorChart(theme='dark')
chart.create_figure(nrows=3)
chart.plot_macd(df, ax_index=0)
chart.plot_rsi(df, ax_index=1)
chart.plot_kdj(df, ax_index=2)
chart.save('indicators.png')
```

**方法:**
- `plot_macd(df, ax_index, fast, slow, signal)`: 绘制 MACD
- `plot_rsi(df, ax_index, period)`: 绘制 RSI
- `plot_kdj(df, ax_index, n, m1, m2)`: 绘制 KDJ
- `plot_volume(df, ax_index)`: 绘制成交量

### 4.4 BacktestChart

回测结果图。

```python
chart = BacktestChart(theme='dark')
chart.plot_summary(equity, returns, trades, save_path='backtest.png')
```

**方法:**
- `plot_equity_curve(equity, benchmark, ax_index)`: 绘制资金曲线
- `plot_drawdown(equity, ax_index)`: 绘制回撤曲线
- `plot_monthly_returns(returns, ax_index)`: 绘制月度收益热力图
- `plot_trade_distribution(trades, ax_index)`: 绘制交易分布
- `plot_summary(equity, returns, trades, save_path)`: 绘制总结

### 4.5 Dashboard

综合仪表盘。

```python
# 股票分析仪表盘
dashboard = Dashboard(theme='dark')
dashboard.create_stock_dashboard(df, signals=signals, analysis=analysis)
dashboard.save('stock_dashboard.png')

# 回测结果仪表盘
dashboard.create_backtest_dashboard(equity, trades=trades, metrics=metrics)
dashboard.save('backtest_dashboard.png')

# 推荐结果仪表盘
dashboard.create_recommendation_dashboard(recommendations)
dashboard.save('recommend_dashboard.png')
```

**方法:**
- `create_stock_dashboard(df, indicators, signals, analysis, title)`: 创建股票分析仪表盘
- `create_backtest_dashboard(equity, returns, trades, metrics, title)`: 创建回测结果仪表盘
- `create_recommendation_dashboard(recommendations, title)`: 创建推荐结果仪表盘

## 5. 快捷函数

```python
from skills.stock_visual import (
    plot_kline,
    plot_indicators,
    plot_backtest,
    create_stock_dashboard,
    create_backtest_dashboard
)

# K 线图
chart = plot_kline(df, ma_periods=[5, 10, 20], save_path='kline.png')

# 指标图
chart = plot_indicators(df, indicators=['macd', 'rsi', 'volume'])

# 回测图
chart = plot_backtest(equity, save_path='backtest.png')

# 仪表盘
dashboard = create_stock_dashboard(df, signals=signals)
dashboard.save('dashboard.png')
```

## 6. 主题系统

### 6.1 暗色主题

```python
from skills.stock_visual.themes import DARK_THEME
```

特点:
- 背景色: #1a1a2e
- 涨: 红色 (#ff4757)
- 跌: 绿色 (#2ed573)
- 适合夜间使用

### 6.2 亮色主题

```python
from skills.stock_visual.themes import LIGHT_THEME
```

特点:
- 背景色: #ffffff
- 涨: 红色 (#ff4757)
- 跌: 绿色 (#2ed573)
- 适合白天使用

### 6.3 自定义主题

```python
CUSTOM_THEME = {
    'background': '#000000',
    'up_color': '#ff0000',
    'down_color': '#00ff00',
    # ... 其他配置
}
```

## 7. 测试结果

```
============================= 32 passed in 14.94s ==============================

tests/test_visualization.py::TestThemes::test_dark_theme PASSED
tests/test_visualization.py::TestThemes::test_light_theme PASSED
tests/test_visualization.py::TestThemes::test_invalid_theme PASSED
tests/test_visualization.py::TestThemes::test_themes_dict PASSED
tests/test_visualization.py::TestKLineChart::test_init PASSED
tests/test_visualization.py::TestKLineChart::test_plot PASSED
tests/test_visualization.py::TestKLineChart::test_plot_with_volume PASSED
tests/test_visualization.py::TestKLineChart::test_add_ma PASSED
tests/test_visualization.py::TestKLineChart::test_add_boll PASSED
tests/test_visualization.py::TestKLineChart::test_add_signals PASSED
tests/test_visualization.py::TestKLineChart::test_plot_kline_function PASSED
tests/test_visualization.py::TestKLineChart::test_light_theme PASSED
tests/test_visualization.py::TestIndicatorChart::test_init PASSED
tests/test_visualization.py::TestIndicatorChart::test_plot_macd PASSED
tests/test_visualization.py::TestIndicatorChart::test_plot_rsi PASSED
tests/test_visualization.py::TestIndicatorChart::test_plot_kdj PASSED
tests/test_visualization.py::TestIndicatorChart::test_plot_volume PASSED
tests/test_visualization.py::TestIndicatorChart::test_plot_multiple_indicators PASSED
tests/test_visualization.py::TestIndicatorChart::test_plot_indicators_function PASSED
tests/test_visualization.py::TestBacktestChart::test_init PASSED
tests/test_visualization.py::TestBacktestChart::test_plot_equity_curve PASSED
tests/test_visualization.py::TestBacktestChart::test_plot_drawdown PASSED
tests/test_visualization.py::TestBacktestChart::test_plot_trade_distribution PASSED
tests/test_visualization.py::TestBacktestChart::test_plot_summary PASSED
tests/test_visualization.py::TestBacktestChart::test_plot_backtest_function PASSED
tests/test_visualization.py::TestDashboard::test_init PASSED
tests/test_visualization.py::TestDashboard::test_create_stock_dashboard PASSED
tests/test_visualization.py::TestDashboard::test_create_backtest_dashboard PASSED
tests/test_visualization.py::TestDashboard::test_create_recommendation_dashboard PASSED
tests/test_visualization.py::TestDashboard::test_create_stock_dashboard_function PASSED
tests/test_visualization.py::TestIntegration::test_full_analysis_visualization PASSED
tests/test_visualization.py::TestIntegration::test_theme_consistency PASSED
```

## 8. 使用示例

### 8.1 股票分析可视化

```python
from skills.stock_visual import plot_kline, plot_indicators
import akshare as ak

# 获取数据
df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                         start_date="20240101", end_date="20240601")

# K 线图
plot_kline(df, title='平安银行', ma_periods=[5, 10, 20],
           save_path='pingan_kline.png')

# 指标图
plot_indicators(df, indicators=['macd', 'rsi', 'kdj'],
                save_path='pingan_indicators.png')
```

### 8.2 回测结果可视化

```python
from skills.stock_visual import plot_backtest, create_backtest_dashboard

# 假设有回测结果
equity_series = backtest_result.equity_curve
trades = backtest_result.trades

# 简单回测图
plot_backtest(equity_series, trades=trades, save_path='backtest.png')

# 详细仪表盘
dashboard = create_backtest_dashboard(
    equity_series,
    trades=trades,
    metrics={'sharpe': 1.5, 'max_dd': -15.2}
)
dashboard.save('backtest_dashboard.png')
```

### 8.3 推荐结果可视化

```python
from skills.stock_visual import Dashboard

recommendations = [
    {'code': '000001', 'name': '平安银行', 'price': 12.50,
     'change': 1.5, 'score': 85.0, 'recommendation': '买入'},
    {'code': '600036', 'name': '招商银行', 'price': 35.20,
     'change': -0.8, 'score': 78.0, 'recommendation': '买入'},
]

dashboard = Dashboard(theme='dark')
dashboard.create_recommendation_dashboard(recommendations)
dashboard.save('recommendations.png')
```

## 9. 技术要点

### 9.1 matplotlib 使用

- 使用 Agg 后端，支持非交互式环境
- 配置中文字体 (SimHei, Microsoft YaHei)
- 使用 PatchCollection 绘制 K 线
- 使用 FuncFormatter 格式化成交量

### 9.2 主题系统

- 使用字典存储主题配置
- 支持动态切换主题
- 颜色配置覆盖所有图表元素

### 9.3 仪表盘设计

- 使用 GridSpec 布局
- 支持多子图组合
- 信息面板使用文本渲染

## 10. 已知限制

1. **中文字体**: 某些环境可能缺少中文字体，会显示方块
2. **交互性**: 当前为静态图表，不支持交互
3. **性能**: 大数据量 (>10000 点) 可能较慢
4. **图表类型**: 仅支持常见金融图表

## 11. 后续优化

1. 添加交互式图表 (plotly)
2. 支持实时数据更新
3. 添加更多图表类型 (点数图、砖形图)
4. 支持导出 HTML 报告
