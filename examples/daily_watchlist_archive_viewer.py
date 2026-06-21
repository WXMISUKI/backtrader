#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常留档查看入口。

用法：
    python examples/daily_watchlist_archive_viewer.py
    python examples/daily_watchlist_archive_viewer.py --archive-dir logs/daily_watchlist_archive
    python examples/daily_watchlist_archive_viewer.py --show-markdown
    python examples/daily_watchlist_archive_viewer.py --show-json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.daily_watchlist_display import print_bullets, print_kv_pairs, print_section
from examples.watchlist_shared import build_daily_prompt_context, build_daily_review_brief, build_diagnosis_evidence, build_production_gate


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_FEEDBACK_PATH = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"
DEFAULT_EFFECTS_JSON = ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json"
DEFAULT_FLOW_JSON = ROOT_DIR / "logs" / "daily_watchlist_flow.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily archive viewer for watchlist pipeline.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--show-markdown", action="store_true", help="Print the latest Markdown document if available.")
    parser.add_argument("--show-json", action="store_true", help="Print the latest JSON payload.")
    parser.add_argument("--limit-lines", type=int, default=24, help="Limit number of lines in concise text output.")
    return parser


def _load_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
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


def _find_latest_run(archive_dir: Path) -> tuple[Path | None, Path | None]:
    latest_json = archive_dir / "latest.json"
    latest_md = archive_dir / "latest.md"
    if latest_json.exists() or latest_md.exists():
        return (latest_json if latest_json.exists() else None, latest_md if latest_md.exists() else None)

    dated_dirs = sorted((path for path in archive_dir.iterdir() if path.is_dir()), reverse=True) if archive_dir.exists() else []
    for run_dir in dated_dirs:
        json_files = sorted(run_dir.glob("*.json"), reverse=True)
        md_files = sorted(run_dir.glob("*.md"), reverse=True)
        if json_files or md_files:
            return (json_files[0] if json_files else None, md_files[0] if md_files else None)
    return None, None


def _shorten_lines(text: str, limit: int) -> str:
    lines = text.splitlines()
    if limit > 0 and len(lines) > limit:
        return "\n".join(lines[:limit] + ["..."])
    return text


