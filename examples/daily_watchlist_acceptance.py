#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常投产验收。

用法：
    python examples/daily_watchlist_acceptance.py
    python examples/daily_watchlist_acceptance.py --output-json logs/daily_watchlist_acceptance.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.watchlist_shared import build_daily_collaboration_pack, build_daily_execution_brief, build_daily_review_brief, build_diagnosis_evidence, build_feedback_effect_brief, build_schedule_hint


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_FEEDBACK_FILE = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist acceptance check.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--feedback-file", default=str(DEFAULT_FEEDBACK_FILE), help="Feedback JSONL file path.")
    parser.add_argument("--run-status", default=str(DEFAULT_RUN_STATUS), help="Run status JSON path.")
    parser.add_argument("--output-json", default=str(DEFAULT_ACCEPTANCE_JSON), help="Acceptance JSON output path.")
    return parser


def _exists(path: Path) -> bool:
    return path.exists()


def _load_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, dict) else {}


def _load_jsonl_payload(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    return records


def _run_script(script: Path, args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(script), *args]
    completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def _score(*, checks_ok: int, checks_total: int, entry_ok: bool) -> str:
    if checks_ok == checks_total and entry_ok:
        return "ok"
    if checks_ok > 0 and entry_ok:
        return "degraded"
    return "failed"


def main() -> int:
    args = build_parser().parse_args()
    archive_dir = Path(args.archive_dir)
    feedback_file = Path(args.feedback_file)
    run_status_path = Path(args.run_status)
    acceptance_path = Path(args.output_json)

    latest_json = archive_dir / "latest.json"
    latest_md = archive_dir / "latest.md"
    viewer_script = ROOT_DIR / "examples" / "daily_watchlist_review.py"
    insights_script = ROOT_DIR / "examples" / "daily_watchlist_feedback_insights.py"
    latest_payload = _load_json_payload(latest_json)
    if not latest_payload:
        latest_payload = _load_json_payload(Path(args.run_status))
    daily_summary = latest_payload.get("daily_summary", {}) if isinstance(latest_payload, dict) else {}
    diagnosis_counts = daily_summary.get("diagnosis_counts", {}) if isinstance(daily_summary, dict) else {}
    confidence_ok = (
        isinstance(daily_summary, dict)
        and "confidence_counts" in daily_summary
        and "average_confidence" in daily_summary
    )
    health_items = latest_payload.get("health", {}).get("items", []) if isinstance(latest_payload, dict) else []
    history_provider_visible = any(
        isinstance(item, dict) and bool(item.get("history_selected_provider"))
        for item in health_items
    )
    diagnosis_evidence = build_diagnosis_evidence(daily_summary=daily_summary, health_items=health_items if isinstance(health_items, list) else [])
    diagnosis_ok = isinstance(diagnosis_evidence, dict) and isinstance(diagnosis_evidence.get("sample_items", []), list)
    action_list = latest_payload.get("action_list", {}) if isinstance(latest_payload, dict) else {}
    action_ok = isinstance(action_list, dict) and bool(action_list.get("items", [])) and bool(action_list.get("summary_text", ""))
    action_hint_ok = False
    if isinstance(action_list, dict):
        first_item = action_list.get("items", [{}])[0] if action_list.get("items") else {}
        action_hint_ok = isinstance(first_item, dict) and bool(first_item.get("action_hint", ""))
    sample_attribution_ok = isinstance(diagnosis_evidence, dict) and bool(diagnosis_evidence.get("sample_attribution", []))
    run_cadence = latest_payload.get("run_cadence", {}) if isinstance(latest_payload, dict) else {}
    if (not isinstance(run_cadence, dict) or not run_cadence) and run_status_path.exists():
        run_status_payload = _load_json_payload(run_status_path)
        run_cadence = run_status_payload.get("run_cadence", {}) if isinstance(run_status_payload, dict) else {}
    run_cadence_ok = isinstance(run_cadence, dict) and bool(run_cadence.get("summary_text", "")) and bool(run_cadence.get("steps", []))
    prompt_context = latest_payload.get("prompt_context", {}) if isinstance(latest_payload, dict) else {}
    if (not isinstance(prompt_context, dict) or not prompt_context) and run_status_path.exists():
        run_status_payload = _load_json_payload(run_status_path)
        prompt_context = run_status_payload.get("prompt_context", {}) if isinstance(run_status_payload, dict) else {}
    prompt_context_ok = (
        isinstance(prompt_context, dict)
        and bool(prompt_context.get("summary_text", ""))
        and bool(prompt_context.get("read_order", []))
    )
    feedback_effects = _load_json_payload(ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json")
    feedback_effect_brief = feedback_effects.get("feedback_effect_brief", {}) if isinstance(feedback_effects, dict) else {}
    if not isinstance(feedback_effect_brief, dict) or not feedback_effect_brief:
        feedback_effect_brief = build_feedback_effect_brief(feedback_effects=feedback_effects if isinstance(feedback_effects, dict) else {})
    feedback_effect_brief_ok = isinstance(feedback_effect_brief, dict) and bool(feedback_effect_brief.get("summary_text", "")) and bool(feedback_effect_brief.get("read_order", []))
    feedback_coverage_ok = isinstance(feedback_effect_brief, dict) and bool(feedback_effect_brief.get("coverage_summary", ""))
    review_brief = build_daily_review_brief(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        production_gate=latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {},
        action_list=action_list if isinstance(action_list, dict) else {},
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
        feedback_effects=feedback_effects,
        feedback_effect_brief=feedback_effect_brief if isinstance(feedback_effect_brief, dict) else {},
    )
    review_brief_ok = isinstance(review_brief, dict) and bool(review_brief.get("summary_text", "")) and bool(review_brief.get("read_order", []))
    run_status_payload = _load_json_payload(run_status_path) if run_status_path.exists() else {}
    schedule_hint = latest_payload.get("schedule_hint", {}) if isinstance(latest_payload, dict) else {}
    if (not isinstance(schedule_hint, dict) or not schedule_hint) and isinstance(run_status_payload, dict):
        schedule_hint = run_status_payload.get("schedule_hint", {})
    if not isinstance(schedule_hint, dict) or not schedule_hint:
        schedule_hint = build_schedule_hint(
            daily_run_status=str(run_status_payload.get("status", "unknown")) if isinstance(run_status_payload, dict) else "unknown",
            production_gate=latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {},
            run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
            prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
            review_brief=review_brief if isinstance(review_brief, dict) else {},
        )
    schedule_hint_ok = isinstance(schedule_hint, dict) and bool(schedule_hint.get("summary_text", "")) and bool(schedule_hint.get("read_order", []))
    daily_collaboration_pack = latest_payload.get("daily_collaboration_pack", {}) if isinstance(latest_payload, dict) else {}
    if (not isinstance(daily_collaboration_pack, dict) or not daily_collaboration_pack) and isinstance(run_status_payload, dict):
        daily_collaboration_pack = run_status_payload.get("daily_collaboration_pack", {})
    if not isinstance(daily_collaboration_pack, dict) or not daily_collaboration_pack:
        daily_collaboration_pack = build_daily_collaboration_pack(
            production_gate=latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {},
            action_list=action_list if isinstance(action_list, dict) else {},
            run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
            prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
            review_brief=review_brief if isinstance(review_brief, dict) else {},
            schedule_hint=schedule_hint if isinstance(schedule_hint, dict) else {},
        )
    daily_collaboration_pack_ok = isinstance(daily_collaboration_pack, dict) and bool(daily_collaboration_pack.get("summary_text", "")) and bool(daily_collaboration_pack.get("read_order", []))
    daily_execution_brief = latest_payload.get("daily_execution_brief", {}) if isinstance(latest_payload, dict) else {}
    if (not isinstance(daily_execution_brief, dict) or not daily_execution_brief) and isinstance(run_status_payload, dict):
        daily_execution_brief = run_status_payload.get("daily_execution_brief", {})
    if not isinstance(daily_execution_brief, dict) or not daily_execution_brief:
        daily_execution_brief = build_daily_execution_brief(
            production_gate=latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {},
            action_list=action_list if isinstance(action_list, dict) else {},
            run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
            review_brief=review_brief if isinstance(review_brief, dict) else {},
            schedule_hint=schedule_hint if isinstance(schedule_hint, dict) else {},
            daily_collaboration_pack=daily_collaboration_pack if isinstance(daily_collaboration_pack, dict) else {},
            feedback_effect_brief=feedback_effect_brief if isinstance(feedback_effect_brief, dict) else {},
        )
    daily_execution_brief_ok = isinstance(daily_execution_brief, dict) and bool(daily_execution_brief.get("summary_text", "")) and bool(daily_execution_brief.get("read_order", []))

    checks = {
        "latest_json": _exists(latest_json),
        "latest_md": _exists(latest_md),
        "run_status": _exists(run_status_path),
        "feedback_file": _exists(feedback_file),
        "diagnosis_summary": diagnosis_ok,
        "confidence_summary": confidence_ok,
        "action_list": action_ok,
        "action_hint": action_hint_ok,
        "sample_attribution": sample_attribution_ok,
        "run_cadence": run_cadence_ok,
        "prompt_context": prompt_context_ok,
        "schedule_hint": schedule_hint_ok,
        "daily_collaboration_pack": daily_collaboration_pack_ok,
        "daily_execution_brief": daily_execution_brief_ok,
        "review_brief": review_brief_ok,
        "feedback_effect_brief": feedback_effect_brief_ok,
        "feedback_coverage": feedback_coverage_ok,
        "history_provider_visible": history_provider_visible,
    }
    checks_ok = sum(1 for value in checks.values() if value)
    checks_total = len(checks)

    review_code, review_output = _run_script(viewer_script, ["--archive-dir", str(archive_dir), "--limit-lines", "3", "--feedback-limit", "3"])
    insights_code, insights_output = _run_script(insights_script, ["--feedback-file", str(feedback_file), "--limit", "3", "--min-samples", "2"])

    status = _score(checks_ok=checks_ok, checks_total=checks_total, entry_ok=review_code == 0 and insights_code == 0)
    generated_at = datetime.now().isoformat(timespec="seconds")
    payload = {
        "status": status,
        "generated_at": generated_at,
        "archive_dir": str(archive_dir),
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
        "run_status": str(run_status_path),
        "feedback_file": str(feedback_file),
        "checks": checks,
        "diagnosis_counts": diagnosis_counts if isinstance(diagnosis_counts, dict) else {},
        "diagnosis_evidence": diagnosis_evidence,
        "review_ok": review_code == 0,
        "insights_ok": insights_code == 0,
        "summary": "投产验收通过。" if status == "ok" else ("部分产物缺失，但主链路可用。" if status == "degraded" else "关键产物或入口不可用。"),
        "data": {
            "latest_payload": latest_payload,
            "run_status_payload": _load_json_payload(run_status_path),
            "feedback_records": len(_load_jsonl_payload(feedback_file)),
            "review_output": review_output.strip(),
            "insights_output": insights_output.strip(),
        },
    }

    acceptance_path.parent.mkdir(parents=True, exist_ok=True)
    with acceptance_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print("== 自选股日常投产验收 ==")
    print(f"状态: {status}")
    print(f"latest.json: {'存在' if checks['latest_json'] else '缺失'}")
    print(f"latest.md: {'存在' if checks['latest_md'] else '缺失'}")
    print(f"run_status: {'存在' if checks['run_status'] else '缺失'}")
    print(f"feedback_file: {'存在' if checks['feedback_file'] else '缺失'}")
    print(f"diagnosis_summary: {'存在' if checks['diagnosis_summary'] else '缺失'}")
    print(f"confidence_summary: {'存在' if checks['confidence_summary'] else '缺失'}")
    print(f"action_list: {'存在' if checks['action_list'] else '缺失'}")
    print(f"action_hint: {'存在' if checks['action_hint'] else '缺失'}")
    print(f"sample_attribution: {'存在' if checks['sample_attribution'] else '缺失'}")
    print(f"run_cadence: {'存在' if checks['run_cadence'] else '缺失'}")
    print(f"prompt_context: {'存在' if checks['prompt_context'] else '缺失'}")
    print(f"schedule_hint: {'存在' if checks['schedule_hint'] else '缺失'}")
    print(f"daily_collaboration_pack: {'存在' if checks['daily_collaboration_pack'] else '缺失'}")
    print(f"daily_execution_brief: {'存在' if checks['daily_execution_brief'] else '缺失'}")
    print(f"review_brief: {'存在' if checks['review_brief'] else '缺失'}")
    print(f"feedback_effect_brief: {'存在' if checks['feedback_effect_brief'] else '缺失'}")
    print(f"feedback_coverage: {'存在' if checks['feedback_coverage'] else '缺失'}")
    print(f"history_provider_visible: {'存在' if checks['history_provider_visible'] else '缺失'}")
    print(f"diagnosis_evidence: {'存在' if bool(diagnosis_evidence.get('top_causes')) else '缺失'}")
    print(f"review: {'可运行' if review_code == 0 else '不可运行'}")
    print(f"insights: {'可运行' if insights_code == 0 else '不可运行'}")
    print(f"验收结果: {acceptance_path}")
    return 0 if status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
