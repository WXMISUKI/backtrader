#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一任务协议。

用于把协作计划、工作流步骤和工作流结果收敛到同一套可回放语义。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .serialization import serialize_value


@dataclass(frozen=True)
class TaskStep:
    """统一任务步骤。"""

    step_id: str
    task_id: str
    workflow_id: str = ""
    intent: str = ""
    tool: str = ""
    role: str = ""
    description: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: str = "planned"
    summary: str = ""
    data_source: Optional[str] = None
    ok: bool = False
    error: Optional[str] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    attempts: int = 1
    data: Any = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["arguments"] = serialize_value(self.arguments)
        payload["depends_on"] = list(self.depends_on)
        payload["data"] = serialize_value(self.data)
        return payload


@dataclass(frozen=True)
class TaskPlan:
    """统一任务计划。"""

    task_id: str
    objective: str
    mode: str
    primary_intent: str
    primary_tool: str
    primary_reason: str
    summary: str = ""
    workflow_id: str = ""
    template_id: str = ""
    template_name: str = ""
    template_reason: str = ""
    template_score: float = 0.0
    template_hit: bool = False
    tasks: List[TaskStep] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    fallback: List[str] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    matched_terms: List[str] = field(default_factory=list)
    route: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["tasks"] = [task.to_dict() for task in self.tasks]
        payload["execution_order"] = list(self.execution_order)
        payload["next_actions"] = list(self.next_actions)
        payload["roles"] = list(dict.fromkeys(self.roles))
        payload["fallback"] = list(self.fallback)
        payload["candidates"] = list(self.candidates)
        payload["matched_terms"] = list(self.matched_terms)
        payload["route"] = serialize_value(self.route)
        payload["meta"] = serialize_value(self.meta)
        return payload


@dataclass(frozen=True)
class TaskResult:
    """统一任务结果。"""

    task_id: str
    workflow_id: str
    ok: bool
    tool: str
    category: str
    data_source: Optional[str]
    summary: str
    plan: Dict[str, Any] = field(default_factory=dict)
    steps: List[TaskStep] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    is_degraded: bool = False
    data: Any = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["plan"] = serialize_value(self.plan)
        payload["steps"] = [step.to_dict() for step in self.steps]
        payload["execution_order"] = list(self.execution_order)
        payload["data"] = serialize_value(self.data)
        payload["meta"] = serialize_value(self.meta)
        return payload


def build_task_step(source: Any, *, task_id: str = "", workflow_id: str = "", status: str = "planned") -> TaskStep:
    """从现有对象构造统一步骤。"""
    if isinstance(source, dict):
        data = dict(source)
    else:
        data = dict(getattr(source, "__dict__", {}) or {})

    step_id = str(data.get("step_id") or data.get("id") or task_id or workflow_id)
    resolved_task_id = str(data.get("task_id") or task_id or step_id)
    return TaskStep(
        step_id=step_id,
        task_id=resolved_task_id,
        workflow_id=str(data.get("workflow_id") or workflow_id or ""),
        intent=str(data.get("intent", "")),
        tool=str(data.get("tool", "")),
        role=str(data.get("role", "")),
        description=str(data.get("description", "")),
        arguments=dict(data.get("arguments", {}) or {}),
        depends_on=list(data.get("depends_on", []) or []),
        status=str(data.get("status", status) or status),
        summary=str(data.get("summary", "")),
        data_source=data.get("data_source"),
        ok=bool(data.get("ok", False)),
        error=data.get("error"),
        fallback_used=bool(data.get("fallback_used", False)),
        fallback_reason=data.get("fallback_reason"),
        attempts=int(data.get("attempts", 1) or 1),
        data=data.get("data"),
    )


def build_task_plan(source: Any, *, task_id: str = "", workflow_id: str = "") -> TaskPlan:
    """从现有计划对象构造统一任务计划。"""
    if isinstance(source, dict):
        data = dict(source)
    else:
        data = dict(getattr(source, "__dict__", {}) or {})

    task_steps = [
        build_task_step(item, task_id=str(data.get("task_id") or task_id or workflow_id), workflow_id=str(data.get("workflow_id") or workflow_id or ""))
        for item in data.get("tasks", []) or []
    ]
    resolved_task_id = str(data.get("task_id") or data.get("workflow_id") or task_id or workflow_id or "")
    return TaskPlan(
        task_id=resolved_task_id,
        objective=str(data.get("objective", "")),
        mode=str(data.get("mode", "")),
        primary_intent=str(data.get("primary_intent", "")),
        primary_tool=str(data.get("primary_tool", "")),
        primary_reason=str(data.get("primary_reason", "")),
        summary=str(data.get("summary", "")),
        workflow_id=str(data.get("workflow_id") or workflow_id or ""),
        template_id=str(data.get("template_id", "")),
        template_name=str(data.get("template_name", "")),
        template_reason=str(data.get("template_reason", "")),
        template_score=float(data.get("template_score", 0.0) or 0.0),
        template_hit=bool(data.get("template_hit", False)),
        tasks=task_steps,
        execution_order=list(data.get("execution_order", []) or []),
        next_actions=list(data.get("next_actions", []) or []),
        roles=list(data.get("roles", []) or []),
        fallback=list(data.get("fallback", []) or []),
        candidates=list(data.get("candidates", []) or []),
        matched_terms=list(data.get("matched_terms", []) or []),
        route=dict(data.get("route", {}) or {}),
        meta=dict(data.get("meta", {}) or {}),
    )


def build_task_result(source: Any, *, task_id: str = "", workflow_id: str = "") -> TaskResult:
    """从现有结果对象构造统一任务结果。"""
    if isinstance(source, dict):
        data = dict(source)
    else:
        data = dict(getattr(source, "__dict__", {}) or {})

    plan_payload = data.get("plan", {}) or {}
    steps_payload = data.get("steps", []) or []
    steps = [
        build_task_step(item, task_id=str(data.get("task_id") or task_id or workflow_id), workflow_id=str(data.get("workflow_id") or workflow_id or ""), status=str(item.get("status", "")) if isinstance(item, dict) else "done")
        for item in steps_payload
    ]
    resolved_task_id = str(data.get("task_id") or task_id or workflow_id or "")
    resolved_workflow_id = str(data.get("workflow_id") or workflow_id or "")
    return TaskResult(
        task_id=resolved_task_id,
        workflow_id=resolved_workflow_id,
        ok=bool(data.get("ok", False)),
        tool=str(data.get("tool", "")),
        category=str(data.get("category", "")),
        data_source=data.get("data_source"),
        summary=str(data.get("summary", "")),
        plan=dict(plan_payload if isinstance(plan_payload, dict) else {}),
        steps=steps,
        execution_order=list(data.get("execution_order", []) or []),
        is_degraded=bool(data.get("is_degraded", False)),
        data=data.get("data"),
        meta=dict(data.get("meta", {}) or {}),
    )

