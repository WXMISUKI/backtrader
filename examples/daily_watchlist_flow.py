#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股默认日常工作流。

用法：
    python examples/daily_watchlist_flow.py
    python examples/daily_watchlist_flow.py --skip-review
    python examples/daily_watchlist_flow.py --skip-acceptance
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.watchlist_shared import (
    build_daily_collaboration_pack,
    build_daily_prompt_context,
    build_daily_review_brief,
    build_diagnosis_evidence,
    build_production_gate,
    build_schedule_hint,
)


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"
DEFAULT_PORTFOLIO_PATH = ROOT_DIR / "config" / "portfolio.json"
DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "logs" / "daily_watchlist_flow.json"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist default workflow.")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH), help="Watchlist JSON file path.")
    parser.add_argument("--portfolio", default=str(DEFAULT_PORTFOLIO_PATH), help="Portfolio JSON file path.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="Workflow JSON output path.")
    parser.add_argument("--skip-review", action="store_true", help="Skip review step.")
    parser.add_argument("--skip-acceptance", action="store_true", help="Skip acceptance step.")
    parser.add_argument("--show-json", action="store_true", help="Print child JSON outputs.")
    return parser


def _run_script(script: Path, args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(script), *args]
    completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def _load_json_payload(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    args = build_parser().parse_args()
    daily_run_script = ROOT_DIR / "examples" / "daily_watchlist_daily_run.py"
    review_script = ROOT_DIR / "examples" / "daily_watchlist_review.py"
    acceptance_script = ROOT_DIR / "examples" / "daily_watchlist_acceptance.py"

    outputs: dict[str, dict[str, object]] = {}

    daily_code, daily_output = _run_script(
        daily_run_script,
        [
            "--watchlist",
            str(args.watchlist),
            "--portfolio",
            str(args.portfolio),
            "--archive-dir",
            str(args.archive_dir),
            "--run-status",
            str(DEFAULT_RUN_STATUS),
            "--output-json",
            str(ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"),
        ],
    )
    outputs["daily_run"] = {"code": daily_code, "output": daily_output.strip()}

    review_code = 0
    review_output = ""
    if not args.skip_review and daily_code == 0:
        review_code, review_output = _run_script(
            review_script,
            ["--archive-dir", str(args.archive_dir), "--limit-lines", "5", "--feedback-limit", "5"],
        )
    outputs["review"] = {"code": review_code, "output": review_output.strip()}

    acceptance_code = 0
    acceptance_output = ""
    if not args.skip_acceptance and daily_code == 0:
        acceptance_code, acceptance_output = _run_script(
            acceptance_script,
            ["--archive-dir", str(args.archive_dir), "--output-json", str(ROOT_DIR / "logs" / "daily_watchlist_acceptance.json")],
        )
    outputs["acceptance"] = {"code": acceptance_code, "output": acceptance_output.strip()}

    daily_run_status_payload = _load_json_payload(DEFAULT_RUN_STATUS)
    pipeline_payload = _load_json_payload(ROOT_DIR / "logs" / "daily_watchlist_pipeline.json")
    daily_summary = pipeline_payload.get("daily_summary", {}) if isinstance(pipeline_payload, dict) else {}
    diagnosis_counts = daily_summary.get("diagnosis_counts", {}) if isinstance(daily_summary, dict) else {}
    health_items = pipeline_payload.get("health", {}).get("items", []) if isinstance(pipeline_payload, dict) else []
    action_list = pipeline_payload.get("action_list", {}) if isinstance(pipeline_payload, dict) else {}
    run_cadence = daily_run_status_payload.get("run_cadence", {}) if isinstance(daily_run_status_payload, dict) else {}
    diagnosis_evidence = build_diagnosis_evidence(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        health_items=health_items if isinstance(health_items, list) else [],
    )
    acceptance_payload = {}
    if not args.skip_acceptance and acceptance_code == 0:
        acceptance_payload = _load_json_payload(DEFAULT_ACCEPTANCE_JSON)

    daily_run_status = "unknown"
    if isinstance(daily_run_status_payload, dict):
        daily_run_status = str(daily_run_status_payload.get("status", "unknown"))

    production_gate = build_production_gate(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        diagnosis_evidence=diagnosis_evidence,
        acceptance=acceptance_payload,
        health_items=health_items if isinstance(health_items, list) else [],
        daily_run_status=daily_run_status,
    )
    prompt_context = build_daily_prompt_context(
        production_gate=production_gate,
        action_list=action_list if isinstance(action_list, dict) else {},
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        diagnosis_evidence=diagnosis_evidence,
    )
    feedback_effects = _load_json_payload(ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json")
    review_brief = build_daily_review_brief(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        production_gate=production_gate,
        action_list=action_list if isinstance(action_list, dict) else {},
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
        feedback_effects=feedback_effects if isinstance(feedback_effects, dict) else {},
    )
    schedule_hint = build_schedule_hint(
        daily_run_status=daily_run_status,
        production_gate=production_gate,
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        prompt_context=prompt_context,
        review_brief=review_brief if isinstance(review_brief, dict) else {},
    )
    daily_collaboration_pack = build_daily_collaboration_pack(
        production_gate=production_gate,
        action_list=action_list if isinstance(action_list, dict) else {},
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
        review_brief=review_brief if isinstance(review_brief, dict) else {},
        schedule_hint=schedule_hint if isinstance(schedule_hint, dict) else {},
    )

    status = "ok"
    if daily_code != 0 or review_code != 0 or acceptance_code != 0:
        status = "failed"
    elif daily_run_status in {"degraded", "failed"}:
        status = daily_run_status

    payload = {
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "daily_run_status": daily_run_status,
        "daily_run_status_payload": daily_run_status_payload,
        "pipeline_payload": pipeline_payload,
        "acceptance_payload": acceptance_payload,
        "diagnosis_counts": diagnosis_counts,
        "diagnosis_evidence": diagnosis_evidence,
        "action_list": action_list,
        "run_cadence": run_cadence,
        "prompt_context": prompt_context,
        "review_brief": review_brief,
        "schedule_hint": schedule_hint,
        "daily_collaboration_pack": daily_collaboration_pack,
        "production_gate": production_gate,
        "daily_run_code": daily_code,
        "review_code": review_code,
        "acceptance_code": acceptance_code,
        "outputs": outputs,
        "summary": "默认日常工作流已完成。" if status == "ok" else "默认日常工作流存在失败。",
    }

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print("== 自选股默认日常工作流 ==")
    print(f"状态: {status}")
    print(f"daily_run_status: {daily_run_status}")
    print(f"daily_run: {'成功' if daily_code == 0 else '失败'}")
    print(f"review: {'成功' if review_code == 0 else '失败'}")
    print(f"acceptance: {'成功' if acceptance_code == 0 else '失败'}")
    if isinstance(run_cadence, dict) and run_cadence.get("summary_text"):
        print(f"run_cadence: {run_cadence.get('summary_text', '')}")
        print(f"next_step: {run_cadence.get('next_step', '')}")
    print(f"production_gate: {production_gate.get('status', 'unknown')}")
    print(f"门禁摘要: {production_gate.get('summary', '')}")
    if isinstance(action_list, dict) and action_list.get("summary_text"):
        print(f"action_list: {action_list.get('summary_text', '')}")
    if isinstance(prompt_context, dict) and prompt_context.get("summary_text"):
        print(f"prompt_context: {prompt_context.get('summary_text', '')}")
    if isinstance(review_brief, dict) and review_brief.get("summary_text"):
        print(f"review_brief: {review_brief.get('summary_text', '')}")
    if isinstance(schedule_hint, dict) and schedule_hint.get("summary_text"):
        print(f"schedule_hint: {schedule_hint.get('summary_text', '')}")
        print(f"schedule_mode: {schedule_hint.get('next_run_mode', '')}")
    if isinstance(daily_collaboration_pack, dict) and daily_collaboration_pack.get("summary_text"):
        print(f"daily_collaboration_pack: {daily_collaboration_pack.get('summary_text', '')}")
    print(f"输出: {output_path}")

    if args.show_json:
        print("\n== 工作流 JSON ==")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    return 0 if status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
