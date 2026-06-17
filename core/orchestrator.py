#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
StockOrchestrator 统一编排入口

负责把项目现有业务能力收束为统一入口，避免上层直接拼接底层算法。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .agent import build_default_tool_registry


@dataclass(frozen=True)
class OrchestratorResult:
    """统一编排结果。"""

    ok: bool
    action: str
    tool: str
    category: str
    data_source: Optional[str]
    summary: str
    data: Any
    meta: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "action": self.action,
            "tool": self.tool,
            "category": self.category,
            "data_source": self.data_source,
            "summary": self.summary,
            "data": self.data,
            "meta": self.meta,
        }


class StockOrchestrator:
    """统一编排器。"""

    def __init__(self, tool_registry=None) -> None:
        self.tool_registry = tool_registry or build_default_tool_registry()

    def analyze(self, stock_code: str, risk_profile: str = "moderate") -> dict:
        """执行个股分析。"""
        return self._dispatch(
            action="analyze",
            tool_name="analyze_stock",
            arguments={
                "stock_code": stock_code,
                "risk_profile": risk_profile,
            },
        )

    def recommend(self, risk_profile: str = "moderate", top_n: int = 5) -> dict:
        """执行统一推荐。"""
        return self._dispatch(
            action="recommend",
            tool_name="recommend_by_risk",
            arguments={
                "risk_profile": risk_profile,
                "top_n": top_n,
            },
        )

    def market_overview(self) -> dict:
        """获取市场概览。"""
        return self._dispatch(
            action="market_overview",
            tool_name="get_market_overview",
            arguments={},
        )

    def risk_profile(self, risk_profile: str = "moderate") -> dict:
        """获取风险配置。"""
        return self._dispatch(
            action="risk_profile",
            tool_name="get_risk_profile",
            arguments={
                "risk_profile": risk_profile,
            },
        )

    def backtest(self, stock_code: str, strategy_name: str, **kwargs) -> dict:
        """执行回测。"""
        payload = {
            "stock_code": stock_code,
            "strategy_name": strategy_name,
        }
        payload.update(kwargs)
        return self._dispatch(
            action="backtest",
            tool_name="run_backtest",
            arguments=payload,
        )

    def report(self, stock_code: str, risk_profile: str = "moderate") -> dict:
        """生成报告。"""
        return self._dispatch(
            action="report",
            tool_name="generate_stock_report",
            arguments={
                "stock_code": stock_code,
                "risk_profile": risk_profile,
            },
        )

    def _dispatch(self, action: str, tool_name: str, arguments: dict) -> dict:
        tool_result = self.tool_registry.dispatch(tool_name, arguments)
        return OrchestratorResult(
            ok=bool(tool_result.get("ok", False)),
            action=action,
            tool=tool_result.get("tool", tool_name),
            category=tool_result.get("category", "analysis"),
            data_source=tool_result.get("data_source"),
            summary=tool_result.get("summary", ""),
            data=tool_result.get("data"),
            meta={
                **tool_result.get("meta", {}),
                "orchestrator": "StockOrchestrator",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        ).to_dict()


def create_stock_orchestrator(tool_registry=None) -> StockOrchestrator:
    """创建统一编排器。"""
    return StockOrchestrator(tool_registry=tool_registry)

