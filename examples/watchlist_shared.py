#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常流程共享工具。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_pct(value: Any) -> str:
    return f"{safe_float(value):.1%}"


def load_watchlist(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"watchlist file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        items = payload.get("watchlist", [])
    elif isinstance(payload, list):
        items = payload
    else:
        items = []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("enabled", True)]


def load_portfolio(path: Path) -> tuple[list[dict[str, Any]], float]:
    if not path.exists():
        return [], 0.0
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict):
        items = payload.get("portfolio", [])
        total_assets = safe_float(payload.get("total_assets"), 0.0)
        cash = safe_float(payload.get("cash"), 0.0)
    elif isinstance(payload, list):
        items = payload
        total_assets = 0.0
        cash = 0.0
    else:
        return [], 0.0

    if not isinstance(items, list):
        return [], 0.0

    portfolio_items = [item for item in items if isinstance(item, dict) and item.get("stock_code")]
    if total_assets <= 0:
        total_assets = cash + sum(
            safe_float(entry.get("market_price"), 0.0) * safe_float(entry.get("size"), 0.0)
            for entry in portfolio_items
        )
    return portfolio_items, total_assets


def build_portfolio_index(portfolio_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    portfolio_index: dict[str, dict[str, Any]] = {}
    for item in portfolio_items:
        stock_code = str(item.get("stock_code", "")).strip()
        if not stock_code:
            continue
        portfolio_index[stock_code] = item
    return portfolio_index


def build_position_context(
    *,
    stock_code: str,
    stock_name: str,
    portfolio_index: dict[str, dict[str, Any]],
    total_assets: float,
) -> dict[str, Any]:
    position = portfolio_index.get(stock_code, {})
    is_position = bool(position)
    position_size = int(safe_float(position.get("size"), 0.0)) if is_position else 0
    avg_cost = position.get("avg_cost") if is_position else None
    market_price = position.get("market_price") if is_position else None
    target_weight = position.get("target_weight") if is_position else None

    if market_price is None and avg_cost is not None and is_position:
        market_price = avg_cost

    position_value = None
    if is_position:
        position_value = safe_float(market_price, 0.0) * position_size

    position_weight = None
    if position_value is not None and total_assets > 0:
        position_weight = position_value / total_assets

    if is_position:
        position_label = "已持有"
        if position_weight is not None and target_weight is not None:
            target_weight_value = safe_float(target_weight, 0.0)
            if target_weight_value > 0 and position_weight >= target_weight_value * 1.2:
                position_label = "已持有 / 仓位偏高"
            elif target_weight_value > 0 and position_weight <= target_weight_value * 0.8:
                position_label = "已持有 / 仓位偏低"
    else:
        position_label = "未持有"

    summary_parts = [position_label]
    if is_position:
        summary_parts.append(f"持仓 {position_size} 股")
        if avg_cost is not None:
            summary_parts.append(f"均价 {safe_float(avg_cost, 0.0):.2f}")
        if market_price is not None:
            summary_parts.append(f"市价 {safe_float(market_price, 0.0):.2f}")
        if position_weight is not None:
            summary_parts.append(f"仓位 {format_pct(position_weight)}")
        if target_weight is not None:
            summary_parts.append(f"目标仓位 {format_pct(target_weight)}")
    else:
        summary_parts.append("当前配置中无持仓记录")

    return {
        "is_position": is_position,
        "position_size": position_size,
        "avg_cost": avg_cost,
        "market_price": market_price,
        "position_value": round(position_value, 2) if position_value is not None else None,
        "position_weight": round(position_weight, 4) if position_weight is not None else None,
        "position_label": position_label,
        "position_summary": "；".join(summary_parts),
        "stock_name": stock_name,
    }


def build_data_health_summary(*, stock_name: str, history: dict[str, Any], fundamental: dict[str, Any]) -> dict[str, Any]:
    """把历史行情和基本面治理结果收成统一健康摘要。"""
    history_quality = history.get("quality", {}) if isinstance(history, dict) else {}
    fundamental_quality = fundamental.get("quality", {}) if isinstance(fundamental, dict) else {}
    history_source = str(history.get("data_source", "unknown"))
    fundamental_source = str(fundamental.get("data_source", "unknown"))
    history_reason = str(history.get("reason", "")) or str(history_quality.get("reason", ""))
    fundamental_reason = str(fundamental.get("reason", "")) or str(fundamental_quality.get("reason", ""))
    history_degraded = bool(history.get("is_degraded", False))
    fundamental_degraded = bool(fundamental.get("is_degraded", False))

    status = "完全可用"
    if history_degraded or fundamental_degraded or history_source != "real" or fundamental_source != "real":
        status = "部分降级"
    if history_source == "mock" and fundamental_source == "mock":
        status = "明显降级"

    score = 0
    if history_source == "real" and not history_degraded:
        score += 50
    elif history_source == "cache":
        score += 35
    elif history_source == "mock":
        score += 15

    if fundamental_source == "real" and not fundamental_degraded:
        score += 50
    elif fundamental_source == "cache":
        score += 35
    elif fundamental_source == "mock":
        score += 15

    if history_quality.get("ok", False):
        score += 5
    if fundamental_quality.get("ok", False):
        score += 5

    score = min(score, 100)
    return {
        "status": status,
        "health_score": score,
        "history_source": history_source,
        "fundamental_source": fundamental_source,
        "history_quality": history_quality,
        "fundamental_quality": fundamental_quality,
        "history_reason": history_reason,
        "fundamental_reason": fundamental_reason,
        "summary": f"{stock_name} 数据健康状态为{status}，健康分 {score} 分。",
        "flags": {
            "history_degraded": history_degraded,
            "fundamental_degraded": fundamental_degraded,
            "history_quality_ok": bool(history_quality.get("ok", False)),
            "fundamental_quality_ok": bool(fundamental_quality.get("ok", False)),
        },
    }
