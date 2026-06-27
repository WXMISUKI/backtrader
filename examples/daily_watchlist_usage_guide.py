#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常使用指南。

这是一个薄入口，只负责把日常使用顺序、可用入口、以及前端对话入口现状讲清楚。
它不做新的分析计算，不引入新的编排层。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = ROOT_DIR / "logs" / "daily_watchlist_usage_guide.json"
DEFAULT_PIPELINE_JSON = ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"
DEFAULT_RUN_STATUS_JSON = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist usage guide.")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="Usage guide JSON output path.")
    parser.add_argument("--show-json", action="store_true", help="Print JSON payload.")
    return parser


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _stringify(value: object, default: str = "") -> str:
    text = str(value).strip()
    return text if text else default


def _build_entry_points() -> list[dict[str, str]]:
    return [
        {
            "name": "数据健康预检",
            "command": "python examples/watchlist_data_health.py --watchlist config/watchlist.json --output-json logs/watchlist_health.json",
            "purpose": "先确认数据是否可用，再决定今天是否继续看决策结果。",
        },
        {
            "name": "日常决策清单",
            "command": "python examples/daily_watchlist_decision.py --watchlist config/watchlist.json --portfolio config/portfolio.json --output-json logs/daily_watchlist.json",
            "purpose": "查看今天哪些股票可参考、哪些只观察、哪些跳过。",
        },
        {
            "name": "回看摘要",
            "command": "python examples/daily_watchlist_review.py",
            "purpose": "先看一眼今天的回看摘要，再展开正文和证据。",
        },
        {
            "name": "投产验收",
            "command": "python examples/daily_watchlist_acceptance.py",
            "purpose": "确认今天的结果是否适合进入日常投产参考。",
        },
        {
            "name": "自动回归门禁",
            "command": "python examples/daily_watchlist_regression_gate.py --watchlist config/watchlist.json --portfolio config/portfolio.json --archive-dir logs/daily_watchlist_archive",
            "purpose": "一键检查 daily_run、acceptance、baseline 是否还能串起来。",
        },
    ]


def _build_usage_steps() -> list[str]:
    return [
        "1. 先跑数据健康预检，确认数据没有明显降级。",
        "2. 再跑日常决策清单，查看今天能否作为参考。",
        "3. 接着看回看摘要，确认今天的核心结论和风险点。",
        "4. 再跑投产验收，确认结果是否可以进入日常使用。",
        "5. 最后跑自动回归门禁，确认默认链路是否仍然稳定。",
    ]


def _build_frontend_status() -> dict[str, str]:
    return {
        "status": "absent",
        "summary": "当前没有独立的前端对话 AI 页面。",
        "alternative": "现阶段可用的是 CLI、HTTP API 和日常脚本入口。",
        "api_entry": "python tools/agent-api.py --host 127.0.0.1 --port 8000",
        "demo_entry": "python examples/api_demo.py --host 127.0.0.1 --port 8000",
    }


def build_usage_guide() -> dict[str, object]:
    pipeline = _load_json(DEFAULT_PIPELINE_JSON)
    acceptance = _load_json(DEFAULT_ACCEPTANCE_JSON)
    run_status = _load_json(DEFAULT_RUN_STATUS_JSON)

    production_gate = pipeline.get("production_gate", {}) if isinstance(pipeline, dict) else {}
    review_brief = pipeline.get("review_brief", {}) if isinstance(pipeline, dict) else {}
    schedule_hint = pipeline.get("schedule_hint", {}) if isinstance(pipeline, dict) else {}

    guide = {
        "status": "ready",
        "summary_text": "日常使用测试入口已整理完成，建议按固定顺序先看数据健康，再看决策和回看。",
        "usage_steps": _build_usage_steps(),
        "entry_points": _build_entry_points(),
        "frontend_chat": _build_frontend_status(),
        "current_gate": {
            "production_gate_status": _stringify(production_gate.get("status", "unknown")),
            "production_gate_summary": _stringify(production_gate.get("summary", "")),
            "review_brief_summary": _stringify(review_brief.get("summary_text", "")),
            "schedule_hint_summary": _stringify(schedule_hint.get("summary_text", "")),
            "acceptance_status": _stringify(acceptance.get("status", acceptance.get("result", "unknown"))),
            "run_status": _stringify(run_status.get("status", "unknown")),
        },
        "read_order": [
            "data_health",
            "daily_decision",
            "review_brief",
            "acceptance",
            "regression_gate",
        ],
    }
    return guide


def main() -> int:
    args = build_parser().parse_args()
    payload = build_usage_guide()

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    frontend = payload.get("frontend_chat", {})
    current_gate = payload.get("current_gate", {})

    print("== 自选股日常使用指南 ==")
    print(payload.get("summary_text", ""))
    print("\n== 推荐顺序 ==")
    for line in payload.get("usage_steps", []):
        print(f"- {line}")
    print("\n== 可用入口 ==")
    for item in payload.get("entry_points", []):
        if not isinstance(item, dict):
            continue
        print(f"- {item.get('name', '')}: {item.get('command', '')}")
        print(f"  {item.get('purpose', '')}")
    print("\n== 前端对话入口现状 ==")
    print(f"状态: {frontend.get('status', '')}")
    print(f"说明: {frontend.get('summary', '')}")
    print(f"替代入口: {frontend.get('alternative', '')}")
    print(f"API: {frontend.get('api_entry', '')}")
    print(f"Demo: {frontend.get('demo_entry', '')}")
    print("\n== 当前门禁摘要 ==")
    print(f"production_gate: {current_gate.get('production_gate_status', '')}")
    print(f"production_gate_summary: {current_gate.get('production_gate_summary', '')}")
    print(f"review_brief_summary: {current_gate.get('review_brief_summary', '')}")
    print(f"schedule_hint_summary: {current_gate.get('schedule_hint_summary', '')}")
    print(f"acceptance_status: {current_gate.get('acceptance_status', '')}")
    print(f"run_status: {current_gate.get('run_status', '')}")
    print(f"\n输出: {output_path}")

    if args.show_json:
        print("\n== JSON ==")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
