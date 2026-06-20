#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
决策会话与用户反馈。

轻量实现：使用 JSONL 记录会话和反馈，服务于回放、统计与产品化接入。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import threading
import uuid
from typing import Any, Dict, List, Optional

from .serialization import serialize_value, build_tool_payload
from .task_protocol import build_task_plan, build_task_result
from .replay import get_workflow_replay, get_workflow_learning_stats


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SESSION_PATH = _PROJECT_ROOT / "logs" / "decision_sessions.jsonl"
_DEFAULT_FEEDBACK_PATH = _PROJECT_ROOT / "logs" / "decision_feedback.jsonl"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    records: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    return records


def _build_summary_card(
    *,
    conclusion: str,
    basis: List[str],
    risk: str | None,
    next_action: str,
    confidence: float | None = None,
    source: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> dict:
    card = {
        "结论": conclusion,
        "依据": basis[:5],
        "风险": risk,
        "下一步动作": next_action,
        "conclusion": conclusion,
        "basis": basis[:5],
        "risk": risk,
        "next_action": next_action,
        "confidence": confidence,
        "source": source,
    }
    if extra:
        card.update(extra)
    return card


@dataclass(frozen=True)
class DecisionSession:
    """一次决策会话。"""

    session_id: str
    decision_id: str
    workflow_id: str
    scenario: str
    objective: str
    route: Dict[str, Any] = field(default_factory=dict)
    task_protocol: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    status: str = "created"
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["route"] = serialize_value(self.route)
        payload["task_protocol"] = serialize_value(self.task_protocol)
        payload["meta"] = serialize_value(self.meta)
        return payload


@dataclass(frozen=True)
class DecisionFeedback:
    """一次会话反馈。"""

    feedback_id: str
    session_id: str
    workflow_id: str
    accepted: Optional[bool] = None
    rating: Optional[int] = None
    reason: str = ""
    correction: str = ""
    comment: str = ""
    created_at: str = field(default_factory=_utcnow)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["meta"] = serialize_value(self.meta)
        return payload


class DecisionSessionStore:
    """决策会话存储。"""

    def __init__(self, session_path: Optional[str] = None, feedback_path: Optional[str] = None, enabled: bool = True) -> None:
        self.session_path = Path(session_path) if session_path else _DEFAULT_SESSION_PATH
        self.feedback_path = Path(feedback_path) if feedback_path else _DEFAULT_FEEDBACK_PATH
        self.enabled = enabled
        self._lock = threading.Lock()
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        *,
        scenario: str,
        objective: str,
        route: dict,
        task_protocol: dict,
        workflow_id: str = "",
        summary: str = "",
        status: str = "created",
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        session = DecisionSession(
            session_id=str(uuid.uuid4()),
            decision_id=str(uuid.uuid4()),
            workflow_id=str(workflow_id or task_protocol.get("workflow_id", "") or ""),
            scenario=str(scenario or "unknown"),
            objective=str(objective or ""),
            route=route or {},
            task_protocol=task_protocol or {},
            summary=summary,
            status=status,
            meta=meta or {},
        )
        payload = session.to_dict()
        if not self.enabled:
            return payload

        with self._lock:
            with self.session_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        return payload

    def submit_feedback(
        self,
        *,
        session_id: str,
        workflow_id: str = "",
        accepted: Optional[bool] = None,
        rating: Optional[int] = None,
        reason: str = "",
        correction: str = "",
        comment: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        resolved_workflow_id = str(workflow_id or "").strip()
        session = self.get_session(session_id) if not resolved_workflow_id and session_id else {}
        if not resolved_workflow_id and isinstance(session, dict):
            resolved_workflow_id = str(session.get("workflow_id", "") or "").strip()
        resolved_meta = dict(meta or {})
        if session and isinstance(session, dict):
            resolved_meta.setdefault("session_workflow_id", resolved_workflow_id)

        feedback = DecisionFeedback(
            feedback_id=str(uuid.uuid4()),
            session_id=str(session_id or ""),
            workflow_id=resolved_workflow_id,
            accepted=accepted,
            rating=rating,
            reason=reason,
            correction=correction,
            comment=comment,
            meta=resolved_meta,
        )
        payload = feedback.to_dict()
        if not self.enabled:
            return payload

        with self._lock:
            with self.feedback_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        return payload

    def recent_sessions(self, limit: int = 20) -> List[dict]:
        return list(reversed(_load_jsonl(self.session_path)[-limit:]))

    def recent_feedback(self, limit: int = 20) -> List[dict]:
        return list(reversed(_load_jsonl(self.feedback_path)[-limit:]))

    def get_session(self, session_id: str) -> dict:
        for item in reversed(_load_jsonl(self.session_path)):
            if str(item.get("session_id", "")) == str(session_id or ""):
                return item
        return {}

    def get_session_replay(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        if not session:
            return {
                "ok": True,
                "summary": "未找到匹配的决策会话。",
                "data_source": "decision_session",
                "data": {},
                "meta": {"session_id": session_id},
            }

        workflow_id = str(session.get("workflow_id", "") or "")
        feedback = [item for item in _load_jsonl(self.feedback_path) if str(item.get("session_id", "")) == str(session_id or "")]
        replay = get_workflow_replay(workflow_id, limit=100) if workflow_id else {}
        payload = {
            "session": session,
            "feedback": feedback[-20:],
            "workflow_replay": replay,
            "task_protocol": session.get("task_protocol", {}),
        }
        return build_tool_payload(
            "get_decision_session",
            payload,
            f"已回放决策会话 {session_id}。",
        )

    def get_session_stats(self, limit: int = 20) -> dict:
        sessions = self.recent_sessions(1000)
        feedback = self.recent_feedback(1000)
        scenario_counts: Counter[str] = Counter()
        status_counts: Counter[str] = Counter()
        accepted_count = 0
        rejected_count = 0
        partial_count = 0
        unknown_count = 0

        for item in sessions:
            scenario_counts[str(item.get("scenario", "unknown"))] += 1
            status_counts[str(item.get("status", "unknown"))] += 1

        for item in feedback:
            accepted = item.get("accepted")
            if accepted is True:
                accepted_count += 1
            elif accepted is False:
                rejected_count += 1
            elif item.get("rating") is not None:
                partial_count += 1
            else:
                unknown_count += 1

        total = len(sessions)
        accept_rate = round(accepted_count / total, 4) if total else 0.0
        recent_sessions = list(reversed(sessions[-limit:]))
        recent_feedback = list(reversed(feedback[-limit:]))
        sample_warning = "样本量较少，统计结果仅供参考。" if total < max(5, limit) else "样本量足够，可以作为当前决策参考。"
        stats_summary = _build_summary_card(
            conclusion=f"已统计 {total} 个决策会话与 {len(feedback)} 条反馈记录。",
            basis=[
                f"采纳率 {accept_rate:.2%}",
                f"最近会话 {len(recent_sessions)} 条",
                f"最近反馈 {len(recent_feedback)} 条",
            ],
            risk=sample_warning,
            next_action="先结合最近反馈判断结果，再决定是否继续优化推荐或工作流。",
            source="decision_session",
            extra={
                "total_sessions": total,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "partial_count": partial_count,
                "unknown_count": unknown_count,
                "accept_rate": accept_rate,
            },
        )

        return {
            "ok": True,
            "summary": f"已统计 {total} 个决策会话与 {len(feedback)} 条反馈记录。",
            "data_source": "decision_session",
            "stats_summary": stats_summary,
            "结论": stats_summary["结论"],
            "依据": stats_summary["依据"],
            "风险": stats_summary["风险"],
            "下一步动作": stats_summary["下一步动作"],
            "conclusion": stats_summary["conclusion"],
            "basis": stats_summary["basis"],
            "risk": stats_summary["risk"],
            "next_action": stats_summary["next_action"],
            "data": {
                "total_sessions": total,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "partial_count": partial_count,
                "unknown_count": unknown_count,
                "accept_rate": accept_rate,
                "scenario_counts": scenario_counts.most_common(20),
                "status_counts": status_counts.most_common(20),
                "recent_sessions": recent_sessions,
                "recent_feedback": recent_feedback,
                "workflow_learning": get_workflow_learning_stats(limit=limit).get("data", {}),
            },
            "meta": {
                "generated_at": _utcnow(),
                "limit": limit,
            },
        }

    def get_feedback_insights(self, limit: int = 20, *, min_samples: int = 2) -> dict:
        """按意图、工具和场景聚合反馈洞察。"""
        sessions = _load_jsonl(self.session_path)
        feedback = _load_jsonl(self.feedback_path)
        session_lookup = {str(item.get("session_id", "") or ""): item for item in sessions if str(item.get("session_id", "") or "")}

        joined_records: List[dict] = []
        accepted_count = 0
        rejected_count = 0
        rating_total = 0
        rated_count = 0

        for item in feedback:
            session_id = str(item.get("session_id", "") or "")
            session = session_lookup.get(session_id, {})
            route = session.get("route", {}) if isinstance(session, dict) else {}
            intent = str(route.get("intent", "") or session.get("scenario", "") or "unknown")
            tool = str(route.get("tool", "") or "unknown")
            scenario = str(session.get("scenario", "") or "unknown")
            accepted = item.get("accepted")
            rating = item.get("rating")

            if accepted is True:
                accepted_count += 1
            elif accepted is False:
                rejected_count += 1

            if isinstance(rating, (int, float)):
                rating_total += int(rating)
                rated_count += 1

            joined_records.append(
                {
                    "session_id": session_id,
                    "workflow_id": str(item.get("workflow_id", "") or session.get("workflow_id", "") or ""),
                    "intent": intent,
                    "tool": tool,
                    "scenario": scenario,
                    "accepted": accepted,
                    "rating": rating,
                    "comment": str(item.get("comment", "") or ""),
                    "created_at": str(item.get("created_at", "") or ""),
                }
            )

        total_feedback = len(feedback)
        total_bool_feedback = accepted_count + rejected_count
        accept_rate = round(accepted_count / total_bool_feedback, 4) if total_bool_feedback else 0.0
        average_rating = round(rating_total / rated_count, 4) if rated_count else 0.0

        def _group_by(field_name: str) -> List[dict]:
            buckets: Dict[str, dict] = {}
            for record in joined_records:
                key = str(record.get(field_name, "") or "unknown")
                bucket = buckets.setdefault(
                    key,
                    {
                        "name": key,
                        "total_feedback": 0,
                        "accepted_count": 0,
                        "rejected_count": 0,
                        "unknown_count": 0,
                        "rating_total": 0,
                        "rated_count": 0,
                        "recent_samples": [],
                    },
                )
                bucket["total_feedback"] += 1
                if record.get("accepted") is True:
                    bucket["accepted_count"] += 1
                elif record.get("accepted") is False:
                    bucket["rejected_count"] += 1
                else:
                    bucket["unknown_count"] += 1
                rating = record.get("rating")
                if isinstance(rating, (int, float)):
                    bucket["rating_total"] += int(rating)
                    bucket["rated_count"] += 1
                bucket["recent_samples"].append(record)

            rows: List[dict] = []
            for bucket in buckets.values():
                bool_total = bucket["accepted_count"] + bucket["rejected_count"]
                row_accept_rate = round(bucket["accepted_count"] / bool_total, 4) if bool_total else 0.0
                row_average_rating = round(bucket["rating_total"] / bucket["rated_count"], 4) if bucket["rated_count"] else 0.0
                rows.append(
                    {
                        "name": bucket["name"],
                        "total_feedback": bucket["total_feedback"],
                        "accepted_count": bucket["accepted_count"],
                        "rejected_count": bucket["rejected_count"],
                        "unknown_count": bucket["unknown_count"],
                        "accept_rate": row_accept_rate,
                        "average_rating": row_average_rating,
                        "sample_size_ok": bucket["total_feedback"] >= min_samples,
                        "recent_samples": list(reversed(bucket["recent_samples"][-3:])),
                    }
                )
            rows.sort(key=lambda item: (item["total_feedback"], item["accept_rate"], item["name"]), reverse=True)
            return rows

        by_intent = _group_by("intent")
        by_tool = _group_by("tool")
        by_scenario = _group_by("scenario")

        optimization_targets = [
            row
            for row in sorted(
                [row for row in by_intent + by_tool if row["sample_size_ok"]],
                key=lambda row: (row["accept_rate"], -row["total_feedback"], row["name"]),
            )
            if row["accept_rate"] <= accept_rate or row["accept_rate"] <= 0.5
        ][:10]
        high_value_paths = [
            row
            for row in sorted(
                [row for row in by_intent + by_tool if row["sample_size_ok"]],
                key=lambda row: (-row["accept_rate"], -row["total_feedback"], row["name"]),
            )
        ][:10]

        recent_samples = list(reversed(joined_records[-limit:]))
        optimization_notes = []
        if optimization_targets:
            for item in optimization_targets[:5]:
                optimization_notes.append(
                    f"优先观察 {item['name']}：采纳率 {item['accept_rate']:.2f}，样本 {item['total_feedback']} 条"
                )
        else:
            optimization_notes.append("当前样本较少，先继续积累真实反馈，再判断优化重点。")

        if optimization_targets:
            top_target = optimization_targets[0]
            insight_conclusion = f"当前最值得优先优化的是 {top_target['name']}。"
            insight_basis = [
                f"优先项采纳率 {top_target['accept_rate']:.2%}",
                f"优先项样本 {top_target['total_feedback']} 条",
                f"总反馈 {total_feedback} 条",
            ]
            insight_next_action = f"先围绕 {top_target['name']} 做小步优化，再观察是否提升采纳率。"
        else:
            insight_conclusion = "当前反馈样本不足，先继续积累真实反馈。"
            insight_basis = [
                f"总反馈 {total_feedback} 条",
                f"样本门槛 {min_samples} 条",
            ]
            insight_next_action = "继续积累反馈后，再判断优先优化点。"

        insight_risk = "样本量偏少，当前洞察只能作为方向参考。" if total_feedback < max(5, min_samples) else "当前洞察可作为阶段性优化参考。"
        insights_summary = _build_summary_card(
            conclusion=insight_conclusion,
            basis=insight_basis,
            risk=insight_risk,
            next_action=insight_next_action,
            source="decision_feedback_insights",
            extra={
                "total_sessions": len(sessions),
                "total_feedback": total_feedback,
                "optimization_targets": optimization_targets[:3],
                "high_value_paths": high_value_paths[:3],
            },
        )

        return {
            "ok": True,
            "summary": f"已汇总 {total_feedback} 条反馈的洞察。",
            "data_source": "decision_feedback_insights",
            "insights_summary": insights_summary,
            "结论": insights_summary["结论"],
            "依据": insights_summary["依据"],
            "风险": insights_summary["风险"],
            "下一步动作": insights_summary["下一步动作"],
            "conclusion": insights_summary["conclusion"],
            "basis": insights_summary["basis"],
            "risk": insights_summary["risk"],
            "next_action": insights_summary["next_action"],
            "data": {
                "total_sessions": len(sessions),
                "total_feedback": total_feedback,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "accept_rate": accept_rate,
                "average_rating": average_rating,
                "by_intent": by_intent[:10],
                "by_tool": by_tool[:10],
                "by_scenario": by_scenario[:10],
                "optimization_targets": optimization_targets,
                "high_value_paths": high_value_paths,
                "recent_samples": recent_samples,
                "workflow_learning": get_workflow_learning_stats(limit=limit).get("data", {}),
                "optimization_notes": optimization_notes,
            },
            "meta": {
                "generated_at": _utcnow(),
                "limit": limit,
                "min_samples": min_samples,
            },
        }


_DEFAULT_DECISION_SESSION_STORE: Optional[DecisionSessionStore] = None


def get_decision_session_store() -> DecisionSessionStore:
    """获取默认决策会话存储。"""
    global _DEFAULT_DECISION_SESSION_STORE
    if _DEFAULT_DECISION_SESSION_STORE is None:
        _DEFAULT_DECISION_SESSION_STORE = DecisionSessionStore()
    return _DEFAULT_DECISION_SESSION_STORE


def create_decision_session(
    *,
    scenario: str,
    objective: str,
    route: dict,
    task_protocol: dict,
    workflow_id: str = "",
    summary: str = "",
    status: str = "created",
    meta: Optional[Dict[str, Any]] = None,
) -> dict:
    """创建决策会话。"""
    return get_decision_session_store().create_session(
        scenario=scenario,
        objective=objective,
        route=route,
        task_protocol=task_protocol,
        workflow_id=workflow_id,
        summary=summary,
        status=status,
        meta=meta,
    )


def submit_decision_feedback(
    *,
    session_id: str,
    workflow_id: str = "",
    accepted: Optional[bool] = None,
    rating: Optional[int] = None,
    reason: str = "",
    correction: str = "",
    comment: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> dict:
    """提交决策反馈。"""
    return get_decision_session_store().submit_feedback(
        session_id=session_id,
        workflow_id=workflow_id,
        accepted=accepted,
        rating=rating,
        reason=reason,
        correction=correction,
        comment=comment,
        meta=meta,
    )


def get_decision_session_replay(session_id: str) -> dict:
    """按 session_id 回放决策会话。"""
    return get_decision_session_store().get_session_replay(session_id)


def get_decision_session_stats(limit: int = 20) -> dict:
    """返回决策会话统计。"""
    return get_decision_session_store().get_session_stats(limit=limit)


def get_decision_feedback_insights(limit: int = 20, *, min_samples: int = 2) -> dict:
    """返回决策反馈洞察。"""
    return get_decision_session_store().get_feedback_insights(limit=limit, min_samples=min_samples)
