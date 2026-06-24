from __future__ import annotations

from pathlib import Path
import json

from examples.daily_watchlist_production_baseline import (
    _build_baseline_observation,
    _build_recent_run_record,
    _derive_failure_class,
    _derive_failure_stage,
    _derive_status,
    _load_history_entries,
    _load_json_payload,
)


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


def test_failure_class_and_repair_hint() -> None:
    from examples.daily_watchlist_production_baseline import _build_repair_hint, _derive_failure_class, _derive_failure_stage

    checks = {
        "run_status": True,
        "pipeline_json": True,
        "latest_json": True,
        "latest_md": True,
        "acceptance_json": True,
        "production_gate": False,
        "daily_execution_brief": True,
        "review_brief": True,
        "schedule_hint": True,
        "feedback_effect_brief": True,
        "history_provider_visible": True,
    }
    failed_stage = _derive_failure_stage(checks)
    failure_class = _derive_failure_class(checks, "failed", failed_stage)
    assert failed_stage == "production_gate"
    assert failure_class == "gate_missing"
    assert "production_gate" in _build_repair_hint(failure_class, failed_stage)


def test_load_json_payload_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    assert _load_json_payload(path) == {}

    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"ok": True}, ensure_ascii=False), encoding="utf-8")
    assert _load_json_payload(payload_path) == {"ok": True}


def test_baseline_observation_counts_and_visibility(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    history_path.write_text(
        json.dumps(
            [
                {
                    "status": "failed",
                    "failed_stage": "pipeline",
                    "failure_class": "execution_missing",
                    "missing_required_checks": ["pipeline_json"],
                    "missing_optional_checks": [],
                    "history_provider_visible": False,
                },
                {
                    "status": "caution",
                    "failed_stage": "none",
                    "failure_class": "partial_artifacts",
                    "missing_required_checks": [],
                    "missing_optional_checks": ["schedule_hint"],
                    "history_provider_visible": True,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entries = _load_history_entries(history_path)
    current = {
        "status": "failed",
        "failed_stage": "production_gate",
        "failure_class": "gate_missing",
        "missing_required_checks": ["production_gate"],
        "missing_optional_checks": ["review_brief"],
        "history_provider_visible": True,
    }
    observation = _build_baseline_observation(
        history_entries=entries,
        current_record=current,
        history_path=history_path,
        limit=5,
    )

    assert observation["failure_class_counts"]["execution_missing"] == 1
    assert observation["failure_class_counts"]["partial_artifacts"] == 1
    assert observation["failure_class_counts"]["gate_missing"] == 1
    assert "production_gate" in observation["top_missing_checks"]
    assert observation["provider_visibility_rate"] == 0.6667
    assert observation["history_path"] == str(history_path)


def test_recent_run_record_tracks_missing_checks() -> None:
    checks = {
        "run_status": True,
        "pipeline_json": True,
        "latest_json": True,
        "latest_md": False,
        "acceptance_json": True,
        "production_gate": True,
        "daily_execution_brief": True,
        "review_brief": True,
        "schedule_hint": False,
        "feedback_effect_brief": True,
        "history_provider_visible": False,
    }
    record = _build_recent_run_record(
        status="caution",
        failed_stage="none",
        failure_class="partial_artifacts",
        checks=checks,
    )

    assert record["status"] == "caution"
    assert "schedule_hint" in record["missing_optional_checks"]
    assert "latest_md" in record["missing_optional_checks"]
    assert record["history_provider_visible"] is False


def test_failure_classification_helpers_still_align() -> None:
    checks = {
        "run_status": True,
        "pipeline_json": True,
        "latest_json": True,
        "latest_md": True,
        "acceptance_json": True,
        "production_gate": False,
        "daily_execution_brief": True,
        "review_brief": True,
        "schedule_hint": True,
        "feedback_effect_brief": True,
        "history_provider_visible": True,
    }
    failed_stage = _derive_failure_stage(checks)
    failure_class = _derive_failure_class(checks, "failed", failed_stage)

    assert failed_stage == "production_gate"
    assert failure_class == "gate_missing"
    assert _derive_status(checks) == "failed"
