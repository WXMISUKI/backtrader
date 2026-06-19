#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体标准工作流模板

用于将高价值协作链路固化为可复用模板。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class WorkflowTemplate:
    """标准工作流模板。"""

    id: str
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    trigger_intents: List[str] = field(default_factory=list)
    task_specs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "keywords": list(self.keywords),
            "trigger_intents": list(self.trigger_intents),
            "task_specs": [dict(spec) for spec in self.task_specs],
        }


WORKFLOW_TEMPLATES: List[WorkflowTemplate] = [
    WorkflowTemplate(
        id="market_risk_analysis",
        name="市场风控分析模板",
        description="先看市场和风控，再做个股分析并输出报告。",
        keywords=["市场", "风控", "分析", "报告"],
        trigger_intents=["analyze_stock", "market_overview", "risk_profile", "report"],
        task_specs=[
            {
                "id": "market",
                "intent": "market_overview",
                "tool": "get_market_overview",
                "role": "market_analyst",
                "description": "先补充市场背景和情绪信息。",
                "priority": 10,
            },
            {
                "id": "risk",
                "intent": "risk_profile",
                "tool": "get_risk_profile",
                "role": "risk_guard",
                "description": "先确认风险偏好、仓位和约束。",
                "priority": 12,
            },
            {
                "id": "analyze",
                "intent": "analyze_stock",
                "tool": "analyze_stock",
                "role": "equity_analyst",
                "description": "执行个股分析，形成可解释结论。",
                "priority": 30,
            },
            {
                "id": "report",
                "intent": "report",
                "tool": "generate_stock_report",
                "role": "report_writer",
                "description": "整理最终结构化报告。",
                "priority": 90,
            },
        ],
    ),
    WorkflowTemplate(
        id="recommendation_validation",
        name="推荐验证模板",
        description="先推荐，再回测，再输出验证报告。",
        keywords=["推荐", "回测", "验证"],
        trigger_intents=["recommend", "recommend_long_term", "recommend_short_term", "backtest", "report"],
        task_specs=[
            {
                "id": "market",
                "intent": "market_overview",
                "tool": "get_market_overview",
                "role": "market_analyst",
                "description": "先补充市场背景和情绪信息。",
                "priority": 10,
            },
            {
                "id": "recommend",
                "intent": "recommend",
                "tool": "recommend_by_risk",
                "role": "portfolio_advisor",
                "description": "生成统一推荐结果。",
                "priority": 42,
            },
            {
                "id": "backtest",
                "intent": "backtest",
                "tool": "run_backtest",
                "role": "backtest_executor",
                "description": "对策略进行回测复验。",
                "priority": 60,
            },
            {
                "id": "report",
                "intent": "report",
                "tool": "generate_stock_report",
                "role": "report_writer",
                "description": "整理最终结构化报告。",
                "priority": 90,
            },
        ],
    ),
    WorkflowTemplate(
        id="screening_research",
        name="选股研究模板",
        description="先选股，再做基本面和风控分析，最后输出报告。",
        keywords=["选股", "筛选", "基本面"],
        trigger_intents=["screen_stocks", "fundamental", "risk_profile", "report"],
        task_specs=[
            {
                "id": "screen",
                "intent": "screen_stocks",
                "tool": "screen_stocks",
                "role": "stock_screener",
                "description": "筛选候选股票池。",
                "priority": 10,
            },
            {
                "id": "fundamental",
                "intent": "fundamental",
                "tool": "analyze_fundamental",
                "role": "fundamental_analyst",
                "description": "补充基本面信息，辅助分析判断。",
                "priority": 20,
            },
            {
                "id": "risk",
                "intent": "risk_profile",
                "tool": "get_risk_profile",
                "role": "risk_guard",
                "description": "先确认风险偏好、仓位和约束。",
                "priority": 30,
            },
            {
                "id": "report",
                "intent": "report",
                "tool": "generate_stock_report",
                "role": "report_writer",
                "description": "整理最终结构化报告。",
                "priority": 90,
            },
        ],
    ),
]


def list_workflow_templates() -> list[dict]:
    """列出所有模板。"""
    return [template.to_dict() for template in WORKFLOW_TEMPLATES]


