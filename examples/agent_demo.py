#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体接入演示

示例：
    python examples/agent_demo.py "帮我看下 000001 的市场状态"
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.agent import load_agent_settings, create_stock_agent_runtime


def main() -> int:
    settings = load_agent_settings()

    if not settings.has_api_key:
        print("未检测到 ARK_API_KEY，请先填写 .env")
        return 1

    question = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "请分析 000001，并给出买入/卖出建议和风险提示。"
    runtime = create_stock_agent_runtime(settings)
    answer = runtime.ask(question)
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
