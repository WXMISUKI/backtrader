#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股数据健康预检。

用法：
    python examples/watchlist_data_health.py
    python examples/watchlist_data_health.py --watchlist config/watchlist.json --output-json logs/watchlist_health.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.data.eastmoney_api import fetch_stock_hist_governed
from core.data.real_provider import RealDataProvider
from examples.watchlist_shared import build_data_health_summary


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watchlist data health preflight.")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH), help="Watchlist JSON file path.")
    parser.add_argument("--start-date", default="20260601", help="History start date, YYYYMMDD.")
    parser.add_argument("--end-date", default="20260614", help="History end date, YYYYMMDD.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of watchlist items. 0 means no limit.")
    parser.add_argument("--output-json", default="", help="Optional JSON output file path.")
    return parser


def _load_watchlist(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"watchlist file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        items = payload.get("watchlist", [])
    elif isinstance(payload, list):
        items = payload
    else:
        items = []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("enabled", True)]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_pct(value: Any) -> str:
    return f"{_safe_float(value):.1%}"


def _quality_label(*, data_source: str, is_degraded: bool, quality: dict[str, Any]) -> str:
    if data_source == "real" and not is_degraded and quality.get("ok", False):
        return "完全可用"
    if is_degraded or data_source in {"mock", "fallback"}:
        return "明显降级"
    return "部分降级"


def _score(*, history: dict[str, Any], fundamental: dict[str, Any]) -> int:
    score = 0
    if history.get("data_source") == "real" and not history.get("is_degraded", False):
        score += 50
    elif history.get("data_source") == "cache":
        score += 35
    elif history.get("data_source") == "mock":
        score += 15

    if fundamental.get("data_source") == "real" and not fundamental.get("is_degraded", False):
        score += 50
    elif fundamental.get("data_source") == "cache":
        score += 35
    elif fundamental.get("data_source") == "mock":
        score += 15

    if history.get("quality", {}).get("ok", False):
        score += 5
    if fundamental.get("quality", {}).get("ok", False):
        score += 5
    return min(score, 100)


def _build_summary(*, stock_name: str, history: dict[str, Any], fundamental: dict[str, Any]) -> dict[str, Any]:
    return build_data_health_summary(stock_name=stock_name, history=history, fundamental=fundamental)


def _print_item(item: dict[str, Any]) -> None:
    print(f"- {item['stock_code']} {item['name']} [{item['status']}]")
    print(f"  摘要: {item['summary']}")
    print(f"  历史: source={item['history_source']} | reason={item['history_reason']} | quality_ok={item['history_quality'].get('ok', False)}")
    if item.get("history_selected_provider"):
        print(
            f"  历史 provider: {item['history_selected_provider']} | "
            f"attempts={len(item.get('history_provider_attempts', []))} | "
            f"summary={item.get('history_provider_summary', '')}"
        )
    print(f"  基本面: source={item['fundamental_source']} | reason={item['fundamental_reason']} | quality_ok={item['fundamental_quality'].get('ok', False)}")
    print(f"  分值: {item['health_score']} | flags={item['flags']}")


def _print_group(title: str, items: list[dict[str, Any]]) -> None:
    print(f"\n== {title} ({len(items)}) ==")
    if not items:
        print("  无")
        return
    for item in items:
        _print_item(item)


def main() -> int:
    args = build_parser().parse_args()
    watchlist_path = Path(args.watchlist)
    provider = RealDataProvider()

    try:
        watchlist = _load_watchlist(watchlist_path)
    except Exception as exc:
        print(f"读取 watchlist 失败: {exc}")
        return 1

    if args.limit and args.limit > 0:
        watchlist = watchlist[: args.limit]

    if not watchlist:
        print("watchlist 为空，未执行预检。")
        return 1

    print("== 自选股数据健康预检 ==")
    print(f"生成时间: {datetime.now().isoformat(timespec='seconds')}")
    print(f"watchlist: {watchlist_path}")
    print(f"历史区间: {args.start_date} ~ {args.end_date}")

    items: list[dict[str, Any]] = []
    for raw in watchlist:
        stock_code = str(raw.get("stock_code", "")).strip()
        stock_name = str(raw.get("name", stock_code or "unknown"))
        if not stock_code:
            items.append(
                {
                    "stock_code": "",
                    "name": stock_name,
                    "status": "明显降级",
                    "history_source": "config_error",
                    "fundamental_source": "config_error",
                    "history_quality": {"ok": False, "reason": "missing stock_code"},
                    "fundamental_quality": {"ok": False, "reason": "missing stock_code"},
                    "history_reason": "watchlist 配置缺少 stock_code",
                    "fundamental_reason": "watchlist 配置缺少 stock_code",
                    "health_score": 0,
                    "summary": f"{stock_name} 配置不完整，无法预检。",
                    "flags": {"history_degraded": True, "fundamental_degraded": True},
                }
            )
            continue

        try:
            history = fetch_stock_hist_governed(
                symbol=stock_code,
                start_date=args.start_date,
                end_date=args.end_date,
            )
        except Exception as exc:
            history = {
                "data_source": "error",
                "is_degraded": True,
                "quality": {"ok": False, "reason": str(exc)},
                "reason": str(exc),
            }

        try:
            fundamental = provider.get_financial_indicators_governed(stock_code)
        except Exception as exc:
            fundamental = {
                "data_source": "error",
                "is_degraded": True,
                "quality": {"ok": False, "reason": str(exc)},
                "reason": str(exc),
            }

        summary = _build_summary(stock_name=stock_name, history=history, fundamental=fundamental)
        summary.update(
            {
                "stock_code": stock_code,
                "name": stock_name,
                "watch_reason": str(raw.get("reason", "")),
                "tags": raw.get("tags", []),
                "risk_profile": raw.get("risk_profile", ""),
                "history_rows": _safe_int(history.get("quality", {}).get("rows", 0)),
                "fundamental_report_date": str(fundamental.get("payload", {}).get("report_date", "")) if isinstance(fundamental, dict) else "",
                "history_date_range": str(history.get("meta", {}).get("start_date", "")) + " ~ " + str(history.get("meta", {}).get("end_date", "")),
            }
        )
        items.append(summary)

    items.sort(key=lambda x: (_status_order(str(x.get("status", ""))), -_safe_int(x.get("health_score", 0)), str(x.get("stock_code", ""))))

    groups = {
        "完全可用": [item for item in items if item.get("status") == "完全可用"],
        "部分降级": [item for item in items if item.get("status") == "部分降级"],
        "明显降级": [item for item in items if item.get("status") == "明显降级"],
    }
    counts = {key: len(value) for key, value in groups.items()}

    print(f"\n总计: {len(items)} 只，完全可用 {counts['完全可用']}，部分降级 {counts['部分降级']}，明显降级 {counts['明显降级']}")

    _print_group("完全可用", groups["完全可用"])
    _print_group("部分降级", groups["部分降级"])
    _print_group("明显降级", groups["明显降级"])

    output_path = Path(args.output_json) if args.output_json else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "watchlist_path": str(watchlist_path),
            "history_start_date": args.start_date,
            "history_end_date": args.end_date,
            "counts": counts,
            "items": items,
            "groups": groups,
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n已导出: {output_path}")

    return 0


def _status_order(status: str) -> int:
    order = {
        "完全可用": 0,
        "部分降级": 1,
        "明显降级": 2,
    }
    return order.get(status, 99)


if __name__ == "__main__":
    raise SystemExit(main())
