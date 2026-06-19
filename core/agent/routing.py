#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体共享路由

为 ArkAgentClient 与 StockOrchestrator 提供统一的意图解析逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Any, Dict, List


@dataclass(frozen=True)
class IntentRoute:
    """结构化意图路由结果。"""

    intent: str
    tool: str
    confidence: float
    reason: str
    arguments: Dict[str, Any]
    candidates: List[Dict[str, Any]] = None
    matched_terms: List[str] = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["candidates"] = payload.get("candidates") or []
        payload["matched_terms"] = payload.get("matched_terms") or []
        return payload


ROUTE_RULES = [
    {
        "intent": "workflow",
        "tool": "execute_workflow",
        "priority": 110,
        "keywords": ["工作流", "流程", "串联", "联动", "协作", "一条龙", "完整", "综合", "依次"],
        "confidence": 0.99,
    },
    {
        "intent": "backtest",
        "tool": "run_backtest",
        "priority": 100,
        "keywords": ["回测", "backtest"],
        "confidence": 0.98,
    },
    {
        "intent": "market_overview",
        "tool": "get_market_overview",
        "priority": 90,
        "keywords": ["市场", "大盘", "行情", "market"],
        "confidence": 0.97,
    },
    {
        "intent": "risk_profile",
        "tool": "get_risk_profile",
        "priority": 80,
        "keywords": ["风控", "仓位", "风险"],
        "confidence": 0.96,
    },
    {
        "intent": "model_governance",
        "tool": "get_model_governance_status",
        "priority": 85,
        "keywords": ["模型", "版本", "特征", "门禁", "回滚"],
        "confidence": 0.95,
    },
    {
        "intent": "report",
        "tool": "generate_stock_report",
        "priority": 70,
        "keywords": ["报告", "report"],
        "confidence": 0.95,
    },
    {
        "intent": "fundamental",
        "tool": "analyze_fundamental",
        "priority": 60,
        "keywords": ["基本面"],
        "confidence": 0.94,
    },
    {
        "intent": "recommend_long_term",
        "tool": "recommend_long_term",
        "priority": 55,
        "keywords": ["长线", "长期", "中长线"],
        "confidence": 0.93,
    },
    {
        "intent": "recommend_short_term",
        "tool": "recommend_short_term",
        "priority": 50,
        "keywords": ["短线", "短期"],
        "confidence": 0.93,
    },
    {
        "intent": "recommend",
        "tool": "recommend_by_risk",
        "priority": 40,
        "keywords": ["推荐", "适合", "买什么", "买哪些", "配置"],
        "confidence": 0.91,
    },
    {
        "intent": "screen_stocks",
        "tool": "screen_stocks",
        "priority": 30,
        "keywords": ["选股", "筛选"],
        "confidence": 0.92,
    },
    {
        "intent": "analyze_stock",
        "tool": "analyze_stock",
        "priority": 20,
        "keywords": ["分析", "建议", "买", "卖"],
        "confidence": 0.9,
    },
]


def parse_intent(user_input: str, *, default_risk_profile: str = "moderate") -> IntentRoute:
    """将自然语言解析为结构化意图。"""
    text = user_input.lower()
    stock_code = _extract_stock_code(user_input)
    risk_profile = _extract_risk_profile(user_input, default_risk_profile=default_risk_profile)
    matched_terms = _collect_matched_terms(text, user_input)

    candidates = []
    for rule in ROUTE_RULES:
        rule_matches = _rule_matches(rule, user_input, text)
        if not rule_matches:
            continue

        score = rule["priority"] * 100 + len(rule_matches) * 10 + int(rule["confidence"] * 100)
        candidates.append(
            {
                "intent": rule["intent"],
                "tool": rule["tool"],
                "confidence": rule["confidence"],
                "priority": rule["priority"],
                "score": score,
                "matched_terms": rule_matches,
            }
        )

    if candidates:
        candidates.sort(key=lambda item: item["score"], reverse=True)
        chosen = candidates[0]
        reason = _build_reason(chosen, candidates)
        return IntentRoute(
            intent=chosen["intent"],
            tool=chosen["tool"],
            confidence=chosen["confidence"],
            reason=reason,
            arguments=_build_arguments(chosen["intent"], stock_code, risk_profile),
            candidates=[{k: v for k, v in item.items() if k != "score"} for item in candidates],
            matched_terms=matched_terms,
        )

    return IntentRoute(
        intent="recommend",
        tool="recommend_by_risk",
        confidence=0.5,
        reason="未命中明确意图，使用默认推荐",
        arguments={
            "risk_profile": risk_profile,
            "top_n": 5,
        },
        candidates=[],
        matched_terms=matched_terms,
    )


def _extract_stock_code(user_input: str) -> str:
    match = re.search(r"\b\d{6}\b", user_input)
    return match.group(0) if match else ""


def _extract_risk_profile(user_input: str, *, default_risk_profile: str = "moderate") -> str:
    if any(keyword in user_input for keyword in ["保守", "稳健", "conservative"]):
        return "conservative"
    if any(keyword in user_input for keyword in ["激进", "aggressive"]):
        return "aggressive"
    return default_risk_profile


def _rule_matches(rule: dict, raw_input: str, lower_input: str) -> list[str]:
    matches = []
    for keyword in rule["keywords"]:
        if keyword in raw_input or keyword.lower() in lower_input:
            matches.append(keyword)
    return matches


def _collect_matched_terms(lower_input: str, raw_input: str) -> list[str]:
    terms = [
        "工作流",
        "流程",
        "串联",
        "联动",
        "协作",
        "一条龙",
        "完整",
        "综合",
        "回测",
        "市场",
        "大盘",
        "行情",
        "风控",
        "仓位",
        "风险",
        "模型",
        "版本",
        "特征",
        "门禁",
        "回滚",
        "报告",
        "基本面",
        "长线",
        "短线",
        "推荐",
        "选股",
        "筛选",
        "分析",
        "建议",
        "买",
        "卖",
    ]
    matched = []
    for term in terms:
        if term in raw_input or term.lower() in lower_input:
            matched.append(term)
    return matched


def _build_reason(chosen: dict, candidates: list[dict]) -> str:
    if len(candidates) == 1:
        return f"命中{chosen['intent']}关键词"

    other_intents = [item["intent"] for item in candidates[1:]]
    return f"同时命中{', '.join(other_intents)}，按优先级选择{chosen['intent']}"


def _build_arguments(intent: str, stock_code: str, risk_profile: str) -> dict:
    if intent == "workflow":
        return {"risk_profile": risk_profile}
    if intent == "backtest":
        return {
            "stock_code": stock_code or "000001",
            "strategy_name": "ma_cross",
            "start_date": "20260101",
            "end_date": "20260614",
            "initial_cash": 100000,
        }
    if intent == "market_overview":
        return {}
    if intent == "model_governance":
        return {}
    if intent == "risk_profile":
        return {"risk_profile": risk_profile}
    if intent == "report":
        return {
            "stock_code": stock_code or "000001",
            "risk_profile": risk_profile,
        }
    if intent == "fundamental":
        return {"stock_code": stock_code or "000001"}
    if intent in {"recommend_long_term", "recommend_short_term"}:
        return {"top_n": 5}
    if intent == "screen_stocks":
        return {}
    if intent == "analyze_stock":
        return {
            "stock_code": stock_code or "000001",
            "risk_profile": risk_profile,
        }
    return {
        "risk_profile": risk_profile,
        "top_n": 5,
    }