def _print_concise_summary(payload: dict[str, Any], json_path: Path | None, md_path: Path | None, limit_lines: int) -> None:
    daily_summary = payload.get("daily_summary", {}) if isinstance(payload, dict) else {}
    daily_report = payload.get("daily_report", {}) if isinstance(payload, dict) else {}
    daily_comparison = payload.get("daily_comparison", {}) if isinstance(payload, dict) else {}
    weekly_report = payload.get("weekly_report", {}) if isinstance(payload, dict) else {}
    stage_report = payload.get("stage_report", {}) if isinstance(payload, dict) else {}
    archive_package = payload.get("archive_package", {}) if isinstance(payload, dict) else {}
    production_gate = payload.get("production_gate", {}) if isinstance(payload, dict) else {}
    action_list = payload.get("action_list", {}) if isinstance(payload, dict) else {}
    run_cadence = payload.get("run_cadence", {}) if isinstance(payload, dict) else {}
    prompt_context = payload.get("prompt_context", {}) if isinstance(payload, dict) else {}
    portfolio_summary = payload.get("portfolio_summary", {}) if isinstance(payload, dict) else {}
    health_items = payload.get("health", {}).get("items", []) if isinstance(payload, dict) else []
    diagnosis_evidence = build_diagnosis_evidence(daily_summary=daily_summary, health_items=health_items if isinstance(health_items, list) else [])
    flow_payload = _load_json_payload(DEFAULT_FLOW_JSON)
    if not production_gate:
        acceptance_payload = _load_json_payload(DEFAULT_ACCEPTANCE_JSON)
        action_list = flow_payload.get("pipeline_payload", {}).get("action_list", action_list) if isinstance(flow_payload, dict) else action_list
        run_cadence = flow_payload.get("run_cadence", {}) if isinstance(flow_payload, dict) else run_cadence
        if not isinstance(run_cadence, dict) or not run_cadence:
            daily_run_status_payload = flow_payload.get("daily_run_status_payload", {}) if isinstance(flow_payload, dict) else {}
            run_cadence = daily_run_status_payload.get("run_cadence", {}) if isinstance(daily_run_status_payload, dict) else {}
        production_gate = build_production_gate(
            daily_summary=flow_payload.get("pipeline_payload", {}).get("daily_summary", daily_summary)
            if isinstance(flow_payload, dict)
            else daily_summary,
            diagnosis_evidence=diagnosis_evidence,
            acceptance=acceptance_payload,
            health_items=health_items if isinstance(health_items, list) else [],
            daily_run_status=str(flow_payload.get("daily_run_status", "")) if isinstance(flow_payload, dict) else "",
        )
    if not isinstance(run_cadence, dict) or not run_cadence:
        if isinstance(flow_payload, dict) and flow_payload:
            run_cadence = flow_payload.get("run_cadence", {})
            if not isinstance(run_cadence, dict) or not run_cadence:
                daily_run_status_payload = flow_payload.get("daily_run_status_payload", {}) if isinstance(flow_payload, dict) else {}
                run_cadence = daily_run_status_payload.get("run_cadence", {}) if isinstance(daily_run_status_payload, dict) else {}
    if not isinstance(prompt_context, dict) or not prompt_context:
        prompt_context = build_daily_prompt_context(
            production_gate=production_gate if isinstance(production_gate, dict) else {},
            action_list=action_list if isinstance(action_list, dict) else {},
            run_cadence=run_cadence if isinstance(run_cadence, dict) else {},
            daily_summary=daily_summary if isinstance(daily_summary, dict) else {},
            diagnosis_evidence=diagnosis_evidence,
        )
    feedback_records = _load_jsonl_payload(DEFAULT_FEEDBACK_PATH)
    effects_payload = _load_json_payload(DEFAULT_EFFECTS_JSON)
    review_brief = build_daily_review_brief(
        daily_summary=daily_summary,
        production_gate=production_gate,
        action_list=action_list,
        run_cadence=run_cadence,
        prompt_context=prompt_context,
        feedback_effects=effects_payload,
    )

    print_section("自选股日常留档查看")
    print_kv_pairs(
        [
            ("归档JSON", json_path or "未找到"),
            ("归档Markdown", md_path or "未找到"),
            ("生成时间", payload.get("generated_at", "")),
            ("回看摘要", review_brief.get("summary_text", "")),
            ("日常总览", daily_summary.get("status", "")),
            ("投产门禁", production_gate.get("status", "")),
            ("门禁摘要", production_gate.get("summary", "")),
            ("诊断摘要", diagnosis_evidence.get("summary_text", "")),
            (
                "持仓摘要",
                f"数量 {portfolio_summary.get('count', 0)}，市值 {portfolio_summary.get('market_value', 0.0):.2f}，总资产 {portfolio_summary.get('total_assets', 0.0):.2f}",
            ),
            ("最近反馈", f"{len(feedback_records)} 条"),
            (
                "反馈效果",
                f"命中率 {effects_payload.get('overall', {}).get('hit_rate', 0.0):.1%}，"
                f"平均回报 {effects_payload.get('overall', {}).get('avg_return', 0.0):.1%}",
            ),
            ("行动清单", action_list.get("summary_text", "")),
            ("运行节奏", run_cadence.get("summary_text", "")),
            ("下一步", run_cadence.get("next_step", "")),
            ("提示语境", prompt_context.get("summary_text", "")),
        ]
    )
    if feedback_records:
        print_bullets(
            [
                f"{item.get('stock_code', '')} {item.get('stock_name', '')} [{item.get('feedback', '')}] {item.get('comment', '')}"
                for item in feedback_records[-3:]
            ]
        )

    print_section("日更报告")
    print(_shorten_lines(str(daily_report.get("report_text", "") or "未提供"), limit_lines))

    if daily_comparison and daily_comparison.get("summary_text"):
        print_section("日报对比")
        print(daily_comparison.get("summary_text", ""))

    if weekly_report and weekly_report.get("report_text"):
        print_section("周报模板")
        print(_shorten_lines(str(weekly_report.get("report_text", "")), limit_lines))

    if stage_report and stage_report.get("report_text"):
        print_section("阶段报告模板")
        print(_shorten_lines(str(stage_report.get("report_text", "")), limit_lines))

    if archive_package and archive_package.get("report_text"):
        print_section("复盘留档包")
        print(_shorten_lines(str(archive_package.get("report_text", "")), limit_lines))

    if diagnosis_evidence.get("top_causes"):
        print_section("诊断证据")
        print_bullets([f"{cause} {count}" for cause, count in diagnosis_evidence.get("top_causes", [])])
        samples = diagnosis_evidence.get("sample_items", [])
        if samples:
            print_bullets([f"{item.get('stock_code', '')} {item.get('name', '')} [{item.get('status', '')}] {item.get('primary_label', '')}" for item in samples])

    if diagnosis_evidence.get("sample_attribution"):
        print_section("样本归因")
        for group in diagnosis_evidence.get("sample_attribution", [])[:5]:
            print(f"- {group.get('cause', '')} {group.get('count', 0)}: {group.get('summary', '')}")
            examples = group.get("examples", [])
            if examples:
                print_bullets([f"{item.get('stock_code', '')} {item.get('name', '')} [{item.get('primary_label', '')}]" for item in examples])

    if effects_payload:
        print_section("反馈效果")
        overall = effects_payload.get("overall", {}) if isinstance(effects_payload, dict) else {}
        print_kv_pairs(
            [
                ("可用反馈", overall.get("usable_feedback", 0)),
                ("评估行数", overall.get("evaluated_rows", 0)),
                ("平均回报", f"{overall.get('avg_return', 0.0):.1%}"),
                ("命中率", f"{overall.get('hit_rate', 0.0):.1%}"),
            ]
        )

    if isinstance(action_list, dict) and action_list.get("items"):
        print_section("行动清单")
        print_bullets(
            [
                f"{item.get('stock_code', '')} {item.get('name', '')} [{item.get('action', '')}] {item.get('action_hint', '')}；{item.get('reason', '')}"
                for item in action_list.get("items", [])[:8]
            ]
        )

    if isinstance(prompt_context, dict) and prompt_context.get("rules"):
        print_section("提示语境")
        print_bullets([str(rule) for rule in prompt_context.get("rules", [])[:6]])

    if isinstance(review_brief, dict) and review_brief.get("key_points"):
        print_section("回看重点")
        print_bullets([str(item) for item in review_brief.get("key_points", [])[:6]])


def main() -> int:
    args = build_parser().parse_args()
    archive_dir = Path(args.archive_dir)
    json_path, md_path = _find_latest_run(archive_dir)

    payload = _load_json_payload(json_path) if json_path is not None else {}
    _print_concise_summary(payload, json_path, md_path, args.limit_lines)

    if args.show_json and json_path is not None:
        print("\n== latest.json ==")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    if args.show_markdown and md_path is not None and md_path.exists():
        print("\n== latest.md ==")
        print(md_path.read_text(encoding="utf-8"))

    if not payload and json_path is None and md_path is None:
        print("\n未找到任何日常留档结果。")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
