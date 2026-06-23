#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史行情多源路由。
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

import pandas as pd
import requests

from .governance import DataQualityChecker, build_snapshot
from .history_diagnostics import build_offline_history_snapshot, classify_stock_hist_failure

try:
    import akshare as ak

    HAS_AKSHARE = True
except ImportError:
    ak = None  # type: ignore[assignment]
    HAS_AKSHARE = False

from eastmoney_config import (
    EASTMONEY_API_BASE,
    EASTMONEY_COOKIES,
    EASTMONEY_HEADERS,
    get_eastmoney_session,
)


def _map_period(period: str) -> str:
    return {
        "daily": "101",
        "weekly": "102",
        "monthly": "103",
    }.get(period, "101")


def _map_adjust(adjust: str) -> str:
    return {
        "qfq": "1",
        "hfq": "2",
        "": "0",
    }.get(adjust, "1")


def _symbol_market(symbol: str) -> str:
    return "0" if symbol.startswith("0") or symbol.startswith("3") else "1"


def fetch_eastmoney_history_dataframe(
    *,
    symbol: str = "000001",
    start_date: str = "20260601",
    end_date: str = "20260614",
    period: str = "daily",
    adjust: str = "qfq",
) -> pd.DataFrame:
    """直接从东方财富获取历史行情。"""
    url = f"{EASTMONEY_API_BASE}/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": _map_period(period),
        "fqt": _map_adjust(adjust),
        "secid": f"{_symbol_market(symbol)}.{symbol}",
        "beg": start_date,
        "end": end_date,
    }

    session = get_eastmoney_session()
    r = session.get(url, params=params, cookies=EASTMONEY_COOKIES, headers=EASTMONEY_HEADERS, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(f"http_status={r.status_code}")

    data = r.json()
    if "data" not in data or not data["data"] or "klines" not in data["data"]:
        raise RuntimeError("返回数据格式异常")

    records = []
    for line in data["data"]["klines"]:
        parts = line.split(",")
        records.append(
            {
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": float(parts[5]),
                "amount": float(parts[6]),
            }
        )

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df


def fetch_akshare_history_dataframe(
    *,
    symbol: str = "000001",
    start_date: str = "20260601",
    end_date: str = "20260614",
    period: str = "daily",
    adjust: str = "qfq",
) -> pd.DataFrame:
    """使用 AKShare 获取历史行情并标准化列名。"""
    if not HAS_AKSHARE:
        raise ImportError("akshare is not available in current environment")

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    if df is None or len(df) == 0:
        raise RuntimeError("akshare returned empty dataframe")

    rename_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
    }
    normalized = df.rename(columns=rename_map).copy()
    if "date" in normalized.columns:
        normalized["date"] = pd.to_datetime(normalized["date"])
        normalized.set_index("date", inplace=True)

    required = ["open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in normalized.columns]
    if missing:
        raise RuntimeError(f"missing columns: {missing}")

    for column in required + ["amount"]:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    return normalized


ProviderFetcher = Callable[..., pd.DataFrame]


def route_stock_history(
    *,
    symbol: str = "000001",
    start_date: str = "20260601",
    end_date: str = "20260614",
    period: str = "daily",
    adjust: str = "qfq",
    provider_order: list[str] | None = None,
) -> dict[str, Any]:
    """按 provider 顺序尝试获取历史行情，并返回治理快照。"""
    checker = DataQualityChecker()
    attempts: list[dict[str, Any]] = []
    providers: list[tuple[str, ProviderFetcher]] = []

    order = provider_order or ["eastmoney_direct", "akshare_hist"]
    for provider_name in order:
        if provider_name == "eastmoney_direct":
            providers.append((provider_name, fetch_eastmoney_history_dataframe))
        elif provider_name == "akshare_hist":
            providers.append((provider_name, fetch_akshare_history_dataframe))
        elif provider_name == "offline_mock":
            providers.append(
                (
                    provider_name,
                    lambda **kwargs: build_offline_history_snapshot(
                        kwargs["symbol"], end_date=kwargs["end_date"]
                    ),
                )
            )

    if not providers:
        providers = [
            (
                "offline_mock",
                lambda **kwargs: build_offline_history_snapshot(kwargs["symbol"], end_date=kwargs["end_date"]),
            )
        ]

    last_failure: dict[str, str] = classify_stock_hist_failure(exc="no provider available")
    last_error_text = "no provider available"

    for provider_name, fetcher in providers:
        started_at = perf_counter()
        try:
            df = fetcher(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust,
            )
            latency_ms = int((perf_counter() - started_at) * 1000)
            quality = checker.check_ohlcv_dataframe(df)
            if not quality.get("ok"):
                failure_meta = classify_stock_hist_failure(quality_reason=quality.get("reason", ""))
                attempts.append(
                    {
                        "provider": provider_name,
                        "status": "failed",
                        "reason": quality.get("reason", ""),
                        "failure_stage": failure_meta["failure_stage"],
                        "failure_kind": failure_meta["failure_kind"],
                        "failure_code": failure_meta["failure_code"],
                        "latency_ms": latency_ms,
                    }
                )
                last_failure = failure_meta
                last_error_text = quality.get("reason", "quality check failed")
                continue

            snapshot = build_snapshot(
                name=f"stock_hist:{symbol}",
                payload=df,
                source="real" if provider_name != "offline_mock" else "mock",
                degraded=provider_name == "offline_mock",
                reason="ok",
            )
            snapshot.data_source = "real" if provider_name != "offline_mock" else "mock"
            snapshot.quality = quality
            snapshot.meta.update(
                {
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "period": period,
                    "adjust": adjust,
                    "selected_provider": provider_name,
                    "provider_attempts": attempts
                    + [
                        {
                            "provider": provider_name,
                            "status": "success",
                            "reason": "ok",
                            "latency_ms": latency_ms,
                            "rows": int(len(df)),
                        }
                    ],
                    "fallback_strategy": "" if provider_name != "offline_mock" else "offline_history_snapshot",
                    "fallback_reason": "",
                    "failure_kind": "",
                    "failure_stage": "",
                    "failure_code": "",
                }
            )
            return snapshot.to_dict()
        except Exception as exc:
            latency_ms = int((perf_counter() - started_at) * 1000)
            failure_meta = classify_stock_hist_failure(exc=exc)
            attempts.append(
                {
                    "provider": provider_name,
                    "status": "failed",
                    "reason": str(exc),
                    "failure_stage": failure_meta["failure_stage"],
                    "failure_kind": failure_meta["failure_kind"],
                    "failure_code": failure_meta["failure_code"],
                    "latency_ms": latency_ms,
                }
            )
            last_failure = failure_meta
            last_error_text = str(exc)

    df = build_offline_history_snapshot(symbol, end_date=end_date)
    quality = checker.check_ohlcv_dataframe(df)
    snapshot = build_snapshot(
        name=f"stock_hist:{symbol}",
        payload=df,
        source="mock",
        degraded=True,
        reason=last_error_text,
    )
    snapshot.data_source = "mock"
    snapshot.quality = quality
    snapshot.meta.update(
        {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "period": period,
            "adjust": adjust,
            "selected_provider": "offline_mock",
            "provider_attempts": attempts,
            "fallback_strategy": last_failure.get("fallback_strategy", "offline_history_snapshot"),
            "fallback_reason": last_error_text,
            "failure_kind": last_failure.get("failure_kind", "request"),
            "failure_stage": last_failure.get("failure_stage", "request"),
            "failure_code": last_failure.get("failure_code", "unknown_failure"),
        }
    )
    return snapshot.to_dict()
