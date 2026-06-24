from __future__ import annotations

from pathlib import Path

from examples.daily_watchlist_regression_gate import _classify_gate_status, _normalize_step_status


def test_normalize_step_status_maps_success_warn_block() -> None:
    assert _normalize_step_status(0, {"status": "ok"}) == "pass"
    assert _normalize_step_status(0, {"status": "degraded"}) == "warn"
    assert _normalize_step_status(1, {"status": "ok"}) == "block"


def test_classify_gate_status_prioritises_block_over_warn() -> None:
    assert _classify_gate_status(["pass", "warn", "pass"]) == "warn"
    assert _classify_gate_status(["pass", "block", "warn"]) == "block"
    assert _classify_gate_status(["pass", "pass"]) == "pass"
