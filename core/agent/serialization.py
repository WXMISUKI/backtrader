#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体结果序列化

将 dataclass / pandas / numpy / 自定义对象转换为适合工具输出的 JSON 结构。
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from datetime import datetime, timezone
from typing import Any

import numpy as np

from .output_contract import TOOL_OUTPUT_FIELDS

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def serialize_value(value: Any, max_list_items: int = 10, max_df_rows: int = 10) -> Any:
    """
    将任意值转换为 JSON 友好的数据结构。
    """
    value = _safe_scalar(value)

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if is_dataclass(value):
        return {k: serialize_value(v, max_list_items=max_list_items, max_df_rows=max_df_rows) for k, v in asdict(value).items()}

    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        try:
            converted = value.to_dict()
            if converted is not value:
                return serialize_value(converted, max_list_items=max_list_items, max_df_rows=max_df_rows)
        except Exception:
            pass

    if pd is not None:
        if isinstance(value, pd.DataFrame):
            frame = value.head(max_df_rows).copy()
            return {
                "type": "dataframe",
                "shape": list(value.shape),
                "columns": list(value.columns),
                "rows": frame.to_dict(orient="records"),
            }
        if isinstance(value, pd.Series):
            series = value.head(max_df_rows)
            return {
                "type": "series",
                "name": value.name,
                "length": int(value.shape[0]),
                "rows": series.to_list(),
            }

    if isinstance(value, dict):
        return {
            str(k): serialize_value(v, max_list_items=max_list_items, max_df_rows=max_df_rows)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        items = list(value)
        if len(items) > max_list_items:
            items = items[:max_list_items]
        return [serialize_value(item, max_list_items=max_list_items, max_df_rows=max_df_rows) for item in items]

    if hasattr(value, "summary") and callable(getattr(value, "summary")):
        try:
            return {
                "type": value.__class__.__name__,
                "summary": str(value.summary()),
            }
        except Exception:
            pass

    return str(value)


def dumps_json(value: Any, *, ensure_ascii: bool = False, indent: int = 2) -> str:
    """安全导出 JSON。"""
    return json.dumps(serialize_value(value), ensure_ascii=ensure_ascii, indent=indent, default=str)


def build_tool_payload(tool_name: str, data: Any, summary: str = "") -> dict:
    """构造标准工具响应。"""
    # 输出遵循统一字段契约：ok/tool/category/data_source/summary/data/meta
    _ = TOOL_OUTPUT_FIELDS
    category = _infer_category(tool_name)
    data_source = _infer_data_source(data)

    return {
        "ok": True,
        "tool": tool_name,
        "category": category,
        "data_source": data_source,
        "summary": summary,
        "data": serialize_value(data),
        "meta": {
            "payload_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "category": category,
            "data_source": data_source,
        },
    }


def _infer_category(tool_name: str) -> str:
    """根据工具名推断分类。"""
    if tool_name in {"plan_collaboration", "execute_workflow", "list_workflow_templates", "get_workflow_template_stats", "list_project_capabilities"}:
        return "workflow"
    if tool_name in {"list_project_tools"}:
        return "knowledge_base"
    if tool_name in {"get_model_governance_status", "evaluate_model_release"}:
        return "model"
    if tool_name in {"run_backtest"}:
        return "backtest"
    if tool_name in {"recommend_long_term", "recommend_short_term", "recommend_by_risk"}:
        return "recommendation"
    if tool_name in {"get_market_overview"}:
        return "market"
    if tool_name in {"get_risk_profile"}:
        return "risk"
    if tool_name in {"get_runtime_health", "evaluate_runtime_health"}:
        return "observability"
    if tool_name in {"generate_stock_report"}:
        return "report"
    return "analysis"


def _infer_data_source(data: Any) -> str | None:
    """尽可能推断数据来源，便于智能体统一展示。"""
    if isinstance(data, dict):
        for key in ("data_source", "source"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        nested = data.get("data")
        if isinstance(nested, dict):
            for key in ("data_source", "source"):
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    return None
