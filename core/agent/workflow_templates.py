#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体标准工作流模板

用于将高价值协作链路固化为可复用模板。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .template_metrics import record_workflow_template_usage


@dataclass(frozen=True)
class WorkflowTemplate:
    """标准工作流模板。"""

    id: str
    name: str
    description: str
    priority: int = 0
    keywords: List[str] = field(default_factory=list)
    trigger_intents: List[str] = field(default_factory=list)
    task_specs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "keywords": list(self.keywords),
            "trigger_intents": list(self.trigger_intents),
            "task_specs": [dict(spec) for spec in self.task_specs],
        }


WORKFLOW_TEMPLATES: List[WorkflowTemplate] = [
    WorkflowTemplate(
        id="pre_market_overview",
        name="盘前概览模板",
        description="盘前先看市场环境、风控约束、运行健康和风险匹配推荐摘要。",
        priority=100,
        keywords=["盘前", "盘前概览", "开盘前", "早盘", "早盘准备", "今日盘前"],
        trigger_intents=["pre_market_overview", "market_overview", "risk_profile", "runtime_health", "recommend"],
        task_specs=[
            {
                "id": "market",
                "intent": "market_overview",
                "tool": "get_market_overview",
                "role": "market_analyst",
                "description": "先确认盘前市场环境和情绪信息。",
                "priority": 10,
            },
            {
                "id": "risk",
                "intent": "risk_profile",
                "tool": "get_risk_profile",
                "role": "risk_guard",
                "description": "先确认当日风险约束和仓位边界。",
                "priority": 15,
            },
            {
                "id": "health",
                "intent": "runtime_health",
                "tool": "get_runtime_health",
                "role": "observability_guard",
                "description": "检查系统运行健康，确认是否存在异常。",
                "priority": 20,
            },
            {
                "id": "recommend",
                "intent": "recommend",
                "tool": "recommend_by_risk",
                "role": "portfolio_advisor",
                "description": "给出风险匹配的盘前关注摘要。",
                "priority": 40,
            },
        ],
    ),
    WorkflowTemplate(
        id="market_risk_analysis",
        name="市场风控分析模板",
        description="先看市场和风控，再做个股分析并输出报告。",
        priority=90,
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
        priority=80,
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
        priority=70,
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

    candidates = _rank_templates(text, intent, tool, route)
    if candidates:
        candidates.sort(key=lambda item: (item["score"], item["priority"], item["template"].id), reverse=True)
        chosen = candidates[0]
        template = chosen["template"]
        selected_by = chosen["selected_by"]
        template_score = chosen["score"]
    else:
        template = None
        selected_by = ""
        template_score = 0.0

    if template is not None:
        payload = template.to_dict()
        payload["template_hit"] = True
        payload["selected_by"] = selected_by or "route"
        payload["template_score"] = template_score
        payload["template_reason"] = _build_template_reason(template, intent, tool, route, text, selected_by, template_score)
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


def _rank_templates(text: str, intent: str, tool: str, route: dict) -> list[dict]:
    ranked: list[dict] = []
    matched_terms = list(route.get("matched_terms") or [])
    candidate_intents = [str(item.get("intent", "")) for item in route.get("candidates", []) or []]

    for template in WORKFLOW_TEMPLATES:
        score, selected_by = _score_template(template, text, intent, tool, matched_terms, candidate_intents)
        if score > 0:
            ranked.append(
                {
                    "template": template,
                    "score": score,
                    "selected_by": selected_by,
                    "priority": template.priority,
                }
            )
    return ranked


def _score_template(
    template: WorkflowTemplate,
    text: str,
    intent: str,
    tool: str,
    matched_terms: List[str],
    candidate_intents: List[str],
) -> tuple[float, str]:
    score = float(template.priority)
    reasons: List[str] = []
    strong_signal_count = 0

    intent_matches = [item for item in template.trigger_intents if item == intent or item in candidate_intents]
    if intent_matches:
        score += 120
        reasons.append("intent")
        strong_signal_count += 1

    keyword_matches = [keyword for keyword in template.keywords if keyword in text]
    if keyword_matches:
        score += 20 * len(keyword_matches)
        reasons.append("keywords")
        strong_signal_count += 1

    route_matches = [term for term in matched_terms if term in template.keywords]
    if route_matches:
        score += 10 * len(route_matches)
        reasons.append("matched_terms")
        strong_signal_count += 1

    if tool == "execute_workflow":
        score += 15
        reasons.append("workflow")

    if tool == "generate_stock_report" and "report" in template.trigger_intents:
        score += 8
        reasons.append("report_hint")
        strong_signal_count += 1

    if tool in {spec.get("tool") for spec in template.task_specs}:
        score += 25
        reasons.append("tool")
        strong_signal_count += 1

    if not reasons or strong_signal_count == 0:
        return 0.0, ""

    return score, reasons[0]


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
    template_score: float,
) -> str:
    matched_terms = route.get("matched_terms") or []
    if selected_by == "intent":
        return f"命中意图 {intent}，使用模板《{template.name}》，评分 {template_score:.1f}。"
    if selected_by == "report_hint":
        return f"报告请求同时包含市场/风控语义，使用模板《{template.name}》，评分 {template_score:.1f}。"
    if selected_by == "runtime_health":
        return f"盘前健康检查命中运行健康语义，使用模板《{template.name}》，评分 {template_score:.1f}。"
    if matched_terms:
        return f"命中关键词 {', '.join(str(term) for term in matched_terms[:3])}，使用模板《{template.name}》，评分 {template_score:.1f}。"
    if tool == "execute_workflow" or intent == "workflow":
        return f"工作流请求使用模板《{template.name}》，评分 {template_score:.1f}。"
    if _contains_any(text, list(template.keywords)):
        return f"命中模板关键词，使用模板《{template.name}》，评分 {template_score:.1f}。"
    return f"使用模板《{template.name}》，评分 {template_score:.1f}。"


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
    if intent == "pre_market_overview":
        return {}
    if intent == "risk_profile":
        return {"risk_profile": risk_profile}
    if intent == "runtime_health":
        return {"window_size": 50}
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
