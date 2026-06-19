#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体能力目录。

把项目现有能力按场景、优先级和回退路径整理为统一目录，
供智能体做能力发现、路由建议和结果解释。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class CapabilityItem:
    """单条能力描述。"""

    id: str
    name: str
    category: str
    primary_tool: str
    support_tools: List[str] = field(default_factory=list)
    when_to_use: List[str] = field(default_factory=list)
    fallback_tools: List[str] = field(default_factory=list)
    output_contract: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "primary_tool": self.primary_tool,
            "support_tools": list(self.support_tools),
            "when_to_use": list(self.when_to_use),
            "fallback_tools": list(self.fallback_tools),
            "output_contract": list(self.output_contract),
            "notes": self.notes,
        }


CAPABILITY_DIRECTORY_VERSION = "1.0"

CAPABILITY_ITEMS: List[CapabilityItem] = [
    CapabilityItem(
        id="decision.primary",
        name="统一决策入口",
        category="decision",
        primary_tool="answer_decision_request",
        support_tools=["plan_collaboration", "execute_workflow"],
        when_to_use=["用户希望快速得到可直接使用的业务结果", "问题需要自动路由和统一输出"],
        fallback_tools=["plan_collaboration", "execute_workflow"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="当前项目最适合优先推荐的对外入口。",
    ),
    CapabilityItem(
        id="workflow.execution",
        name="协作工作流",
        category="workflow",
        primary_tool="execute_workflow",
        support_tools=["plan_collaboration", "list_workflow_templates"],
        when_to_use=["用户需求同时包含分析、推荐、风控、回测、报告", "需要多步骤串联执行"],
        fallback_tools=["plan_collaboration", "answer_decision_request"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="适合复杂问题的主执行路径。",
    ),
    CapabilityItem(
        id="market.overview",
        name="市场概览",
        category="market",
        primary_tool="get_market_overview",
        support_tools=["get_risk_profile"],
        when_to_use=["用户问市场、大盘、行情、盘面", "需要先看环境再做决策"],
        fallback_tools=["recommend_by_risk"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="适合作为分析链路的前置入口。",
    ),
    CapabilityItem(
        id="risk.profile",
        name="风控配置",
        category="risk",
        primary_tool="get_risk_profile",
        support_tools=["get_market_overview", "answer_decision_request"],
        when_to_use=["用户问风控、仓位、风险等级", "需要确认保守/稳健/激进偏好"],
        fallback_tools=["answer_decision_request"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="用于先收紧约束，再展开分析。",
    ),
    CapabilityItem(
        id="analysis.stock",
        name="个股分析",
        category="analysis",
        primary_tool="analyze_stock",
        support_tools=["analyze_fundamental", "generate_stock_report"],
        when_to_use=["用户给出股票代码并要求分析", "需要技术面与风险判断"],
        fallback_tools=["generate_stock_report"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="适合进入深度分析链路。",
    ),
    CapabilityItem(
        id="recommendation.risk",
        name="风险匹配推荐",
        category="recommendation",
        primary_tool="recommend_by_risk",
        support_tools=["recommend_long_term", "recommend_short_term", "screen_stocks"],
        when_to_use=["用户问买什么、推荐什么、适合什么", "用户未明确长线或短线"],
        fallback_tools=["recommend_long_term", "recommend_short_term"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="默认推荐入口，适合大多数开放式提问。",
    ),
    CapabilityItem(
        id="verification.backtest",
        name="回测验证",
        category="verification",
        primary_tool="run_backtest",
        support_tools=["answer_decision_request", "execute_workflow"],
        when_to_use=["用户明确提到回测", "需要验证策略有效性"],
        fallback_tools=["execute_workflow"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="用于结果复验，不用于口头结论替代。",
    ),
    CapabilityItem(
        id="reporting.summary",
        name="结构化报告",
        category="report",
        primary_tool="generate_stock_report",
        support_tools=["analyze_stock", "run_backtest"],
        when_to_use=["用户要求总结、报告、复盘", "需要把分析结果整理成可读结构"],
        fallback_tools=["answer_decision_request"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="作为最终交付物的收口能力。",
    ),
    CapabilityItem(
        id="governance.runtime",
        name="运行监控与健康检查",
        category="governance",
        primary_tool="get_runtime_health",
        support_tools=["evaluate_runtime_health"],
        when_to_use=["需要查看运行健康", "需要判断是否存在异常和告警"],
        fallback_tools=["evaluate_runtime_health"],
        output_contract=["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        notes="用于排查系统运行状态。",
    ),
]


def list_capability_directory() -> dict:
    """返回能力目录快照。"""
    high_value_paths = [
        "answer_decision_request -> 统一决策",
        "execute_workflow -> 复杂需求串联",
        "recommend_by_risk -> 默认推荐",
        "run_backtest -> 结果验证",
        "get_market_overview -> 市场前置",
        "get_risk_profile -> 风控前置",
        "generate_stock_report -> 结果收口",
    ]
    recommended_path = [
        "先问清目标",
        "再走统一决策或工作流",
        "复杂场景优先工作流",
        "开放式提问优先风险匹配推荐",
    ]
    fallback_path = [
        "统一决策失败时回退到协作计划",
        "工作流失败时回退到分步工具",
        "业务结果不足时回退到报告或摘要",
    ]
    next_actions = [
        "补充目录工具入口",
        "把能力目录接入智能体路由",
        "把目录沉淀到知识库",
    ]
    return {
        "directory_version": CAPABILITY_DIRECTORY_VERSION,
        "focus": "agent_capability_directory",
        "capabilities": [item.to_dict() for item in CAPABILITY_ITEMS],
        "recommended_path": recommended_path,
        "fallback_path": fallback_path,
        "high_value_paths": high_value_paths,
        "next_actions": next_actions,
        "meta": {
            "total_capabilities": len(CAPABILITY_ITEMS),
            "categories": sorted({item.category for item in CAPABILITY_ITEMS}),
            "output_contract": ["ok", "tool", "category", "data_source", "summary", "data", "meta"],
        },
    }


def build_capability_lookup() -> Dict[str, CapabilityItem]:
    """构建按工具名索引的能力映射。"""
    lookup: Dict[str, CapabilityItem] = {}
    for item in CAPABILITY_ITEMS:
        lookup[item.primary_tool] = item
        for tool_name in item.support_tools:
            lookup.setdefault(tool_name, item)
        for tool_name in item.fallback_tools:
            lookup.setdefault(tool_name, item)
    return lookup

