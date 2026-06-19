#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
StockOrchestrator 统一编排入口

负责把项目现有业务能力收束为统一入口，避免上层直接拼接底层算法。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .agent.audit import RouteAuditLogger, get_route_audit_logger
from .agent.collaboration import build_collaboration_plan, should_plan_collaboration
from .agent.workflow import execute_collaboration_workflow
from .agent import build_default_tool_registry
from .agent.routing import parse_intent
from .model import get_model_governance_service
from .data import CacheManager, DataQualityChecker, build_snapshot


@dataclass(frozen=True)
class OrchestratorResult:
    """统一编排结果。"""

    ok: bool
    action: str
    tool: str
    category: str
    data_source: Optional[str]
    summary: str
    data: Any
    meta: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "action": self.action,
            "tool": self.tool,
            "category": self.category,
            "data_source": self.data_source,
            "summary": self.summary,
            "data": self.data,
            "meta": self.meta,
        }


class StockOrchestrator:
    """统一编排器。"""

    def __init__(self, tool_registry=None, audit_logger: Optional[RouteAuditLogger] = None) -> None:
        self.tool_registry = tool_registry or build_default_tool_registry()
        self.cache = CacheManager()
        self.quality = DataQualityChecker()
        self.audit_logger = audit_logger or get_route_audit_logger()

    def analyze(self, stock_code: str, risk_profile: str = "moderate") -> dict:
        """执行个股分析。"""
        return self._dispatch_with_data_governance(
            action="analyze",
            tool_name="analyze_stock",
            arguments={
                "stock_code": stock_code,
                "risk_profile": risk_profile,
            },
            cache_key=f"analyze:{stock_code}:{risk_profile}",
            cache_ttl=300,
        )

    def recommend(self, risk_profile: str = "moderate", top_n: int = 5) -> dict:
        """执行统一推荐。"""
        return self._dispatch_with_data_governance(
            action="recommend",
            tool_name="recommend_by_risk",
            arguments={
                "risk_profile": risk_profile,
                "top_n": top_n,
            },
            cache_key=f"recommend:{risk_profile}:{top_n}",
            cache_ttl=300,
        )

    def market_overview(self) -> dict:
        """获取市场概览。"""
        return self._dispatch_with_data_governance(
            action="market_overview",
            tool_name="get_market_overview",
            arguments={},
            cache_key="market_overview",
            cache_ttl=60,
        )

    def risk_profile(self, risk_profile: str = "moderate") -> dict:
        """获取风险配置。"""
        return self._dispatch_with_data_governance(
            action="risk_profile",
            tool_name="get_risk_profile",
            arguments={
                "risk_profile": risk_profile,
            },
            cache_key=f"risk_profile:{risk_profile}",
            cache_ttl=3600,
        )

    def backtest(self, stock_code: str, strategy_name: str, **kwargs) -> dict:
        """执行回测。"""
        payload = {
            "stock_code": stock_code,
            "strategy_name": strategy_name,
        }
        payload.update(kwargs)
        return self._dispatch_with_data_governance(
            action="backtest",
            tool_name="run_backtest",
            arguments=payload,
            cache_key=f"backtest:{stock_code}:{strategy_name}:{payload.get('start_date', '20260101')}:{payload.get('end_date', '20260614')}",
            cache_ttl=300,
        )

    def report(self, stock_code: str, risk_profile: str = "moderate") -> dict:
        """生成报告。"""
        return self._dispatch_with_data_governance(
            action="report",
            tool_name="generate_stock_report",
            arguments={
                "stock_code": stock_code,
                "risk_profile": risk_profile,
            },
            cache_key=f"report:{stock_code}:{risk_profile}",
            cache_ttl=300,
        )

    def route(self, user_input: str, **kwargs) -> dict:
        """
        根据自然语言意图路由到最合适的能力。

        该入口用于智能体或上层控制器直接调用。
        """
        route = self.parse_intent(user_input)
        collaboration_recommended = should_plan_collaboration(route)
        tool_name = route.get("tool", "recommend_by_risk")
        arguments = dict(route.get("arguments", {}))
        arguments.update({k: v for k, v in kwargs.items() if v is not None})

        if tool_name == "run_backtest":
            arguments.setdefault("stock_code", "000001")
            arguments.setdefault("strategy_name", "ma_cross")
            arguments.setdefault("start_date", "20260101")
            arguments.setdefault("end_date", "20260614")
            arguments.setdefault("initial_cash", 100000)
            result = self._dispatch_with_data_governance(
                action="backtest",
                tool_name=tool_name,
                arguments=arguments,
                cache_key=f"route:backtest:{arguments.get('stock_code')}:{arguments.get('strategy_name')}",
                cache_ttl=300,
            )
        elif tool_name == "get_market_overview":
            result = self.market_overview()
        elif tool_name == "get_risk_profile":
            result = self.risk_profile(risk_profile=arguments.get("risk_profile", kwargs.get("risk_profile", "moderate")))
        elif tool_name == "generate_stock_report":
            result = self.report(
                stock_code=arguments.get("stock_code", kwargs.get("stock_code", "000001")),
                risk_profile=arguments.get("risk_profile", kwargs.get("risk_profile", "moderate")),
            )
        elif tool_name == "plan_collaboration":
            result = self.plan_collaboration(
                user_input,
                risk_profile=arguments.get("risk_profile", kwargs.get("risk_profile", "moderate")),
            )
        elif tool_name == "execute_workflow":
            result = self.execute_workflow(
                user_input,
                risk_profile=arguments.get("risk_profile", kwargs.get("risk_profile", "moderate")),
            )
        elif tool_name == "analyze_fundamental":
            result = self._dispatch_with_data_governance(
                action="fundamental",
                tool_name=tool_name,
                arguments=arguments or {"stock_code": "000001"},
                cache_key=f"route:fundamental:{arguments.get('stock_code', kwargs.get('stock_code', '000001'))}",
                cache_ttl=300,
            )
        elif tool_name == "recommend_long_term":
            result = self._dispatch_with_data_governance(
                action="recommend",
                tool_name=tool_name,
                arguments=arguments or {"top_n": 5},
                cache_key=f"route:recommend_long:{arguments.get('top_n', 5)}",
                cache_ttl=300,
            )
        elif tool_name == "recommend_short_term":
            result = self._dispatch_with_data_governance(
                action="recommend",
                tool_name=tool_name,
                arguments=arguments or {"top_n": 5},
                cache_key=f"route:recommend_short:{arguments.get('top_n', 5)}",
                cache_ttl=300,
            )
        elif tool_name == "screen_stocks":
            result = self._dispatch_with_data_governance(
                action="screen",
                tool_name=tool_name,
                arguments=arguments,
                cache_key="route:screen_stocks",
                cache_ttl=300,
            )
        elif tool_name == "get_model_governance_status":
            result = self.model_governance_status(model_name=arguments.get("model_name"))
        elif tool_name == "analyze_stock":
            result = self.analyze(
                stock_code=arguments.get("stock_code", kwargs.get("stock_code", "000001")),
                risk_profile=arguments.get("risk_profile", kwargs.get("risk_profile", "moderate")),
            )
        else:
            result = self.recommend(
                risk_profile=arguments.get("risk_profile", kwargs.get("risk_profile", "moderate")),
                top_n=int(arguments.get("top_n", kwargs.get("top_n", 5))),
            )

        result_meta = dict(result.get("meta", {}))
        result_meta["route"] = route
        result_meta["collaboration_recommended"] = collaboration_recommended
        governance = dict(result.get("governance", {}))
        governance["route"] = route
        governance["collaboration_recommended"] = collaboration_recommended
        result["meta"] = result_meta
        result["governance"] = governance
        audit_entry = self.audit_logger.record(
            entrypoint="orchestrator.route",
            input_text=user_input,
            route=route,
            data_source=result.get("data_source"),
            notes=f"tool={route.get('tool')}",
            meta={
                "cache_hit": bool(governance.get("cache_hit")),
                "is_degraded": bool(governance.get("is_degraded")),
                "collaboration_recommended": collaboration_recommended,
            },
        )
        result["meta"]["route_audit_id"] = audit_entry.get("id")
        result["governance"]["route_audit_id"] = audit_entry.get("id")
        return result

    def plan_collaboration(self, user_input: str, **kwargs) -> dict:
        """根据自然语言生成协作计划。"""
        default_risk_profile = kwargs.get("risk_profile", "moderate")
        plan = build_collaboration_plan(user_input, default_risk_profile=default_risk_profile)
        audit_entry = self.audit_logger.record(
            entrypoint="orchestrator.plan_collaboration",
            input_text=user_input,
            route=plan.route,
            event_type="workflow_plan",
            phase="plan",
            data_source=plan.data_source,
            notes=f"mode={plan.mode}",
            meta={
                "planner_version": plan.meta.get("planner_version"),
                "task_count": len(plan.tasks),
                "collaboration_recommended": plan.meta.get("collaboration_recommended", False),
            },
        )
        payload = OrchestratorResult(
            ok=True,
            action="collaboration_plan",
            tool="plan_collaboration",
            category="workflow",
            data_source=plan.data_source,
            summary=plan.summary,
            data=plan.to_dict(),
            meta={
                "orchestrator": "StockOrchestrator",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "collaboration_recommended": plan.meta.get("collaboration_recommended", False),
            },
        ).to_dict()
        payload["meta"]["route_audit_id"] = audit_entry.get("id")
        payload["governance"] = {
            "collaboration_recommended": plan.meta.get("collaboration_recommended", False),
            "collaboration_mode": plan.mode,
            "task_count": len(plan.tasks),
            "route_audit_id": audit_entry.get("id"),
        }
        return payload

    def execute_workflow(self, user_input: str, **kwargs) -> dict:
        """执行协作工作流。"""
        default_risk_profile = kwargs.get("risk_profile", "moderate")
        result = execute_collaboration_workflow(
            user_input,
            self.tool_registry,
            default_risk_profile=default_risk_profile,
            audit_logger=self.audit_logger,
        )
        if isinstance(result, dict):
            result.setdefault("meta", {})["orchestrator"] = "StockOrchestrator"
            result.setdefault("governance", {})["workflow_mode"] = result.get("data", {}).get("mode")
            result["governance"]["is_degraded"] = result.get("meta", {}).get("is_degraded", False)
        return result

    def _dispatch(self, action: str, tool_name: str, arguments: dict) -> dict:
        tool_result = self.tool_registry.dispatch(tool_name, arguments)
        data = tool_result.get("data")
        governance = self._infer_governance(tool_result, data)
        return OrchestratorResult(
            ok=bool(tool_result.get("ok", False)),
            action=action,
            tool=tool_result.get("tool", tool_name),
            category=tool_result.get("category", "analysis"),
            data_source=tool_result.get("data_source"),
            summary=tool_result.get("summary", ""),
            data=data,
            meta={
                **tool_result.get("meta", {}),
                "orchestrator": "StockOrchestrator",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "governance": governance,
            },
        ).to_dict()

    def _dispatch_with_data_governance(
        self,
        action: str,
        tool_name: str,
        arguments: dict,
        *,
        cache_key: str,
        cache_ttl: int,
    ) -> dict:
        cached = self.cache.get(cache_key)
        if cached is not None:
            payload = dict(cached) if isinstance(cached, dict) else {"data": cached}
            governance = dict(payload.get("governance", {}))
            governance.update(
                {
                    "cache_key": cache_key,
                    "cache_ttl": cache_ttl,
                    "cache_hit": True,
                    "is_degraded": payload.get("data_source") == "mock",
                }
            )
            payload.update(
                {
                    "data_source": "cache",
                    "summary": "已从缓存返回结果。",
                    "governance": governance,
                }
            )
            return payload

        result = self._dispatch(action=action, tool_name=tool_name, arguments=arguments)
        payload = result.get("data")
        quality = self.quality.check_dict(payload) if isinstance(payload, dict) else {"ok": True, "reason": "ok"}
        governance = dict(result.get("meta", {}).get("governance", {}))
        is_degraded = governance.get("data_source") == "mock" or result.get("data_source") == "mock"

        governed_payload = {
            **result,
            "quality": quality,
            "governance": {
                "cache_key": cache_key,
                "cache_ttl": cache_ttl,
                "cache_hit": False,
                "is_degraded": is_degraded,
                **governance,
            },
        }
        self.cache.set(cache_key, governed_payload, ttl=cache_ttl)
        return governed_payload

    def _infer_governance(self, tool_result: dict, data: Any) -> dict:
        """尽量从工具输出里提取统一治理信息。"""
        governance = {}
        if isinstance(data, dict):
            for key in ("governance", "quality"):
                value = data.get(key)
                if isinstance(value, dict):
                    governance[key] = value
            if isinstance(data.get("data_source"), str):
                governance["data_source"] = data.get("data_source")
        if "data_source" not in governance and isinstance(tool_result.get("data_source"), str):
            governance["data_source"] = tool_result.get("data_source")
        return governance

    def parse_intent(self, user_input: str) -> dict:
        """解析自然语言并返回结构化路由结果。"""
        return parse_intent(user_input).to_dict()

    def recent_routes(self, limit: int = 20) -> list[dict]:
        """查看最近的路由审计记录。"""
        return self.audit_logger.recent(limit)

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

    def model_governance_status(self, model_name: Optional[str] = None) -> dict:
        """查看模型治理状态。"""
        return get_model_governance_service().get_status(model_name)

    def evaluate_model_release(
        self,
        model_name: str,
        version: str,
        *,
        metrics: Optional[dict] = None,
        thresholds: Optional[dict] = None,
    ) -> dict:
        """评估模型是否可发布。"""
        return get_model_governance_service().evaluate_release(
            model_name,
            version,
            metrics=metrics,
            thresholds=thresholds,
        )


def create_stock_orchestrator(tool_registry=None) -> StockOrchestrator:
    """创建统一编排器。"""
    return StockOrchestrator(tool_registry=tool_registry)
