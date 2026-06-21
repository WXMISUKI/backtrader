#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常流程共享工具。
"""

from __future__ import annotations

import json
import re
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


def _normalize_reason_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "ok"
    mapping = {
        "missing stock_code": "missing_stock_code",
        "watchlist 配置缺少 stock_code": "missing_stock_code",
        "dataframe is none": "dataframe_none",
        "dataframe is empty": "dataframe_empty",
        "not a dict": "not_a_dict",
        "dict is empty": "dict_empty",
        "missing columns": "missing_columns",
        "financial indicators unavailable or empty fallback": "financial_unavailable",
        "watchlist 配置缺少 stock_code": "missing_stock_code",
    }
    for needle, code in mapping.items():
        if needle in text:
            return code
    normalized = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return normalized or "unknown_reason"


def _confidence_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _source_confidence_score(*, source: str, degraded: bool, quality: dict[str, Any], reason: str) -> dict[str, Any]:
    base_score_map = {
        "real": 0.92,
        "cache": 0.78,
        "mock": 0.42,
        "config": 0.2,
        "config_error": 0.15,
        "error": 0.12,
        "unknown": 0.3,
    }
    source_key = str(source or "unknown").strip().lower()
    score = base_score_map.get(source_key, 0.3)
    reason_codes = [f"source:{_normalize_reason_code(source_key)}"]

    if degraded:
        score -= 0.18
        reason_codes.append("degraded")

    quality_ok = bool(quality.get("ok", False))
    if quality_ok:
        score += 0.08
    else:
        score -= 0.18

    quality_reason = str(quality.get("reason", "")).strip()
    if quality_reason:
        reason_codes.append(f"quality:{_normalize_reason_code(quality_reason)}")
        lowered = quality_reason.lower()
        if any(token in lowered for token in ("empty", "missing", "none", "error", "failed")):
            score -= 0.08

    normalized_reason = _normalize_reason_code(reason)
    if normalized_reason != "ok":
        reason_codes.append(f"reason:{normalized_reason}")
        lowered_reason = str(reason).lower()
        if any(token in lowered_reason for token in ("empty", "missing", "none", "error", "failed")):
            score -= 0.06

    score = max(0.0, min(1.0, round(score, 4)))
    return {
        "score": score,
        "level": _confidence_level(score),
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "source": source_key,
        "degraded": degraded,
        "quality_ok": quality_ok,
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
    history_confidence = _source_confidence_score(
        source=history_source,
        degraded=history_degraded,
        quality=history_quality,
        reason=history_reason,
    )
    fundamental_confidence = _source_confidence_score(
        source=fundamental_source,
        degraded=fundamental_degraded,
        quality=fundamental_quality,
        reason=fundamental_reason,
    )
    data_confidence = round((history_confidence["score"] + fundamental_confidence["score"]) / 2, 4)
    confidence_level = _confidence_level(data_confidence)
    normalized_reasons = list(
        dict.fromkeys(
            history_confidence["reason_codes"] + fundamental_confidence["reason_codes"]
        )
    )
    diagnosis = _build_health_diagnosis(
        stock_name=stock_name,
        history_source=history_source,
        fundamental_source=fundamental_source,
        history_reason=history_reason,
        fundamental_reason=fundamental_reason,
        history_degraded=history_degraded,
        fundamental_degraded=fundamental_degraded,
        history_quality=history_quality,
        fundamental_quality=fundamental_quality,
    )
    return {
        "status": status,
        "health_score": score,
        "history_source": history_source,
        "fundamental_source": fundamental_source,
        "history_quality": history_quality,
        "fundamental_quality": fundamental_quality,
        "history_reason": history_reason,
        "fundamental_reason": fundamental_reason,
        "data_confidence": data_confidence,
        "confidence_level": confidence_level,
        "confidence_breakdown": {
            "history": history_confidence,
            "fundamental": fundamental_confidence,
        },
        "normalized_reasons": normalized_reasons,
        "summary": f"{stock_name} 数据健康状态为{status}，健康分 {score} 分。",
        "diagnosis": diagnosis,
        "flags": {
            "history_degraded": history_degraded,
            "fundamental_degraded": fundamental_degraded,
            "history_quality_ok": bool(history_quality.get("ok", False)),
            "fundamental_quality_ok": bool(fundamental_quality.get("ok", False)),
        },
    }


def build_daily_diagnosis_summary(*, health_groups: dict[str, list[dict[str, Any]]], decision_groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """把日常健康分组和决策分组收成统一摘要模板。"""
    health_counts = {key: len(value) for key, value in health_groups.items()}
    decision_counts = {key: len(value) for key, value in decision_groups.items()}
    confidence_scores: list[float] = []
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    top_focus = [item["stock_code"] + " " + item["name"] for item in decision_groups.get("重点关注", [])[:3]]
    watch_list = [item["stock_code"] + " " + item["name"] for item in decision_groups.get("继续观察", [])[:3]]
    held_alerts = [
        item["stock_code"] + " " + item["name"]
        for item in decision_groups.get("继续观察", [])
        if str(item.get("position_label", "")).startswith("已持有")
    ][:3]
    diagnosis_counts: dict[str, int] = {}
    for group_items in health_groups.values():
        for item in group_items:
            confidence = safe_float(item.get("data_confidence"), 0.0)
            if "data_confidence" in item:
                confidence_scores.append(confidence)
                confidence_counts[_confidence_level(confidence)] += 1
            diagnosis = item.get("diagnosis", {}) if isinstance(item, dict) else {}
            primary_cause = str(diagnosis.get("primary_cause", "")) if isinstance(diagnosis, dict) else ""
            if primary_cause and primary_cause != "healthy":
                diagnosis_counts[primary_cause] = diagnosis_counts.get(primary_cause, 0) + 1

    average_confidence = round(sum(confidence_scores) / len(confidence_scores), 4) if confidence_scores else 0.0

    status = "平稳"
    if health_counts.get("明显降级", 0) > 0 or decision_counts.get("数据不足", 0) > 0:
        status = "需要谨慎"
    elif decision_counts.get("重点关注", 0) > 0:
        status = "出现重点关注"

    summary_lines = [
        f"今日总览: {status}",
        f"健康状态: 完全可用 {health_counts.get('完全可用', 0)}，部分降级 {health_counts.get('部分降级', 0)}，明显降级 {health_counts.get('明显降级', 0)}",
        f"决策分布: 重点关注 {decision_counts.get('重点关注', 0)}，继续观察 {decision_counts.get('继续观察', 0)}，暂不行动 {decision_counts.get('暂不行动', 0)}，数据不足 {decision_counts.get('数据不足', 0)}",
    ]
    if confidence_scores:
        summary_lines.append(
            "可信度分布: "
            f"高 {confidence_counts['high']}，中 {confidence_counts['medium']}，低 {confidence_counts['low']}，"
            f"平均 {average_confidence:.1%}"
        )
    if top_focus:
        summary_lines.append(f"重点关注: {'，'.join(top_focus)}")
    if watch_list:
        summary_lines.append(f"继续观察: {'，'.join(watch_list)}")
    if held_alerts:
        summary_lines.append(f"持仓留意: {'，'.join(held_alerts)}")
    if diagnosis_counts:
        sorted_diagnosis = sorted(diagnosis_counts.items(), key=lambda item: (-item[1], item[0]))
        summary_lines.append("降级原因: " + "，".join(f"{cause} {count}" for cause, count in sorted_diagnosis))

    return {
        "status": status,
        "health_counts": health_counts,
        "decision_counts": decision_counts,
        "diagnosis_counts": diagnosis_counts,
        "confidence_counts": confidence_counts,
        "average_confidence": average_confidence,
        "highlights": {
            "top_focus": top_focus,
            "watch_list": watch_list,
            "held_alerts": held_alerts,
        },
        "summary_lines": summary_lines,
        "summary_text": "；".join(summary_lines),
    }


def build_diagnosis_evidence(*, daily_summary: dict[str, Any], health_items: list[dict[str, Any]]) -> dict[str, Any]:
    """把日常诊断摘要进一步整理成可给验收和回看消费的证据视图。"""
    diagnosis_counts = daily_summary.get("diagnosis_counts", {}) if isinstance(daily_summary, dict) else {}
    confidence_counts = daily_summary.get("confidence_counts", {}) if isinstance(daily_summary, dict) else {}
    top_causes = []
    if isinstance(diagnosis_counts, dict):
        top_causes = sorted(diagnosis_counts.items(), key=lambda item: (-item[1], item[0]))
    sample_items = []
    for item in health_items[:5]:
        diagnosis = item.get("diagnosis", {}) if isinstance(item, dict) else {}
        sample_items.append(
            {
                "stock_code": item.get("stock_code", ""),
                "name": item.get("name", ""),
                "status": item.get("status", ""),
                "primary_cause": diagnosis.get("primary_cause", ""),
                "primary_label": diagnosis.get("primary_label", ""),
                "data_confidence": item.get("data_confidence", 0.0),
                "confidence_level": item.get("confidence_level", ""),
                "summary": diagnosis.get("summary", ""),
                "normalized_reasons": item.get("normalized_reasons", []),
            }
        )

    return {
        "summary_text": daily_summary.get("summary_text", "") if isinstance(daily_summary, dict) else "",
        "status": daily_summary.get("status", "") if isinstance(daily_summary, dict) else "",
        "diagnosis_counts": diagnosis_counts if isinstance(diagnosis_counts, dict) else {},
        "confidence_counts": confidence_counts if isinstance(confidence_counts, dict) else {},
        "top_causes": top_causes,
        "sample_items": sample_items,
        "average_confidence": daily_summary.get("average_confidence", 0.0) if isinstance(daily_summary, dict) else 0.0,
    }


def build_production_gate(
    *,
    daily_summary: dict[str, Any],
    diagnosis_evidence: dict[str, Any],
    acceptance: dict[str, Any],
    health_items: list[dict[str, Any]],
    daily_run_status: str,
) -> dict[str, Any]:
    """把日常摘要、证据、验收和健康项汇总成统一投产门禁。"""
    summary_status = str(daily_summary.get("status", "")).strip()
    acceptance_status = str(acceptance.get("status", "")).strip()
    daily_run_status = str(daily_run_status or "").strip() or "unknown"
    diagnosis_counts = daily_summary.get("diagnosis_counts", {}) if isinstance(daily_summary, dict) else {}
    confidence_counts = daily_summary.get("confidence_counts", {}) if isinstance(daily_summary, dict) else {}
    average_confidence = safe_float(daily_summary.get("average_confidence"), 0.0) if isinstance(daily_summary, dict) else 0.0

    total_items = len(health_items)
    pass_count = 0
    warn_count = 0
    block_count = 0
    low_confidence_count = 0
    high_confidence_count = 0
    confidence_scores: list[float] = []
    degraded_items: list[dict[str, Any]] = []
    critical_items: list[dict[str, Any]] = []

    for item in health_items:
        if not isinstance(item, dict):
            continue
        confidence = safe_float(item.get("data_confidence"), 0.0)
        confidence_scores.append(confidence)
        if confidence < 0.45:
            low_confidence_count += 1
        if confidence >= 0.8:
            high_confidence_count += 1
        status = str(item.get("status", "")).strip()
        diagnosis = item.get("diagnosis", {}) if isinstance(item.get("diagnosis", {}), dict) else {}
        severity = str(diagnosis.get("severity", "")).strip()
        primary_cause = str(diagnosis.get("primary_cause", "")).strip()
        item_summary = {
            "stock_code": item.get("stock_code", ""),
            "name": item.get("name", ""),
            "status": status,
            "primary_cause": primary_cause,
            "primary_label": diagnosis.get("primary_label", ""),
        }
        if status == "明显降级" or severity == "critical":
            block_count += 1
            critical_items.append(item_summary)
        elif status == "部分降级" or severity == "warning":
            warn_count += 1
            degraded_items.append(item_summary)
        else:
            pass_count += 1

    data_ratio = (block_count / total_items) if total_items else 0.0
    reasons: list[str] = []
    allowed_actions = ["review_now", "hold_watch", "wait"]
    blocked_actions: list[str] = []
    risk_level = "normal"
    status = "pass"

    if daily_run_status in {"failed", "error"}:
        reasons.append("daily_run_failed")
        status = "block"
    if acceptance_status in {"failed", "error"}:
        reasons.append("acceptance_failed")
        status = "block"
    if total_items and (block_count >= max(1, total_items // 2 + total_items % 2) or data_ratio >= 0.6):
        reasons.append("core_data_unavailable")
        status = "block"
    if total_items and average_confidence < 0.45 and status != "block":
        reasons.append("average_confidence_too_low")
        status = "block"
    elif total_items and average_confidence < 0.65 and status == "pass":
        reasons.append("average_confidence_low")
        status = "warn"
    if summary_status in {"需要谨慎"} and status != "block":
        reasons.append("daily_summary_cautious")
        status = "warn"
    if summary_status in {"出现重点关注"} and status == "pass":
        reasons.append("summary_contains_focus_items")
        status = "warn"
    if warn_count > 0 and status == "pass":
        reasons.append("partial_degradation")
        status = "warn"
    if diagnosis_counts and status == "pass":
        reasons.append("diagnosis_signals_present")
        status = "warn"
    if acceptance_status == "degraded" and status == "pass":
        reasons.append("acceptance_degraded")
        status = "warn"
    if daily_run_status == "degraded" and status == "pass":
        reasons.append("daily_run_degraded")
        status = "warn"
    if acceptance_status in {"", "unknown"} and status == "pass":
        reasons.append("acceptance_missing")
        status = "warn"
    if daily_run_status in {"", "unknown"} and status == "pass":
        reasons.append("daily_run_status_missing")
        status = "warn"
    if low_confidence_count > 0 and status == "pass":
        reasons.append("low_confidence_items_present")
        status = "warn"

    if status == "pass":
        allowed_actions = ["review_now", "hold_watch", "wait"]
        blocked_actions = []
        risk_level = "normal"
    elif status == "warn":
        allowed_actions = ["review_now", "hold_watch", "wait", "skip_due_to_data"]
        blocked_actions = ["new_buy", "add_position", "strong_action"]
        risk_level = "cautious"
    else:
        allowed_actions = ["diagnose", "repair_data", "wait"]
        blocked_actions = ["review_now", "review_now_strong", "hold_watch", "new_buy", "add_position", "strong_action"]
        risk_level = "unsafe"

    summary_map = {
        "pass": "今日数据和验收整体可用，可以参考日常决策。",
        "warn": "今日存在部分降级或验收警告，只建议谨慎参考。",
        "block": "今日核心数据或验收存在阻断问题，不建议用于交易决策。",
    }

    evidence = {
        "daily_run_status": daily_run_status,
        "daily_summary_status": summary_status,
        "acceptance_status": acceptance_status,
        "diagnosis_counts": diagnosis_counts if isinstance(diagnosis_counts, dict) else {},
        "confidence_counts": confidence_counts if isinstance(confidence_counts, dict) else {},
        "average_confidence": average_confidence,
        "degraded_count": warn_count,
        "blocked_count": block_count,
        "low_confidence_count": low_confidence_count,
        "high_confidence_count": high_confidence_count,
        "total_items": total_items,
        "pass_count": pass_count,
        "data_unavailable_ratio": round(data_ratio, 4),
        "top_causes": diagnosis_evidence.get("top_causes", []) if isinstance(diagnosis_evidence, dict) else [],
        "sample_items": diagnosis_evidence.get("sample_items", []) if isinstance(diagnosis_evidence, dict) else [],
        "critical_items": critical_items[:5],
        "degraded_items": degraded_items[:5],
    }

    if total_items == 0:
        reasons.append("no_health_items")
        if status == "pass":
            status = "warn"
            risk_level = "cautious"
            allowed_actions = ["review_now", "hold_watch", "wait", "skip_due_to_data"]
            blocked_actions = ["new_buy", "add_position", "strong_action"]

    return {
        "status": status,
        "summary": summary_map[status],
        "allowed_actions": allowed_actions,
        "blocked_actions": blocked_actions,
        "risk_level": risk_level,
        "reasons": reasons,
        "evidence": evidence,
    }


def _build_health_diagnosis(
    *,
    stock_name: str,
    history_source: str,
    fundamental_source: str,
    history_reason: str,
    fundamental_reason: str,
    history_degraded: bool,
    fundamental_degraded: bool,
    history_quality: dict[str, Any],
    fundamental_quality: dict[str, Any],
) -> dict[str, Any]:
    cause = "healthy"
    label = "历史和基本面都正常"
    severity = "ok"

    history_ok = bool(history_quality.get("ok", False))
    fundamental_ok = bool(fundamental_quality.get("ok", False))
    cause_tags: list[str] = []

    if history_source == "mock" and fundamental_source == "mock":
        cause = "double_mock_fallback"
        label = "历史与基本面均回退到 mock"
        severity = "critical"
    elif history_source == "mock":
        cause = "history_mock_fallback"
        label = "历史行情回退到 mock"
        severity = "critical"
    elif fundamental_source == "mock":
        cause = "fundamental_mock_fallback"
        label = "基本面回退到 mock"
        severity = "critical"
    elif history_source == "error" and fundamental_source == "error":
        cause = "double_error"
        label = "历史与基本面都发生异常"
        severity = "critical"
    elif history_source == "error":
        cause = "history_error"
        label = "历史行情链路异常"
        severity = "critical"
    elif fundamental_source == "error":
        cause = "fundamental_error"
        label = "基本面链路异常"
        severity = "critical"
    elif history_degraded and fundamental_degraded:
        cause = "double_degraded"
        label = "历史与基本面都处于降级"
        severity = "warning"
    elif history_degraded:
        cause = "history_degraded"
        label = "历史行情处于降级"
        severity = "warning"
    elif fundamental_degraded:
        cause = "fundamental_degraded"
        label = "基本面处于降级"
        severity = "warning"
    elif not history_ok and not fundamental_ok:
        cause = "double_quality_issue"
        label = "历史与基本面质量都不稳定"
        severity = "warning"
    elif not history_ok:
        cause = "history_quality_issue"
        label = "历史行情质量不稳定"
        severity = "warning"
    elif not fundamental_ok:
        cause = "fundamental_quality_issue"
        label = "基本面质量不稳定"
        severity = "warning"

    if history_source != "real":
        cause_tags.append(f"history_source:{history_source}")
    if fundamental_source != "real":
        cause_tags.append(f"fundamental_source:{fundamental_source}")
    if history_degraded:
        cause_tags.append("history_degraded")
    if fundamental_degraded:
        cause_tags.append("fundamental_degraded")
    if not history_ok:
        cause_tags.append("history_quality_not_ok")
    if not fundamental_ok:
        cause_tags.append("fundamental_quality_not_ok")

    detail_parts = [
        f"历史={history_source}({history_reason or 'ok'})",
        f"基本面={fundamental_source}({fundamental_reason or 'ok'})",
    ]
    summary = f"{stock_name} 主要诊断: {label}。"
    if cause != "healthy":
        summary = f"{stock_name} 主要诊断: {label}；" + "；".join(detail_parts)

    return {
        "primary_cause": cause,
        "primary_label": label,
        "severity": severity,
        "cause_tags": cause_tags,
        "summary": summary,
        "details": {
            "history_source": history_source,
            "fundamental_source": fundamental_source,
            "history_reason": history_reason,
            "fundamental_reason": fundamental_reason,
            "history_quality_ok": history_ok,
            "fundamental_quality_ok": fundamental_ok,
        },
    }
