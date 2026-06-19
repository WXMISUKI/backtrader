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

from .collaboration import build_collaboration_plan, should_plan_collaboration
from .audit import RouteAuditLogger, get_route_audit_logger
from .config import AgentSettings, load_agent_settings
from .routing import parse_intent
from .task_protocol import build_task_plan, build_task_result
from .session import create_decision_session
from .tools import ProjectToolRegistry, build_default_tool_registry


DEFAULT_SYSTEM_PROMPT = """你是一个中文股票量化投顾智能体。

你必须优先使用工具来获取事实数据，不要凭空编造价格、指标、财务数据或回测结果。
当用户询问个股分析、基本面、市场概览、选股、交易决策、回测、风险控制或报告时，请调用对应工具。
当用户询问模型版本、特征清单、发布门禁、回滚或治理状态时，请调用对应模型治理工具。
当用户询问系统健康、监控、告警、运行状态、指标或最近异常时，请调用对应可观测性工具。
如果同一个问题里同时包含多个分析、回测、风控或报告目标，请优先调用 plan_collaboration 先生成协作计划，再决定后续工具调用顺序。
如果同一个问题里同时包含多个分析、回测、风控或报告目标，并且工具可用，请优先调用 execute_workflow 直接执行完整协作工作流。
如果用户希望快速得到一个可直接使用的业务结果，请优先调用 answer_decision_request 作为统一决策入口。

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
        audit_logger: Optional[RouteAuditLogger] = None,
    ) -> None:
        self.settings = settings or load_agent_settings()
        self.tool_registry = tool_registry or build_default_tool_registry()
        self.audit_logger = audit_logger or get_route_audit_logger()

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
        route = self.parse_intent(user_input)
        collaboration_recommended = should_plan_collaboration(route)
        preferred_tool = self._infer_preferred_tool(user_input, route=route)
        self.audit_logger.record(
            entrypoint="agent.ask",
            input_text=user_input,
            route=route,
            notes=f"preferred_tool={preferred_tool}",
            meta={
                "system_prompt_provided": bool(system_prompt),
                "collaboration_recommended": collaboration_recommended,
            },
        )

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

    def _infer_preferred_tool(self, user_input: str, route: Optional[dict] = None) -> str:
        """根据用户输入做轻量路由，优先选择最相关的工具。"""
        if route is None:
            route = self.parse_intent(user_input)
        return self._infer_preferred_tool_from_route(route)

    def _infer_preferred_tool_from_route(self, route: dict) -> str:
        """根据路由结果选择首轮工具。"""
        if should_plan_collaboration(route):
            if "execute_workflow" in self.tool_registry.list_tools():
                return "execute_workflow"
            if "plan_collaboration" in self.tool_registry.list_tools():
                return "plan_collaboration"
        return route.get("tool", "")

    def plan_collaboration(self, user_input: str) -> dict:
        """直接生成协作计划，供上层调用或调试。"""
        plan = build_collaboration_plan(user_input, default_risk_profile=self.settings.default_risk_profile)
        audit_entry = self.audit_logger.record(
            entrypoint="agent.plan_collaboration",
            input_text=user_input,
            route=plan.route,
            event_type="workflow_plan",
            phase="plan",
            data_source=plan.data_source,
            notes=f"mode={plan.mode}",
            meta={
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
        payload = plan.to_dict()
        payload.setdefault("meta", {})["route_audit_id"] = audit_entry.get("id")
        payload["task_protocol"] = build_task_plan(plan, workflow_id=audit_entry.get("id", "")).to_dict()
        payload["decision_session"] = create_decision_session(
            scenario=str(plan.primary_intent or "workflow"),
            objective=user_input,
            route=plan.route,
            task_protocol=payload["task_protocol"],
            workflow_id=audit_entry.get("id", ""),
            summary=plan.summary,
            meta={
                "template_id": plan.template_id,
                "template_name": plan.template_name,
                "template_hit": plan.template_hit,
            },
        )
        return payload

    def execute_workflow(self, user_input: str) -> dict:
        """直接执行协作工作流，返回统一工作流结果。"""
        result = self.tool_registry.dispatch(
            "execute_workflow",
            {
                "user_input": user_input,
                "risk_profile": self.settings.default_risk_profile,
            },
        )
        if isinstance(result, dict):
            audit_entry = self.audit_logger.record(
                entrypoint="agent.execute_workflow",
                input_text=user_input,
                route=result.get("data", {}).get("plan", {}).get("route", {}),
                event_type="workflow_result",
                phase="result",
                workflow_id=result.get("meta", {}).get("workflow_id"),
                status="degraded" if result.get("meta", {}).get("is_degraded") else "ok",
                data_source=result.get("data_source"),
                notes=f"workflow_id={result.get('meta', {}).get('workflow_id', '')}",
                meta={
                    "workflow_id": result.get("meta", {}).get("workflow_id"),
                    "route_audit_id": result.get("meta", {}).get("route_audit_id"),
                    "template_id": result.get("data", {}).get("template_id") or result.get("meta", {}).get("template_id"),
                    "template_name": result.get("data", {}).get("template_name") or result.get("meta", {}).get("template_name"),
                    "template_reason": result.get("data", {}).get("template_reason") or result.get("meta", {}).get("template_reason"),
                    "template_score": result.get("data", {}).get("template_score") or result.get("meta", {}).get("template_score"),
                    "template_hit": result.get("data", {}).get("template_hit", result.get("meta", {}).get("template_hit", False)),
                },
            )
            result.setdefault("meta", {})["agent_audit_id"] = audit_entry.get("id")
            result["task_protocol"] = build_task_result(result, task_id=result.get("meta", {}).get("workflow_id", ""), workflow_id=result.get("meta", {}).get("workflow_id", "")).to_dict()
            result["decision_session"] = create_decision_session(
                scenario=str(result.get("data", {}).get("plan", {}).get("primary_intent", "workflow") or "workflow"),
                objective=user_input,
                route=result.get("data", {}).get("plan", {}).get("route", {}),
                task_protocol=result.get("task_protocol", {}),
                workflow_id=result.get("meta", {}).get("workflow_id", ""),
                summary=str(result.get("summary", "")),
                status="executed" if result.get("ok", False) else "degraded",
                meta={
                    "template_id": result.get("meta", {}).get("template_id"),
                    "template_name": result.get("meta", {}).get("template_name"),
                    "template_hit": result.get("meta", {}).get("template_hit", False),
                },
            )
        return result

    def parse_intent(self, user_input: str) -> dict:
        """解析自然语言并返回结构化路由结果。"""
        return parse_intent(user_input, default_risk_profile=self.settings.default_risk_profile).to_dict()

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
