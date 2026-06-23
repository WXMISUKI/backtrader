#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富 cookie 刷新助手。

用途：
    1. 从 cookie 文本或文件中标准化 cookie
    2. 可选写入项目根目录 .env
    3. 可选顺手跑一次历史行情 smoke test
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Eastmoney cookie refresh helper.")
    parser.add_argument("--cookie", default="", help="Cookie string override.")
    parser.add_argument("--cookie-text", default="", help="Raw cookie blob override.")
    parser.add_argument("--cookie-file", default="", help="Read cookie string from file.")
    parser.add_argument("--persist", action="store_true", help="Write normalized cookie into project .env.")
    parser.add_argument("--smoke-test", action="store_true", help="Run a history smoke test after refresh.")
    parser.add_argument("--symbol", default="000001", help="Smoke test stock code.")
    parser.add_argument("--start-date", default="20260601", help="Smoke test history start date.")
    parser.add_argument("--end-date", default="20260614", help="Smoke test history end date.")
    return parser


def _load_cookie_text(args: argparse.Namespace) -> str:
    cookie_value = args.cookie_text.strip() or args.cookie.strip()
    if cookie_value:
        return cookie_value
    if args.cookie_file:
        from core.data.eastmoney_cookie_tools import load_cookie_file

        return load_cookie_file(args.cookie_file)
    return ""


def _persist_cookie(cookie_string: str) -> Path:
    env_path = ROOT_DIR / ".env"
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("EASTMONEY_COOKIE="):
            new_lines.append(f"EASTMONEY_COOKIE={cookie_string}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"EASTMONEY_COOKIE={cookie_string}")
    env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    return env_path


def main() -> int:
    args = build_parser().parse_args()
    cookie_text = _load_cookie_text(args)
    if not cookie_text:
        print("未提供 cookie 内容。")
        return 1

    from core.data.eastmoney_cookie_tools import format_cookie_string, parse_cookie_blob

    parsed = parse_cookie_blob(cookie_text)
    if not parsed:
        print("cookie 内容无法解析。")
        return 1

    cookie_string = format_cookie_string(parsed)
    os.environ["EASTMONEY_COOKIE"] = cookie_string
    print(f"已标准化 cookie，键数量: {len(parsed)}")
    print(f"cookie 预览: {list(parsed.keys())[:10]}")

    if args.persist:
        env_path = _persist_cookie(cookie_string)
        print(f"已写入: {env_path}")

    if args.smoke_test:
        root = ROOT_DIR
        import sys

        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from core.data.eastmoney_api import fetch_stock_hist_governed

        result = fetch_stock_hist_governed(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        print(
            {
                "data_source": result.get("data_source"),
                "selected_provider": result.get("meta", {}).get("selected_provider"),
                "failure_kind": result.get("meta", {}).get("failure_kind"),
                "failure_stage": result.get("meta", {}).get("failure_stage"),
                "failure_code": result.get("meta", {}).get("failure_code"),
                "fallback_strategy": result.get("meta", {}).get("fallback_strategy"),
            }
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
