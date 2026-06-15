#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体运行时

对外提供更简洁的业务入口。
"""

from __future__ import annotations

from typing import Optional

from .client import ArkAgentClient
from .config import AgentSettings, load_agent_settings


class StockAgentRuntime:
    """股票智能体运行时。"""

    def __init__(self, settings: Optional[AgentSettings] = None) -> None:
        self.settings = settings or load_agent_settings()
        self.client = ArkAgentClient(settings=self.settings)

    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        """向智能体发起一次问答。"""
        return self.client.ask(question, system_prompt=system_prompt)


def create_stock_agent_runtime(settings: Optional[AgentSettings] = None) -> StockAgentRuntime:
    """创建股票智能体运行时。"""
    return StockAgentRuntime(settings=settings)
