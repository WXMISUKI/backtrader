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


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_FEEDBACK_FILE = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"
DEFAULT_EFFECTS_JSON = ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json"


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


def main() -> int:
    args = build_parser().parse_args()
    viewer_script = ROOT_DIR / "examples" / "daily_watchlist_archive_viewer.py"
    insights_script = ROOT_DIR / "examples" / "daily_watchlist_feedback_insights.py"
    effects_script = ROOT_DIR / "examples" / "daily_watchlist_feedback_effects.py"

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
