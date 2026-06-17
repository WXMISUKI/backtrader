#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
StockOrchestrator 演示。
"""

from __future__ import annotations

from core.orchestrator import create_stock_orchestrator


def main() -> int:
    orchestrator = create_stock_orchestrator()

    print(orchestrator.route("请给我推荐几只适合稳健风格的股票，并说明数据来源", risk_profile="moderate", top_n=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
