"""
可视化模块测试
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')

from skills.stock_visual import (
    KLineChart,
    IndicatorChart,
    BacktestChart,
    Dashboard,
    plot_kline,
    plot_indicators,
    plot_backtest,
    create_stock_dashboard,
    create_backtest_dashboard
)
from skills.stock_visual.themes import THEMES, get_theme


def create_sample_data(n=100):
    """创建示例股票数据"""
    np.random.seed(42)

    dates = pd.date_range('2024-01-01', periods=n, freq='B')
    price = 100 + np.cumsum(np.random.randn(n) * 2)

    df = pd.DataFrame({
        'date': dates,
        'open': price + np.random.randn(n) * 0.5,
        'high': price + abs(np.random.randn(n)) * 2,
        'low': price - abs(np.random.randn(n)) * 2,
        'close': price,
        'volume': np.random.randint(1000000, 10000000, n)
    })

    return df


def create_sample_signals(df, n_signals=10):
    """创建示例信号数据"""
    np.random.seed(42)

    indices = np.random.choice(len(df), n_signals, replace=False)
    signals = []

    for idx in indices:
        signal_type = 'BUY' if np.random.random() > 0.5 else 'SELL'
        signals.append({
            'date': df.iloc[idx]['date'],
            'type': signal_type,
            'price': df.iloc[idx]['close']
        })

    return pd.DataFrame(signals)


class TestThemes:
    """主题测试"""

    def test_dark_theme(self):
        """测试暗色主题"""
        theme = get_theme('dark')
        assert 'background' in theme
        assert 'up_color' in theme
        assert 'down_color' in theme

    def test_light_theme(self):
        """测试亮色主题"""
        theme = get_theme('light')
        assert 'background' in theme
        assert 'up_color' in theme
        assert 'down_color' in theme

    def test_invalid_theme(self):
        """测试无效主题"""
        with pytest.raises(ValueError, match="Unknown theme"):
            get_theme('invalid')

    def test_themes_dict(self):
        """测试主题字典"""
        assert 'dark' in THEMES
        assert 'light' in THEMES


class TestKLineChart:
    """K 线图测试"""

    def test_init(self):
        """测试初始化"""
        chart = KLineChart(theme='dark')
        assert chart.theme['name'] == 'dark'

    def test_plot(self):
        """测试绘制"""
        df = create_sample_data(50)

        chart = KLineChart(theme='dark')
        chart.plot(df, title='Test KLine')

        assert chart.fig is not None
        assert chart.axes is not None

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kline.png'))

    def test_plot_with_volume(self):
        """测试带成交量的绘制"""
        df = create_sample_data(50)

        chart = KLineChart(theme='dark')
        chart.plot(df, show_volume=True)

        assert len(chart.axes) == 2

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kline_volume.png'))

    def test_add_ma(self):
        """测试添加均线"""
        df = create_sample_data(50)

        chart = KLineChart(theme='dark')
        chart.plot(df)
        chart.add_ma([5, 10, 20])

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kline_ma.png'))

    def test_add_boll(self):
        """测试添加布林带"""
        df = create_sample_data(50)

        chart = KLineChart(theme='dark')
        chart.plot(df)
        chart.add_boll()

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kline_boll.png'))

    def test_add_signals(self):
        """测试添加信号"""
        df = create_sample_data(50)
        signals = create_sample_signals(df, 5)

        chart = KLineChart(theme='dark')
        chart.plot(df)
        chart.add_signals(signals)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kline_signals.png'))

    def test_plot_kline_function(self):
        """测试快捷函数"""
        df = create_sample_data(50)
        signals = create_sample_signals(df, 5)

        save_path = os.path.join(tempfile.gettempdir(), 'test_plot_kline.png')
        chart = plot_kline(
            df,
            title='Test',
            ma_periods=[5, 10],
            signals=signals,
            save_path=save_path
        )

        assert chart is not None
        assert os.path.exists(save_path)

    def test_light_theme(self):
        """测试亮色主题"""
        df = create_sample_data(50)

        chart = KLineChart(theme='light')
        chart.plot(df)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kline_light.png'))


class TestIndicatorChart:
    """指标图测试"""

    def test_init(self):
        """测试初始化"""
        chart = IndicatorChart(theme='dark')
        assert chart.theme['name'] == 'dark'

    def test_plot_macd(self):
        """测试绘制 MACD"""
        df = create_sample_data(50)

        chart = IndicatorChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_macd(df)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_macd.png'))

    def test_plot_rsi(self):
        """测试绘制 RSI"""
        df = create_sample_data(50)

        chart = IndicatorChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_rsi(df)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_rsi.png'))

    def test_plot_kdj(self):
        """测试绘制 KDJ"""
        df = create_sample_data(50)

        chart = IndicatorChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_kdj(df)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_kdj.png'))

    def test_plot_volume(self):
        """测试绘制成交量"""
        df = create_sample_data(50)

        chart = IndicatorChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_volume(df)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_volume.png'))

    def test_plot_multiple_indicators(self):
        """测试绘制多个指标"""
        df = create_sample_data(50)

        chart = IndicatorChart(theme='dark')
        chart.create_figure(nrows=3, height_ratios=[1, 1, 1])
        chart.plot_macd(df, ax_index=0)
        chart.plot_rsi(df, ax_index=1)
        chart.plot_volume(df, ax_index=2)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_indicators.png'))

    def test_plot_indicators_function(self):
        """测试快捷函数"""
        df = create_sample_data(50)

        save_path = os.path.join(tempfile.gettempdir(), 'test_plot_indicators.png')
        chart = plot_indicators(
            df,
            indicators=['macd', 'rsi', 'volume'],
            save_path=save_path
        )

        assert chart is not None
        assert os.path.exists(save_path)


class TestBacktestChart:
    """回测结果图测试"""

    def test_init(self):
        """测试初始化"""
        chart = BacktestChart(theme='dark')
        assert chart.theme['name'] == 'dark'

    def test_plot_equity_curve(self):
        """测试绘制资金曲线"""
        dates = pd.date_range('2024-01-01', periods=100, freq='B')
        equity = pd.Series(
            100000 * (1 + np.random.randn(100) * 0.01).cumprod(),
            index=dates
        )

        chart = BacktestChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_equity_curve(equity)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_equity.png'))

    def test_plot_drawdown(self):
        """测试绘制回撤"""
        dates = pd.date_range('2024-01-01', periods=100, freq='B')
        equity = pd.Series(
            100000 * (1 + np.random.randn(100) * 0.01).cumprod(),
            index=dates
        )

        chart = BacktestChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_drawdown(equity)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_drawdown.png'))

    def test_plot_trade_distribution(self):
        """测试绘制交易分布"""
        trades = [
            {'entry_price': 100, 'exit_price': 110},
            {'entry_price': 110, 'exit_price': 105},
            {'entry_price': 105, 'exit_price': 115},
            {'entry_price': 115, 'exit_price': 108},
            {'entry_price': 108, 'exit_price': 120},
        ]

        chart = BacktestChart(theme='dark')
        chart.create_figure(nrows=1)
        chart.plot_trade_distribution(trades)

        chart.save(os.path.join(tempfile.gettempdir(), 'test_trades.png'))

    def test_plot_summary(self):
        """测试绘制总结"""
        dates = pd.date_range('2024-01-01', periods=100, freq='B')
        equity = pd.Series(
            100000 * (1 + np.random.randn(100) * 0.01).cumprod(),
            index=dates
        )
        trades = [
            {'entry_price': 100, 'exit_price': 110},
            {'entry_price': 110, 'exit_price': 105},
        ]

        save_path = os.path.join(tempfile.gettempdir(), 'test_summary.png')
        chart = BacktestChart(theme='dark')
        chart.plot_summary(equity, trades=trades, save_path=save_path)

        assert os.path.exists(save_path)

    def test_plot_backtest_function(self):
        """测试快捷函数"""
        dates = pd.date_range('2024-01-01', periods=100, freq='B')
        equity = pd.Series(
            100000 * (1 + np.random.randn(100) * 0.01).cumprod(),
            index=dates
        )

        save_path = os.path.join(tempfile.gettempdir(), 'test_plot_backtest.png')
        chart = plot_backtest(equity, save_path=save_path)

        assert chart is not None
        assert os.path.exists(save_path)


class TestDashboard:
    """仪表盘测试"""

    def test_init(self):
        """测试初始化"""
        dashboard = Dashboard(theme='dark')
        assert dashboard.theme['name'] == 'dark'

    def test_create_stock_dashboard(self):
        """测试创建股票分析仪表盘"""
        df = create_sample_data(100)
        signals = create_sample_signals(df, 10)

        save_path = os.path.join(tempfile.gettempdir(), 'test_stock_dashboard.png')
        dashboard = Dashboard(theme='dark')
        dashboard.create_stock_dashboard(df, signals=signals)
        dashboard.save(save_path)

        assert os.path.exists(save_path)

    def test_create_backtest_dashboard(self):
        """测试创建回测结果仪表盘"""
        dates = pd.date_range('2024-01-01', periods=100, freq='B')
        equity = pd.Series(
            100000 * (1 + np.random.randn(100) * 0.01).cumprod(),
            index=dates
        )
        trades = [
            {'entry_price': 100, 'exit_price': 110},
            {'entry_price': 110, 'exit_price': 105},
            {'entry_price': 105, 'exit_price': 115},
        ]

        save_path = os.path.join(tempfile.gettempdir(), 'test_backtest_dashboard.png')
        dashboard = Dashboard(theme='dark')
        dashboard.create_backtest_dashboard(equity, trades=trades)
        dashboard.save(save_path)

        assert os.path.exists(save_path)

    def test_create_recommendation_dashboard(self):
        """测试创建推荐结果仪表盘"""
        recommendations = [
            {'code': '000001', 'name': '平安银行', 'price': 12.50,
             'change': 1.5, 'score': 85.0, 'recommendation': '买入'},
            {'code': '600036', 'name': '招商银行', 'price': 35.20,
             'change': -0.8, 'score': 78.0, 'recommendation': '买入'},
            {'code': '000858', 'name': '五粮液', 'price': 150.00,
             'change': 2.1, 'score': 72.0, 'recommendation': '持有'},
        ]

        save_path = os.path.join(tempfile.gettempdir(), 'test_recommend_dashboard.png')
        dashboard = Dashboard(theme='dark')
        dashboard.create_recommendation_dashboard(recommendations)
        dashboard.save(save_path)

        assert os.path.exists(save_path)

    def test_create_stock_dashboard_function(self):
        """测试快捷函数"""
        df = create_sample_data(100)

        save_path = os.path.join(tempfile.gettempdir(), 'test_dashboard_func.png')
        dashboard = create_stock_dashboard(df, title='Test Dashboard')
        dashboard.save(save_path)

        assert os.path.exists(save_path)


class TestIntegration:
    """集成测试"""

    def test_full_analysis_visualization(self):
        """测试完整分析可视化"""
        # 创建数据
        df = create_sample_data(200)
        signals = create_sample_signals(df, 20)

        # K 线图
        kline_path = os.path.join(tempfile.gettempdir(), 'integration_kline.png')
        plot_kline(df, ma_periods=[5, 10, 20], save_path=kline_path)

        # 指标图
        indicator_path = os.path.join(tempfile.gettempdir(), 'integration_indicators.png')
        plot_indicators(df, indicators=['macd', 'rsi', 'kdj'], save_path=indicator_path)

        # 回测图
        dates = df['date']
        equity = pd.Series(
            100000 * (1 + np.random.randn(len(df)) * 0.01).cumprod(),
            index=dates
        )
        backtest_path = os.path.join(tempfile.gettempdir(), 'integration_backtest.png')
        plot_backtest(equity, save_path=backtest_path)

        # 仪表盘
        dashboard_path = os.path.join(tempfile.gettempdir(), 'integration_dashboard.png')
        dashboard = create_stock_dashboard(df, signals=signals)
        dashboard.save(dashboard_path)

        # 验证所有文件
        for path in [kline_path, indicator_path, backtest_path, dashboard_path]:
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_theme_consistency(self):
        """测试主题一致性"""
        df = create_sample_data(50)

        for theme_name in ['dark', 'light']:
            # K 线图
            chart = KLineChart(theme=theme_name)
            chart.plot(df)
            chart.save(os.path.join(tempfile.gettempdir(), f'theme_{theme_name}_kline.png'))

            # 指标图
            chart = IndicatorChart(theme=theme_name)
            chart.create_figure(nrows=1)
            chart.plot_macd(df)
            chart.save(os.path.join(tempfile.gettempdir(), f'theme_{theme_name}_macd.png'))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
