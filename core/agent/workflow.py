#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体工作流执行

将协作计划执行为多步骤工作流，并输出统一结果。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import uuid
from typing import Any, Dict, List, Optional

from .audit import RouteAuditLogger, get_route_audit_logger
from .collaboration import CollaborationPlan, build_collaboration_plan
from .serialization import build_tool_payload, serialize_value


@dataclass(frozen=True)
class WorkflowStepResult:
    """单个工作流步骤结果。"""

    id: str
    intent: str
    tool: str
    role: str
    description: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    ok: bool = False
    summary: str = ""
    data_source: Optional[str] = None
    data: Any = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["arguments"] = serialize_value(self.arguments)
        payload["depends_on"] = list(self.depends_on)
        payload["data"] = serialize_value(self.data)
        return payload


@dataclass(frozen=True)
class WorkflowExecutionResult:
    """工作流执行结果。"""

    workflow_id: str
    objective: str
    mode: str
    plan: Dict[str, Any]
    steps: List[WorkflowStepResult] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    summary: str = ""
    is_degraded: bool = False
    primary_ok: bool = True
    route_audit_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["plan"] = serialize_value(self.plan)
        payload["steps"] = [step.to_dict() for step in self.steps]
        payload["execution_order"] = list(self.execution_order)
        payload["meta"] = serialize_value(self.meta)
        return payload


class WorkflowExecutor:
    """轻量工作流执行器。"""

    def __init__(self, tool_registry, audit_logger: Optional[RouteAuditLogger] = None) -> None:
        self.tool_registry = tool_registry
        self.audit_logger = audit_logger or get_route_audit_logger()

    def execute(self, user_input: str, *, default_risk_profile: str = "moderate") -> dict:
        """生成协作计划并依次执行。"""
        plan = build_collaboration_plan(user_input, default_risk_profile=default_risk_profile)
        workflow_id = str(uuid.uuid4())

        step_results: List[WorkflowStepResult] = []
        primary_ok = False
        is_degraded = False
        primary_source = "workflow"

        for task in plan.tasks:
            result = self._dispatch_task(task.tool, task.arguments)
            step = WorkflowStepResult(
                id=task.id,
                intent=task.intent,
                tool=task.tool,
                role=task.role,
                description=task.description,
                arguments=task.arguments,
                depends_on=task.depends_on,
                ok=bool(result.get("ok", False)),
                summary=str(result.get("summary", "")),
                data_source=result.get("data_source"),
                data=result.get("data"),
                error=None if result.get("ok", False) else _extract_error(result),
            )
            step_results.append(step)

            if task.id == "primary":
                primary_ok = step.ok
                if step.data_source:
                    primary_source = str(step.data_source)
            elif not step.ok:
                is_degraded = True

        summary = self._build_summary(plan, step_results, is_degraded)
        payload = WorkflowExecutionResult(
            workflow_id=workflow_id,
            objective=user_input,
            mode=plan.mode,
            plan=plan.to_dict(),
            steps=step_results,
            execution_order=plan.execution_order,
            summary=summary,
            is_degraded=is_degraded,
            primary_ok=primary_ok,
            meta={
                "planner_version": plan.meta.get("planner_version"),
                "collaboration_recommended": plan.meta.get("collaboration_recommended", False),
                "task_count": len(step_results),
                "primary_data_source": primary_source,
                "default_risk_profile": default_risk_profile,
            },
        ).to_dict()

        audit_entry = self.audit_logger.record(
            entrypoint="workflow.execute",
            input_text=user_input,
            route=plan.route,
            data_source=primary_source,
            notes=f"workflow_id={workflow_id}",
            meta={
                "workflow_id": workflow_id,
                "mode": plan.mode,
                "task_count": len(step_results),
                "primary_ok": primary_ok,
                "is_degraded": is_degraded,
            },
        )
        payload["route_audit_id"] = audit_entry.get("id")
        payload["meta"]["route_audit_id"] = audit_entry.get("id")
        payload["meta"]["workflow_id"] = workflow_id

        tool_payload = build_tool_payload("execute_workflow", payload, summary)
        tool_payload["ok"] = primary_ok
        tool_payload["data_source"] = "workflow"
        tool_payload["meta"]["data_source"] = "workflow"
        tool_payload["meta"]["workflow_id"] = workflow_id
        tool_payload["meta"]["route_audit_id"] = audit_entry.get("id")
        tool_payload["meta"]["primary_data_source"] = primary_source
        tool_payload["meta"]["is_degraded"] = is_degraded
        tool_payload["meta"]["overall_ok"] = primary_ok
        tool_payload["meta"]["execution_engine"] = "WorkflowExecutor"
        return tool_payload

    def _dispatch_task(self, tool_name: str, arguments: dict) -> dict:
        try:
            return self.tool_registry.dispatch(tool_name, arguments)
        except Exception as exc:
            return {
                "ok": False,
                "tool": tool_name,
                "category": "workflow",
                "data_source": None,
                "summary": f"工作流任务执行失败: {exc}",
                "data": {"error": str(exc)},
                "meta": {
                    "tool": tool_name,
                    "error": str(exc),
                },
            }

    def _build_summary(self, plan: CollaborationPlan, steps: List[WorkflowStepResult], is_degraded: bool) -> str:
        suffix = "，存在部分降级。" if is_degraded else "。"
        return f"已执行协作工作流，共 {len(steps)} 个步骤，主路由为 {plan.primary_tool}{suffix}"


def execute_collaboration_workflow(
    user_input: str,
    tool_registry,
    *,
    default_risk_profile: str = "moderate",
    audit_logger: Optional[RouteAuditLogger] = None,
) -> dict:
    """执行协作工作流的便捷入口。"""
    executor = WorkflowExecutor(tool_registry=tool_registry, audit_logger=audit_logger)
    return executor.execute(user_input, default_risk_profile=default_risk_profile)


def _extract_error(result: dict) -> str:
    """从工具结果里尽量提取错误信息。"""
    data = result.get("data")
    if isinstance(data, dict):
        for key in ("error", "message", "reason"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    meta = result.get("meta")
    if isinstance(meta, dict):
        for key in ("error", "reason"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    summary = result.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()

    return "workflow step failed"
