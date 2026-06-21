#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富 API 数据获取模块

封装东方财富 API，提供股票数据获取功能。
同时提供治理后的统一入口，便于上层读取 data_source / quality / reason。
"""

import requests
import pandas as pd
import numpy as np
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
    # 周期映射
    period_map = {
        "daily": "101",
        "weekly": "102",
        "monthly": "103"
    }

    # 复权映射
    adjust_map = {
        "qfq": "1",
        "hfq": "2",
        "": "0"
    }

    # 市场代码
    market = "0" if symbol.startswith("0") or symbol.startswith("3") else "1"

    url = f"{EASTMONEY_API_BASE}/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": period_map.get(period, "101"),
        "fqt": adjust_map.get(adjust, "1"),
        "secid": f"{market}.{symbol}",
        "beg": start_date,
        "end": end_date
    }

    session = get_eastmoney_session()
    r = session.get(url, params=params, cookies=EASTMONEY_COOKIES,
                    headers=EASTMONEY_HEADERS, timeout=30)

    if r.status_code != 200:
        raise Exception(f"请求失败: {r.status_code}")

    data = r.json()
    if "data" not in data or not data["data"] or "klines" not in data["data"]:
        raise Exception("返回数据格式异常")

    klines = data["data"]["klines"]
    records = []
    for line in klines:
        parts = line.split(",")
        records.append({
            "date": parts[0],
            "open": float(parts[1]),
            "close": float(parts[2]),
            "high": float(parts[3]),
            "low": float(parts[4]),
            "volume": float(parts[5]),
            "amount": float(parts[6])
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    return df


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
    checker = DataQualityChecker()
    data_source = "real"
    reason = "ok"
    failure_kind = ""

    try:
        df = get_stock_hist(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            adjust=adjust,
        )
        quality = checker.check_ohlcv_dataframe(df)
        if not quality.get("ok"):
            failure_kind = "quality"
            raise ValueError(quality.get("reason", "quality check failed"))
    except Exception as exc:
        df = _build_fallback_stock_hist(symbol, end_date=end_date)
        data_source = "mock"
        reason = str(exc)
        if not failure_kind:
            reason_text = str(exc).lower()
            if "remote end closed connection" in reason_text or "connection aborted" in reason_text:
                failure_kind = "request"
            elif "返回数据格式异常" in str(exc) or "json" in reason_text:
                failure_kind = "response"
            else:
                failure_kind = "request"
        quality = checker.check_ohlcv_dataframe(df)

    snapshot = build_snapshot(
        name=f"stock_hist:{symbol}",
        payload=df,
        source=data_source,
        degraded=data_source != "real",
        reason=reason,
    )
    snapshot.quality = quality
    snapshot.data_source = data_source
    snapshot.meta.update(
        {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "period": period,
            "adjust": adjust,
            "failure_kind": failure_kind,
            "fallback_reason": reason if data_source != "real" else "",
        }
    )
    return snapshot.to_dict()


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
