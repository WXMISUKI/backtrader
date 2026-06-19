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

        return {
            "ok": True,
            "summary": f"已统计 {total} 个决策会话与 {len(feedback)} 条反馈记录。",
            "data_source": "decision_session",
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