def select_workflow_template(user_input: str, route: Optional[dict] = None) -> Optional[dict]:
    """根据用户输入和路由结果选择模板。"""
    route = route or {}
    text = user_input.lower()
    intent = str(route.get("intent", ""))
    tool = str(route.get("tool", ""))

    template, selected_by = _choose_by_keywords(text, intent, tool)
    if template is None and tool == "generate_stock_report" and _contains_any(text, ["市场", "风控"]):
        template = _template_by_id("market_risk_analysis")
        selected_by = "report_hint"

    if template is not None:
        payload = template.to_dict()
        payload["template_hit"] = True
        payload["selected_by"] = selected_by or "route"
        payload["template_reason"] = _build_template_reason(template, intent, tool, route, text, selected_by)
        return payload

    return None


def build_template_task_specs(template: dict, *, route: Optional[dict] = None, default_risk_profile: str = "moderate") -> list[dict]:
    """将模板转为可执行任务规格。"""
    route = route or {}
    task_specs: list[dict] = []
    stock_code = _extract_stock_code(route, default_stock_code="000001")
    risk_profile = _extract_risk_profile(route, default_risk_profile=default_risk_profile)

    for spec in template.get("task_specs", []):
        task_spec = dict(spec)
        task_spec["arguments"] = _build_arguments(task_spec["intent"], stock_code=stock_code, risk_profile=risk_profile)
        task_specs.append(task_spec)

    return task_specs


def _choose_by_keywords(text: str, intent: str, tool: str) -> tuple[Optional[WorkflowTemplate], str]:
    if intent in {"recommend", "recommend_long_term", "recommend_short_term", "backtest"}:
        return _template_by_id("recommendation_validation"), "intent"
    if intent in {"screen_stocks", "fundamental"}:
        return _template_by_id("screening_research"), "intent"
    if intent in {"analyze_stock", "market_overview", "risk_profile"}:
        return _template_by_id("market_risk_analysis"), "intent"

    if _contains_any(text, ["推荐", "回测", "验证"]):
        return _template_by_id("recommendation_validation"), "keywords"
    if _contains_any(text, ["选股", "筛选", "基本面"]):
        return _template_by_id("screening_research"), "keywords"
    if _contains_any(text, ["市场", "风控", "分析", "报告"]):
        return _template_by_id("market_risk_analysis"), "keywords"
    return None, ""


def _template_by_id(template_id: str) -> WorkflowTemplate:
    for template in WORKFLOW_TEMPLATES:
        if template.id == template_id:
            return template
    raise KeyError(f"unknown workflow template: {template_id}")


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _build_template_reason(
    template: WorkflowTemplate,
    intent: str,
    tool: str,
    route: dict,
    text: str,
    selected_by: str,
) -> str:
    matched_terms = route.get("matched_terms") or []
    if selected_by == "intent":
        return f"命中意图 {intent}，使用模板《{template.name}》。"
    if selected_by == "report_hint":
        return f"报告请求同时包含市场/风控语义，使用模板《{template.name}》。"
    if matched_terms:
        return f"命中关键词 {', '.join(str(term) for term in matched_terms[:3])}，使用模板《{template.name}》。"
    if tool == "execute_workflow" or intent == "workflow":
        return f"工作流请求使用模板《{template.name}》。"
    if _contains_any(text, list(template.keywords)):
        return f"命中模板关键词，使用模板《{template.name}》。"
    return f"使用模板《{template.name}》。"


def _extract_stock_code(route: dict, *, default_stock_code: str) -> str:
    arguments = route.get("arguments") if isinstance(route, dict) else {}
    if isinstance(arguments, dict):
        value = arguments.get("stock_code")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default_stock_code


def _extract_risk_profile(route: dict, *, default_risk_profile: str) -> str:
    arguments = route.get("arguments") if isinstance(route, dict) else {}
    if isinstance(arguments, dict):
        value = arguments.get("risk_profile")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default_risk_profile


def _build_arguments(intent: str, *, stock_code: str, risk_profile: str) -> dict:
    if intent == "market_overview":
        return {}
    if intent == "risk_profile":
        return {"risk_profile": risk_profile}
    if intent == "analyze_stock":
        return {"stock_code": stock_code, "risk_profile": risk_profile}
    if intent == "recommend":
        return {"risk_profile": risk_profile, "top_n": 5}
    if intent == "recommend_long_term":
        return {"top_n": 5}
    if intent == "recommend_short_term":
        return {"top_n": 5}
    if intent == "backtest":
        return {
            "stock_code": stock_code,
            "strategy_name": "ma_cross",
            "start_date": "20260101",
            "end_date": "20260614",
            "initial_cash": 100000,
        }
    if intent == "screen_stocks":
        return {"risk_profile": risk_profile}
    if intent == "fundamental":
        return {"stock_code": stock_code}
    if intent == "report":
        return {"stock_code": stock_code, "risk_profile": risk_profile}
    return {}
