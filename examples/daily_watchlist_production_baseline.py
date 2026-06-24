#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常投产实跑基线。

用法：
    python examples/daily_watchlist_production_baseline.py
    python examples/daily_watchlist_production_baseline.py --archive-dir logs/daily_watchlist_archive
    python examples/daily_watchlist_production_baseline.py --show-json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.watchlist_shared import build_feedback_effect_brief


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"
DEFAULT_FLOW_JSON = ROOT_DIR / "logs" / "daily_watchlist_flow.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"
DEFAULT_PIPELINE_JSON = ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"
DEFAULT_FEEDBACK_JSON = ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "logs" / "daily_watchlist_production_baseline.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily production baseline for watchlist workflow.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--run-status", default=str(DEFAULT_RUN_STATUS), help="Run status JSON path.")
    parser.add_argument("--flow-json", default=str(DEFAULT_FLOW_JSON), help="Flow JSON path.")
    parser.add_argument("--acceptance-json", default=str(DEFAULT_ACCEPTANCE_JSON), help="Acceptance JSON path.")
    parser.add_argument("--pipeline-json", default=str(DEFAULT_PIPELINE_JSON), help="Pipeline JSON path.")
    parser.add_argument("--feedback-json", default=str(DEFAULT_FEEDBACK_JSON), help="Feedback effects JSON path.")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="Baseline JSON output path.")
    parser.add_argument("--show-json", action="store_true", help="Print JSON payload.")
    return parser


def _load_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _exists_and_nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _derive_status(checks: dict[str, bool]) -> str:
    required_failed = [
        "run_status",
        "pipeline_json",
        "latest_json",
        "production_gate",
        "daily_execution_brief",
        "acceptance_json",
    ]
    if any(not checks.get(key, False) for key in required_failed):
        return "failed"
    if not all(checks.get(key, False) for key in checks):
        return "caution"
    return "ready"


def main() -> int:
    args = build_parser().parse_args()
    archive_dir = Path(args.archive_dir)
    run_status_path = Path(args.run_status)
    flow_path = Path(args.flow_json)
    acceptance_path = Path(args.acceptance_json)
    pipeline_path = Path(args.pipeline_json)
    feedback_path = Path(args.feedback_json)
    output_path = Path(args.output_json)

    run_status_payload = _load_json_payload(run_status_path)
    flow_payload = _load_json_payload(flow_path)
    acceptance_payload = _load_json_payload(acceptance_path)
    pipeline_payload = _load_json_payload(pipeline_path)
    feedback_payload = _load_json_payload(feedback_path)

    latest_json = archive_dir / "latest.json"
    latest_md = archive_dir / "latest.md"
    latest_payload = _load_json_payload(latest_json)
    if not latest_payload and isinstance(pipeline_payload, dict):
        latest_payload = pipeline_payload

    production_gate = latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {}
    daily_execution_brief = latest_payload.get("daily_execution_brief", {}) if isinstance(latest_payload, dict) else {}
    review_brief = latest_payload.get("review_brief", {}) if isinstance(latest_payload, dict) else {}
    schedule_hint = latest_payload.get("schedule_hint", {}) if isinstance(latest_payload, dict) else {}
    feedback_effect_brief = feedback_payload.get("feedback_effect_brief", {}) if isinstance(feedback_payload, dict) else {}
    if not isinstance(feedback_effect_brief, dict) or not feedback_effect_brief:
        feedback_effect_brief = build_feedback_effect_brief(feedback_effects=feedback_payload if isinstance(feedback_payload, dict) else {})

    checks = {
        "run_status": _exists_and_nonempty(run_status_path),
        "pipeline_json": _exists_and_nonempty(pipeline_path),
        "latest_json": _exists_and_nonempty(latest_json),
        "latest_md": _exists_and_nonempty(latest_md),
        "acceptance_json": _exists_and_nonempty(acceptance_path),
        "production_gate": bool(isinstance(production_gate, dict) and production_gate.get("status", "")),
        "daily_execution_brief": bool(isinstance(daily_execution_brief, dict) and daily_execution_brief.get("summary_text", "")),
        "review_brief": bool(isinstance(review_brief, dict) and review_brief.get("summary_text", "")),
        "schedule_hint": bool(isinstance(schedule_hint, dict) and schedule_hint.get("summary_text", "")),
        "feedback_effect_brief": bool(isinstance(feedback_effect_brief, dict) and feedback_effect_brief.get("summary_text", "")),
        "history_provider_visible": any(
            isinstance(item, dict) and bool(item.get("history_selected_provider"))
            for item in (latest_payload.get("health", {}).get("items", []) if isinstance(latest_payload, dict) else [])
        ),
    }
    status = _derive_status(checks)
    failed_stage = "none"
    if not checks["run_status"]:
        failed_stage = "run_status"
    elif not checks["pipeline_json"]:
        failed_stage = "pipeline"
    elif not checks["latest_json"]:
        failed_stage = "archive"
    elif not checks["acceptance_json"]:
        failed_stage = "acceptance"
    elif not checks["production_gate"]:
        failed_stage = "production_gate"
    elif not checks["daily_execution_brief"]:
        failed_stage = "daily_execution_brief"
    elif not checks["feedback_effect_brief"]:
        failed_stage = "feedback_effect_brief"
    elif not checks["history_provider_visible"]:
        failed_stage = "history_provider_visible"

    if status == "ready":
        summary_text = "日常投产基线通过，主链路可完整参考。"
        next_action = "继续按日常节奏运行，并保持现有门禁顺序。"
    elif status == "caution":
        summary_text = "日常投产基线可用，但存在部分非阻断缺口。"
        next_action = "先复核缺失入口，再决定是否继续参考。"
    else:
        summary_text = "日常投产基线失败，当前不建议直接参考。"
        next_action = "先修复失败阶段，再重新跑基线。"

    evidence = {
        "run_status": run_status_payload,
        "flow": flow_payload,
        "acceptance": acceptance_payload,
        "pipeline": pipeline_payload,
        "latest_payload": latest_payload,
        "production_gate": production_gate,
        "daily_execution_brief": daily_execution_brief,
        "review_brief": review_brief,
        "schedule_hint": schedule_hint,
        "feedback_effect_brief": feedback_effect_brief,
    }

    payload = {
        "status": status,
        "summary_text": summary_text,
        "failed_stage": failed_stage,
        "next_action": next_action,
        "checks": checks,
        "evidence": evidence,
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print("== 自选股日常投产基线 ==")
    print(f"状态: {status}")
    print(f"结论: {summary_text}")
    print(f"失败阶段: {failed_stage}")
    print(f"下一步: {next_action}")
    print(f"production_gate: {'存在' if checks['production_gate'] else '缺失'}")
    print(f"daily_execution_brief: {'存在' if checks['daily_execution_brief'] else '缺失'}")
    print(f"feedback_effect_brief: {'存在' if checks['feedback_effect_brief'] else '缺失'}")
    print(f"history_provider_visible: {'存在' if checks['history_provider_visible'] else '缺失'}")
    print(f"验收JSON: {'存在' if checks['acceptance_json'] else '缺失'}")
    print(f"输出JSON: {output_path}")

    if args.show_json:
        print("\n== baseline.json ==")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    return 0 if status in {"ready", "caution"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
