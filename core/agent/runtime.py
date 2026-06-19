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

    def recent_routes(self, limit: int = 20) -> list[dict]:
        """查看最近的路由审计记录。"""
        return self.audit_logger.recent(limit)


def create_stock_agent_runtime(settings: Optional[AgentSettings] = None) -> StockAgentRuntime:
    """创建股票智能体运行时。"""
    return StockAgentRuntime(settings=settings)
