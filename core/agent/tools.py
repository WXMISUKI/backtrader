#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目工具注册表

将现有分析/推荐/回测/风控能力暴露给智能体。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Callable, Dict, List

from .collaboration import build_collaboration_plan
from .capability_directory import list_capability_directory
from .replay import get_workflow_learning_stats, get_workflow_replay
from .session import create_decision_session, get_decision_session_replay, get_decision_session_stats, submit_decision_feedback
from .template_metrics import get_workflow_template_stats
from .workflow_templates import list_workflow_templates
from .workflow import execute_collaboration_workflow
from .serialization import build_tool_payload, serialize_value
from core.model import get_model_governance_service
from core.observability import (
    evaluate_runtime_health as evaluate_runtime_health_snapshot,
    get_observability_service,
    get_runtime_health as get_runtime_health_snapshot,
)


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
        observability = get_observability_service()

        if isinstance(arguments, str):
            arguments = arguments.strip()
            params = json.loads(arguments) if arguments else {}
        elif isinstance(arguments, dict):
            params = arguments
        else:
            params = {}

        started_at = time.perf_counter()
        try:
            result = tool.handler(params)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            category = _tool_category(tool.name)
            observability.record_metric(
                "tool.failure_count",
                1,
                source=tool.name,
                category=category,
                labels={"status": "exception"},
                meta={"error": str(exc)},
            )
            observability.record_latency(
                tool.name,
                duration_ms,
                source=tool.name,
                category=category,
                labels={"status": "exception", "tool": tool.name},
                meta={"error": str(exc)},
            )
            observability.record_runtime_event(
                "tool.dispatch",
                status="failed",
                source=tool.name,
                category=category,
                duration_ms=duration_ms,
                message=f"工具执行失败: {exc}",
                meta={
                    "tool": tool.name,
                    "arguments_keys": list(params.keys()),
                    "error": str(exc),
                },
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        if isinstance(result, dict) and {"ok", "tool", "data"}.issubset(result.keys()):
            payload = result
        else:
            payload = build_tool_payload(tool.name, result)

        category = str(payload.get("category") or _tool_category(tool.name))
        data_source = payload.get("data_source")
        ok = bool(payload.get("ok", False))
        degraded = bool(payload.get("meta", {}).get("is_degraded")) or data_source in {"mock", "fallback"}
        status = "failed" if not ok else ("degraded" if degraded else "ok")

        observability.record_metric(
            "tool.call_count",
            1,
            source=tool.name,
            category=category,
            labels={"status": status},
            meta={"tool": tool.name},
        )
        if ok:
            observability.record_metric(
                "tool.success_count",
                1,
                source=tool.name,
                category=category,
                labels={"status": status},
                meta={"tool": tool.name},
            )
        else:
            observability.record_metric(
                "tool.failure_count",
                1,
                source=tool.name,
                category=category,
                labels={"status": status},
                meta={"tool": tool.name},
            )
        if degraded and ok:
            observability.record_metric(
                "tool.degraded_count",
                1,
                source=tool.name,
                category=category,
                labels={"status": status},
                meta={"tool": tool.name},
            )
        observability.record_latency(
            tool.name,
            duration_ms,
            source=tool.name,
            category=category,
            labels={"status": status, "tool": tool.name},
            meta={"tool": tool.name},
        )
        observability.record_runtime_event(
            "tool.dispatch",
            status=status,
            source=tool.name,
            category=category,
            duration_ms=duration_ms,
            data_source=data_source,
            message=str(payload.get("summary", "")),
            meta={
                "tool": tool.name,
                "category": category,
                "ok": ok,
                "degraded": degraded,
                "arguments_keys": list(params.keys()),
                "summary": payload.get("summary", ""),
            },
        )
        return payload


def _tool_response(name: str, data: Any, summary: str = "") -> dict:
    return build_tool_payload(name, data, summary)


def _runtime_tool_response(name: str, data: Any, summary: str = "", *, ok: Optional[bool] = None) -> dict:
    payload = build_tool_payload(name, data, summary)
    if ok is not None:
        payload["ok"] = bool(ok)
    return payload


def _tool_category(tool_name: str) -> str:
    """推断工具分类，供监控埋点使用。"""
    if tool_name in {"plan_collaboration", "execute_workflow", "answer_decision_request", "list_workflow_templates", "get_workflow_template_stats", "get_workflow_replay", "get_workflow_learning_stats", "create_decision_session", "submit_decision_feedback", "get_decision_session_replay", "get_decision_session_stats", "list_project_capabilities"}:
        return "workflow"
    if tool_name in {"list_project_tools"}:
        return "knowledge_base"
    if tool_name in {"get_model_governance_status", "evaluate_model_release"}:
        return "model"
    if tool_name in {"run_backtest"}:
        return "backtest"
    if tool_name in {"recommend_long_term", "recommend_short_term", "recommend_by_risk"}:
        return "recommendation"
    if tool_name in {"get_market_overview"}:
        return "market"
    if tool_name in {"get_risk_profile"}:
        return "risk"
    if tool_name in {"get_runtime_health", "evaluate_runtime_health"}:
        return "observability"
    if tool_name in {"generate_stock_report"}:
        return "report"
    return "analysis"


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

    def _get_runtime_health(params: dict) -> dict:
        return _runtime_tool_response(
            "get_runtime_health",
            get_runtime_health_snapshot(
                window_size=int(params.get("window_size", 50) or 50),
                category=params.get("category"),
                tool_name=params.get("tool_name"),
            ),
            "已返回运行健康状态。",
            ok=True,
        )

    def _evaluate_runtime_health(params: dict) -> dict:
        evaluation = evaluate_runtime_health_snapshot(
            window_size=int(params.get("window_size", 50) or 50),
            category=params.get("category"),
            tool_name=params.get("tool_name"),
            thresholds=params.get("thresholds") or {},
        )
        return _runtime_tool_response(
            "evaluate_runtime_health",
            evaluation,
            "已完成运行健康评估。",
            ok=evaluation.get("status", "ok") != "critical",
        )

    def _answer_decision_request(params: dict) -> dict:
        from core.orchestrator import StockOrchestrator

        orchestrator = StockOrchestrator(tool_registry=registry)
        return _tool_response(
            "answer_decision_request",
            orchestrator.answer_decision_request(
                str(params["user_input"]),
                risk_profile=params.get("risk_profile", "moderate"),
            ),
            "已返回统一决策结果。",
        )

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
            name="list_project_capabilities",
            description="查看当前项目面向智能体的能力目录、推荐路径和回退路径。适合回答项目能做什么、该先用哪个入口、下一步该怎么走。",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=lambda _params: _tool_response(
                "list_project_capabilities",
                list_capability_directory(),
                "已返回项目能力目录。",
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
            name="answer_decision_request",
            description="统一决策入口：根据用户问题自动路由、执行并返回业务可读结果，同时创建决策会话。",
            parameters={
                "type": "object",
                "properties": {
                    "user_input": {"type": "string", "description": "用户的原始自然语言问题"},
                    "risk_profile": {"type": "string", "enum": ["conservative", "moderate", "aggressive"]},
                },
                "required": ["user_input"],
                "additionalProperties": False,
            },
            handler=_answer_decision_request,
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
            name="get_workflow_template_stats",
            description="查看标准工作流模板的命中统计、最近命中和选择来源分布。",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_workflow_template_stats",
                get_workflow_template_stats(int(params.get("limit", 20) or 20)),
                "已返回标准工作流模板统计。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_workflow_replay",
            description="按 workflow_id 回放任务链路，查看规划、步骤、结果和模板命中。",
            parameters={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string", "description": "workflow_id 或回放标识"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 100},
                },
                "required": ["workflow_id"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_workflow_replay",
                get_workflow_replay(str(params.get("workflow_id", "") or ""), limit=int(params.get("limit", 100) or 100)),
                "已返回任务回放结果。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_workflow_learning_stats",
            description="查看任务回放与轻量学习统计，包括模板命中、降级和失败分布。",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_workflow_learning_stats",
                get_workflow_learning_stats(int(params.get("limit", 20) or 20)),
                "已返回任务学习统计。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="create_decision_session",
            description="将一次分析、推荐或回测请求创建为决策会话，作为后续反馈与复盘的主对象。",
            parameters={
                "type": "object",
                "properties": {
                    "scenario": {"type": "string", "description": "场景，例如 analyze、recommend、backtest、report"},
                    "objective": {"type": "string", "description": "用户原始目标"},
                    "route": {"type": "object", "description": "结构化路由结果"},
                    "task_protocol": {"type": "object", "description": "统一任务协议"},
                    "workflow_id": {"type": "string", "description": "可选 workflow_id"},
                    "summary": {"type": "string", "description": "会话摘要"},
                },
                "required": ["scenario", "objective", "route", "task_protocol"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "create_decision_session",
                create_decision_session(
                    scenario=str(params["scenario"]),
                    objective=str(params["objective"]),
                    route=params.get("route", {}) or {},
                    task_protocol=params.get("task_protocol", {}) or {},
                    workflow_id=str(params.get("workflow_id", "") or ""),
                    summary=str(params.get("summary", "") or ""),
                    meta={"data_kind": "decision_session"},
                ),
                "已创建决策会话。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="submit_decision_feedback",
            description="提交对某次决策会话的反馈，用于采纳率和复盘统计。",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "决策会话 ID"},
                    "workflow_id": {"type": "string", "description": "对应 workflow_id，可选；未提供时会尝试从会话回推"},
                    "accepted": {"type": "boolean", "description": "是否采纳"},
                    "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                    "reason": {"type": "string"},
                    "correction": {"type": "string"},
                    "comment": {"type": "string"},
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "submit_decision_feedback",
                submit_decision_feedback(
                    session_id=str(params["session_id"]),
                    workflow_id=str(params.get("workflow_id", "") or ""),
                    accepted=params.get("accepted"),
                    rating=params.get("rating"),
                    reason=str(params.get("reason", "") or ""),
                    correction=str(params.get("correction", "") or ""),
                    comment=str(params.get("comment", "") or ""),
                    meta={"data_kind": "decision_feedback"},
                ),
                "已提交决策反馈。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_decision_session_replay",
            description="按 session_id 回放决策会话，查看计划、执行、反馈和 workflow 结果。",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "决策会话 ID"},
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_decision_session_replay",
                get_decision_session_replay(str(params["session_id"])),
                "已返回决策会话回放。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_decision_session_stats",
            description="查看决策会话与用户反馈统计。",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_decision_session_stats",
                get_decision_session_stats(int(params.get("limit", 20) or 20)),
                "已返回决策会话统计。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_model_governance_status",
            description="查看当前模型治理状态、稳定版本、特征清单和最近治理事件。",
            parameters={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "可选的模型名称"},
                },
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "get_model_governance_status",
                get_model_governance_service().get_status(params.get("model_name") or None),
                "已返回模型治理状态。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="evaluate_model_release",
            description="根据指标和阈值评估模型是否可以发布。",
            parameters={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "模型名称"},
                    "version": {"type": "string", "description": "模型版本"},
                    "metrics": {"type": "object", "description": "模型评估指标"},
                    "thresholds": {"type": "object", "description": "发布阈值"},
                },
                "required": ["model_name", "version"],
                "additionalProperties": False,
            },
            handler=lambda params: _tool_response(
                "evaluate_model_release",
                get_model_governance_service().evaluate_release(
                    params["model_name"],
                    params["version"],
                    metrics=params.get("metrics", {}) or {},
                    thresholds=params.get("thresholds", {}) or {},
                ),
                "已完成模型发布评估。",
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="get_runtime_health",
            description="查看当前运行健康状态、最近事件和最近告警。",
            parameters={
                "type": "object",
                "properties": {
                    "window_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
                    "category": {"type": "string", "description": "可选的分类过滤，如 workflow、analysis、recommendation"},
                    "tool_name": {"type": "string", "description": "可选的工具名称过滤"},
                },
                "additionalProperties": False,
            },
            handler=_get_runtime_health,
        )
    )

    registry.register(
        ToolSpec(
            name="evaluate_runtime_health",
            description="根据阈值评估运行健康并在必要时生成告警。",
            parameters={
                "type": "object",
                "properties": {
                    "window_size": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
                    "category": {"type": "string", "description": "可选的分类过滤，如 workflow、analysis、recommendation"},
                    "tool_name": {"type": "string", "description": "可选的工具名称过滤"},
                    "thresholds": {"type": "object", "description": "可选阈值配置"},
                },
                "additionalProperties": False,
            },
            handler=_evaluate_runtime_health,
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
