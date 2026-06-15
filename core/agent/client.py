#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ark / OpenAI-compatible 智能体客户端

负责与模型对话，并在需要时执行项目工具调用。
"""

from __future__ import annotations

import json
from typing import Optional

from openai import OpenAI

from .config import AgentSettings, load_agent_settings
from .tools import ProjectToolRegistry, build_default_tool_registry


DEFAULT_SYSTEM_PROMPT = """你是一个中文股票量化投顾智能体。

你必须优先使用工具来获取事实数据，不要凭空编造价格、指标、财务数据或回测结果。
当用户询问个股分析、基本面、市场概览、选股、交易决策、回测、风险控制或报告时，请调用对应工具。

回答要求：
- 使用中文
- 结论要结构化
- 优先输出：结论 / 依据 / 风险 / 数据来源
- 清楚区分事实数据、推理和建议
- 默认给出风险提示
- 如果数据不足或工具失败，要明确说明原因，不要假装结果可用
- 如果工具结果包含 data_source 字段，必须在回答中明确写出
- 如果 data_source 为 mock，必须明确标注为 mock，并说明真实数据源不可用
"""


class ArkAgentClient:
    """Ark 智能体客户端。"""

    def __init__(
        self,
        settings: Optional[AgentSettings] = None,
        tool_registry: Optional[ProjectToolRegistry] = None,
        client: Optional[OpenAI] = None,
    ) -> None:
        self.settings = settings or load_agent_settings()
        self.tool_registry = tool_registry or build_default_tool_registry()

        if client is not None:
            self.client = client
        else:
            if not self.settings.has_api_key:
                raise ValueError("未配置 ARK_API_KEY，请先填写 .env")
            self.client = OpenAI(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                timeout=self.settings.timeout,
            )

    def ask(self, user_input: str, system_prompt: Optional[str] = None, max_rounds: int = 6) -> str:
        """
        发起一次带工具调用的对话。

        返回最终文本回答。
        """
        messages = [
            {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        tools = self.tool_registry.to_openai_tools()
        preferred_tool = self._infer_preferred_tool(user_input)

        for round_index in range(max_rounds):
            tool_choice = (
                {"type": "function", "function": {"name": preferred_tool}}
                if round_index == 0 and preferred_tool in self.tool_registry.list_tools()
                else "auto"
            )

            response = self.client.chat.completions.create(
                model=self.settings.chat_model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )

            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []

            if not tool_calls:
                return (message.content or "").strip()

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )

            for call in tool_calls:
                try:
                    tool_result = self.tool_registry.dispatch(call.function.name, call.function.arguments)
                except Exception as exc:
                    tool_result = {
                        "ok": False,
                        "tool": call.function.name,
                        "summary": f"工具执行失败: {exc}",
                        "data": {"error": str(exc)},
                    }

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

        raise RuntimeError("超过最大工具调用轮次，仍未收敛到最终回答。")

    def _infer_preferred_tool(self, user_input: str) -> str:
        """根据用户输入做轻量路由，优先选择最相关的工具。"""
        text = user_input.lower()

        if "回测" in user_input or "backtest" in text:
            return "run_backtest"
        if "市场" in user_input or "大盘" in user_input or "market" in text:
            return "get_market_overview"
        if "基本面" in user_input:
            return "analyze_fundamental"
        if "长线" in user_input:
            return "recommend_long_term"
        if "短线" in user_input:
            return "recommend_short_term"
        if "风控" in user_input or "仓位" in user_input or "风险" in user_input:
            return "get_risk_profile"
        if "选股" in user_input or "筛选" in user_input:
            return "screen_stocks"
        if any(keyword in user_input for keyword in ["推荐", "适合", "买什么", "买哪些", "配置"]):
            return "recommend_by_risk"
        if any(keyword in user_input for keyword in ["分析", "建议", "报告", "买", "卖"]):
            return "analyze_stock"

        return ""
