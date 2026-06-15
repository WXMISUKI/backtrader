#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富 API 数据获取模块

封装东方财富 API，提供股票数据获取功能
"""

import requests
import pandas as pd
import numpy as np
from typing import Optional

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
