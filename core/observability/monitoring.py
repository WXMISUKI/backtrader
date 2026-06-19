#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行保障与监控告警。

轻量实现：内存聚合 + JSONL 持久化，优先服务于智能体调用和编排层观测。
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import uuid
from statistics import mean
from typing import Any, Deque, Dict, Iterable, List, Optional


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STORE_PATH = _PROJECT_ROOT / "logs" / "runtime_observability.jsonl"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _normalize_window_size(window_size: Any, default: int = 50) -> int:
    try:
        value = int(window_size)
    except Exception:
        value = default
    return max(1, value)


def _normalize_mapping(value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return dict(value or {})


@dataclass(frozen=True)
class RuntimeMetricEvent:
    """运行指标事件。"""

    id: str
    metric_name: str
    value: float
    unit: str = ""
    source: str = ""
    category: str = "runtime"
    timestamp: str = field(default_factory=_utcnow)
    labels: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["record_type"] = "metric"
        payload["labels"] = dict(self.labels)
        payload["meta"] = dict(self.meta)
        return payload


@dataclass(frozen=True)
class RuntimeEventRecord:
    """运行事件。"""

    id: str
    event_name: str
    status: str
    source: str = ""
    category: str = "runtime"
    timestamp: str = field(default_factory=_utcnow)
    duration_ms: Optional[float] = None
    data_source: Optional[str] = None
    message: str = ""
    labels: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["record_type"] = "event"
        payload["labels"] = dict(self.labels)
        payload["meta"] = dict(self.meta)
        return payload


@dataclass(frozen=True)
class RuntimeAlertEvent:
    """运行告警事件。"""

    alert_id: str
    name: str
    severity: str
    status: str = "firing"
    reason: str = ""
    metric_name: str = ""
    metric_value: Any = None
    threshold: Any = None
    triggered_at: str = field(default_factory=_utcnow)
    source: str = ""
    category: str = "runtime"
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["record_type"] = "alert"
        payload["meta"] = dict(self.meta)
        return payload


def _default_thresholds() -> Dict[str, Dict[str, float]]:
    return {
        "error_rate": {"warning": 0.05, "critical": 0.15},
        "degraded_rate": {"warning": 0.10, "critical": 0.25},
        "avg_latency_ms": {"warning": 1000.0, "critical": 2000.0},
        "alert_count": {"warning": 3.0, "critical": 5.0},
    }


def _build_tool_payload(tool_name: str, data: Any, summary: str = "") -> dict:
    data_source = None
    if isinstance(data, dict):
        if isinstance(data.get("data_source"), str) and data.get("data_source"):
            data_source = data.get("data_source")
    return {
        "ok": True,
        "tool": tool_name,
        "category": "observability",
        "data_source": data_source,
        "summary": summary,
        "data": data,
        "meta": {
            "payload_version": "1.0",
            "generated_at": _utcnow(),
            "tool": tool_name,
            "category": "observability",
            "data_source": data_source,
        },
    }


class ObservabilityService:
    """轻量运行保障服务。"""

    def __init__(
        self,
        path: Optional[str] = None,
        *,
        enabled: bool = True,
        max_events: int = 1000,
        max_metrics: int = 1000,
        max_alerts: int = 300,
    ) -> None:
        self.path = Path(path) if path else _DEFAULT_STORE_PATH
        self.enabled = enabled
        self._events: Deque[dict] = deque(maxlen=max_events)
        self._metrics: Deque[dict] = deque(maxlen=max_metrics)
        self._alerts: Deque[dict] = deque(maxlen=max_alerts)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def record_metric(
        self,
        metric_name: str,
        value: Any,
        *,
        source: str = "",
        unit: str = "",
        category: str = "runtime",
        labels: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """记录一个数值指标。"""
        event = RuntimeMetricEvent(
            id=str(uuid.uuid4()),
            metric_name=str(metric_name),
            value=_safe_float(value),
            unit=str(unit or ""),
            source=str(source or ""),
            category=str(category or "runtime"),
            labels=_normalize_mapping(labels),
            meta=_normalize_mapping(meta),
        )
        payload = event.to_dict()
        self._append_record(payload)
        return payload

    def record_latency(
        self,
        operation_name: str,
        latency_ms: Any,
        *,
        source: str = "",
        category: str = "runtime",
        labels: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """记录延迟指标。"""
        merged_labels = _normalize_mapping(labels)
        merged_labels.setdefault("operation", operation_name)
        return self.record_metric(
            f"{operation_name}.latency_ms",
            latency_ms,
            source=source or operation_name,
            unit="ms",
            category=category,
            labels=merged_labels,
            meta=meta,
        )

    def record_runtime_event(
        self,
        event_name: str,
        *,
        status: str = "ok",
        source: str = "",
        category: str = "runtime",
        duration_ms: Optional[Any] = None,
        data_source: Optional[str] = None,
        message: str = "",
        labels: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """记录运行事件。"""
        event = RuntimeEventRecord(
            id=str(uuid.uuid4()),
            event_name=str(event_name),
            status=str(status or "ok"),
            source=str(source or ""),
            category=str(category or "runtime"),
            duration_ms=_safe_float(duration_ms, default=0.0) if duration_ms is not None else None,
            data_source=str(data_source) if data_source is not None else None,
            message=str(message or ""),
            labels=_normalize_mapping(labels),
            meta=_normalize_mapping(meta),
        )
        payload = event.to_dict()
        self._append_record(payload)
        self._maybe_emit_status_alert(payload)
        return payload

    def recent_alerts(
        self,
        limit: int = 20,
        *,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
    ) -> list[dict]:
        """查询最近告警。"""
        limit = _normalize_window_size(limit, default=20)
        with self._lock:
            alerts = list(self._alerts)

        filtered = []
        for item in alerts:
            if severity and item.get("severity") != severity:
                continue
            if status and item.get("status") != status:
                continue
            if category and item.get("category") != category:
                continue
            if source and item.get("source") != source:
                continue
            filtered.append(item)
        return list(reversed(filtered[-limit:]))

    def get_health(
        self,
        *,
        window_size: int = 50,
        category: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> dict:
        """获取当前运行健康态。"""
        window_size = _normalize_window_size(window_size)
        events = self._select_events(window_size, category=category, tool_name=tool_name)
        metrics = self._select_metrics(window_size, category=category, tool_name=tool_name)
        alerts = self.recent_alerts(window_size, category=category)

        status_counts = Counter(item.get("status", "ok") for item in events)
        total_events = len(events)
        ok_count = int(status_counts.get("ok", 0))
        warning_count = int(status_counts.get("warning", 0))
        degraded_count = int(status_counts.get("degraded", 0))
        failed_count = int(status_counts.get("failed", 0)) + int(status_counts.get("error", 0))
        alert_count = len(alerts)
        critical_alert_count = len([item for item in alerts if item.get("severity") == "critical"])
        warning_alert_count = len([item for item in alerts if item.get("severity") == "warning"])

        latency_values = [float(item.get("value", 0.0) or 0.0) for item in metrics if self._is_latency_metric(item)]
        avg_latency_ms = round(mean(latency_values), 3) if latency_values else 0.0
        max_latency_ms = round(max(latency_values), 3) if latency_values else 0.0

        success_rate = round(ok_count / total_events, 4) if total_events else 1.0
        error_rate = round(failed_count / total_events, 4) if total_events else 0.0
        degraded_rate = round(degraded_count / total_events, 4) if total_events else 0.0

        status = self._derive_status(
            total_events=total_events,
            warning_count=warning_count,
            degraded_count=degraded_count,
            failed_count=failed_count,
            critical_alert_count=critical_alert_count,
            warning_alert_count=warning_alert_count,
            error_rate=error_rate,
            degraded_rate=degraded_rate,
            avg_latency_ms=avg_latency_ms,
        )

        score = self._derive_score(
            status=status,
            success_rate=success_rate,
            error_rate=error_rate,
            degraded_rate=degraded_rate,
            alert_count=alert_count,
            avg_latency_ms=avg_latency_ms,
        )
        summary = self._build_summary(
            status=status,
            total_events=total_events,
            failed_count=failed_count,
            degraded_count=degraded_count,
            warning_count=warning_count,
            avg_latency_ms=avg_latency_ms,
            alert_count=alert_count,
        )
        return {
            "data_source": "observability",
            "status": status,
            "score": score,
            "window_size": window_size,
            "scope": {
                "category": category or "all",
                "tool_name": tool_name or "",
            },
            "counts": {
                "total_events": total_events,
                "ok": ok_count,
                "warning": warning_count,
                "degraded": degraded_count,
                "failed": failed_count,
                "alerts": alert_count,
                "critical_alerts": critical_alert_count,
                "warning_alerts": warning_alert_count,
            },
            "metrics": {
                "success_rate": success_rate,
                "error_rate": error_rate,
                "degraded_rate": degraded_rate,
                "avg_latency_ms": avg_latency_ms,
                "max_latency_ms": max_latency_ms,
            },
            "alerts": alerts,
            "recent_events": events[-10:],
            "summary": summary,
            "generated_at": _utcnow(),
        }

    def evaluate(
        self,
        *,
        window_size: int = 50,
        category: Optional[str] = None,
        tool_name: Optional[str] = None,
        thresholds: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """按阈值评估当前运行健康态，并在触发时生成告警。"""
        window_size = _normalize_window_size(window_size)
        observed = self.get_health(window_size=window_size, category=category, tool_name=tool_name)
        observed_metrics = dict(observed.get("metrics", {}))
        observed_counts = dict(observed.get("counts", {}))
        observed_metrics["alert_count"] = float(observed_counts.get("alerts", 0))

        normalized_thresholds = thresholds or _default_thresholds()
        checks = []
        created_alerts = []

        for metric_name, threshold in normalized_thresholds.items():
            metric_value = observed_metrics.get(metric_name)
            if metric_value is None:
                alert = self._record_alert(
                    name=f"missing:{metric_name}",
                    severity="critical",
                    reason=f"missing metric: {metric_name}",
                    metric_name=metric_name,
                    metric_value=None,
                    threshold=threshold,
                    source=tool_name or category or "observability",
                    category=category or "observability",
                    meta={
                        "window_size": window_size,
                        "scope": {"category": category or "all", "tool_name": tool_name or ""},
                    },
                )
                checks.append(
                    {
                        "metric": metric_name,
                        "metric_value": None,
                        "threshold": threshold,
                        "passed": False,
                        "severity": "critical",
                        "reason": f"missing metric: {metric_name}",
                        "alert_id": alert["alert_id"],
                    }
                )
                created_alerts.append(alert)
                continue

            passed, severity, reason = _assess_threshold(metric_value, threshold, metric_name)
            check = {
                "metric": metric_name,
                "metric_value": metric_value,
                "threshold": threshold,
                "passed": passed,
                "severity": severity,
                "reason": reason,
            }
            if not passed:
                alert = self._record_alert(
                    name=metric_name,
                    severity=severity,
                    reason=reason,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    threshold=threshold,
                    source=tool_name or category or "observability",
                    category=category or "observability",
                    meta={
                        "window_size": window_size,
                        "scope": {"category": category or "all", "tool_name": tool_name or ""},
                    },
                )
                check["alert_id"] = alert["alert_id"]
                created_alerts.append(alert)
            checks.append(check)

        refreshed_health = self.get_health(window_size=window_size, category=category, tool_name=tool_name)
        evaluation_status = refreshed_health.get("status", "ok")
        return {
            "data_source": "observability",
            "status": evaluation_status,
            "window_size": window_size,
            "scope": {
                "category": category or "all",
                "tool_name": tool_name or "",
            },
            "health": refreshed_health,
            "thresholds": normalized_thresholds,
            "checks": checks,
            "created_alerts": created_alerts,
            "summary": self._build_evaluation_summary(evaluation_status, created_alerts, refreshed_health),
            "generated_at": _utcnow(),
        }

    def _load_history(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except Exception:
                        continue
                    self._append_loaded_record(record)
        except Exception:
            return

    def _append_loaded_record(self, record: dict) -> None:
        record_type = record.get("record_type")
        if record_type == "metric":
            self._metrics.append(record)
        elif record_type == "alert":
            self._alerts.append(record)
        self._events.append(record)

    def _append_record(self, record: dict) -> None:
        with self._lock:
            self._append_loaded_record(record)
            if not self.enabled:
                return
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def _select_events(
        self,
        window_size: int,
        *,
        category: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> list[dict]:
        with self._lock:
            events = list(self._events)
        filtered = []
        for item in events:
            if item.get("record_type") != "event":
                continue
            if category and item.get("category") != category:
                continue
            if tool_name and not self._matches_tool_name(item, tool_name):
                continue
            filtered.append(item)
        return filtered[-window_size:]

    def _select_metrics(
        self,
        window_size: int,
        *,
        category: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> list[dict]:
        with self._lock:
            metrics = list(self._metrics)
        filtered = []
        for item in metrics:
            if category and item.get("category") != category:
                continue
            if tool_name and not self._matches_tool_name(item, tool_name):
                continue
            filtered.append(item)
        return filtered[-window_size:]

    def _matches_tool_name(self, item: dict, tool_name: str) -> bool:
        if item.get("source") == tool_name:
            return True
        labels = item.get("labels")
        if isinstance(labels, dict) and labels.get("tool") == tool_name:
            return True
        metric_name = str(item.get("metric_name", ""))
        event_name = str(item.get("event_name", ""))
        return tool_name in metric_name or tool_name in event_name

    def _is_latency_metric(self, item: dict) -> bool:
        metric_name = str(item.get("metric_name", ""))
        return metric_name.endswith(".latency_ms") or metric_name.endswith("latency_ms")

    def _maybe_emit_status_alert(self, payload: dict) -> None:
        status = str(payload.get("status", "ok"))
        if status not in {"warning", "degraded", "critical", "failed", "error"}:
            return

        severity = "warning" if status in {"warning", "degraded"} else "critical"
        self._record_alert(
            name=str(payload.get("event_name", "runtime_event")),
            severity=severity,
            reason=str(payload.get("message", "") or status),
            metric_name=str(payload.get("event_name", "")),
            metric_value=payload.get("duration_ms"),
            threshold={"status": status},
            source=str(payload.get("source", "")),
            category=str(payload.get("category", "runtime")),
            meta={
                "event_id": payload.get("id"),
                "labels": dict(payload.get("labels") or {}),
                "status": status,
                "data_source": payload.get("data_source"),
            },
        )

    def _record_alert(
        self,
        *,
        name: str,
        severity: str,
        reason: str,
        metric_name: str,
        metric_value: Any,
        threshold: Any,
        source: str,
        category: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        alert = RuntimeAlertEvent(
            alert_id=str(uuid.uuid4()),
            name=str(name),
            severity=str(severity),
            reason=str(reason),
            metric_name=str(metric_name),
            metric_value=metric_value,
            threshold=threshold,
            source=str(source or ""),
            category=str(category or "runtime"),
            meta=_normalize_mapping(meta),
        )
        payload = alert.to_dict()
        self._append_record(payload)
        return payload

    def _derive_status(
        self,
        *,
        total_events: int,
        warning_count: int,
        degraded_count: int,
        failed_count: int,
        critical_alert_count: int,
        warning_alert_count: int,
        error_rate: float,
        degraded_rate: float,
        avg_latency_ms: float,
    ) -> str:
        if critical_alert_count > 0 or failed_count >= 3 or error_rate >= 0.2 or avg_latency_ms >= 2000:
            return "critical"
        if failed_count > 0 or degraded_count > 0 or error_rate >= 0.05 or degraded_rate >= 0.1 or avg_latency_ms >= 1000:
            return "degraded"
        if warning_alert_count > 0 or warning_count > 0:
            return "warning"
        if total_events == 0:
            return "ok"
        return "ok"

    def _derive_score(
        self,
        *,
        status: str,
        success_rate: float,
        error_rate: float,
        degraded_rate: float,
        alert_count: int,
        avg_latency_ms: float,
    ) -> float:
        score = 100.0
        score -= min(50.0, error_rate * 300.0)
        score -= min(25.0, degraded_rate * 200.0)
        score -= min(15.0, alert_count * 2.5)
        score -= min(20.0, avg_latency_ms / 100.0)
        score += min(5.0, success_rate * 5.0)

        if status == "warning":
            score -= 10.0
        elif status == "degraded":
            score -= 25.0
        elif status == "critical":
            score -= 45.0

        return round(max(0.0, min(100.0, score)), 2)

    def _build_summary(
        self,
        *,
        status: str,
        total_events: int,
        failed_count: int,
        degraded_count: int,
        warning_count: int,
        avg_latency_ms: float,
        alert_count: int,
    ) -> str:
        return (
            f"当前运行状态为 {status}，近 {total_events} 条事件中失败 {failed_count} 次、"
            f"降级 {degraded_count} 次、告警 {alert_count} 条，平均延迟 {avg_latency_ms:.2f}ms。"
        )

    def _build_evaluation_summary(self, status: str, alerts: list[dict], health: dict) -> str:
        return (
            f"已完成运行健康评估，当前状态 {status}，"
            f"本次新增 {len(alerts)} 条告警，窗口内总告警 {health.get('counts', {}).get('alerts', 0)} 条。"
        )


def _assess_threshold(value: Any, threshold: Any, metric_name: str) -> tuple[bool, str, str]:
    """判断指标是否触发阈值。"""
    numeric_value = _safe_float(value)

    if isinstance(threshold, dict):
        if any(key in threshold for key in ("min", "greater_equal")):
            critical_value = threshold.get("critical", threshold.get("min", threshold.get("greater_equal")))
            warning_value = threshold.get("warning")
            if critical_value is not None and numeric_value < _safe_float(critical_value):
                return False, "critical", f"{metric_name} below critical threshold {critical_value}"
            if warning_value is not None and numeric_value < _safe_float(warning_value):
                return False, "warning", f"{metric_name} below warning threshold {warning_value}"
            return True, "ok", f"{metric_name} passed"

        critical_value = threshold.get("critical", threshold.get("max", threshold.get("less_equal")))
        warning_value = threshold.get("warning")
        if critical_value is not None and numeric_value > _safe_float(critical_value):
            return False, "critical", f"{metric_name} above critical threshold {critical_value}"
        if warning_value is not None and numeric_value > _safe_float(warning_value):
            return False, "warning", f"{metric_name} above warning threshold {warning_value}"
        return True, "ok", f"{metric_name} passed"

    numeric_threshold = _safe_float(threshold)
    if numeric_value > numeric_threshold:
        return False, "critical", f"{metric_name} above threshold {numeric_threshold}"
    return True, "ok", f"{metric_name} passed"


_DEFAULT_OBSERVABILITY_SERVICE: Optional[ObservabilityService] = None


def get_observability_service() -> ObservabilityService:
    """获取默认运行保障服务。"""
    global _DEFAULT_OBSERVABILITY_SERVICE
    if _DEFAULT_OBSERVABILITY_SERVICE is None:
        _DEFAULT_OBSERVABILITY_SERVICE = ObservabilityService()
    return _DEFAULT_OBSERVABILITY_SERVICE


def get_runtime_health(
    *,
    window_size: int = 50,
    category: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> dict:
    """获取运行健康状态的统一入口。"""
    service = get_observability_service()
    health = service.get_health(window_size=window_size, category=category, tool_name=tool_name)
    payload = _build_tool_payload(
        "get_runtime_health",
        health,
        health.get("summary", "已返回运行健康状态。"),
    )
    payload["meta"]["window_size"] = health.get("window_size", window_size)
    payload["meta"]["scope"] = health.get("scope", {})
    payload["meta"]["status"] = health.get("status", "ok")
    return payload


def evaluate_runtime_health(
    *,
    window_size: int = 50,
    category: Optional[str] = None,
    tool_name: Optional[str] = None,
    thresholds: Optional[Dict[str, Any]] = None,
) -> dict:
    """评估运行健康并在触发阈值时生成告警。"""
    service = get_observability_service()
    evaluation = service.evaluate(
        window_size=window_size,
        category=category,
        tool_name=tool_name,
        thresholds=thresholds,
    )
    payload = _build_tool_payload(
        "evaluate_runtime_health",
        evaluation,
        evaluation.get("summary", "已完成运行健康评估。"),
    )
    payload["ok"] = evaluation.get("status", "ok") != "critical"
    payload["meta"]["window_size"] = evaluation.get("window_size", window_size)
    payload["meta"]["scope"] = evaluation.get("scope", {})
    payload["meta"]["status"] = evaluation.get("status", "ok")
    return payload
