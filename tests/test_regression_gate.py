from __future__ import annotations

from pathlib import Path

from examples.daily_watchlist_regression_gate import _classify_gate_status, _normalize_step_status
from examples.watchlist_shared import build_regression_gate


def test_normalize_step_status_maps_success_warn_block() -> None:
    assert _normalize_step_status(0, {"status": "ok"}) == "pass"
    assert _normalize_step_status(0, {"status": "degraded"}) == "warn"
    assert _normalize_step_status(1, {"status": "ok"}) == "block"


def test_classify_gate_status_prioritises_block_over_warn() -> None:
    assert _classify_gate_status(["pass", "warn", "pass"]) == "warn"
    assert _classify_gate_status(["pass", "block", "warn"]) == "block"
    assert _classify_gate_status(["pass", "pass"]) == "pass"


def test_build_regression_gate_defaults_to_readable_summary() -> None:
    gate = build_regression_gate(
        daily_run_status="degraded",
        acceptance={"status": "warn", "summary": "验收有部分缺口。"},
        baseline={"status": "caution", "summary_text": "基线可用。"},
        regression_gate={
            "status": "warn",
            "summary_text": "自动回归门禁告警。",
            "next_step": "先复核 warn 步骤。",
            "step_records": [{"name": "daily_run", "status": "warn"}],
            "blocked_steps": [],
            "warning_steps": ["daily_run"],
            "skipped_steps": [],
        },
    )

    assert gate["status"] == "warn"
    assert "自动回归门禁告警" in gate["summary_text"]
    assert "daily_run" in gate["read_order"]
    assert gate["evidence"]["regression_gate"]["warning_steps"] == ["daily_run"]
