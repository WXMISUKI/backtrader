#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史行情诊断与离线兜底辅助函数。
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


def normalize_failure_code(text: str) -> str:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return "unknown_failure"

    if "remote end closed connection" in lowered or "remote disconnected" in lowered:
        return "remote_disconnected"
    if "connection aborted" in lowered:
        return "connection_aborted"
    if "connection reset" in lowered:
        return "connection_reset"
    if "read timed out" in lowered or "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    if "json" in lowered or "decode" in lowered:
        return "json_decode"
    if "返回数据格式异常" in text or "response format" in lowered:
        return "response_format"
    if "missing columns" in lowered:
        return "missing_columns"
    if "dataframe is empty" in lowered or "empty payload" in lowered:
        return "empty_payload"
    if "dataframe is none" in lowered:
        return "payload_none"
    if "http_status=" in lowered:
        match = re.search(r"http_status=(\d+)", lowered)
        if match:
            return f"http_{match.group(1)}"
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", lowered).strip("_")
    return normalized or "unknown_failure"


def classify_stock_hist_failure(
    *,
    exc: Exception | str | None = None,
    quality_reason: str = "",
    status_code: int | None = None,
) -> dict[str, str]:
    """把历史行情失败收束成稳定的分层语义。"""
    exc_text = str(exc or "").strip()
    quality_text = str(quality_reason or "").strip()
    combined_text = quality_text or exc_text
    lowered = combined_text.lower()

    failure_stage = "unknown"
    failure_kind = "unknown"
    failure_code = "unknown_failure"
    fallback_strategy = "offline_history_snapshot"

    if quality_text:
        failure_stage = "quality"
        failure_kind = "quality"
        failure_code = normalize_failure_code(quality_text)
    elif status_code is not None and status_code >= 400:
        failure_stage = "request"
        failure_kind = "request"
        failure_code = f"http_{status_code}"
    elif "返回数据格式异常" in combined_text or "json" in lowered or "decode" in lowered:
        failure_stage = "response"
        failure_kind = "response"
        failure_code = normalize_failure_code(combined_text)
    elif any(
        token in lowered
        for token in (
            "remote end closed connection",
            "remote disconnected",
            "connection aborted",
            "connection reset",
            "timeout",
            "timed out",
            "read timed out",
        )
    ):
        failure_stage = "request"
        failure_kind = "request"
        failure_code = normalize_failure_code(combined_text)
    elif combined_text:
        failure_stage = "request"
        failure_kind = "request"
        failure_code = normalize_failure_code(combined_text)

    return {
        "failure_kind": failure_kind,
        "failure_stage": failure_stage,
        "failure_code": failure_code,
        "fallback_strategy": fallback_strategy,
    }


def build_offline_history_snapshot(stock_code: str, end_date: str = "20260614") -> pd.DataFrame:
    """构建离线模拟 OHLCV 数据。"""
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
