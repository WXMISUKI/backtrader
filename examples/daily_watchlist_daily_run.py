#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常生产运行守门入口。

用法：
    python examples/daily_watchlist_daily_run.py
    python examples/daily_watchlist_daily_run.py --archive-dir logs/daily_watchlist_archive
    python examples/daily_watchlist_daily_run.py --skip-view
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

from examples.env_guard import build_env_guard
from examples.watchlist_shared import build_daily_execution_brief, build_daily_prompt_context, build_daily_review_brief, build_daily_collaboration_pack, build_feedback_effect_brief, build_schedule_hint


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"
DEFAULT_PORTFOLIO_PATH = ROOT_DIR / "config" / "portfolio.json"
DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_PIPELINE_JSON = ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"
DEFAULT_FEEDBACK_PATH = ROOT_DIR / "logs" / "daily_watchlist_feedback.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily production runner for watchlist pipeline.")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH), help="Watchlist JSON file path.")
    parser.add_argument("--portfolio", default=str(DEFAULT_PORTFOLIO_PATH), help="Portfolio JSON file path.")
    parser.add_argument("--start-date", default="20260601", help="History start date, YYYYMMDD.")
    parser.add_argument("--end-date", default="20260614", help="History end date, YYYYMMDD.")
    parser.add_argument("--risk-profile", default="moderate", choices=("conservative", "moderate", "aggressive"))
    parser.add_argument("--limit", type=int, default=0, help="Limit number of watchlist items. 0 means no limit.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--skip-view", action="store_true", help="Skip the archive viewer after running.")
    parser.add_argument("--output-json", default=str(DEFAULT_PIPELINE_JSON), help="Pipeline JSON output path.")
    parser.add_argument("--run-status", default=str(DEFAULT_RUN_STATUS), help="Run status JSON output path.")
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


def _ensure_dict(payload: object) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


def _call_script(script: Path, args: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(script), *args]
    completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def _write_run_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)


def _derive_status(*, preflight_ok: bool, pipeline_ok: bool, archive_ok: bool, degraded: bool) -> str:
    if not preflight_ok or not pipeline_ok or not archive_ok:
        return "failed"
    if degraded:
        return "degraded"
    return "ok"


def _derive_preflight_status(*, code: int, counts: dict[str, Any]) -> str:
    if code != 0:
        return "failed"
    if int(counts.get("明显降级", 0) or 0) > 0:
        return "degraded"
    if int(counts.get("部分降级", 0) or 0) > 0:
        return "degraded"
    return "ok"


def _build_run_cadence(*, preflight_status: str, pipeline_status: str, archive_status: str, view_status: str) -> dict[str, Any]:
    steps = [
        {"name": "preflight", "status": preflight_status},
        {"name": "pipeline", "status": pipeline_status},
        {"name": "archive", "status": archive_status},
        {"name": "view", "status": view_status},
    ]
    statuses = [str(step["status"]) for step in steps]
    if "failed" in statuses:
        overall = "failed"
        summary_text = "运行节奏失败：至少有一步失败。"
    elif "degraded" in statuses:
        overall = "degraded"
        summary_text = "运行节奏可用但存在降级。"
    elif "skipped" in statuses:
        overall = "ok"
        summary_text = "今日运行节奏完整，但查看步骤已跳过。"
    else:
        overall = "ok"
        summary_text = "今日运行节奏完整：预检、执行、归档、查看都已完成。"

    if pipeline_status == "failed":
        next_step = "先看预检和执行输出，再确认数据或 cookie。"
    elif archive_status == "failed":
        next_step = "先补归档，再看 latest 留档。"
    elif view_status == "failed":
        next_step = "先看留档目录，再检查查看入口。"
    elif preflight_status != "ok":
        next_step = "先看数据健康，再继续后续入口。"
    else:
        next_step = "先看 production_gate，再看 action_list。"

    return {
        "status": overall,
        "steps": steps,
        "summary_text": summary_text,
        "next_step": next_step,
    }


