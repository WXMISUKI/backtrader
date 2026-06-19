#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目工具注册表

将现有分析/推荐/回测/风控能力暴露给智能体。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Dict, List

from .collaboration import build_collaboration_plan
from .workflow_templates import list_workflow_templates
from .workflow import execute_collaboration_workflow
from .serialization import build_tool_payload, serialize_value


@dataclass(frozen=True)
class ToolSpec:
    """单个工具定义。"""

    name: str
    description: str
    parameters: dict
    handler: Callable[[dict], dict]

    def to_openai_tool(self) -> dict:
        """转换为 OpenAI-compatible tools 结构。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ProjectToolRegistry:
    """项目工具注册表。"""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"未知工具: {name}")
        return self._tools[name]

    def list_tools(self) -> List[str]:
        return sorted(self._tools.keys())

    def to_openai_tools(self) -> List[dict]:
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def dispatch(self, name: str, arguments: Any) -> dict:
        """执行工具调用并返回标准响应。"""
        tool = self.get(name)

        if isinstance(arguments, str):
            arguments = arguments.strip()
            params = json.loads(arguments) if arguments else {}
        elif isinstance(arguments, dict):
            params = arguments
        else:
            params = {}

        result = tool.handler(params)
        if isinstance(result, dict) and {"ok", "tool", "data"}.issubset(result.keys()):
            return result
        return build_tool_payload(tool.name, result)


def _tool_response(name: str, data: Any, summary: str = "") -> dict:
    return build_tool_payload(name, data, summary)


def _wrap_governed_data(data: Any, *, source: str, is_degraded: bool = False, reason: str = "", quality: dict | None = None, meta: dict | None = None) -> dict:
    """统一包装治理信息。"""
    return {
        "data_source": source,
        "is_degraded": is_degraded,
        "reason": reason,
        "quality": quality or {},
        "meta": meta or {},
        "payload": serialize_value(data),
    }


def _wrap_tool_result(tool_name: str, data: Any, summary: str = "", *, source: str | None = None, is_degraded: bool = False, reason: str = "", quality: dict | None = None, meta: dict | None = None) -> dict:
    """统一构造智能体工具结果。"""
    wrapped = data
    if isinstance(data, dict) and {"data_source", "payload"}.issubset(data.keys()):
        wrapped = data
    elif source is not None or is_degraded or reason or quality or meta:
        wrapped = _wrap_governed_data(
            data,
            source=source or "unknown",
            is_degraded=is_degraded,
            reason=reason,
            quality=quality,
            meta=meta,
        )
    return build_tool_payload(tool_name, wrapped, summary)


def _register_project_tools(registry: ProjectToolRegistry) -> None:
    from backtest import run_backtest
    from core.data.real_provider import get_financial_indicators
    from core.risk import get_risk_manager
    from skills.stock_advisor import analyze as analyze_stock
    from skills.stock_fundamental import analyze_fundamental
    from skills.stock_market import get_market_overview
    from skills.stock_recommender import recommend_by_risk, recommend_long_term, recommend_short_term
    from skills.stock_report import generate_stock_report
    from skills.stock_selector import screen_stocks
    from skills.trading_advisor import analyze_stock as analyze_trading_stock

    registry.register(
        ToolSpec(
            name="list_project_tools",
            description="列出当前项目已暴露给智能体的工具。",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=lambda _params: _tool_response(
                "list_project_tools",
                {"tools": registry.list_tools()},
                "已返回项目工具列表。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="plan_collaboration",
            description="将用户需求拆解为主任务、支持任务和执行顺序，并在适合时匹配标准工作流模板。",
            parameters={
                "type": "object",
                "properties": {
                    "user_input": {"type": "string", "description": "用户的原始自然语言需求"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                },
                "required": ["user_input"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "plan_collaboration",
                build_collaboration_plan(
                    params["user_input"],
                    default_risk_profile=params.get("risk_profile", "moderate"),
                ).to_dict(),
                "已生成协作计划。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="list_workflow_templates",
            description="列出当前项目可复用的标准工作流模板，便于智能体选择和调试。",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=lambda _params: _tool_response(
                "list_workflow_templates",
                {"templates": list_workflow_templates()},
                "已返回标准工作流模板列表。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="execute_workflow",
            description="将用户需求先规划再执行，必要时自动匹配标准工作流模板，串联市场、风控、分析、回测和报告等能力。",
            parameters={
                "type": "object",
                "properties": {
                    "user_input": {"type": "string", "description": "用户的原始自然语言需求"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                },
                "required": ["user_input"],
                "additionalProperties": False,
            },
            handler=lambda params: execute_collaboration_workflow(
                params["user_input"],
                registry,
                default_risk_profile=params.get("risk_profile", "moderate"),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="analyze_stock",
            description="执行个股分析，返回技术信号、风险评估和投资建议。",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string", "description": "股票代码，例如 000001"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                    "start_date": {"type": "string", "description": "开始日期，格式 YYYYMMDD"},
                    "end_date": {"type": "string", "description": "结束日期，格式 YYYYMMDD"},
                },
                "required": ["stock_code"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "analyze_stock",
                analyze_stock(
                    params["stock_code"],
                    risk_profile=params.get("risk_profile", "moderate"),
                    start_date=params.get("start_date", "20260101"),
                    end_date=params.get("end_date", "20260614"),
                ).to_dict(),
                "已完成个股分析。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="analyze_fundamental",
            description="分析股票基本面，返回估值、盈利、成长和安全评分。",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string"},
                },
                "required": ["stock_code"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "analyze_fundamental",
                analyze_fundamental(params["stock_code"]).to_dict(),
                "已完成基本面分析。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_market_overview",
            description="获取当前市场概览，包括指数、热门板块和市场情绪。",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=lambda _params: _tool_response(
                "get_market_overview",
                _wrap_tool_result(
                    "get_market_overview",
                    get_market_overview().to_dict(),
                    "已返回市场概览。",
                    source="mock",
                    is_degraded=False,
                    reason="market overview currently uses mock baseline data",
                    quality={"ok": True, "reason": "ok"},
                    meta={"data_kind": "market_overview"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="recommend_long_term",
            description="生成长线推荐列表，适合基本面驱动的中长周期决策。",
            parameters={
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "recommend_long_term",
                _wrap_tool_result(
                    "recommend_long_term",
                    {
                        "mode": "long_term",
                        "risk_profile": "moderate",
                        "recommendations": [
                            item.to_dict() for item in recommend_long_term(int(params.get("top_n", 5)))
                        ],
                    },
                    "已生成长线推荐列表。",
                    source="mock",
                    reason="recommendation currently uses mock baseline data",
                    quality={"ok": True, "reason": "ok"},
                    meta={"data_kind": "recommendation"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="recommend_short_term",
            description="生成短线推荐列表，适合技术面驱动的短周期决策。",
            parameters={
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "recommend_short_term",
                _wrap_tool_result(
                    "recommend_short_term",
                    {
                        "mode": "short_term",
                        "risk_profile": "aggressive",
                        "recommendations": [
                            item.to_dict() for item in recommend_short_term(int(params.get("top_n", 5)))
                        ],
                    },
                    "已生成短线推荐列表。",
                    source="mock",
                    reason="recommendation currently uses mock baseline data",
                    quality={"ok": True, "reason": "ok"},
                    meta={"data_kind": "recommendation"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="recommend_by_risk",
            description="按风险偏好自动融合长线/短线推荐，作为统一推荐入口。",
            parameters={
                "type": "object",
                "properties": {
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                    "top_n": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "recommend_by_risk",
                _wrap_tool_result(
                    "recommend_by_risk",
                    {
                        "mode": "risk_aware",
                        "risk_profile": params.get("risk_profile", "moderate"),
                        "recommendations": [
                            item.to_dict()
                            for item in recommend_by_risk(params.get("risk_profile", "moderate"))[
                                : int(params.get("top_n", 5))
                            ]
                        ],
                    },
                    "已生成风险匹配推荐列表。",
                    source="mock",
                    reason="recommendation currently uses mock baseline data",
                    quality={"ok": True, "reason": "ok"},
                    meta={"data_kind": "recommendation"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="screen_stocks",
            description="根据条件筛选股票，返回候选股票列表。",
            parameters={
                "type": "object",
                "properties": {
                    "ma_cross": {"type": "boolean"},
                    "rsi_oversold": {"type": "boolean"},
                    "macd_cross": {"type": "boolean"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "screen_stocks",
                _wrap_tool_result(
                    "screen_stocks",
                    [item.to_dict() for item in screen_stocks(
                    ma_cross=bool(params.get("ma_cross", False)),
                    rsi_oversold=bool(params.get("rsi_oversold", False)),
                    macd_cross=bool(params.get("macd_cross", False)),
                    risk_profile=params.get("risk_profile", "moderate"),
                )],
                    "已完成选股筛选。",
                    source="mock",
                    reason="screening currently uses mock baseline data",
                    quality={"ok": True, "reason": "ok"},
                    meta={"data_kind": "screening"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="generate_stock_report",
            description="对指定股票生成结构化个股分析报告。",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["stock_code"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "generate_stock_report",
                _wrap_tool_result(
                    "generate_stock_report",
                    generate_stock_report(
                    analyze_stock(
                        params["stock_code"],
                        risk_profile=params.get("risk_profile", "moderate"),
                        start_date=params.get("start_date", "20260101"),
                        end_date=params.get("end_date", "20260614"),
                    )
                    ),
                    "已生成个股分析报告。",
                    source="analysis",
                    meta={"data_kind": "report"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="analyze_trading_decision",
            description="基于趋势、入场出场和风控逻辑生成交易决策。",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["stock_code"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "analyze_trading_decision",
                _wrap_tool_result(
                    "analyze_trading_decision",
                    analyze_trading_stock(
                    analyze_stock(
                        params["stock_code"],
                        risk_profile=params.get("risk_profile", "moderate"),
                        start_date=params.get("start_date", "20260101"),
                        end_date=params.get("end_date", "20260614"),
                    ).stock_data.df,
                    stock_code=params["stock_code"],
                    risk_profile=params.get("risk_profile", "moderate"),
                    ).summary(),
                    "已生成交易决策摘要。",
                    source="analysis",
                    meta={"data_kind": "trading_decision"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="run_backtest",
            description="对指定股票和策略执行回测，返回回测结果摘要。",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string"},
                    "strategy_name": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "initial_cash": {"type": "number"},
                },
                "required": ["stock_code", "strategy_name"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "run_backtest",
                _wrap_tool_result(
                    "run_backtest",
                    run_backtest(
                    stock_code=params["stock_code"],
                    strategy_name=params["strategy_name"],
                    start_date=params.get("start_date", "20260101"),
                    end_date=params.get("end_date", "20260614"),
                    initial_cash=float(params.get("initial_cash", 100000)),
                    ).to_dict(),
                    "已完成回测。",
                    source="real",
                    meta={"data_kind": "backtest"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_financial_indicators",
            description="获取真实财务指标数据，作为基本面分析的补充来源。",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string"},
                },
                "required": ["stock_code"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_financial_indicators",
                _wrap_tool_result(
                    "get_financial_indicators",
                    get_financial_indicators(params["stock_code"]).to_dict(),
                    "已返回财务指标。",
                    source="real",
                    meta={"data_kind": "financial_indicators"},
                ),
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_risk_profile",
            description="返回当前风险配置摘要。",
            parameters={
                "type": "object",
                "properties": {
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_risk_profile",
                _wrap_tool_result(
                    "get_risk_profile",
                    get_risk_manager(params.get("risk_profile", "moderate")).get_profile_summary(),
                    "已返回风险配置摘要。",
                    source="config",
                    reason="risk profile comes from config",
                    quality={"ok": True, "reason": "ok"},
                    meta={"data_kind": "risk_profile"},
                ),
            ),
        )
    )


def build_default_tool_registry() -> ProjectToolRegistry:
    """创建默认工具注册表。"""
    registry = ProjectToolRegistry()
    _register_project_tools(registry)
    return registry
