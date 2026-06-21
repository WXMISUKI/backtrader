#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常反馈洞察。

用法：
    python examples/daily_watchlist_feedback_insights.py
    python examples/daily_watchlist_feedback_insights.py --limit 10 --output-json logs/daily_watchlist_feedback_insights.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.daily_watchlist_display import print_block, print_bullets, print_kv_pairs, print_section

DEFAULT_FEEDBACK_PATH = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist feedback insights.")
    parser.add_argument("--feedback-file", default=str(DEFAULT_FEEDBACK_PATH), help="Feedback JSONL file path.")
    parser.add_argument("--limit", type=int, default=20, help="Limit recent feedback samples.")
    parser.add_argument("--min-samples", type=int, default=2, help="Minimum samples for stable stock insight.")
    parser.add_argument("--output-json", default="", help="Optional JSON output path.")
    return parser


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


def _normalize_feedback(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"accepted", "accept", "ok", "yes", "true"}:
        return "accepted"
    if text in {"ignored", "ignore"}:
        return "ignored"
    if text in {"wrong", "reject", "rejected"}:
        return "wrong"
    return "watching"


def _build_summary(records: list[dict[str, Any]], limit: int, min_samples: int) -> dict[str, Any]:
    total_feedback = len(records)
    type_counts = Counter(_normalize_feedback(item.get("feedback", item.get("accepted", ""))) for item in records)
    stock_counts = Counter(str(item.get("stock_code", "") or "unknown") for item in records)
    recent_samples = list(reversed(records[-limit:])) if limit > 0 else list(reversed(records))
    stable_stocks = [
        {"stock_code": stock_code, "count": count}
        for stock_code, count in stock_counts.most_common()
        if count >= min_samples
    ]
    summary = "暂无反馈记录。"
    if total_feedback:
        summary = f"已统计 {total_feedback} 条反馈，最近关注 {len(recent_samples)} 条。"
    return {
        "total_feedback": total_feedback,
        "accepted_count": type_counts.get("accepted", 0),
        "ignored_count": type_counts.get("ignored", 0),
        "watching_count": type_counts.get("watching", 0),
        "wrong_count": type_counts.get("wrong", 0),
        "stock_counts": stock_counts.most_common(20),
        "stable_stocks": stable_stocks[:20],
        "recent_samples": recent_samples,
        "summary": summary,
        "sample_size_ok": total_feedback >= max(5, min_samples),
    }


def _print_summary(payload: dict[str, Any], feedback_file: Path) -> None:
    print_section("自选股日常反馈洞察")
    print_kv_pairs(
        [
            ("反馈文件", feedback_file),
            ("总反馈", payload.get("total_feedback", 0)),
            (
                "分布",
                f"采纳 {payload.get('accepted_count', 0)}，继续观察 {payload.get('watching_count', 0)}，"
                f"忽略 {payload.get('ignored_count', 0)}，错误 {payload.get('wrong_count', 0)}",
            ),
            ("摘要", payload.get("summary", "")),
            ("样本量充足", "是" if payload.get("sample_size_ok") else "否"),
        ]
    )

    if payload.get("stable_stocks"):
        print_section("高频股票")
        print_bullets([f"{item.get('stock_code', '')} {item.get('count', 0)} 条" for item in payload["stable_stocks"]])

    if payload.get("recent_samples"):
        print_section("最近样本")
        print_bullets(
            [
                f"{item.get('stock_code', '')} {item.get('stock_name', '')} "
                f"[{item.get('feedback', '')}] {item.get('comment', '')}"
                for item in payload["recent_samples"][:10]
            ]
        )


def main() -> int:
    args = build_parser().parse_args()
    feedback_file = Path(args.feedback_file)
    records = _load_jsonl_payload(feedback_file)
    payload = _build_summary(records, args.limit, args.min_samples)

    _print_summary(payload, feedback_file)

    output_path = Path(args.output_json) if args.output_json else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "feedback_file": str(feedback_file),
                    "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                    **payload,
                },
                f,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        print(f"\n已导出: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
