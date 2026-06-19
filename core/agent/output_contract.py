#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一输出字段契约。

只定义稳定字段名称，供工具、编排器、客户端和回放统计复用。
"""

from __future__ import annotations

TOOL_OUTPUT_FIELDS = (
    "ok",
    "tool",
    "category",
    "data_source",
    "summary",
    "data",
    "meta",
)

TASK_PROTOCOL_FIELDS = (
    "task_protocol",
    "workflow_id",
    "plan_audit_id",
    "route_audit_id",
    "result_audit_id",
)

GOVERNANCE_FIELDS = (
    "governance",
    "is_degraded",
    "cache_hit",
    "overall_ok",
)

REPLAY_FIELDS = (
    "workflow_id",
    "event_type",
    "phase",
    "template_id",
    "template_hit",
)

