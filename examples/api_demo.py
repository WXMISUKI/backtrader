#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小 API 联调用例。

示例：
    python examples/api_demo.py --host 127.0.0.1 --port 8000 --user-input "帮我看下 000001 的市场状态"
"""

from __future__ import annotations

import argparse
import json
from urllib import error, request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal API demo for stock agent server.")
    parser.add_argument("--host", default="127.0.0.1", help="API host.")
    parser.add_argument("--port", type=int, default=8000, help="API port.")
    parser.add_argument(
        "--user-input",
        default="请分析 000001，并给出买入/卖出建议和持仓建议。",
        help="Prompt for /decision.",
    )
    parser.add_argument(
        "--risk-profile",
        default="moderate",
        choices=("conservative", "moderate", "aggressive"),
        help="Risk profile for /decision.",
    )
    parser.add_argument(
        "--submit-feedback",
        action="store_true",
        help="Submit feedback when decision response contains session_id.",
    )
    parser.add_argument(
        "--accepted",
        action="store_true",
        help="Feedback accepted flag when --submit-feedback is enabled.",
    )
    parser.add_argument("--rating", type=int, default=5, help="Feedback rating when --submit-feedback is enabled.")
    parser.add_argument("--comment", default="示例联调反馈", help="Feedback comment.")
    return parser


def _request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def _print_json(title: str, payload: dict) -> None:
    print(f"\n== {title} ==")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    args = build_parser().parse_args()
    base_url = f"http://{args.host}:{args.port}"

    try:
        health = _request_json("GET", f"{base_url}/health")
        _print_json("health", health)

        decision = _request_json(
            "POST",
            f"{base_url}/decision",
            {
                "user_input": args.user_input,
                "risk_profile": args.risk_profile,
            },
        )
        _print_json("decision", decision)

        if args.submit_feedback:
            session_id = str(decision.get("session_id", "") or "").strip()
            workflow_id = str(decision.get("workflow_id", "") or "").strip()
            if not session_id:
                print("\n跳过 feedback：decision 响应缺少 session_id。")
                return 0

            feedback_payload = {
                "session_id": session_id,
                "accepted": bool(args.accepted),
                "rating": int(args.rating),
                "reason": "",
                "correction": "",
                "comment": args.comment,
            }
            if workflow_id:
                feedback_payload["workflow_id"] = workflow_id

            feedback = _request_json("POST", f"{base_url}/feedback", feedback_payload)
            _print_json("feedback", feedback)

        return 0
    except error.URLError as exc:
        print(f"请求失败: {exc}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
