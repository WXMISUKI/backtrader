#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体运行时

对外提供更简洁的业务入口。
"""

from __future__ import annotations

from typing import Optional

from .audit import RouteAuditLogger, get_route_audit_logger
from .client import ArkAgentClient
from .config import AgentSettings, load_agent_settings
from .session import create_decision_session, get_decision_feedback_insights, get_decision_session_replay, get_decision_session_stats, submit_decision_feedback


class StockAgentRuntime:
    """股票智能体运行时。"""

    def __init__(self, settings: Optional[AgentSettings] = None, audit_logger: Optional[RouteAuditLogger] = None) -> None:
        self.settings = settings or load_agent_settings()
        self.audit_logger = audit_logger or get_route_audit_logger()
        self.client = ArkAgentClient(settings=self.settings, audit_logger=self.audit_logger)

    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        """向智能体发起一次问答。"""
        return self.client.ask(question, system_prompt=system_prompt)

    def parse_intent(self, question: str) -> dict:
        """解析用户问题，返回结构化路由结果。"""
        return self.client.parse_intent(question)

    def plan_collaboration(self, question: str) -> dict:
        """生成协作计划。"""
        return self.client.plan_collaboration(question)

    def execute_workflow(self, question: str) -> dict:
        """执行协作工作流。"""
        return self.client.execute_workflow(question)

    def answer_decision_request(self, question: str, **kwargs) -> dict:
        """统一决策入口。"""
        from core.orchestrator import StockOrchestrator

        return StockOrchestrator(
            tool_registry=self.client.tool_registry,
            audit_logger=self.audit_logger,
        ).answer_decision_request(question, **kwargs)

    def answer_decision_summary(self, question: str, **kwargs) -> dict:
        """统一决策的四段式摘要入口。"""
        from core.orchestrator import StockOrchestrator

        return StockOrchestrator(
            tool_registry=self.client.tool_registry,
            audit_logger=self.audit_logger,
        ).answer_decision_summary(question, **kwargs)

    def list_project_capabilities(self) -> dict:
        """查看项目能力目录。"""
        return self.client.tool_registry.dispatch("list_project_capabilities", {})

    def recent_routes(self, limit: int = 20) -> list[dict]:
        """查看最近的路由审计记录。"""
        return self.audit_logger.recent(limit)

    def recent_workflow_events(
        self,
        limit: int = 20,
        *,
        workflow_id: Optional[str] = None,
        phase: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> list[dict]:
        """按工作流维度查看审计记录。"""
        return self.audit_logger.recent(
            limit,
            workflow_id=workflow_id,
            phase=phase,
            event_type=event_type,
        )

    def create_decision_session(self, scenario: str, objective: str, route: dict, task_protocol: dict, *, workflow_id: str = "", summary: str = "") -> dict:
        """创建决策会话。"""
        return create_decision_session(
            scenario=scenario,
            objective=objective,
            route=route,
            task_protocol=task_protocol,
            workflow_id=workflow_id,
            summary=summary,
        )

    def submit_decision_feedback(
        self,
        session_id: str,
        workflow_id: str = "",
        *,
        accepted: Optional[bool] = None,
        rating: Optional[int] = None,
        reason: str = "",
        correction: str = "",
        comment: str = "",
    ) -> dict:
        """提交决策反馈。"""
        return submit_decision_feedback(
            session_id=session_id,
            workflow_id=workflow_id,
            accepted=accepted,
            rating=rating,
            reason=reason,
            correction=correction,
            comment=comment,
        )

    def get_decision_session_replay(self, session_id: str) -> dict:
        """回放决策会话。"""
        return get_decision_session_replay(session_id)

    def get_decision_session_stats(self, limit: int = 20) -> dict:
        """查看决策会话统计。"""
        return get_decision_session_stats(limit=limit)

    def get_decision_feedback_insights(self, limit: int = 20, *, min_samples: int = 2) -> dict:
        """查看决策反馈洞察。"""
        return get_decision_feedback_insights(limit=limit, min_samples=min_samples)


def create_stock_agent_runtime(settings: Optional[AgentSettings] = None) -> StockAgentRuntime:
    """创建股票智能体运行时。"""
    return StockAgentRuntime(settings=settings)
