#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富历史行情数据源韧性回归测试。

目标：
- 远端断开时固定输出结构化失败语义
- 质量失败时也能落到统一回退策略
- 日常健康摘要可以消费新增加的失败元数据
"""

from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data.eastmoney_api import fetch_stock_hist_governed
from examples.watchlist_shared import build_data_health_summary


def test_fetch_stock_hist_governed_classifies_remote_disconnect(monkeypatch):
    def _raise_remote_disconnect(*args, **kwargs):
        raise ConnectionError("RemoteDisconnected('Remote end closed connection without response')")

    monkeypatch.setattr("core.data.eastmoney_api.get_stock_hist", _raise_remote_disconnect)

    result = fetch_stock_hist_governed(symbol="000001", start_date="20260601", end_date="20260614")

    meta = result["meta"]
    assert result["data_source"] == "mock"
    assert meta["failure_kind"] == "request"
    assert meta["failure_stage"] == "request"
    assert meta["failure_code"] == "remote_disconnected"
    assert meta["fallback_strategy"] == "offline_history_snapshot"
    assert meta["fallback_reason"]
    assert result["quality"]["ok"] is True


def test_fetch_stock_hist_governed_classifies_quality_failure(monkeypatch):
    df = pd.DataFrame(
        {
            "open": [10.1, 10.2],
            "high": [10.4, 10.5],
            "low": [9.9, 10.0],
            "close": [10.2, 10.3],
        }
    )

    monkeypatch.setattr("core.data.history_router.fetch_eastmoney_history_dataframe", lambda **kwargs: df)
    monkeypatch.setattr("core.data.history_router.fetch_akshare_history_dataframe", lambda **kwargs: df)

    result = fetch_stock_hist_governed(symbol="000001", start_date="20260601", end_date="20260614")

    meta = result["meta"]
    assert result["data_source"] == "mock"
    assert meta["failure_kind"] == "quality"
    assert meta["failure_stage"] == "quality"
    assert meta["failure_code"] == "missing_columns"
    assert meta["fallback_strategy"] == "offline_history_snapshot"
    assert "missing columns" in meta["fallback_reason"].lower()
    assert result["quality"]["ok"] is True


def test_build_data_health_summary_includes_history_failure_meta():
    history = {
        "data_source": "mock",
        "reason": "RemoteDisconnected('Remote end closed connection without response')",
        "quality": {"ok": True, "reason": "ok"},
        "failure_kind": "request",
        "failure_stage": "request",
        "failure_code": "remote_disconnected",
        "fallback_strategy": "offline_history_snapshot",
        "selected_provider": "offline_mock",
        "provider_attempts": [{"provider": "eastmoney_direct", "status": "failed"}],
        "is_degraded": True,
    }
    fundamental = {
        "data_source": "real",
        "reason": "ok",
        "quality": {"ok": True, "reason": "ok"},
        "is_degraded": False,
    }

    summary = build_data_health_summary(stock_name="平安银行", history=history, fundamental=fundamental)

    assert summary["history_failure_stage"] == "request"
    assert summary["history_failure_code"] == "remote_disconnected"
    assert summary["history_fallback_strategy"] == "offline_history_snapshot"
    assert summary["history_selected_provider"] == "offline_mock"
    assert "history_failure_code:remote_disconnected" in summary["normalized_reasons"]
    assert "历史失败=request/remote_disconnected/offline_history_snapshot" in summary["diagnosis"]["summary"]
