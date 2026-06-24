#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常自动回归门禁。

用法：
    python examples/daily_watchlist_regression_gate.py
    python examples/daily_watchlist_regression_gate.py --archive-dir logs/daily_watchlist_archive
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


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"
DEFAULT_PORTFOLIO_PATH = ROOT_DIR / "config" / "portfolio.json"
DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"
DEFAULT_REGRESSION_JSON = ROOT_DIR / "logs" / "daily_watchlist_regression_gate.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"
DEFAULT_BASELINE_JSON = ROOT_DIR / "logs" / "daily_watchlist_production_baseline.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily regression gate for watchlist workflow.")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH), help="Watchlist JSON file path.")
    parser.add_argument("--portfolio", default=str(DEFAULT_PORTFOLIO_PATH), help="Portfolio JSON file path.")
    parser.add_argument("--start-date", default="20260601", help="History start date, YYYYMMDD.")
    parser.add_argument("--end-date", default="20260614", help="History end date, YYYYMMDD.")
    parser.add_argument("--risk-profile", default="moderate", choices=("conservative", "moderate", "aggressive"))
    parser.add_argument("--limit", type=int, default=0, help="Limit number of watchlist items. 0 means no limit.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--run-status", default=str(DEFAULT_RUN_STATUS), help="Run status JSON path.")
    parser.add_argument("--output-json", default=str(DEFAULT_REGRESSION_JSON), help="Regression gate JSON output path.")
    parser.add_argument("--acceptance-json", default=str(DEFAULT_ACCEPTANCE_JSON), help="Acceptance JSON output path.")
    parser.add_argument("--baseline-json", default=str(DEFAULT_BASELINE_JSON), help="Baseline JSON output path.")
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


def _write_json_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)


def _run_script(script: Path, args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(script), *args]
    completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def _ensure_dict(payload: object) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _extract_summary(payload: dict[str, Any]) -> str:
    summary = payload.get("summary")
    if isinstance(summary, dict):
        for key in ("message", "summary_text", "text"):
            text = str(summary.get(key, "")).strip()
            if text:
                return text
    elif isinstance(summary, str) and summary.strip():
        return summary.strip()

    for key in ("summary_text", "headline", "next_action", "repair_hint"):
        text = str(payload.get(key, "")).strip()
        if text:
            return text
    return ""


def _normalize_step_status(code: int, payload: dict[str, Any]) -> str:
    if code != 0:
        return "block"
    status = str(payload.get("status", "")).strip().lower()
    if status in {"failed", "blocked"}:
        return "block"
    if status in {"degraded", "caution", "warn"}:
        return "warn"
    return "pass"


def _classify_gate_status(step_statuses: list[str]) -> str:
    statuses = [str(item).strip().lower() for item in step_statuses]
    if any(status == "block" for status in statuses):
        return "block"
    if any(status in {"warn", "skipped"} for status in statuses):
        return "warn"
    return "pass"


def _merge_artifact_field(path: Path, field: str, value: dict[str, Any]) -> bool:
    if not path.exists():
        return False
    payload = _load_json_payload(path)
    if not payload:
        return False
    payload[field] = value
    _write_json_payload(path, payload)
    return True


