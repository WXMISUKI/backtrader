#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体路由审计

记录路由决策，方便回放、排查和持续优化。
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import uuid
from typing import Any, Dict, List, Optional


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_AUDIT_PATH = _PROJECT_ROOT / "logs" / "route_audit.jsonl"


def _safe_route_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        try:
            converted = value.to_dict()
            if converted is not value:
                return converted
        except Exception:
            pass
    return value


@dataclass
class RouteAuditRecord:
    """结构化路由审计记录。"""

    id: str
    timestamp: str
    entrypoint: str
    input_text: str
    intent: str
    tool: str
    confidence: float
    reason: str
    matched_terms: List[str] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    arguments: Dict[str, Any] = field(default_factory=dict)
    data_source: Optional[str] = None
    notes: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "entrypoint": self.entrypoint,
            "input_text": self.input_text,
            "intent": self.intent,
            "tool": self.tool,
            "confidence": self.confidence,
            "reason": self.reason,
            "matched_terms": list(self.matched_terms),
            "candidates": list(self.candidates),
            "arguments": _safe_route_value(self.arguments),
            "data_source": self.data_source,
            "notes": self.notes,
            "meta": _safe_route_value(self.meta),
        }


class RouteAuditLogger:
    """路由审计日志器。"""

    def __init__(self, path: Optional[str] = None, max_memory: int = 500, enabled: bool = True) -> None:
        self.path = Path(path) if path else _DEFAULT_AUDIT_PATH
        self.enabled = enabled
        self._records = deque(maxlen=max_memory)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        entrypoint: str,
        input_text: str,
        route: Any,
        data_source: Optional[str] = None,
        notes: str = "",
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """记录一次路由决策。"""
        route_dict = _safe_route_value(route)
        if not isinstance(route_dict, dict):
            route_dict = {}

        record = RouteAuditRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            entrypoint=entrypoint,
            input_text=input_text,
            intent=str(route_dict.get("intent", "")),
            tool=str(route_dict.get("tool", "")),
            confidence=float(route_dict.get("confidence", 0.0) or 0.0),
            reason=str(route_dict.get("reason", "")),
            matched_terms=list(route_dict.get("matched_terms", []) or []),
            candidates=list(route_dict.get("candidates", []) or []),
            arguments=_safe_route_value(route_dict.get("arguments", {})) or {},
            data_source=data_source or route_dict.get("data_source"),
            notes=notes,
            meta=meta or {},
        )
        payload = record.to_dict()

        if not self.enabled:
            return payload

        with self._lock:
            self._records.append(payload)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

        return payload

    def recent(self, limit: int = 20) -> list[dict]:
        """返回最近的路由记录，最新的在前。"""
        with self._lock:
            items = list(self._records)
        return list(reversed(items[-limit:]))


_DEFAULT_ROUTE_AUDIT_LOGGER: Optional[RouteAuditLogger] = None


def get_route_audit_logger() -> RouteAuditLogger:
    """获取默认路由审计日志器。"""
    global _DEFAULT_ROUTE_AUDIT_LOGGER
    if _DEFAULT_ROUTE_AUDIT_LOGGER is None:
        _DEFAULT_ROUTE_AUDIT_LOGGER = RouteAuditLogger()
    return _DEFAULT_ROUTE_AUDIT_LOGGER

