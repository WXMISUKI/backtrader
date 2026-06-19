#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目级最小命令行入口。

用于快速启动统一 HTTP API，保持启动路径极薄，不引入额外框架。
"""

from __future__ import annotations

import argparse
import os
from typing import Sequence

from .api_server import run_agent_api_server


def build_parser() -> argparse.ArgumentParser:
    """构建最小 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="stock-agent-api",
        description="Start the minimal stock agent HTTP API server.",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("STOCK_AGENT_API_HOST", "127.0.0.1"),
        help="Bind host. Defaults to STOCK_AGENT_API_HOST or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("STOCK_AGENT_API_PORT", "8000")),
        help="Bind port. Defaults to STOCK_AGENT_API_PORT or 8000.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 入口。"""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    run_agent_api_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
