#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体协作规划

将复合意图拆解为主任务、支持任务和执行顺序，供智能体或编排器使用。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Sequence

from .routing import IntentRoute, parse_intent


_ROLE_BY_INTENT = {
    "market_overview": "market_analyst",
    "risk_profile": "risk_guard",
    "fundamental": "fundamental_analyst",
    "analyze_stock": "equity_analyst",
    "recommend_long_term": "portfolio_advisor",
    "recommend_short_term": "portfolio_advisor",
    "recommend": "portfolio_advisor",
    "screen_stocks": "stock_screener",
    "report": "report_writer",
    "backtest": "backtest_executor",
}

_STAGE_BY_INTENT = {
    "market_overview": 10,
    "risk_profile": 12,
    "fundamental": 20,
    "analyze_stock": 30,
    "screen_stocks": 32,
    "recommend_long_term": 40,
    "recommend_short_term": 40,
    "recommend": 42,
    "backtest": 60,
    "report": 90,
}

_DESCRIPTION_BY_INTENT = {
    "market_overview": "先补充市场背景和情绪信息。",
    "risk_profile": "先确认风险偏好、仓位和约束。",
    "fundamental": "补充基本面信息，辅助分析判断。",
    "analyze_stock": "执行个股分析，形成可解释结论。",
    "recommend_long_term": "生成长线推荐列表。",
    "recommend_short_term": "生成短线推荐列表。",
    "recommend": "生成统一推荐结果。",
    "screen_stocks": "筛选候选股票池。",
    "report": "整理最终结构化报告。",
    "backtest": "对策略进行回测复验。",
}


@dataclass(frozen=True)
class CollaborationTask:
    """协作任务定义。"""

    id: str
    intent: str
    tool: str
    role: str
    description: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    confidence: float = 0.0
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CollaborationPlan:
    """协作计划结果。"""

    objective: str
    mode: str
    primary_intent: str
    primary_tool: str
    primary_reason: str
    summary: str
    tasks: List[CollaborationTask] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    fallback: List[str] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    matched_terms: List[str] = field(default_factory=list)
    route: Dict[str, Any] = field(default_factory=dict)
    data_source: str = "workflow"
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["tasks"] = [task.to_dict() for task in self.tasks]
        payload["roles"] = list(dict.fromkeys(self.roles))
        payload["execution_order"] = list(self.execution_order)
        payload["next_actions"] = list(self.next_actions)
        payload["fallback"] = list(self.fallback)
        payload["candidates"] = list(self.candidates)
        payload["matched_terms"] = list(self.matched_terms)
        payload["route"] = _normalize_route(self.route)
        return payload


def should_plan_collaboration(route: dict | IntentRoute) -> bool:
    """判断当前路由是否建议进入协作规划。"""
    normalized = _normalize_route(route)
    if normalized.get("intent") == "workflow" or normalized.get("tool") == "execute_workflow":
        return True

    candidates = normalized.get("candidates") or []
    if len(candidates) > 1:
        return True

    matched_terms = normalized.get("matched_terms") or []
    if len(matched_terms) > 1:
        return True

    return False


def build_collaboration_plan(user_input: str, *, default_risk_profile: str = "moderate") -> CollaborationPlan:
    """根据用户输入生成协作计划。"""
    route = parse_intent(user_input, default_risk_profile=default_risk_profile)
    route_dict = route.to_dict()
    tasks = _build_tasks(route)
    ordered_tasks = _order_tasks(tasks)
    execution_order = [task.id for task in ordered_tasks]
    next_actions = [f"{index + 1}. {task.description}（{task.tool}）" for index, task in enumerate(ordered_tasks)]
    roles = [task.role for task in ordered_tasks]
    fallback = _build_fallback(route_dict, ordered_tasks)
    mode = "multi_agent" if len(ordered_tasks) > 1 else "single_agent"
    summary = _build_summary(route_dict, ordered_tasks, mode)
    primary_intent = ordered_tasks[0].intent if ordered_tasks and route_dict.get("tool") == "execute_workflow" else route_dict.get("intent", "")
    primary_tool = ordered_tasks[0].tool if ordered_tasks and route_dict.get("tool") == "execute_workflow" else route_dict.get("tool", "")
    primary_reason = route_dict.get("reason", "")
    if route_dict.get("tool") == "execute_workflow" and ordered_tasks:
        primary_reason = f"执行工作流后拆解为 {ordered_tasks[0].intent} 等业务任务"

    return CollaborationPlan(
        objective=user_input,
        mode=mode,
        primary_intent=primary_intent,
        primary_tool=primary_tool,
        primary_reason=primary_reason,
        summary=summary,
        tasks=ordered_tasks,
        execution_order=execution_order,
        next_actions=next_actions,
        roles=roles,
        fallback=fallback,
        candidates=list(route_dict.get("candidates", []) or []),
        matched_terms=list(route_dict.get("matched_terms", []) or []),
        route=route_dict,
        meta={
            "planner_version": "1.0",
            "collaboration_recommended": should_plan_collaboration(route_dict),
            "default_risk_profile": default_risk_profile,
        },
    )


