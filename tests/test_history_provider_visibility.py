#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史行情 provider 可见性测试。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples import daily_watchlist_pipeline as pipeline


class _FakeProvider:
    def get_financial_indicators_governed(self, stock_code: str) -> dict:
        return {
            "data_source": "real",
            "is_degraded": False,
            "quality": {"ok": True, "reason": "ok"},
            "reason": "ok",
            "payload": {"report_date": "2026-06-30"},
        }


def test_build_history_summary_keeps_provider_fields(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "fetch_stock_hist_governed",
        lambda **kwargs: {
            "data_source": "real",
            "quality": {"ok": True, "rows": 2, "reason": "ok"},
            "reason": "ok",
            "selected_provider": "akshare_hist",
            "provider_attempts": [
                {"provider": "eastmoney_direct", "status": "failed"},
                {"provider": "akshare_hist", "status": "success"},
            ],
            "history_selected_provider": "akshare_hist",
            "history_provider_attempts": [
                {"provider": "eastmoney_direct", "status": "failed"},
                {"provider": "akshare_hist", "status": "success"},
            ],
            "history_provider_summary": "历史 provider akshare_hist；尝试 2 次",
            "meta": {
                "selected_provider": "akshare_hist",
                "provider_attempts": [
                    {"provider": "eastmoney_direct", "status": "failed"},
                    {"provider": "akshare_hist", "status": "success"},
                ],
                "failure_kind": "",
                "failure_stage": "",
                "failure_code": "",
                "fallback_strategy": "",
                "fallback_reason": "",
            },
        },
    )
    monkeypatch.setattr(pipeline, "RealDataProvider", lambda: _FakeProvider())

    summary = pipeline._build_history_summary(
        raw={"start_date": "20260601", "end_date": "20260614"},
        stock_code="000001",
        stock_name="平安银行",
    )

    assert summary["history_selected_provider"] == "akshare_hist"
    assert len(summary["history_provider_attempts"]) == 2
    assert summary["history_provider_summary"] == "历史 provider akshare_hist；尝试 2 次"
    assert summary["summary"].startswith("平安银行 数据健康状态为完全可用")
