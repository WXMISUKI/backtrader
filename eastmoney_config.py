#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富 API 配置文件
使用前需要先从浏览器获取 Cookie
"""

from __future__ import annotations

import os
import requests
from pathlib import Path

_DEFAULT_EASTMONEY_COOKIES = {
    "wsc_checkuser_ok": "1",
    "websitepoptg_api_time": "1781405857968",
    "st_sp": "2026-06-14%2010%3A57%3A37",
    "st_sn": "10",
    "st_si": "64558801295943",
    "st_pvi": "02774739984287",
    "st_psi": "20260615152629628-113200301201-7078485547",
    "st_nvi": "V2uP-nftxkKSY2zjRviHree55",
    "st_inirUrl": "https%3A%2F%2Fcn.bing.com%2F",
    "st_asi": "delete",
    "qgqp_b_id": "fcb22465cffb74af28274518f6a09319",
    "nid18_create_time": "1781405858445",
    "nid18": "0cca8a925df2af21e27d1da02e0fc350",
    "gviem_create_time": "1781405858445",
    "gviem": "MzDbV1b6rfOeDd8K8AkLP9b6e",
    "JSESSIONID": "8B78078AF69B86B3F97251681B658604"
}


def _parse_cookie_string(cookie_str: str) -> dict:
    """解析浏览器导出的 Cookie 字符串。"""
    cookies = {}
    for chunk in cookie_str.split(";"):
        part = chunk.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def _load_env_file() -> dict:
    """读取本地 .env 中的简单 KEY=VALUE 配置。"""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return {}

    result: dict[str, str] = {}
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and value and key not in result:
                result[key] = value
    except Exception:
        return {}
    return result


def _load_cookies() -> dict:
    """加载 cookie，优先使用环境变量 EASTMONEY_COOKIE。"""
    cookie_str = os.getenv("EASTMONEY_COOKIE", "").strip()
    if cookie_str:
        parsed = _parse_cookie_string(cookie_str)
        if parsed:
            return parsed

    env_file = _load_env_file()
    cookie_str = env_file.get("EASTMONEY_COOKIE", "").strip()
    if cookie_str:
        parsed = _parse_cookie_string(cookie_str)
        if parsed:
            return parsed

    return _DEFAULT_EASTMONEY_COOKIES.copy()


def get_eastmoney_cookie_source() -> str:
    """返回当前 cookie 的来源。"""
    cookie_str = os.getenv("EASTMONEY_COOKIE", "").strip()
    if cookie_str:
        return "env"

    env_file = _load_env_file()
    cookie_str = env_file.get("EASTMONEY_COOKIE", "").strip()
    if cookie_str:
        return "env_file"

    return "default"


def get_eastmoney_cookie_meta() -> dict:
    """返回 cookie 的轻量诊断信息。"""
    cookies = EASTMONEY_COOKIES
    return {
        "cookie_loaded": bool(cookies),
        "cookie_source": get_eastmoney_cookie_source(),
        "cookie_keys": list(cookies.keys())[:20],
        "has_jsessionid": "JSESSIONID" in cookies and bool(cookies.get("JSESSIONID")),
        "has_ut": "ut" in cookies and bool(cookies.get("ut")),
    }


def get_eastmoney_session() -> requests.Session:
    """创建一个不依赖系统代理的 requests Session。"""
    session = requests.Session()
    session.trust_env = False
    return session


# 东方财富 Cookie（需要定期更新）
EASTMONEY_COOKIES = _load_cookies()

# 请求头
EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json, text/plain, */*"
}

# API 基础地址
EASTMONEY_API_BASE = "https://push2his.eastmoney.com"


def get_stock_hist(symbol="000001", start_date="20260601", end_date="20260614", period="daily", adjust="qfq"):
    """
    获取股票历史数据

    参数:
        symbol: 股票代码，如 "000001"
        start_date: 开始日期，格式 "YYYYMMDD"
        end_date: 结束日期，格式 "YYYYMMDD"
        period: 周期，daily/weekly/monthly
        adjust: 复权方式，qfq(前复权)/hfq(后复权)/空(不复权)

    返回:
        pandas DataFrame
    """
    import requests
    import pandas as pd

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


def get_realtime_quotes(page=1, page_size=10):
    """
    获取A股实时行情

    参数:
        page: 页码
        page_size: 每页数量

    返回:
        pandas DataFrame
    """
    import requests
    import pandas as pd

    url = "https://82.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": str(page),
        "pz": str(page_size),
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f12,f14"
    }

    session = get_eastmoney_session()
    r = session.get(url, params=params, cookies=EASTMONEY_COOKIES,
                    headers=EASTMONEY_HEADERS, timeout=30)

    if r.status_code != 200:
        raise Exception(f"请求失败: {r.status_code}")

    data = r.json()
    if "data" not in data or not data["data"] or "diff" not in data["data"]:
        raise Exception("返回数据格式异常")

    stocks = data["data"]["diff"]
    df = pd.DataFrame(stocks)
    df = df.rename(columns={
        "f12": "code",
        "f14": "name",
        "f2": "price",
        "f3": "change_pct",
        "f4": "change",
        "f5": "volume",
        "f6": "amount"
    })

    return df


if __name__ == "__main__":
    # 测试
    print("测试东方财富 API...")
    print("\n获取平安银行历史数据:")
    df = get_stock_hist("000001", "20260601", "20260614")
    print(df.tail())

    print("\n获取实时行情:")
    df_spot = get_realtime_quotes(page_size=5)
    print(df_spot)
