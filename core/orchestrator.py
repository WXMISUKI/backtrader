#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
StockOrchestrator 统一编排入口

负责把项目现有业务能力收束为统一入口，避免上层直接拼接底层算法。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
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

    def route(self, user_input: str, **kwargs) -> dict:
        """
        根据自然语言意图路由到最合适的能力。

        该入口用于智能体或上层控制器直接调用。
        """
        text = user_input.strip()
        lower = text.lower()
        stock_code = self._extract_stock_code(text)
        risk_profile = kwargs.get("risk_profile", "moderate")

        if any(keyword in text for keyword in ["回测", "backtest"]):
            return self._dispatch(
                action="backtest",
                tool_name="run_backtest",
                arguments={
                    "stock_code": stock_code or kwargs.get("stock_code", "000001"),
                    "strategy_name": kwargs.get("strategy_name", "ma_cross"),
                    "start_date": kwargs.get("start_date", "20260101"),
                    "end_date": kwargs.get("end_date", "20260614"),
                    "initial_cash": kwargs.get("initial_cash", 100000),
                },
            )

        if any(keyword in text for keyword in ["市场", "大盘", "行情"]) or "market" in lower:
            return self.market_overview()

        if any(keyword in text for keyword in ["风控", "仓位", "风险"]):
            return self.risk_profile(risk_profile=risk_profile)

        if any(keyword in text for keyword in ["报告", "report"]):
            return self.report(stock_code=stock_code or kwargs.get("stock_code", "000001"), risk_profile=risk_profile)

        if any(keyword in text for keyword in ["推荐", "适合", "买什么", "买哪些", "配置"]):
            return self.recommend(risk_profile=risk_profile, top_n=int(kwargs.get("top_n", 5)))

        if any(keyword in text for keyword in ["分析", "建议", "买", "卖"]):
            return self.analyze(stock_code=stock_code or kwargs.get("stock_code", "000001"), risk_profile=risk_profile)

        return self.recommend(risk_profile=risk_profile, top_n=int(kwargs.get("top_n", 5)))

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

    def _extract_stock_code(self, text: str) -> Optional[str]:
        """从自然语言中提取股票代码。"""
        match = re.search(r"\b\d{6}\b", text)
        if match:
            return match.group(0)
        return None


def create_stock_orchestrator(tool_registry=None) -> StockOrchestrator:
    """创建统一编排器。"""
    return StockOrchestrator(tool_registry=tool_registry)
