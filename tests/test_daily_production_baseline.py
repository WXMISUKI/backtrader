from __future__ import annotations

from pathlib import Path
import json

from examples.daily_watchlist_production_baseline import _derive_status, _load_json_payload


def test_derive_status_ready() -> None:
    checks = {
        "run_status": True,
        "pipeline_json": True,
        "latest_json": True,
        "latest_md": True,
        "acceptance_json": True,
        "production_gate": True,
        "daily_execution_brief": True,
        "review_brief": True,
        "schedule_hint": True,
        "feedback_effect_brief": True,
        "history_provider_visible": True,
    }
    assert _derive_status(checks) == "ready"


def test_derive_status_failed() -> None:
    checks = {
        "run_status": True,
        "pipeline_json": False,
        "latest_json": True,
        "latest_md": True,
        "acceptance_json": True,
        "production_gate": True,
        "daily_execution_brief": True,
        "review_brief": True,
        "schedule_hint": True,
        "feedback_effect_brief": True,
        "history_provider_visible": True,
    }
    assert _derive_status(checks) == "failed"


def test_load_json_payload_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    assert _load_json_payload(path) == {}

    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"ok": True}, ensure_ascii=False), encoding="utf-8")
    assert _load_json_payload(payload_path) == {"ok": True}