def main() -> int:
    args = build_parser().parse_args()
    watchlist_path = Path(args.watchlist)
    portfolio_path = Path(args.portfolio)
    archive_dir = Path(args.archive_dir)
    output_json = Path(args.output_json)
    run_status_path = Path(args.run_status)
    feedback_records = _load_jsonl_payload(DEFAULT_FEEDBACK_PATH)
    env_guard = build_env_guard()

    timestamp = datetime.now().isoformat(timespec="seconds")
    preflight_script = ROOT_DIR / "examples" / "watchlist_data_health.py"
    pipeline_script = ROOT_DIR / "examples" / "daily_watchlist_pipeline.py"
    viewer_script = ROOT_DIR / "examples" / "daily_watchlist_archive_viewer.py"
    cookie_source = "unknown"
    cookie_loaded = False
    try:
        from eastmoney_config import get_eastmoney_cookie_meta

        cookie_meta = get_eastmoney_cookie_meta()
        cookie_source = str(cookie_meta.get("cookie_source", "unknown"))
        cookie_loaded = bool(cookie_meta.get("cookie_loaded", False))
    except Exception:
        cookie_source = "unknown"
        cookie_loaded = False

    preflight_args = [
        "--watchlist",
        str(watchlist_path),
        "--start-date",
        str(args.start_date),
        "--end-date",
        str(args.end_date),
        "--output-json",
        str(ROOT_DIR / "logs" / "daily_watchlist_preflight.json"),
    ]
    preflight_code, preflight_output = _call_script(preflight_script, preflight_args)
    preflight_payload = _load_json_payload(ROOT_DIR / "logs" / "daily_watchlist_preflight.json")
    preflight_ok = preflight_code == 0 and bool(preflight_payload)
    preflight_counts = preflight_payload.get("counts", {}) if isinstance(preflight_payload, dict) else {}
    preflight_status = _derive_preflight_status(code=preflight_code, counts=preflight_counts)

    pipeline_code = 1
    pipeline_output = ""
    pipeline_payload = {}
    archive_ok = False
    if preflight_ok:
        pipeline_args = [
            "--watchlist",
            str(watchlist_path),
            "--portfolio",
            str(portfolio_path),
            "--start-date",
            str(args.start_date),
            "--end-date",
            str(args.end_date),
            "--risk-profile",
            str(args.risk_profile),
            "--limit",
            str(args.limit),
            "--archive-dir",
            str(archive_dir),
            "--export-markdown",
            "--write-latest",
            "--archive-package",
            "--output-json",
            str(output_json),
        ]
        pipeline_code, pipeline_output = _call_script(pipeline_script, pipeline_args)
        pipeline_payload = _load_json_payload(output_json)
        archive_ok = pipeline_code == 0 and bool(pipeline_payload)

    view_code = 1
    view_output = ""
    if archive_ok and not args.skip_view:
        view_code, view_output = _call_script(
            viewer_script,
            ["--archive-dir", str(archive_dir), "--limit-lines", "12"],
        )

    degraded = bool(preflight_counts.get("部分降级", 0)) or bool(preflight_counts.get("明显降级", 0))
    preflight_status = preflight_status if "preflight_status" in locals() else "failed"
    pipeline_status = "ok" if archive_ok else "failed"
    archive_status = "ok" if archive_ok else "failed"
    view_status = "ok" if view_code == 0 else ("skipped" if args.skip_view else "failed")
    run_cadence = _build_run_cadence(
        preflight_status=preflight_status,
        pipeline_status=pipeline_status,
        archive_status=archive_status,
        view_status=view_status,
    )
    production_gate = _ensure_dict(pipeline_payload.get("production_gate", {}) if isinstance(pipeline_payload, dict) else {})
    action_list = _ensure_dict(pipeline_payload.get("action_list", {}) if isinstance(pipeline_payload, dict) else {})
    daily_summary = _ensure_dict(pipeline_payload.get("daily_summary", {}) if isinstance(pipeline_payload, dict) else {})
    diagnosis_evidence = _ensure_dict(pipeline_payload.get("diagnosis_evidence", {}) if isinstance(pipeline_payload, dict) else {})
    run_cadence = _ensure_dict(pipeline_payload.get("run_cadence", {}) if isinstance(pipeline_payload, dict) else {})
    prompt_context = _ensure_dict(pipeline_payload.get("prompt_context", {}) if isinstance(pipeline_payload, dict) else {})
    review_brief = _ensure_dict(pipeline_payload.get("review_brief", {}) if isinstance(pipeline_payload, dict) else {})
    schedule_hint = _ensure_dict(pipeline_payload.get("schedule_hint", {}) if isinstance(pipeline_payload, dict) else {})
    daily_collaboration_pack = _ensure_dict(pipeline_payload.get("daily_collaboration_pack", {}) if isinstance(pipeline_payload, dict) else {})
    daily_execution_brief = _ensure_dict(pipeline_payload.get("daily_execution_brief", {}) if isinstance(pipeline_payload, dict) else {})
    feedback_effects = _load_json_payload(ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json")
    feedback_effect_brief = build_feedback_effect_brief(feedback_effects=feedback_effects if isinstance(feedback_effects, dict) else {})
    if not prompt_context:
        prompt_context = build_daily_prompt_context(
            production_gate=production_gate,
            action_list=action_list,
            run_cadence=run_cadence,
            daily_summary=daily_summary,
            diagnosis_evidence=diagnosis_evidence,
        )
    if not review_brief:
        review_brief = build_daily_review_brief(
            daily_summary=daily_summary,
            production_gate=production_gate,
            action_list=action_list,
            run_cadence=run_cadence,
            prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
            feedback_effects=feedback_effects if isinstance(feedback_effects, dict) else {},
            feedback_effect_brief=feedback_effect_brief if isinstance(feedback_effect_brief, dict) else {},
        )
    status = _derive_status(
        preflight_ok=preflight_ok,
        pipeline_ok=archive_ok,
        archive_ok=archive_ok,
        degraded=degraded,
    )
    if not schedule_hint:
        schedule_hint = build_schedule_hint(
            daily_run_status=status,
            production_gate=production_gate,
            run_cadence=run_cadence,
            prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
            review_brief=review_brief if isinstance(review_brief, dict) else {},
        )
    if not daily_collaboration_pack:
        daily_collaboration_pack = build_daily_collaboration_pack(
            production_gate=production_gate,
            action_list=action_list,
            run_cadence=run_cadence,
            prompt_context=prompt_context if isinstance(prompt_context, dict) else {},
            review_brief=review_brief if isinstance(review_brief, dict) else {},
            schedule_hint=schedule_hint if isinstance(schedule_hint, dict) else {},
        )
    if not daily_execution_brief:
        daily_execution_brief = build_daily_execution_brief(
            production_gate=production_gate,
            action_list=action_list,
            run_cadence=run_cadence,
            review_brief=review_brief if isinstance(review_brief, dict) else {},
            schedule_hint=schedule_hint if isinstance(schedule_hint, dict) else {},
            daily_collaboration_pack=daily_collaboration_pack if isinstance(daily_collaboration_pack, dict) else {},
            feedback_effect_brief=feedback_effect_brief if isinstance(feedback_effect_brief, dict) else {},
        )

    run_status = {
        "status": status,
        "generated_at": timestamp,
        "env_guard": env_guard,
        "watchlist_path": str(watchlist_path),
        "portfolio_path": str(portfolio_path),
        "archive_dir": str(archive_dir),
        "pipeline_output": str(output_json),
        "latest_json": str(archive_dir / "latest.json"),
        "latest_md": str(archive_dir / "latest.md"),
        "preflight": {
            "ok": preflight_ok,
            "code": preflight_code,
            "status": preflight_status,
            "counts": preflight_counts,
        },
        "pipeline": {
            "ok": archive_ok,
            "code": pipeline_code,
            "daily_summary": pipeline_payload.get("daily_summary", {}) if isinstance(pipeline_payload, dict) else {},
            "archive_package": bool(pipeline_payload.get("archive_package")) if isinstance(pipeline_payload, dict) else False,
        },
        "cookie": {
            "loaded": cookie_loaded,
            "source": cookie_source,
        },
        "summary": {
            "message": "预检通过并已完成归档。" if status == "ok" else ("存在降级，但已完成归档。" if status == "degraded" else "预检或执行失败。"),
            "feedback_count": len(feedback_records),
        },
        "run_cadence": run_cadence,
        "prompt_context": prompt_context,
        "review_brief": review_brief,
        "feedback_effect_brief": feedback_effect_brief,
        "schedule_hint": schedule_hint,
        "daily_collaboration_pack": daily_collaboration_pack,
        "daily_execution_brief": daily_execution_brief,
        "outputs": {
            "preflight_output": preflight_output.strip(),
            "pipeline_output": pipeline_output.strip(),
            "view_output": view_output.strip(),
        },
    }
    _write_run_status(run_status_path, run_status)

    print("== 自选股日常生产运行守门 ==")
    print(f"状态: {status}")
    print(f"环境门禁: {env_guard['summary_text']}")
    print(f"预检: {'通过' if preflight_ok else '失败'}")
    print(f"执行: {'成功' if archive_ok else '失败'}")
    print(f"东财 Cookie: {'已加载' if cookie_loaded else '未加载'} ({cookie_source})")
    print(f"反馈记录: {len(feedback_records)} 条")
    print(f"归档目录: {archive_dir}")
    print(f"运行状态: {run_status_path}")
    print(f"查看入口: {viewer_script}")
    print(f"运行节奏: {run_cadence['summary_text']}")
    print(f"提示语境: {prompt_context['summary_text']}")
    print(f"回看摘要: {review_brief['summary_text']}")
    print(f"反馈覆盖: {feedback_effect_brief['coverage_summary']}")
    print(f"反馈稳定性: {feedback_effect_brief['stability_note']}")
    print(f"反馈效果: {feedback_effect_brief['summary_text']}")
    print(f"调度准备: {schedule_hint['summary_text']}")
    print(f"协作总包: {daily_collaboration_pack['summary_text']}")
    print(f"执行简报: {daily_execution_brief['headline']} / {daily_execution_brief['summary_text']}")
    print(f"下一步: {run_cadence['next_step']}")
    print(f"下次运行模式: {schedule_hint['next_run_mode']}")
    print(f"下次运行窗口: {schedule_hint['next_run_window']}")

    if not args.skip_view and archive_ok:
        print("\n== 留档查看 ==")
        print(view_output.strip())
        if view_code != 0:
            print("查看入口执行失败。")

    if not preflight_ok:
        return 1
    if not archive_ok:
        return 1
    return 0 if status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
