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


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"
DEFAULT_PORTFOLIO_PATH = ROOT_DIR / "config" / "portfolio.json"
DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_PIPELINE_JSON = ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"


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


def main() -> int:
    args = build_parser().parse_args()
    watchlist_path = Path(args.watchlist)
    portfolio_path = Path(args.portfolio)
    archive_dir = Path(args.archive_dir)
    output_json = Path(args.output_json)
    run_status_path = Path(args.run_status)

    timestamp = datetime.now().isoformat(timespec="seconds")
    preflight_script = ROOT_DIR / "examples" / "watchlist_data_health.py"
    pipeline_script = ROOT_DIR / "examples" / "daily_watchlist_pipeline.py"
    viewer_script = ROOT_DIR / "examples" / "daily_watchlist_archive_viewer.py"

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

    degraded = bool(preflight_counts.get("部分降级", 0)) or bool(preflight_counts.get("明显降级", 0))
    status = _derive_status(
        preflight_ok=preflight_ok,
        pipeline_ok=archive_ok,
        archive_ok=archive_ok,
        degraded=degraded,
    )

    run_status = {
        "status": status,
        "generated_at": timestamp,
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
        "summary": {
            "message": "预检通过并已完成归档。" if status == "ok" else ("存在降级，但已完成归档。" if status == "degraded" else "预检或执行失败。"),
        },
        "outputs": {
            "preflight_output": preflight_output.strip(),
            "pipeline_output": pipeline_output.strip(),
        },
    }
    _write_run_status(run_status_path, run_status)

    print("== 自选股日常生产运行守门 ==")
    print(f"状态: {status}")
    print(f"预检: {'通过' if preflight_ok else '失败'}")
    print(f"执行: {'成功' if archive_ok else '失败'}")
    print(f"归档目录: {archive_dir}")
    print(f"运行状态: {run_status_path}")
    print(f"查看入口: {viewer_script}")

    if not args.skip_view and archive_ok:
        view_code, view_output = _call_script(
            viewer_script,
            ["--archive-dir", str(archive_dir), "--limit-lines", "12"],
        )
        print("\n== 留档查看 ==")
        print(view_output.strip())
        if view_code != 0:
            print("查看入口执行失败。")

    if not preflight_ok:
        return 1
    if not archive_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
