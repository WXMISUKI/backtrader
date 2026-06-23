#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富 API 数据获取模块

封装东方财富 API，提供股票数据获取功能。
同时提供治理后的统一入口，便于上层读取 data_source / quality / reason。
"""

import pandas as pd
from typing import Optional, Tuple, Any, Dict

# 导入配置
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from eastmoney_config import (
    EASTMONEY_COOKIES,
    EASTMONEY_HEADERS,
    EASTMONEY_API_BASE,
    get_eastmoney_session,
)
from .governance import build_snapshot, DataQualityChecker
from .history_diagnostics import build_offline_history_snapshot, classify_stock_hist_failure
from .history_router import fetch_eastmoney_history_dataframe, route_stock_history


def get_stock_hist(
    symbol: str = "000001",
    start_date: str = "20260601",
    end_date: str = "20260614",
    period: str = "daily",
    adjust: str = "qfq"
) -> pd.DataFrame:
    """
    获取股票历史数据

    参数:
        symbol: 股票代码，如 "000001"
        start_date: 开始日期，格式 "YYYYMMDD"
        end_date: 结束日期，格式 "YYYYMMDD"
        period: 周期，daily/weekly/monthly
        adjust: 复权方式，qfq(前复权)/hfq(后复权)/空(不复权)

    返回:
        pd.DataFrame: OHLCV 数据
    """
    return fetch_eastmoney_history_dataframe(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        period=period,
        adjust=adjust,
    )


def fetch_stock_hist_governed(
    symbol: str = "000001",
    start_date: str = "20260601",
    end_date: str = "20260614",
    period: str = "daily",
    adjust: str = "qfq",
) -> dict:
    """
    获取治理后的行情快照。

    返回值保留原始行情数据，同时补充质量、降级和来源信息。
    """
    return route_stock_history(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        period=period,
        adjust=adjust,
    )


def _build_fallback_stock_hist(stock_code: str, end_date: str = "20260614") -> pd.DataFrame:
    """
    构建离线模拟 OHLCV 数据。

    该数据仅用于降级演示与工具链验证，不应被视为真实行情。
    """
    seed = int(stock_code) % 10000
    rng = np.random.default_rng(seed)
    dates = pd.date_range(
        end=pd.to_datetime(end_date),
        periods=120,
        freq="B",
    )

    base_price = 10 + (seed % 500) / 10
    trend = np.linspace(0, rng.normal(8, 2), len(dates))
    noise = rng.normal(0, 0.6, len(dates)).cumsum()
    close = np.maximum(1, base_price + trend + noise)
    open_ = close + rng.normal(0, 0.25, len(dates))
    high = np.maximum(open_, close) + np.abs(rng.normal(0.4, 0.15, len(dates)))
    low = np.minimum(open_, close) - np.abs(rng.normal(0.4, 0.15, len(dates)))
    volume = rng.integers(1_000_000, 10_000_000, len(dates))

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("东方财富 API 测试")
    print("=" * 60)

    print("\n获取平安银行(000001)数据...")
    try:
        df = get_stock_hist("000001", "20260601", "20260614")
        print(f"获取到 {len(df)} 条数据")
        print(f"\n最近5条数据:")
        print(df.tail())
    except Exception as e:
        print(f"获取失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
