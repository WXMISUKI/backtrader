#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体接入层

将项目现有分析、推荐、回测和风控能力包装为可供大模型调用的工具，
并提供 Ark / OpenAI-compatible 客户端封装。
"""

from .config import AgentSettings, load_agent_settings
from .client import ArkAgentClient
from .runtime import StockAgentRuntime, create_stock_agent_runtime
from .tools import ProjectToolRegistry, build_default_tool_registry

__all__ = [
    "AgentSettings",
    "load_agent_settings",
    "ArkAgentClient",
    "StockAgentRuntime",
    "create_stock_agent_runtime",
    "ProjectToolRegistry",
    "build_default_tool_registry",
]
