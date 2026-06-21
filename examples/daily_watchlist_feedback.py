#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常反馈入口。

用法：
    python examples/daily_watchlist_feedback.py --feedback watching --comment "继续观察"
    python examples/daily_watchlist_feedback.py --archive-dir logs/daily_watchlist_archive --stock-code 000001 --feedback accepted
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.agent.session import get_decision_session_store


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_FEEDBACK_PATH = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist feedback helper.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--stock-code", default="", help="Stock code for the feedback item.")
    parser.add_argument("--stock-name", default="", help="Stock name for the feedback item.")
    parser.add_argument("--feedback", default="watching", choices=("accepted", "watching", "ignored", "wrong"))
    parser.add_argument("--comment", default="", help="Free-form feedback comment.")
    parser.add_argument("--rating", type=int, default=0, help="Optional rating, 1-5 recommended.")
    parser.add_argument("--accepted", action="store_true", help="Mark the feedback as accepted.")
    parser.add_argument("--session-id", default="", help="Optional decision session id.")
    parser.add_argument("--workflow-id", default="", help="Optional workflow id.")
    parser.add_argument("--output-json", default=str(DEFAULT_FEEDBACK_PATH), help="Feedback JSONL output path.")
    return parser


def _load_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, dict) else {}


def _find_latest_payload(archive_dir: Path) -> dict[str, Any]:
    latest_json = archive_dir / "latest.json"
    if latest_json.exists():
        return _load_json_payload(latest_json)
    dated_dirs = sorted((path for path in archive_dir.iterdir() if path.is_dir()), reverse=True) if archive_dir.exists() else []
    for run_dir in dated_dirs:
        json_files = sorted(run_dir.glob("*.json"), reverse=True)
        if json_files:
            return _load_json_payload(json_files[0])
    return {}


def _load_existing_records(path: Path) -> list[dict[str, Any]]:
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    args = build_parser().parse_args()
    archive_dir = Path(args.archive_dir)
    output_path = Path(args.output_json)
    latest_payload = _find_latest_payload(archive_dir)
    latest_generated_at = str(latest_payload.get("generated_at", "")) if isinstance(latest_payload, dict) else ""

    decision_items = latest_payload.get("decision", {}).get("items", []) if isinstance(latest_payload, dict) else []
    target_item: dict[str, Any] = {}
    if args.stock_code:
        for item in decision_items:
            if str(item.get("stock_code", "")) == str(args.stock_code):
                target_item = item
                break
    elif isinstance(decision_items, list) and decision_items:
        target_item = decision_items[0] if isinstance(decision_items[0], dict) else {}

    if not target_item and not args.session_id and not args.workflow_id:
        print("未找到可反馈的最新日常结果，请先运行 daily_watchlist_daily_run。")
        return 1

    session_store = get_decision_session_store()
    comment = args.comment.strip() or f"日常反馈: {args.feedback}"
    accepted = args.accepted if args.feedback != "accepted" else True
    if args.feedback == "ignored":
        accepted = False
    elif args.feedback == "wrong":
        accepted = False
    elif args.feedback == "watching" and not args.accepted:
        accepted = None

    reference_price = _safe_float(target_item.get("latest_price"), 0.0)
    if reference_price <= 0:
        reference_price = _safe_float(target_item.get("market_price"), 0.0)

    feedback_payload = session_store.submit_feedback(
        session_id=args.session_id or str(target_item.get("session_id", "") or ""),
        workflow_id=args.workflow_id or str(target_item.get("workflow_id", "") or ""),
        accepted=accepted,
        rating=args.rating if args.rating > 0 else None,
        reason=str(target_item.get("结论", target_item.get("summary", "")) or ""),
        correction="",
        comment=comment,
        meta={
            "source": "daily_watchlist_feedback",
            "archive_dir": str(archive_dir),
            "stock_code": str(args.stock_code or target_item.get("stock_code", "") or ""),
            "stock_name": str(args.stock_name or target_item.get("name", "") or ""),
            "feedback_type": args.feedback,
            "latest_json": str(archive_dir / "latest.json"),
            "reference_generated_at": latest_generated_at,
            "reference_group": str(target_item.get("group", "") or ""),
            "reference_action": str(target_item.get("action", "") or ""),
            "reference_confidence": _safe_float(target_item.get("confidence"), 0.0),
            "reference_data_confidence": _safe_float(target_item.get("data_confidence"), 0.0),
            "reference_price": reference_price,
            "reference_gate_status": str(latest_payload.get("production_gate", {}).get("status", "")) if isinstance(latest_payload, dict) else "",
        },
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_existing_records(output_path)
    existing.append(
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "archive_dir": str(archive_dir),
            "stock_code": str(args.stock_code or target_item.get("stock_code", "") or ""),
            "stock_name": str(args.stock_name or target_item.get("name", "") or ""),
            "feedback": args.feedback,
            "accepted": accepted,
            "rating": args.rating if args.rating > 0 else None,
            "comment": comment,
            "reference_generated_at": latest_generated_at,
            "reference_group": str(target_item.get("group", "") or ""),
            "reference_action": str(target_item.get("action", "") or ""),
            "reference_confidence": _safe_float(target_item.get("confidence"), 0.0),
            "reference_data_confidence": _safe_float(target_item.get("data_confidence"), 0.0),
            "reference_price": reference_price,
            "reference_gate_status": str(latest_payload.get("production_gate", {}).get("status", "")) if isinstance(latest_payload, dict) else "",
            "session_id": feedback_payload.get("session_id", ""),
            "workflow_id": feedback_payload.get("workflow_id", ""),
            "feedback_id": feedback_payload.get("feedback_id", ""),
        }
    )
    with output_path.open("w", encoding="utf-8") as f:
        for item in existing:
            f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")

    print("== 自选股日常反馈 ==")
    print(f"archive_dir: {archive_dir}")
    print(f"stock_code: {args.stock_code or target_item.get('stock_code', '')}")
    print(f"feedback: {args.feedback}")
    print(f"accepted: {accepted}")
    print(f"comment: {comment}")
    print(f"session_id: {feedback_payload.get('session_id', '')}")
    print(f"workflow_id: {feedback_payload.get('workflow_id', '')}")
    print(f"feedback_id: {feedback_payload.get('feedback_id', '')}")
    print(f"output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
