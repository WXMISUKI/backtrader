#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常回看入口。

用法：
    python examples/daily_watchlist_review.py
    python examples/daily_watchlist_review.py --archive-dir logs/daily_watchlist_archive --show-json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.daily_watchlist_display import print_block, print_section
from examples.watchlist_shared import build_daily_execution_brief, build_daily_prompt_context, build_daily_review_brief


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_FEEDBACK_FILE = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"
DEFAULT_EFFECTS_JSON = ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json"
DEFAULT_FLOW_JSON = ROOT_DIR / "logs" / "daily_watchlist_flow.json"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist review flow.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--limit-lines", type=int, default=12, help="Limit lines shown from archive summary.")
    parser.add_argument("--feedback-file", default=str(DEFAULT_FEEDBACK_FILE), help="Feedback JSONL file path.")
    parser.add_argument("--feedback-limit", type=int, default=10, help="Limit feedback samples in insights output.")
    parser.add_argument("--min-samples", type=int, default=2, help="Minimum samples for stable stock insight.")
    parser.add_argument("--effects-json", default=str(DEFAULT_EFFECTS_JSON), help="Feedback effects JSON output path.")
    parser.add_argument("--show-json", action="store_true", help="Print JSON payloads from viewer and insights.")
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
    viewer_script = ROOT_DIR / "examples" / "daily_watchlist_archive_viewer.py"
    insights_script = ROOT_DIR / "examples" / "daily_watchlist_feedback_insights.py"
    effects_script = ROOT_DIR / "examples" / "daily_watchlist_feedback_effects.py"
    latest_json = Path(args.archive_dir) / "latest.json"
    latest_payload = _load_json_payload(latest_json)
    flow_payload = _load_json_payload(DEFAULT_FLOW_JSON)
    run_status_payload = _load_json_payload(DEFAULT_RUN_STATUS)
    pipeline_payload = flow_payload.get("pipeline_payload", {}) if isinstance(flow_payload, dict) else {}
    if not latest_payload:
        latest_payload = pipeline_payload

    viewer_code, viewer_output = _run_script(
        viewer_script,
        ["--archive-dir", str(args.archive_dir), "--limit-lines", str(args.limit_lines)],
    )
    insights_code, insights_output = _run_script(
        insights_script,
        [
            "--feedback-file",
            str(args.feedback_file),
            "--limit",
            str(args.feedback_limit),
            "--min-samples",
            str(args.min_samples),
        ],
    )
    effects_code, effects_output = _run_script(
        effects_script,
        [
            "--feedback-file",
            str(args.feedback_file),
            "--archive-dir",
            str(args.archive_dir),
            "--output-json",
            str(args.effects_json),
        ],
    )

    daily_summary = latest_payload.get("daily_summary", {}) if isinstance(latest_payload, dict) else {}
    if not isinstance(daily_summary, dict) or not daily_summary:
        daily_summary = pipeline_payload.get("daily_summary", {}) if isinstance(pipeline_payload, dict) else {}
    production_gate = latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {}
    if not isinstance(production_gate, dict) or not str(production_gate.get("status", "")).strip():
        production_gate = flow_payload.get("production_gate", {}) if isinstance(flow_payload, dict) else {}
    action_list = latest_payload.get("action_list", {}) if isinstance(latest_payload, dict) else {}
    if not isinstance(action_list, dict) or not str(action_list.get("summary_text", "")).strip():
        action_list = pipeline_payload.get("action_list", {}) if isinstance(pipeline_payload, dict) else {}
    run_cadence = latest_payload.get("run_cadence", {}) if isinstance(latest_payload, dict) else {}
    if not isinstance(run_cadence, dict) or not str(run_cadence.get("summary_text", "")).strip():
        run_cadence = flow_payload.get("run_cadence", {}) if isinstance(flow_payload, dict) else {}
    if (not isinstance(run_cadence, dict) or not run_cadence) and isinstance(run_status_payload, dict):
        run_cadence = run_status_payload.get("run_cadence", {})
    prompt_context = latest_payload.get("prompt_context", {}) if isinstance(latest_payload, dict) else {}
    if not isinstance(prompt_context, dict) or not str(prompt_context.get("summary_text", "")).strip():
        prompt_context = flow_payload.get("prompt_context", {}) if isinstance(flow_payload, dict) else {}
    if not isinstance(prompt_context, dict) or not prompt_context:
        prompt_context = build_daily_prompt_context(
            production_gate=production_gate if isinstance(production_gate, dict) else {},
            action_list=action_list if isinstance(action_list, dict) else {},
            run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
            daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
            diagnosis_evidence={},
        )
    feedback_effects = _load_json_payload(Path(args.effects_json))
    review_brief = build_daily_review_brief(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        production_gate=production_gate if isinstance(production_gate, dict) else {},
        action_list=action_list if isinstance(action_list, dict) else {},
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
        feedback_effects=feedback_effects if isinstance(feedback_effects, dict) else {},
    )
    daily_execution_brief = build_daily_execution_brief(
        production_gate=production_gate if isinstance(production_gate, dict) else {},
        action_list=action_list if isinstance(action_list, dict) else {},
        run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
        review_brief=review_brief if isinstance(review_brief, dict) else {},
        schedule_hint=run_status_payload.get("schedule_hint", {}) if isinstance(run_status_payload, dict) else {},
        daily_collaboration_pack=run_status_payload.get("daily_collaboration_pack", {}) if isinstance(run_status_payload, dict) else {},
    )

    print_section("回看摘要")
    print(f"{daily_execution_brief.get('headline', '')} | {daily_execution_brief.get('summary_text', '')}")
    print(review_brief.get("summary_text", ""))
    print(f"顺序: {' -> '.join(review_brief.get('read_order', []))}")
    print(f"下一步: {review_brief.get('next_step', '')}")
    print(f"风险: {review_brief.get('risk_note', '')}")
    if review_brief.get("key_points"):
        print_block("回看重点", [str(item) for item in review_brief.get("key_points", [])[:6]])

    print_section("自选股日常回看")
    print(viewer_output.strip())
    print_section("自选股反馈洞察")
    print(insights_output.strip())

    print_section("自选股反馈效果")
    print(effects_output.strip())

    if args.show_json:
        viewer_json_script = ROOT_DIR / "examples" / "daily_watchlist_archive_viewer.py"
        viewer_json_code, viewer_json_output = _run_script(
            viewer_json_script,
            ["--archive-dir", str(args.archive_dir), "--show-json", "--limit-lines", str(args.limit_lines)],
        )
        print_section("回看 JSON")
        print(viewer_json_output.strip())
        if viewer_json_code != 0:
            viewer_code = viewer_json_code

    return 0 if viewer_code == 0 and insights_code == 0 and effects_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