def main() -> int:
    args = build_parser().parse_args()
    daily_run_script = ROOT_DIR / "examples" / "daily_watchlist_daily_run.py"
    acceptance_script = ROOT_DIR / "examples" / "daily_watchlist_acceptance.py"
    baseline_script = ROOT_DIR / "examples" / "daily_watchlist_production_baseline.py"

    run_status_path = Path(args.run_status)
    archive_dir = Path(args.archive_dir)
    latest_json_path = archive_dir / "latest.json"
    acceptance_json_path = Path(args.acceptance_json)
    baseline_json_path = Path(args.baseline_json)
    regression_json_path = Path(args.output_json)

    step_records: list[dict[str, Any]] = []

    daily_run_args = [
        "--watchlist",
        str(args.watchlist),
        "--portfolio",
        str(args.portfolio),
        "--start-date",
        str(args.start_date),
        "--end-date",
        str(args.end_date),
        "--risk-profile",
        str(args.risk_profile),
        "--limit",
        str(args.limit),
        "--archive-dir",
        str(args.archive_dir),
        "--run-status",
        str(run_status_path),
        "--output-json",
        str(ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"),
        "--skip-view",
    ]
    daily_code, daily_output = _run_script(daily_run_script, daily_run_args)
    daily_payload = _load_json_payload(run_status_path)
    daily_status = _normalize_step_status(daily_code, daily_payload)
    step_records.append(
        {
            "name": "daily_run",
            "code": daily_code,
            "status": daily_status,
            "summary_text": _extract_summary(daily_payload),
            "output_path": str(run_status_path),
            "command": "daily_watchlist_daily_run.py --skip-view",
        }
    )

    acceptance_code = 0
    acceptance_output = ""
    acceptance_payload: dict[str, Any] = {}
    acceptance_status = "skipped"
    if daily_status != "block":
        acceptance_args = [
            "--archive-dir",
            str(args.archive_dir),
            "--run-status",
            str(run_status_path),
            "--output-json",
            str(acceptance_json_path),
        ]
        acceptance_code, acceptance_output = _run_script(acceptance_script, acceptance_args)
        acceptance_payload = _load_json_payload(acceptance_json_path)
        acceptance_status = _normalize_step_status(acceptance_code, acceptance_payload)
    step_records.append(
        {
            "name": "acceptance",
            "code": acceptance_code,
            "status": acceptance_status,
            "summary_text": _extract_summary(acceptance_payload),
            "output_path": str(acceptance_json_path),
            "command": "daily_watchlist_acceptance.py",
        }
    )

    baseline_code = 0
    baseline_output = ""
    baseline_payload: dict[str, Any] = {}
    baseline_status = "skipped"
    if acceptance_status != "block" and daily_status != "block":
        baseline_args = [
            "--archive-dir",
            str(args.archive_dir),
            "--run-status",
            str(run_status_path),
            "--acceptance-json",
            str(acceptance_json_path),
            "--output-json",
            str(baseline_json_path),
        ]
        baseline_code, baseline_output = _run_script(baseline_script, baseline_args)
        baseline_payload = _load_json_payload(baseline_json_path)
        baseline_status = _normalize_step_status(baseline_code, baseline_payload)
    step_records.append(
        {
            "name": "baseline",
            "code": baseline_code,
            "status": baseline_status,
            "summary_text": _extract_summary(baseline_payload),
            "output_path": str(baseline_json_path),
            "command": "daily_watchlist_production_baseline.py",
        }
    )

    gate_status = _classify_gate_status([str(step.get("status", "skipped")) for step in step_records])
    blocked_steps = [step["name"] for step in step_records if step.get("status") == "block"]
    warning_steps = [step["name"] for step in step_records if step.get("status") == "warn"]
    skipped_steps = [step["name"] for step in step_records if step.get("status") == "skipped"]

    if gate_status == "block":
        summary_text = "自动回归门禁阻断，至少有一个关键步骤失败。"
        next_step = "先修复 blocked 步骤，再重新跑一键回归。"
    elif gate_status == "warn":
        summary_text = "自动回归门禁告警，主链路可跑但存在降级或非阻断缺口。"
        next_step = "先复核 warn 步骤，再决定是否继续参考。"
    else:
        summary_text = "自动回归门禁通过，daily_run、acceptance、baseline 都可用。"
        next_step = "可以把这次结果作为当前回归基线。"

    regression_gate = {
        "status": gate_status,
        "summary_text": summary_text,
        "next_step": next_step,
        "step_order": ["daily_run", "acceptance", "baseline"],
        "step_records": step_records,
        "blocked_steps": blocked_steps,
        "warning_steps": warning_steps,
        "skipped_steps": skipped_steps,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_status": str(run_status_path),
        "latest_json": str(latest_json_path),
        "acceptance_json": str(acceptance_json_path),
        "baseline_json": str(baseline_json_path),
        "command_sequence": [
            "daily_watchlist_daily_run.py --skip-view",
            "daily_watchlist_acceptance.py",
            "daily_watchlist_production_baseline.py",
        ],
        "read_order": ["daily_run", "acceptance", "baseline"],
        "rules": [
            "先跑 daily_run，再跑 acceptance，最后跑 baseline。",
            "任何关键步骤失败时，门禁状态必须是 block。",
            "出现降级但仍可运行时，门禁状态可以是 warn，不把它误当成 pass。",
            "门禁结果要回写到 run_status，若 latest.json 已存在也要同步回写。",
        ],
    }

    if daily_payload:
        _merge_artifact_field(run_status_path, "regression_gate", regression_gate)
        _merge_artifact_field(latest_json_path, "regression_gate", regression_gate)

    payload = {
        "status": gate_status,
        "summary_text": summary_text,
        "next_step": next_step,
        "step_order": regression_gate["step_order"],
        "step_records": step_records,
        "blocked_steps": blocked_steps,
        "warning_steps": warning_steps,
        "skipped_steps": skipped_steps,
        "run_status": str(run_status_path),
        "latest_json": str(latest_json_path),
        "acceptance_json": str(acceptance_json_path),
        "baseline_json": str(baseline_json_path),
        "generated_at": regression_gate["generated_at"],
        "commands": regression_gate["command_sequence"],
        "rules": regression_gate["rules"],
        "outputs": {
            "daily_run": daily_output.strip(),
            "acceptance": acceptance_output.strip(),
            "baseline": baseline_output.strip(),
        },
    }

    _write_json_payload(regression_json_path, payload)

    print("== 自选股自动回归门禁 ==")
    print(f"状态: {gate_status}")
    print(f"结论: {summary_text}")
    for step in step_records:
        print(f"{step['name']}: {step['status']} (code={step['code']})")
        if step.get("summary_text"):
            print(f"  {step['summary_text']}")
    if blocked_steps:
        print(f"阻断步骤: {', '.join(blocked_steps)}")
    if warning_steps:
        print(f"告警步骤: {', '.join(warning_steps)}")
    if skipped_steps:
        print(f"跳过步骤: {', '.join(skipped_steps)}")
    print(f"回写 run_status: {'是' if daily_payload else '否'}")
    print(f"回写 latest.json: {'是' if daily_payload and latest_json_path.exists() else '否'}")
    print(f"输出: {regression_json_path}")

    return 0 if gate_status in {"pass", "warn"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
