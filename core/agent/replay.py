#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务回放与学习统计。

轻量实现：直接复用审计 JSONL 与模板统计 JSONL，不引入额外存储。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Dict, List, Optional


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_ROUTE_AUDIT_PATH = _PROJECT_ROOT / "logs" / "route_audit.jsonl"
_DEFAULT_TEMPLATE_USAGE_PATH = _PROJECT_ROOT / "logs" / "workflow_template_usage.jsonl"


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


def _normalize_workflow_id(value: Any) -> str:
    return str(value or "").strip()


def get_workflow_replay(workflow_id: str, *, limit: int = 100) -> dict:
    """按 workflow_id 回放任务链路。"""
    workflow_id = _normalize_workflow_id(workflow_id)
    audit_records = [item for item in _load_jsonl(_DEFAULT_ROUTE_AUDIT_PATH) if _normalize_workflow_id(item.get("workflow_id")) == workflow_id]
    template_records = [item for item in _load_jsonl(_DEFAULT_TEMPLATE_USAGE_PATH) if _normalize_workflow_id(item.get("workflow_id")) == workflow_id]
    audit_records = audit_records[-limit:]
    template_records = template_records[-limit:]

    step_records = [item for item in audit_records if item.get("event_type") == "workflow_step"]
    plan_records = [item for item in audit_records if item.get("event_type") == "workflow_plan"]
    result_records = [item for item in audit_records if item.get("event_type") == "workflow_result"]

    summary = "未找到匹配的 workflow_id 回放记录。"
    if audit_records:
        summary = f"已回放 workflow_id={workflow_id} 的 {len(audit_records)} 条审计记录。"

    return {
        "ok": True,
        "summary": summary,
        "data_source": "replay",
        "data": {
            "workflow_id": workflow_id,
            "plan": plan_records[-1] if plan_records else {},
            "steps": step_records,
            "result": result_records[-1] if result_records else {},
            "template": template_records[-1] if template_records else {},
            "audit": audit_records,
            "meta": {
                "audit_count": len(audit_records),
                "step_count": len(step_records),
                "plan_count": len(plan_records),
                "result_count": len(result_records),
                "template_count": len(template_records),
            },
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workflow_id": workflow_id,
            "limit": limit,
        },
    }


def get_workflow_learning_stats(limit: int = 20) -> dict:
    """返回轻量学习统计。"""
    audits = _load_jsonl(_DEFAULT_ROUTE_AUDIT_PATH)
    templates = _load_jsonl(_DEFAULT_TEMPLATE_USAGE_PATH)

    workflow_ids = []
    intent_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    degraded_count = 0
    failed_count = 0
    step_count = 0

    for item in audits:
        workflow_id = _normalize_workflow_id(item.get("workflow_id"))
        if workflow_id:
            workflow_ids.append(workflow_id)

        intent = str(item.get("intent", "") or "")
        tool = str(item.get("tool", "") or "")
        event_type = str(item.get("event_type", "") or "")
        status = str(item.get("status", "") or "")

        if intent:
            intent_counts[intent] += 1
        if tool:
            tool_counts[tool] += 1
        if event_type:
            event_counts[event_type] += 1
        if event_type == "workflow_step":
            step_count += 1
        if status == "degraded":
            degraded_count += 1
        if status == "failed":
            failed_count += 1

    for item in templates:
        template_id = str(item.get("template_id", "") or "")
        if template_id:
            template_counts[template_id] += 1

    recent_workflows = []
    for workflow_id in list(dict.fromkeys(reversed(workflow_ids)))[:limit]:
        recent_workflows.append(get_workflow_replay(workflow_id, limit=50))

    total_workflows = len(set(workflow_ids))
    template_hit_count = len(templates)
    total_events = len(audits)
    template_hit_rate = round(template_hit_count / total_workflows, 4) if total_workflows else 0.0
    degraded_rate = round(degraded_count / total_events, 4) if total_events else 0.0
    failed_rate = round(failed_count / total_events, 4) if total_events else 0.0

    return {
        "ok": True,
        "summary": f"已统计 {total_workflows} 个 workflow 与 {total_events} 条审计记录。",
        "data_source": "learning_stats",
        "data": {
            "total_workflows": total_workflows,
            "total_steps": step_count,
            "template_hit_count": template_hit_count,
            "template_hit_rate": template_hit_rate,
            "degraded_count": degraded_count,
            "degraded_rate": degraded_rate,
            "failed_count": failed_count,
            "failed_rate": failed_rate,
            "intent_counts": intent_counts.most_common(20),
            "tool_counts": tool_counts.most_common(20),
            "template_counts": template_counts.most_common(20),
            "recent_workflows": recent_workflows,
            "event_counts": event_counts.most_common(20),
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limit": limit,
        },
    }

