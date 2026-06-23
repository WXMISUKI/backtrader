#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史行情多源路由测试。
"""

from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data.history_router import route_stock_history
from core.data.eastmoney_cookie_tools import format_cookie_string, parse_cookie_blob


def _build_history_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [10.0, 10.2],
            "high": [10.5, 10.6],
            "low": [9.8, 10.0],
            "close": [10.3, 10.4],
            "volume": [1000, 1200],
            "amount": [10300, 12480],
        },
        index=pd.to_datetime(["2026-06-01", "2026-06-02"]),
    )


def test_route_stock_history_falls_back_to_akshare(monkeypatch):
    def _eastmoney_fail(*args, **kwargs):
        raise ConnectionError("RemoteDisconnected('Remote end closed connection without response')")

    monkeypatch.setattr("core.data.history_router.fetch_eastmoney_history_dataframe", _eastmoney_fail)
    monkeypatch.setattr("core.data.history_router.fetch_akshare_history_dataframe", lambda **kwargs: _build_history_df())

    result = route_stock_history(symbol="000001", start_date="20260601", end_date="20260614")

    meta = result["meta"]
    assert result["data_source"] == "real"
    assert meta["selected_provider"] == "akshare_hist"
    assert len(meta["provider_attempts"]) == 2
    assert meta["provider_attempts"][0]["provider"] == "eastmoney_direct"
    assert meta["provider_attempts"][0]["status"] == "failed"
    assert meta["provider_attempts"][1]["provider"] == "akshare_hist"
    assert meta["provider_attempts"][1]["status"] == "success"


def test_route_stock_history_uses_offline_mock_after_all_failures(monkeypatch):
    def _fail(*args, **kwargs):
        raise ConnectionError("RemoteDisconnected('Remote end closed connection without response')")

    monkeypatch.setattr("core.data.history_router.fetch_eastmoney_history_dataframe", _fail)
    monkeypatch.setattr("core.data.history_router.fetch_akshare_history_dataframe", _fail)

    result = route_stock_history(symbol="000001", start_date="20260601", end_date="20260614")

    meta = result["meta"]
    assert result["data_source"] == "mock"
    assert meta["selected_provider"] == "offline_mock"
    assert meta["failure_kind"] == "request"
    assert meta["failure_stage"] == "request"
    assert meta["failure_code"] == "remote_disconnected"
    assert meta["fallback_strategy"] == "offline_history_snapshot"
    assert len(meta["provider_attempts"]) == 2


def test_cookie_blob_parser_round_trip():
    blob = "A=1; B=2\nC\t3"
    parsed = parse_cookie_blob(blob)
    assert parsed == {"A": "1", "B": "2", "C": "3"}
    assert format_cookie_string(parsed) == "A=1; B=2; C=3"
