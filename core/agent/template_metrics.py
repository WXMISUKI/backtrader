#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体工作流模板指标

记录模板命中与使用情况，支持轻量统计和回放。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import threading
import uuid
from typing import Any, Dict, List, Optional

from .serialization import serialize_value


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_TEMPLATE_USAGE_PATH = _PROJECT_ROOT / "logs" / "workflow_template_usage.jsonl"


class TemplateMetricsStore:
    """模板使用记录存储。"""

    def __init__(self, path: Optional[str] = None, enabled: bool = True) -> None:
        self.path = Path(path) if path else _DEFAULT_TEMPLATE_USAGE_PATH
        self.enabled = enabled
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, payload: dict) -> dict:
        """记录一条模板命中事件。"""
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **serialize_value(payload),
        }
        if not self.enabled:
            return record

        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def load(self) -> List[dict]:
        """加载全部模板命中事件。"""
        if not self.path.exists():
            return []

        records: List[dict] = []
        with self._lock:
            with self.path.open("r", encoding="utf-8") as f:
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


_DEFAULT_TEMPLATE_METRICS_STORE: Optional[TemplateMetricsStore] = None


def get_template_metrics_store() -> TemplateMetricsStore:
    """获取默认模板指标存储。"""
    global _DEFAULT_TEMPLATE_METRICS_STORE
    if _DEFAULT_TEMPLATE_METRICS_STORE is None:
        _DEFAULT_TEMPLATE_METRICS_STORE = TemplateMetricsStore()
    return _DEFAULT_TEMPLATE_METRICS_STORE


def record_workflow_template_usage(
    *,
    template: dict,
    route: dict,
    objective: str,
    selected_by: str,
    workflow_id: Optional[str] = None,
    mode: Optional[str] = None,
    task_count: Optional[int] = None,
    score: Optional[float] = None,
    data_source: Optional[str] = None,
) -> dict:
    """记录一次模板使用。"""
    store = get_template_metrics_store()
    payload = {
        "template_id": template.get("id", ""),
        "template_name": template.get("name", ""),
        "template_hit": bool(template),
        "selected_by": selected_by,
        "template_score": score,
        "objective": objective,
        "workflow_id": workflow_id,
        "mode": mode,
        "task_count": task_count,
        "data_source": data_source,
        "route": route,
        "intent": route.get("intent", ""),
        "tool": route.get("tool", ""),
        "matched_terms": route.get("matched_terms", []) or [],
        "candidates": route.get("candidates", []) or [],
        "template_keywords": template.get("keywords", []) or [],
        "trigger_intents": template.get("trigger_intents", []) or [],
    }
    return store.record(payload)


def get_workflow_template_stats(limit: int = 20) -> dict:
    """返回模板命中统计。"""
    store = get_template_metrics_store()
    records = store.load()
    if not records:
        return {
            "ok": True,
            "summary": "暂无模板命中记录。",
            "data_source": "template_metrics",
            "data": {
                "total_hits": 0,
                "templates": [],
                "selected_by": [],
                "recent_hits": [],
            },
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "limit": limit,
            },
        }

    template_counts: Counter[str] = Counter()
    selected_by_counts: Counter[str] = Counter()
    template_names: Dict[str, str] = {}
    template_scores: Dict[str, List[float]] = defaultdict(list)
    recent_hits = list(reversed(records[-limit:]))

    for record in records:
        template_id = str(record.get("template_id", "") or "")
        if template_id:
            template_counts[template_id] += 1
            template_names[template_id] = str(record.get("template_name", "") or template_id)

        selected_by = str(record.get("selected_by", "") or "unknown")
        selected_by_counts[selected_by] += 1

        score = record.get("template_score")
        if isinstance(score, (int, float)) and template_id:
            template_scores[template_id].append(float(score))

    templates = []
    for template_id, count in template_counts.most_common():
        scores = template_scores.get(template_id, [])
        avg_score = round(sum(scores) / len(scores), 2) if scores else None
        templates.append(
            {
                "template_id": template_id,
                "template_name": template_names.get(template_id, template_id),
                "hit_count": count,
                "avg_score": avg_score,
            }
        )

    return {
        "ok": True,
        "summary": f"已统计 {len(records)} 条模板命中记录。",
        "data_source": "template_metrics",
        "data": {
            "total_hits": len(records),
            "templates": templates,
            "selected_by": [
                {"selected_by": selected_by, "count": count}
                for selected_by, count in selected_by_counts.most_common()
            ],
            "recent_hits": recent_hits,
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "limit": limit,
        },
    }