def _build_tasks(route: IntentRoute | dict) -> List[CollaborationTask]:
    normalized = _normalize_route(route)
    candidates = list(normalized.get("candidates") or [])
    route_tool = normalized.get("tool", "")

    if route_tool == "execute_workflow":
        candidates = [candidate for candidate in candidates if candidate.get("tool") != "execute_workflow"]
        if not candidates:
            candidates = [
                {
                    "intent": "recommend",
                    "tool": "recommend_by_risk",
                    "confidence": 0.5,
                    "arguments": {
                        "risk_profile": "moderate",
                        "top_n": 5,
                    },
                }
            ]
        primary = candidates[0]
        support_candidates = candidates[1:3]
    else:
        primary = {
            "intent": normalized.get("intent", ""),
            "tool": normalized.get("tool", ""),
            "confidence": float(normalized.get("confidence", 0.0) or 0.0),
            "arguments": normalized.get("arguments", {}) or {},
        }
        support_candidates = candidates[1:3]

    task_specs: List[dict] = []
    task_specs.append(_make_task_spec("primary", primary))

    for index, candidate in enumerate(support_candidates, start=1):
        task_specs.append(_make_task_spec(f"support_{index}", candidate))

    return [_task_from_spec(spec) for spec in task_specs if spec["tool"]]


def _make_task_spec(task_id: str, item: dict) -> dict:
    intent = str(item.get("intent", ""))
    tool = str(item.get("tool", ""))
    confidence = float(item.get("confidence", 0.0) or 0.0)
    arguments = _build_arguments(intent, item.get("arguments", {}) or {})
    return {
        "id": task_id,
        "intent": intent,
        "tool": tool,
        "role": _ROLE_BY_INTENT.get(intent, "general_analyst"),
        "description": _DESCRIPTION_BY_INTENT.get(intent, "执行协作任务。"),
        "arguments": arguments,
        "priority": _STAGE_BY_INTENT.get(intent, 99),
        "confidence": confidence,
    }


def _task_from_spec(spec: dict) -> CollaborationTask:
    return CollaborationTask(
        id=spec["id"],
        intent=spec["intent"],
        tool=spec["tool"],
        role=spec["role"],
        description=spec["description"],
        arguments=spec["arguments"],
        priority=spec["priority"],
        confidence=spec["confidence"],
    )


def _order_tasks(tasks: Sequence[CollaborationTask]) -> List[CollaborationTask]:
    ordered = sorted(tasks, key=lambda task: (task.priority, task.confidence), reverse=False)
    ordered_ids = [task.id for task in ordered]
    staged: List[CollaborationTask] = []
    for index, task in enumerate(ordered):
        depends_on = [task_id for task_id in ordered_ids[:index]]
        staged.append(
            CollaborationTask(
                id=task.id,
                intent=task.intent,
                tool=task.tool,
                role=task.role,
                description=task.description,
                arguments=task.arguments,
                priority=task.priority,
                confidence=task.confidence,
                depends_on=depends_on,
            )
        )
    return staged


def _build_arguments(intent: str, source_arguments: dict) -> dict:
    arguments = dict(source_arguments)
    if intent == "backtest":
        arguments.setdefault("stock_code", "000001")
        arguments.setdefault("strategy_name", "ma_cross")
        arguments.setdefault("start_date", "20260101")
        arguments.setdefault("end_date", "20260614")
        arguments.setdefault("initial_cash", 100000)
    elif intent == "report":
        arguments.setdefault("stock_code", "000001")
    elif intent in {"analyze_stock", "fundamental"}:
        arguments.setdefault("stock_code", "000001")
    elif intent in {"recommend", "recommend_long_term", "recommend_short_term"}:
        arguments.setdefault("top_n", 5)
    elif intent == "risk_profile":
        arguments.setdefault("risk_profile", "moderate")
    return arguments


def _build_fallback(route: dict, tasks: List[CollaborationTask]) -> List[str]:
    if not tasks:
        return ["回退到默认推荐入口 recommend_by_risk。"]
    return [
        f"若协作规划不可执行，回退到主工具 {route.get('tool', '')}。",
        "若支持任务失败，保留主工具结果并明确标记降级。",
    ]


def _build_summary(route: dict, tasks: List[CollaborationTask], mode: str) -> str:
    if mode == "single_agent":
        return f"单任务即可完成，直接执行 {route.get('tool', '')}。"

    support_count = max(len(tasks) - 1, 0)
    return (
        f"已将请求拆解为 1 个主任务和 {support_count} 个支持任务，"
        f"主工具为 {route.get('tool', '')}。"
    )


def _normalize_route(route: dict | IntentRoute) -> dict:
    if isinstance(route, IntentRoute):
        return route.to_dict()
    if hasattr(route, "to_dict") and callable(getattr(route, "to_dict")):
        try:
            converted = route.to_dict()
            if isinstance(converted, dict):
                return converted
        except Exception:
            pass
    return dict(route or {})
