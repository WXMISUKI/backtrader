#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
StockOrchestrator 演示。
"""

from __future__ import annotations

from core.orchestrator import create_stock_orchestrator


def main() -> int:
    orchestrator = create_stock_orchestrator()

    print(orchestrator.recommend(risk_profile="moderate", top_n=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

