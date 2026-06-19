#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体工作流执行

将协作计划执行为多步骤工作流，并输出统一结果。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import uuid
import time
from typing import Any, Dict, List, Optional

from .audit import RouteAuditLogger, get_route_audit_logger
from .collaboration import CollaborationPlan, build_collaboration_plan
from .serialization import build_tool_payload, serialize_value
from core.observability import get_observability_service


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
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    attempts: int = 1

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
    template_id: str = ""
    template_name: str = ""
    template_reason: str = ""
    template_score: float = 0.0
    template_hit: bool = False
    is_degraded: bool = False
    primary_ok: bool = True
    route_audit_id: Optional[str] = None
    plan_audit_id: Optional[str] = None
    result_audit_id: Optional[str] = None
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
        observability = get_observability_service()
        started_at = time.perf_counter()
        plan = build_collaboration_plan(user_input, default_risk_profile=default_risk_profile)
        workflow_id = str(uuid.uuid4())

        plan_audit = self.audit_logger.record(
            entrypoint="workflow.plan",
            input_text=user_input,
            route=plan.route,
            event_type="workflow_plan",
            phase="plan",
            workflow_id=workflow_id,
            status="planned",
            data_source="workflow",
            notes=f"workflow_id={workflow_id}",
            meta={
                "workflow_id": workflow_id,
                "planner_version": plan.meta.get("planner_version"),
                "collaboration_recommended": plan.meta.get("collaboration_recommended", False),
                "task_count": len(plan.tasks),
                "template_id": plan.template_id,
                "template_name": plan.template_name,
                "template_reason": plan.template_reason,
                "template_score": plan.template_score,
                "template_hit": plan.template_hit,
            },
        )

        step_results: List[WorkflowStepResult] = []
        primary_ok = False
        is_degraded = False
        primary_source = "workflow"
        step_audit_ids: List[str] = []

        for task in plan.tasks:
            result, fallback_used, fallback_reason, attempts = self._execute_task(task, step_results)
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
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                attempts=attempts,
            )
            step_results.append(step)

            if task.id == "primary":
                primary_ok = step.ok
                if step.data_source:
                    primary_source = str(step.data_source)
            if fallback_used or not step.ok:
                is_degraded = True

            step_audit = self.audit_logger.record(
                entrypoint="workflow.step",
                input_text=user_input,
                route=self._task_route(task, step),
                event_type="workflow_step",
                phase="step",
                workflow_id=workflow_id,
                parent_id=plan_audit.get("id"),
                step_id=task.id,
                status="fallback" if fallback_used else ("ok" if step.ok else "failed"),
                data_source=step.data_source,
                notes=step.fallback_reason or step.summary,
                meta={
                    "workflow_id": workflow_id,
                    "fallback_used": fallback_used,
                    "fallback_reason": step.fallback_reason,
                    "attempts": attempts,
                },
            )
            step_audit_ids.append(step_audit.get("id"))

        summary = self._build_summary(plan, step_results, is_degraded)
        fallback_used_count = sum(1 for step in step_results if step.fallback_used)
        failed_step_count = sum(1 for step in step_results if not step.ok)
        payload = WorkflowExecutionResult(
            workflow_id=workflow_id,
            objective=user_input,
            mode=plan.mode,
            plan=plan.to_dict(),
            steps=step_results,
            execution_order=plan.execution_order,
            summary=summary,
            template_id=plan.template_id,
            template_name=plan.template_name,
            template_reason=plan.template_reason,
            template_score=plan.template_score,
            template_hit=plan.template_hit,
            is_degraded=is_degraded,
            primary_ok=primary_ok,
            plan_audit_id=plan_audit.get("id"),
            meta={
                "planner_version": plan.meta.get("planner_version"),
                "collaboration_recommended": plan.meta.get("collaboration_recommended", False),
                "task_count": len(step_results),
                "primary_data_source": primary_source,
                "default_risk_profile": default_risk_profile,
                "step_audit_ids": step_audit_ids,
                "fallback_used_count": fallback_used_count,
                "failed_step_count": failed_step_count,
                "template_id": plan.template_id,
                "template_name": plan.template_name,
                "template_reason": plan.template_reason,
                "template_score": plan.template_score,
                "template_hit": plan.template_hit,
            },
        ).to_dict()

        result_audit = self.audit_logger.record(
            entrypoint="workflow.result",
            input_text=user_input,
            route=plan.route,
            event_type="workflow_result",
            phase="result",
            workflow_id=workflow_id,
            parent_id=plan_audit.get("id"),
            status="degraded" if is_degraded else "ok",
            data_source=primary_source,
            notes=f"workflow_id={workflow_id}",
            meta={
                "workflow_id": workflow_id,
                "mode": plan.mode,
                "task_count": len(step_results),
                "primary_ok": primary_ok,
                "is_degraded": is_degraded,
                "step_audit_ids": step_audit_ids,
                "fallback_used_count": fallback_used_count,
                "failed_step_count": failed_step_count,
                "template_id": plan.template_id,
                "template_name": plan.template_name,
                "template_reason": plan.template_reason,
                "template_score": plan.template_score,
                "template_hit": plan.template_hit,
            },
        )
        payload["route_audit_id"] = result_audit.get("id")
        payload["meta"]["route_audit_id"] = result_audit.get("id")
        payload["meta"]["workflow_id"] = workflow_id
        payload["plan_audit_id"] = plan_audit.get("id")
        payload["result_audit_id"] = result_audit.get("id")

        tool_payload = build_tool_payload("execute_workflow", payload, summary)
        tool_payload["ok"] = primary_ok
        tool_payload["data_source"] = "workflow"
        tool_payload["meta"]["data_source"] = "workflow"
        tool_payload["meta"]["workflow_id"] = workflow_id
        tool_payload["meta"]["plan_audit_id"] = plan_audit.get("id")
        tool_payload["meta"]["route_audit_id"] = result_audit.get("id")
        tool_payload["meta"]["result_audit_id"] = result_audit.get("id")
        tool_payload["meta"]["primary_data_source"] = primary_source
        tool_payload["meta"]["is_degraded"] = is_degraded
        tool_payload["meta"]["overall_ok"] = primary_ok
        tool_payload["meta"]["fallback_used_count"] = fallback_used_count
        tool_payload["meta"]["failed_step_count"] = failed_step_count
        tool_payload["meta"]["template_id"] = plan.template_id
        tool_payload["meta"]["template_name"] = plan.template_name
        tool_payload["meta"]["template_reason"] = plan.template_reason
        tool_payload["meta"]["template_score"] = plan.template_score
        tool_payload["meta"]["template_hit"] = plan.template_hit
        tool_payload["meta"]["execution_engine"] = "WorkflowExecutor"
        tool_payload["meta"]["step_audit_ids"] = step_audit_ids

        duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        observability.record_metric(
            "workflow.step_count",
            len(step_results),
            source="WorkflowExecutor",
            category="workflow",
            labels={"workflow_id": workflow_id},
            meta={"workflow_id": workflow_id},
        )
        observability.record_metric(
            "workflow.fallback_count",
            fallback_used_count,
            source="WorkflowExecutor",
            category="workflow",
            labels={"workflow_id": workflow_id},
            meta={"workflow_id": workflow_id},
        )
        observability.record_metric(
            "workflow.failed_step_count",
            failed_step_count,
            source="WorkflowExecutor",
            category="workflow",
            labels={"workflow_id": workflow_id},
            meta={"workflow_id": workflow_id},
        )
        observability.record_latency(
            "execute_workflow",
            duration_ms,
            source="WorkflowExecutor",
            category="workflow",
            labels={"workflow_id": workflow_id, "template_hit": str(plan.template_hit).lower()},
            meta={
                "workflow_id": workflow_id,
                "template_hit": plan.template_hit,
                "is_degraded": is_degraded,
                "primary_ok": primary_ok,
            },
        )
        observability.record_runtime_event(
            "workflow.execute",
            status="degraded" if is_degraded else "ok",
            source="WorkflowExecutor",
            category="workflow",
            duration_ms=duration_ms,
            data_source=primary_source,
            message=summary,
            meta={
                "workflow_id": workflow_id,
                "template_hit": plan.template_hit,
                "template_id": plan.template_id,
                "template_name": plan.template_name,
                "step_count": len(step_results),
                "fallback_used_count": fallback_used_count,
                "failed_step_count": failed_step_count,
                "primary_ok": primary_ok,
            },
        )
        return tool_payload

    def _execute_task(self, task, prior_steps: List[WorkflowStepResult]) -> tuple[dict, bool, Optional[str], int]:
        """执行任务并在必要时尝试降级回退。"""
        attempts = 1
        result = self._dispatch_task(task.tool, task.arguments)
        if bool(result.get("ok", False)):
            return result, False, None, attempts

        fallback_result, fallback_reason = self._fallback_task(task, result, prior_steps)
        if fallback_result is not None:
            attempts += 1
            return fallback_result, True, fallback_reason, attempts

        return result, False, _extract_error(result), attempts

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

    def _fallback_task(
        self,
        task,
        failed_result: dict,
        prior_steps: List[WorkflowStepResult],
    ) -> tuple[Optional[dict], Optional[str]]:
        """基于任务类型提供降级结果。"""
        error_text = _extract_error(failed_result)
        if task.tool == "generate_stock_report":
            fallback_data = self._compose_report_fallback(task.arguments, prior_steps, error_text)
            return (
                build_tool_payload(
                    "generate_stock_report",
                    fallback_data,
                    "报告任务失败，已返回降级报告。",
                ),
                f"report fallback: {error_text}",
            )
        if task.tool == "run_backtest":
            fallback_data = {
                "data_source": "fallback",
                "fallback": True,
                "backtest_status": "unavailable",
                "reason": error_text,
                "stock_code": task.arguments.get("stock_code"),
                "strategy_name": task.arguments.get("strategy_name"),
                "note": "回测失败，已返回降级结果。",
            }
            return (
                build_tool_payload(
                    "run_backtest",
                    fallback_data,
                    "回测任务失败，已返回降级结果。",
                ),
                f"backtest fallback: {error_text}",
            )
        if task.tool == "get_market_overview":
            fallback_data = {
                "data_source": "fallback",
                "fallback": True,
                "market_state": "unknown",
                "reason": error_text,
                "note": "市场概览失败，已返回降级结果。",
            }
            return (
                build_tool_payload(
                    "get_market_overview",
                    fallback_data,
                    "市场概览失败，已返回降级结果。",
                ),
                f"market fallback: {error_text}",
            )
        return None, None

    def _compose_report_fallback(
        self,
        arguments: dict,
        prior_steps: List[WorkflowStepResult],
        reason: str,
    ) -> dict:
        """根据已有步骤结果拼出一个降级报告。"""
        market_step = self._find_step(prior_steps, "get_market_overview")
        backtest_step = self._find_step(prior_steps, "run_backtest")
        overview_summary = market_step.summary if market_step else "市场概览不可用"
        backtest_summary = backtest_step.summary if backtest_step else "回测不可用"
        return {
            "data_source": "fallback",
            "fallback": True,
            "report_mode": "degraded",
            "stock_code": arguments.get("stock_code"),
            "risk_profile": arguments.get("risk_profile"),
            "reason": reason,
            "highlights": [
                overview_summary,
                backtest_summary,
            ],
            "summary": "报告已降级生成，关键步骤信息已保留。",
        }

    def _find_step(self, steps: List[WorkflowStepResult], tool_name: str) -> Optional[WorkflowStepResult]:
        for step in steps:
            if step.tool == tool_name:
                return step
        return None

    def _task_route(self, task, step: WorkflowStepResult) -> dict:
        """把节点结果包装成可审计的路由样式。"""
        return {
            "intent": step.intent,
            "tool": step.tool,
            "confidence": float(getattr(task, "confidence", 0.0) or 0.0),
            "reason": step.fallback_reason or task.description,
            "arguments": step.arguments,
            "matched_terms": [],
            "candidates": [],
        }

    def _build_summary(self, plan: CollaborationPlan, steps: List[WorkflowStepResult], is_degraded: bool) -> str:
        suffix = "，存在部分降级。" if is_degraded else "。"
        template_prefix = f"已匹配模板《{plan.template_name}》，" if plan.template_hit and plan.template_name else ""
        return f"{template_prefix}已执行协作工作流，共 {len(steps)} 个步骤，主路由为 {plan.primary_tool}{suffix}"


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
