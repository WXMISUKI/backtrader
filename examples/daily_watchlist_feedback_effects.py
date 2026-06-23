#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常反馈效果评估。

用法：
    python examples/daily_watchlist_feedback_effects.py
    python examples/daily_watchlist_feedback_effects.py --output-json logs/daily_watchlist_feedback_effects.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.daily_watchlist_display import print_bullets, print_kv_pairs, print_section
from examples.watchlist_shared import build_feedback_effect_brief


DEFAULT_FEEDBACK_PATH = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"
DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json"
WINDOWS = (1, 3, 5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist feedback effect evaluation.")
    parser.add_argument("--feedback-file", default=str(DEFAULT_FEEDBACK_PATH), help="Feedback JSONL file path.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory path.")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="Effect summary output path.")
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _snapshot_items(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    decision_items = payload.get("decision", {}).get("items", []) if isinstance(payload, dict) else []
    if isinstance(decision_items, list):
        for item in decision_items:
            if isinstance(item, dict):
                stock_code = str(item.get("stock_code", "")).strip()
                if stock_code:
                    lookup[stock_code] = item
    return lookup


def _load_snapshots(archive_dir: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if not archive_dir.exists():
        return candidates
    for path in archive_dir.rglob("daily_watchlist_pipeline*.json"):
        payload = _load_json_payload(path)
        generated_at = _parse_dt(payload.get("generated_at"))
        if generated_at is None:
            continue
        candidates.append(
            {
                "path": path,
                "generated_at": generated_at,
                "payload": payload,
                "lookup": _snapshot_items(payload),
            }
        )
    candidates.sort(key=lambda item: (item["generated_at"], str(item["path"])))
    return candidates


def _direction_hint(record: dict[str, Any]) -> str:
    action = str(record.get("reference_action", "") or "").upper()
    group = str(record.get("reference_group", "") or "")
    if action == "BUY" or group == "重点关注":
        return "positive"
    if action == "SELL":
        return "negative"
    return "neutral"


def _calc_return(reference_price: float, future_price: float) -> float | None:
    if reference_price <= 0 or future_price <= 0:
        return None
    return round(future_price / reference_price - 1.0, 6)


def _window_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [item["return_pct"] for item in records if item.get("return_pct") is not None]
    hit_values = [item["hit"] for item in records if item.get("hit") is not None]
    return {
        "evaluable": len(returns),
        "positive": sum(1 for value in returns if value > 0),
        "negative": sum(1 for value in returns if value < 0),
        "flat": sum(1 for value in returns if value == 0),
        "avg_return": round(mean(returns), 6) if returns else 0.0,
        "hit_count": sum(1 for value in hit_values if value),
        "hit_rate": round(sum(1 for value in hit_values if value) / len(hit_values), 4) if hit_values else 0.0,
        "sample_count": len(records),
    }


def _evaluate_feedback(
    *,
    feedback_records: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    windows: tuple[int, ...] = WINDOWS,
) -> dict[str, Any]:
    window_records: dict[int, list[dict[str, Any]]] = {window: [] for window in windows}
    feedback_samples: list[dict[str, Any]] = []
    usable_feedback = 0

    for record in feedback_records:
        stock_code = str(record.get("stock_code", "")).strip()
        created_at = _parse_dt(record.get("created_at"))
        reference_price = _safe_float(record.get("reference_price"), 0.0)
        baseline_snapshot = None
        if not stock_code or created_at is None:
            continue

        past_snaps = [snapshot for snapshot in snapshots if snapshot["generated_at"] <= created_at]
        future_snaps = [snapshot for snapshot in snapshots if snapshot["generated_at"] > created_at]
        if reference_price <= 0 and past_snaps:
            baseline_snapshot = past_snaps[-1]
            baseline_item = baseline_snapshot["lookup"].get(stock_code, {})
            reference_price = _safe_float(baseline_item.get("latest_price"), 0.0)
            if reference_price <= 0:
                reference_price = _safe_float(baseline_item.get("market_price"), 0.0)
            if not str(record.get("reference_group", "")).strip():
                record["reference_group"] = str(baseline_item.get("group", "") or "")
            if not str(record.get("reference_action", "")).strip():
                record["reference_action"] = str(baseline_item.get("action", "") or "")
            if not _safe_float(record.get("reference_confidence"), 0.0):
                record["reference_confidence"] = _safe_float(baseline_item.get("confidence"), 0.0)
            if not _safe_float(record.get("reference_data_confidence"), 0.0):
                record["reference_data_confidence"] = _safe_float(baseline_item.get("data_confidence"), 0.0)
            if not str(record.get("reference_gate_status", "")).strip():
                record["reference_gate_status"] = str(baseline_snapshot.get("payload", {}).get("production_gate", {}).get("status", ""))
        if not future_snaps:
            continue

        hint = _direction_hint(record)
        usable_feedback += 1
        sample_item = {
            "created_at": record.get("created_at", ""),
            "stock_code": stock_code,
            "stock_name": record.get("stock_name", ""),
            "feedback": record.get("feedback", ""),
            "reference_group": record.get("reference_group", ""),
            "reference_action": record.get("reference_action", ""),
            "reference_price": reference_price,
            "reference_confidence": _safe_float(record.get("reference_confidence"), 0.0),
            "reference_data_confidence": _safe_float(record.get("reference_data_confidence"), 0.0),
            "reference_gate_status": record.get("reference_gate_status", ""),
            "window_returns": {},
        }

        for window in windows:
            if len(future_snaps) < window:
                continue
            snapshot = future_snaps[window - 1]
            item = snapshot["lookup"].get(stock_code, {})
            future_price = _safe_float(item.get("latest_price"), 0.0)
            if future_price <= 0:
                future_price = _safe_float(item.get("market_price"), 0.0)
            return_pct = _calc_return(reference_price, future_price)
            hit: bool | None = None
            if return_pct is not None:
                if hint == "positive":
                    hit = return_pct >= 0
                elif hint == "negative":
                    hit = return_pct <= 0
            row = {
                "created_at": record.get("created_at", ""),
                "stock_code": stock_code,
                "stock_name": record.get("stock_name", ""),
                "feedback": record.get("feedback", ""),
                "hint": hint,
                "window": window,
                "snapshot_at": snapshot["generated_at"].isoformat(timespec="seconds"),
                "snapshot_path": str(snapshot["path"]),
                "future_price": future_price,
                "return_pct": return_pct,
                "hit": hit,
            }
            window_records[window].append(row)
            sample_item["window_returns"][str(window)] = {
                "snapshot_at": row["snapshot_at"],
                "future_price": future_price,
                "return_pct": return_pct,
                "hit": hit,
            }

        feedback_samples.append(sample_item)

    windows_summary = {
        str(window): _window_stats(window_records[window])
        for window in windows
    }
    overall_returns = [
        row["return_pct"]
        for rows in window_records.values()
        for row in rows
        if row.get("return_pct") is not None
    ]
    overall_hits = [
        row["hit"]
        for rows in window_records.values()
        for row in rows
        if row.get("hit") is not None
    ]
    overall = {
        "usable_feedback": usable_feedback,
        "evaluated_rows": sum(len(rows) for rows in window_records.values()),
        "avg_return": round(mean(overall_returns), 6) if overall_returns else 0.0,
        "hit_count": sum(1 for value in overall_hits if value),
        "hit_rate": round(sum(1 for value in overall_hits if value) / len(overall_hits), 4) if overall_hits else 0.0,
    }
    return {
        "overall": overall,
        "windows": windows_summary,
        "samples": feedback_samples[-10:],
    }


def _print_summary(payload: dict[str, Any], feedback_file: Path, archive_dir: Path) -> None:
    print_section("自选股反馈效果评估")
    print_kv_pairs(
        [
            ("反馈文件", feedback_file),
            ("留档目录", archive_dir),
            ("可用反馈", payload.get("overall", {}).get("usable_feedback", 0)),
            ("评估行数", payload.get("overall", {}).get("evaluated_rows", 0)),
            ("平均回报", f"{payload.get('overall', {}).get('avg_return', 0.0):.1%}"),
            ("命中率", f"{payload.get('overall', {}).get('hit_rate', 0.0):.1%}"),
        ]
    )

    print_section("窗口统计")
    for window, stats in payload.get("windows", {}).items():
        print_bullets(
            [
                f"T+{window}: 样本 {stats.get('sample_count', 0)}，可评估 {stats.get('evaluable', 0)}，"
                f"正 {stats.get('positive', 0)}，负 {stats.get('negative', 0)}，平 {stats.get('flat', 0)}，"
                f"平均 {stats.get('avg_return', 0.0):.1%}，命中率 {stats.get('hit_rate', 0.0):.1%}"
            ]
        )

    if payload.get("samples"):
        print_section("最近样本")
        print_bullets(
            [
                f"{item.get('stock_code', '')} {item.get('stock_name', '')} "
                f"[{item.get('feedback', '')}] 基线 {item.get('reference_price', 0.0):.2f}"
                for item in payload["samples"]
            ]
        )


def main() -> int:
    args = build_parser().parse_args()
    feedback_file = Path(args.feedback_file)
    archive_dir = Path(args.archive_dir)
    output_path = Path(args.output_json)

    feedback_records = _load_jsonl_payload(feedback_file)
    snapshots = _load_snapshots(archive_dir)
    payload = {
        "feedback_file": str(feedback_file),
        "archive_dir": str(archive_dir),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **_evaluate_feedback(feedback_records=feedback_records, snapshots=snapshots),
    }
    payload["feedback_effect_brief"] = build_feedback_effect_brief(feedback_effects=payload)

    _print_summary(payload, feedback_file, archive_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n已导出: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
