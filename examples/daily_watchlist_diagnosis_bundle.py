#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常诊断收口包。

用法：
    python examples/daily_watchlist_diagnosis_bundle.py
    python examples/daily_watchlist_diagnosis_bundle.py --show-json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.watchlist_shared import build_diagnosis_evidence
from examples.watchlist_shared import build_production_gate


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_FLOW_JSON = ROOT_DIR / "logs" / "daily_watchlist_flow.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"
DEFAULT_BUNDLE_JSON = ROOT_DIR / "logs" / "daily_watchlist_diagnosis_bundle.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily diagnosis bundle for watchlist pipeline.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--flow-json", default=str(DEFAULT_FLOW_JSON), help="Default workflow JSON path.")
    parser.add_argument("--acceptance-json", default=str(DEFAULT_ACCEPTANCE_JSON), help="Acceptance JSON path.")
    parser.add_argument("--output-json", default=str(DEFAULT_BUNDLE_JSON), help="Bundle JSON output path.")
    parser.add_argument("--show-json", action="store_true", help="Print the bundle JSON payload.")
    return parser


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
    archive_dir = Path(args.archive_dir)
    flow_json = Path(args.flow_json)
    acceptance_json = Path(args.acceptance_json)
    output_json = Path(args.output_json)

    flow_payload = _load_json_payload(flow_json)
    acceptance_payload = _load_json_payload(acceptance_json)
    latest_payload = _load_json_payload(archive_dir / "latest.json")
    if not latest_payload:
        latest_payload = flow_payload.get("pipeline_payload", {}) if isinstance(flow_payload, dict) else {}
    action_list = flow_payload.get("pipeline_payload", {}).get("action_list", {}) if isinstance(flow_payload, dict) else {}
    if not isinstance(action_list, dict) or not action_list:
        action_list = latest_payload.get("action_list", {}) if isinstance(latest_payload, dict) else {}

    daily_summary = flow_payload.get("pipeline_payload", {}).get("daily_summary", {}) if isinstance(flow_payload, dict) else {}
    if not isinstance(daily_summary, dict) or not daily_summary:
        daily_summary = latest_payload.get("daily_summary", {}) if isinstance(latest_payload, dict) else {}

    health_items = latest_payload.get("health", {}).get("items", []) if isinstance(latest_payload, dict) else []
    diagnosis_evidence = build_diagnosis_evidence(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        health_items=health_items if isinstance(health_items, list) else [],
    )
    production_gate = build_production_gate(
        daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
        diagnosis_evidence=diagnosis_evidence,
        acceptance=acceptance_payload if isinstance(acceptance_payload, dict) else {},
        health_items=health_items if isinstance(health_items, list) else [],
        daily_run_status=str(flow_payload.get("daily_run_status", "")) if isinstance(flow_payload, dict) else "",
    )

    bundle = {
        "generated_at": flow_payload.get("generated_at", acceptance_payload.get("generated_at", "")) if isinstance(flow_payload, dict) else "",
        "archive_dir": str(archive_dir),
        "daily_summary": daily_summary,
        "diagnosis_evidence": diagnosis_evidence,
        "action_list": action_list,
        "production_gate": production_gate,
        "acceptance": {
            "status": acceptance_payload.get("status", ""),
            "summary": acceptance_payload.get("summary", ""),
            "checks": acceptance_payload.get("checks", {}),
            "diagnosis_counts": acceptance_payload.get("diagnosis_counts", {}),
        },
        "archive_paths": {
            "latest_json": str(archive_dir / "latest.json"),
            "latest_md": str(archive_dir / "latest.md"),
            "flow_json": str(flow_json),
            "acceptance_json": str(acceptance_json),
        },
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2, default=str)

    print("== 自选股日常诊断收口包 ==")
    print(f"日常总览: {daily_summary.get('status', '') if isinstance(daily_summary, dict) else ''}")
    print(f"诊断摘要: {diagnosis_evidence.get('summary_text', '')}")
    print(f"验收状态: {acceptance_payload.get('status', '')}")
    print(f"投产门禁: {production_gate.get('status', '')}")
    print(f"门禁摘要: {production_gate.get('summary', '')}")
    if isinstance(action_list, dict) and action_list.get("summary_text"):
        print(f"行动清单: {action_list.get('summary_text', '')}")
    print(f"输出: {output_json}")

    if args.show_json:
        print("\n== 收口包 JSON ==")
        print(json.dumps(bundle, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
