#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富真实联调脚本。

用途:
    1. 验证历史行情接口是否可用
    2. 验证实时行情接口是否可用
    3. 输出结构化结果，便于回传联调结论

示例:
    python examples/eastmoney_live_check.py --symbol 000001 --start-date 20260601 --end-date 20260614

可选:
    python examples/eastmoney_live_check.py --cookie-file .\\eastmoney.cookie
    python examples/eastmoney_live_check.py --cookie "key=value; key2=value2"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Eastmoney live validation helper.")
    parser.add_argument("--symbol", default="000001", help="Stock code, default 000001.")
    parser.add_argument("--start-date", default="20260601", help="History start date, YYYYMMDD.")
    parser.add_argument("--end-date", default="20260614", help="History end date, YYYYMMDD.")
    parser.add_argument("--page", type=int, default=1, help="Realtime quotes page.")
    parser.add_argument("--page-size", type=int, default=5, help="Realtime quotes page size.")
    parser.add_argument("--cookie", default="", help="Cookie string override.")
    parser.add_argument(
        "--cookie-text",
        default="",
        help="Raw cookie blob override. Supports semicolon format and browser-export tabular text.",
    )
    parser.add_argument("--cookie-file", default="", help="Read cookie string from file.")
    parser.add_argument("--skip-realtime", action="store_true", help="Skip realtime quotes check.")
    parser.add_argument("--skip-history", action="store_true", help="Skip history check.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def _parse_cookie_blob(cookie_blob: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    text = (cookie_blob or "").strip()
    if not text:
        return cookies

    for chunk in text.split(";"):
        part = chunk.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            cookies[key] = value

    if cookies:
        return cookies

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            columns = [col.strip() for col in line.split("\t")]
            if len(columns) >= 2 and columns[0] and columns[1]:
                cookies[columns[0]] = columns[1]
                continue
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                cookies[key] = value

    return cookies


def _load_cookie_from_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"cookie file not found: {p}")
    return p.read_text(encoding="utf-8").strip()


def _print_block(title: str, payload: Any, pretty: bool = True) -> None:
    print(f"\n== {title} ==")
    if pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(json.dumps(payload, ensure_ascii=False, default=str))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    cookie_value = args.cookie_text.strip() or args.cookie.strip()
    if not cookie_value and args.cookie_file:
        cookie_value = _load_cookie_from_file(args.cookie_file)
    if cookie_value:
        parsed = _parse_cookie_blob(cookie_value)
        if parsed:
            os.environ["EASTMONEY_COOKIE"] = "; ".join(f"{k}={v}" for k, v in parsed.items())
        else:
            os.environ["EASTMONEY_COOKIE"] = cookie_value

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        import eastmoney_config as ec
        from core.data.eastmoney_api import get_stock_hist, fetch_stock_hist_governed
    except Exception as exc:
        print(f"初始化失败: {exc}")
        return 1

    cookie_meta = {}
    try:
        cookie_meta = ec.get_eastmoney_cookie_meta()
    except Exception:
        cookie_meta = {
            "cookie_loaded": bool(os.getenv("EASTMONEY_COOKIE", "").strip()),
            "cookie_source": "unknown",
            "cookie_keys": [],
            "has_jsessionid": False,
            "has_ut": False,
        }

    results: dict[str, Any] = {
        "symbol": args.symbol,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "page": args.page,
        "page_size": args.page_size,
        "cookie_loaded": bool(cookie_meta.get("cookie_loaded", False)),
        "cookie_source": str(cookie_meta.get("cookie_source", "unknown")),
        "cookie_keys": cookie_meta.get("cookie_keys", []),
        "has_jsessionid": bool(cookie_meta.get("has_jsessionid", False)),
        "has_ut": bool(cookie_meta.get("has_ut", False)),
        "history": {},
        "realtime": {},
        "governed": {},
    }

    exit_code = 0

    if not args.skip_history:
        try:
            hist_df = get_stock_hist(
                symbol=args.symbol,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            governed = fetch_stock_hist_governed(
                symbol=args.symbol,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            history_payload = {
                "ok": True,
                "rows": int(len(hist_df)),
                "columns": list(hist_df.columns),
                "head": hist_df.head(2).reset_index().to_dict("records"),
                "tail": hist_df.tail(2).reset_index().to_dict("records"),
                "data_source": governed.get("data_source"),
                "reason": governed.get("reason", ""),
                "quality": governed.get("quality", {}),
                "failure_kind": governed.get("meta", {}).get("failure_kind", ""),
                "fallback_reason": governed.get("meta", {}).get("fallback_reason", ""),
            }
            governed_payload = {
                "ok": True,
                "data_source": governed.get("data_source"),
                "reason": governed.get("reason", ""),
                "quality": governed.get("quality", {}),
                "meta": governed.get("meta", {}),
            }
            results["history"] = history_payload
            results["governed"] = governed_payload
            _print_block("history", history_payload, pretty=args.pretty)
            _print_block("governed", governed_payload, pretty=args.pretty)
        except Exception as exc:
            exit_code = 1
            history_payload = {"ok": False, "error": str(exc)}
            results["history"] = history_payload
            _print_block("history", history_payload, pretty=args.pretty)

    if not args.skip_realtime:
        try:
            quotes = ec.get_realtime_quotes(page=args.page, page_size=args.page_size)
            realtime_payload = {
                "ok": True,
                "rows": int(len(quotes)),
                "columns": list(quotes.columns),
                "sample": quotes[["code", "name", "price", "change_pct"]].head(5).to_dict("records")
                if {"code", "name", "price", "change_pct"}.issubset(set(quotes.columns))
                else quotes.head(5).to_dict("records"),
            }
            results["realtime"] = realtime_payload
            _print_block("realtime", realtime_payload, pretty=args.pretty)
        except Exception as exc:
            exit_code = 1
            realtime_payload = {"ok": False, "error": str(exc)}
            results["realtime"] = realtime_payload
            _print_block("realtime", realtime_payload, pretty=args.pretty)

    _print_block("summary", results, pretty=args.pretty)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
