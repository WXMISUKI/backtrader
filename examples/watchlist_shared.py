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
