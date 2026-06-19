#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体接入层

将项目现有分析、推荐、回测和风控能力包装为可供大模型调用的工具，
并提供 Ark / OpenAI-compatible 客户端封装。
"""

from .config import AgentSettings, load_agent_settings
from .audit import RouteAuditLogger, RouteAuditRecord, get_route_audit_logger
from .collaboration import CollaborationPlan, CollaborationTask, build_collaboration_plan, should_plan_collaboration
from .workflow_templates import WorkflowTemplate, build_template_task_specs, list_workflow_templates, select_workflow_template
from .workflow import WorkflowExecutionResult, WorkflowExecutor, WorkflowStepResult, execute_collaboration_workflow
from .client import ArkAgentClient
from .runtime import StockAgentRuntime, create_stock_agent_runtime
from .tools import ProjectToolRegistry, build_default_tool_registry

__all__ = [
    "AgentSettings",
    "load_agent_settings",
    "RouteAuditLogger",
    "RouteAuditRecord",
    "get_route_audit_logger",
    "CollaborationPlan",
    "CollaborationTask",
    "build_collaboration_plan",
    "should_plan_collaboration",
    "WorkflowTemplate",
    "build_template_task_specs",
    "list_workflow_templates",
    "select_workflow_template",
    "WorkflowStepResult",
    "WorkflowExecutionResult",
    "WorkflowExecutor",
    "execute_collaboration_workflow",
    "ArkAgentClient",
    "StockAgentRuntime",
    "create_stock_agent_runtime",
    "ProjectToolRegistry",
    "build_default_tool_registry",
]
