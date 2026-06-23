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
    history_meta = history.get("meta", {}) if isinstance(history.get("meta", {}), dict) else {}
    fundamental_meta = fundamental.get("meta", {}) if isinstance(fundamental.get("meta", {}), dict) else {}
    history_source = str(history.get("data_source", "unknown"))
    fundamental_source = str(fundamental.get("data_source", "unknown"))
    history_reason = str(history.get("reason", "")) or str(history_quality.get("reason", ""))
    fundamental_reason = str(fundamental.get("reason", "")) or str(fundamental_quality.get("reason", ""))
    history_failure_stage = str(history.get("failure_stage", "") or history_meta.get("failure_stage", ""))
    history_failure_code = str(history.get("failure_code", "") or history_meta.get("failure_code", ""))
    history_fallback_strategy = str(history.get("fallback_strategy", "") or history_meta.get("fallback_strategy", ""))
    history_selected_provider = str(history.get("selected_provider", "") or history_meta.get("selected_provider", ""))
    history_provider_attempts = history.get("provider_attempts", history_meta.get("provider_attempts", []))
    fundamental_failure_stage = str(fundamental.get("failure_stage", "") or fundamental_meta.get("failure_stage", ""))
    fundamental_failure_code = str(fundamental.get("failure_code", "") or fundamental_meta.get("failure_code", ""))
    fundamental_fallback_strategy = str(fundamental.get("fallback_strategy", "") or fundamental_meta.get("fallback_strategy", ""))
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
    for prefix, value in (
        ("history_failure_stage", history_failure_stage),
        ("history_failure_code", history_failure_code),
        ("history_fallback_strategy", history_fallback_strategy),
        ("fundamental_failure_stage", fundamental_failure_stage),
        ("fundamental_failure_code", fundamental_failure_code),
        ("fundamental_fallback_strategy", fundamental_fallback_strategy),
    ):
        if value:
            normalized_reasons.append(f"{prefix}:{_normalize_reason_code(value)}")
    normalized_reasons = list(dict.fromkeys(normalized_reasons))
    diagnosis = _build_health_diagnosis(
        stock_name=stock_name,
        history_source=history_source,
        fundamental_source=fundamental_source,
        history_reason=history_reason,
        fundamental_reason=fundamental_reason,
        history_failure_stage=history_failure_stage,
        history_failure_code=history_failure_code,
        history_fallback_strategy=history_fallback_strategy,
        history_selected_provider=history_selected_provider,
        history_provider_attempts=history_provider_attempts,
        fundamental_failure_stage=fundamental_failure_stage,
        fundamental_failure_code=fundamental_failure_code,
        fundamental_fallback_strategy=fundamental_fallback_strategy,
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
        "history_failure_stage": history_failure_stage,
        "history_failure_code": history_failure_code,
        "history_fallback_strategy": history_fallback_strategy,
        "history_selected_provider": history_selected_provider,
        "history_provider_attempts": history_provider_attempts,
        "history_provider_summary": _build_history_provider_summary(
            selected_provider=history_selected_provider,
            attempts=history_provider_attempts,
            fallback_strategy=history_fallback_strategy,
        ),
        "fundamental_failure_stage": fundamental_failure_stage,
        "fundamental_failure_code": fundamental_failure_code,
        "fundamental_fallback_strategy": fundamental_fallback_strategy,
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


def _build_history_provider_summary(
    *,
    selected_provider: str,
    attempts: list[dict[str, Any]] | list[Any],
    fallback_strategy: str,
) -> str:
    provider = str(selected_provider or "").strip() or "unknown"
    attempt_count = len(attempts) if isinstance(attempts, list) else 0
    summary_parts = [f"历史 provider {provider}"]
    summary_parts.append(f"尝试 {attempt_count} 次")
    if fallback_strategy:
        summary_parts.append(f"回退策略 {fallback_strategy}")
    return "；".join(summary_parts)


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
    sample_attribution_map: dict[str, dict[str, Any]] = {}
    for item in health_items:
        diagnosis = item.get("diagnosis", {}) if isinstance(item, dict) else {}
        primary_cause = str(diagnosis.get("primary_cause", "") or "").strip()
        primary_label = str(diagnosis.get("primary_label", "") or "").strip()
        sample_entry = {
            "stock_code": item.get("stock_code", ""),
            "name": item.get("name", ""),
            "status": item.get("status", ""),
            "primary_cause": primary_cause,
            "primary_label": primary_label,
            "data_confidence": item.get("data_confidence", 0.0),
            "confidence_level": item.get("confidence_level", ""),
            "summary": diagnosis.get("summary", ""),
            "normalized_reasons": item.get("normalized_reasons", []),
        }
        sample_items.append(
            sample_entry
        )
        if primary_cause and primary_cause != "healthy":
            bucket = sample_attribution_map.setdefault(
                primary_cause,
                {
                    "cause": primary_cause,
                    "label": primary_label or primary_cause,
                    "count": 0,
                    "examples": [],
                },
            )
            bucket["count"] += 1
            if len(bucket["examples"]) < 3:
                bucket["examples"].append(
                    {
                        "stock_code": sample_entry["stock_code"],
                        "name": sample_entry["name"],
                        "status": sample_entry["status"],
                        "primary_label": sample_entry["primary_label"],
                    }
                )

    sample_attribution = []
    for cause, bucket in sample_attribution_map.items():
        examples = bucket.get("examples", [])
        sample_attribution.append(
            {
                "cause": cause,
                "label": bucket.get("label", cause),
                "count": bucket.get("count", 0),
                "summary": f"{bucket.get('label', cause)} 相关样本 {bucket.get('count', 0)} 只。",
                "examples": examples,
            }
        )
    sample_attribution.sort(key=lambda item: (-int(item.get("count", 0)), str(item.get("cause", ""))))

    return {
        "summary_text": daily_summary.get("summary_text", "") if isinstance(daily_summary, dict) else "",
        "status": daily_summary.get("status", "") if isinstance(daily_summary, dict) else "",
        "diagnosis_counts": diagnosis_counts if isinstance(diagnosis_counts, dict) else {},
        "confidence_counts": confidence_counts if isinstance(confidence_counts, dict) else {},
        "top_causes": top_causes,
        "sample_items": sample_items,
        "sample_attribution": sample_attribution,
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


def build_daily_prompt_context(
    *,
    production_gate: dict[str, Any] | None = None,
    action_list: dict[str, Any] | None = None,
    run_cadence: dict[str, Any] | None = None,
    daily_summary: dict[str, Any] | None = None,
    diagnosis_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把日常门禁、行动清单和运行节奏收成可复用的提示语境。"""
    production_gate = production_gate if isinstance(production_gate, dict) else {}
    action_list = action_list if isinstance(action_list, dict) else {}
    run_cadence = run_cadence if isinstance(run_cadence, dict) else {}
    daily_summary = daily_summary if isinstance(daily_summary, dict) else {}
    diagnosis_evidence = diagnosis_evidence if isinstance(diagnosis_evidence, dict) else {}

    gate_status = str(production_gate.get("status", "")).strip() or "unknown"
    gate_summary = str(production_gate.get("summary", "")).strip()
    gate_allowed_actions = [
        str(item).strip()
        for item in (production_gate.get("allowed_actions", []) if isinstance(production_gate.get("allowed_actions", []), list) else [])
        if str(item).strip()
    ]
    gate_blocked_actions = [
        str(item).strip()
        for item in (production_gate.get("blocked_actions", []) if isinstance(production_gate.get("blocked_actions", []), list) else [])
        if str(item).strip()
    ]

    action_summary = str(action_list.get("summary_text", "")).strip()
    action_items = action_list.get("items", []) if isinstance(action_list.get("items", []), list) else []
    top_actions: list[dict[str, Any]] = []
    for item in action_items[:3]:
        if not isinstance(item, dict):
            continue
        top_actions.append(
            {
                "stock_code": str(item.get("stock_code", "")).strip(),
                "name": str(item.get("name", "")).strip(),
                "action": str(item.get("action", "")).strip(),
                "action_hint": str(item.get("action_hint", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
            }
        )

    cadence_status = str(run_cadence.get("status", "")).strip() or "unknown"
    cadence_summary = str(run_cadence.get("summary_text", "")).strip()
    cadence_next_step = str(run_cadence.get("next_step", "")).strip()
    diagnosis_summary = str(daily_summary.get("summary_text", "")).strip()

    read_order = ["production_gate", "action_list", "run_cadence", "diagnosis_evidence"]
    rules = [
        "先看 production_gate，再看 action_list，再看 run_cadence。",
        "production_gate 为 block 时，只能给出诊断、修复数据或等待建议，不给强行动建议。",
        "production_gate 为 warn 时，必须保持谨慎，只输出观察、复核和小心处理建议。",
        "action_list 的 action_hint 是默认执行语境，不要被更长的报告正文覆盖。",
    ]

    summary_text = "提示语境已收拢：先看投产门禁，再看行动清单，再看运行节奏。"
    if gate_status == "block":
        summary_text += " 门禁为 block 时只做诊断。"
    elif gate_status == "warn":
        summary_text += " 门禁为 warn 时谨慎参考。"

    prompt_lines = [
        "日常协作语境：",
        f"- 投产门禁: {gate_status}" + (f" / {gate_summary}" if gate_summary else ""),
        f"- 行动清单: {action_summary or '未提供'}",
        f"- 运行节奏: {cadence_summary or '未提供'}",
        f"- 读取顺序: {' -> '.join(read_order)}",
    ]
    if top_actions:
        prompt_lines.append(
            "- 优先行动: "
            + "；".join(
                f"{item.get('stock_code', '')} {item.get('name', '')} [{item.get('action', '')}] {item.get('action_hint', '')}"
                for item in top_actions
            )
        )
    prompt_lines.extend(
        [
            "- 规则: 门禁 block 时只做诊断、修复数据或等待，不给强行动建议。",
            "- 规则: 门禁 warn 时保持谨慎，不把降级数据当成强信号。",
        ]
    )
    prompt_text = "\n".join(prompt_lines)

    return {
        "status": gate_status,
        "summary_text": summary_text,
        "prompt_text": prompt_text,
        "read_order": read_order,
        "rules": rules,
        "gate_status": gate_status,
        "gate_summary": gate_summary,
        "gate_allowed_actions": gate_allowed_actions,
        "gate_blocked_actions": gate_blocked_actions,
        "action_summary": action_summary,
        "action_count": len(action_items),
        "top_actions": top_actions,
        "run_cadence_status": cadence_status,
        "run_cadence_summary": cadence_summary,
        "run_cadence_next_step": cadence_next_step,
        "diagnosis_summary": diagnosis_summary,
        "evidence": {
            "production_gate": {
                "status": gate_status,
                "summary": gate_summary,
                "allowed_actions": gate_allowed_actions,
                "blocked_actions": gate_blocked_actions,
            },
            "action_list": {
                "status": str(action_list.get("status", "")).strip() or gate_status,
                "summary_text": action_summary,
                "count": len(action_items),
            },
            "run_cadence": {
                "status": cadence_status,
                "summary_text": cadence_summary,
                "next_step": cadence_next_step,
            },
            "diagnosis_evidence": {
                "summary_text": str(diagnosis_evidence.get("summary_text", "")).strip(),
                "top_causes": diagnosis_evidence.get("top_causes", []),
            },
        },
    }


def build_daily_review_brief(
    *,
    daily_summary: dict[str, Any] | None = None,
    production_gate: dict[str, Any] | None = None,
    action_list: dict[str, Any] | None = None,
    run_cadence: dict[str, Any] | None = None,
    prompt_context: dict[str, Any] | None = None,
    feedback_effects: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把回看材料收成一段更短、更适合日常打开的摘要。"""
    daily_summary = daily_summary if isinstance(daily_summary, dict) else {}
    production_gate = production_gate if isinstance(production_gate, dict) else {}
    action_list = action_list if isinstance(action_list, dict) else {}
    run_cadence = run_cadence if isinstance(run_cadence, dict) else {}
    prompt_context = prompt_context if isinstance(prompt_context, dict) else {}
    feedback_effects = feedback_effects if isinstance(feedback_effects, dict) else {}

    gate_status = str(production_gate.get("status", "")).strip() or "unknown"
    gate_summary = str(production_gate.get("summary", "")).strip()
    action_summary = str(action_list.get("summary_text", "")).strip()
    cadence_summary = str(run_cadence.get("summary_text", "")).strip()
    cadence_next_step = str(run_cadence.get("next_step", "")).strip()
    prompt_summary = str(prompt_context.get("summary_text", "")).strip()
    prompt_rules = prompt_context.get("rules", []) if isinstance(prompt_context.get("rules", []), list) else []
    daily_summary_text = str(daily_summary.get("summary_text", "")).strip()
    effect_overall = feedback_effects.get("overall", {}) if isinstance(feedback_effects.get("overall", {}), dict) else {}
    hit_rate = safe_float(effect_overall.get("hit_rate"), 0.0)
    avg_return = safe_float(effect_overall.get("avg_return"), 0.0)
    evaluable_rows = safe_int(effect_overall.get("evaluated_rows"), 0)
    usable_feedback = safe_int(effect_overall.get("usable_feedback"), 0)

    action_items = action_list.get("items", []) if isinstance(action_list.get("items", []), list) else []
    top_action = action_items[0] if action_items and isinstance(action_items[0], dict) else {}
    top_action_text = ""
    if top_action:
        top_action_text = (
            f"{top_action.get('stock_code', '')} {top_action.get('name', '')} "
            f"[{top_action.get('action', '')}] {top_action.get('action_hint', '')}"
        ).strip()

    read_order = ["production_gate", "action_list", "run_cadence", "prompt_context", "feedback_effects"]

    if gate_status == "block":
        summary_text = "回看摘要：当前应先处理门禁阻断，再看行动和效果。"
        next_step = "先看数据健康和门禁原因，再决定是否继续观察。"
    elif gate_status == "warn":
        summary_text = "回看摘要：当前需要谨慎复核，先看门禁，再看行动和效果。"
        next_step = "先复核行动清单和提示语境，再看反馈效果。"
    else:
        summary_text = "回看摘要：当前可按门禁、行动、节奏和效果顺序复核。"
        next_step = "先看优先行动，再回看效果是否稳定。"

    if prompt_summary and gate_status != "block":
        summary_text += " 提示语境已收拢。"

    key_points = [
        f"门禁 {gate_status}" + (f" / {gate_summary}" if gate_summary else ""),
        f"行动清单 {action_summary}" if action_summary else "行动清单未提供",
        f"运行节奏 {cadence_summary}" if cadence_summary else "运行节奏未提供",
        f"提示语境 {prompt_summary}" if prompt_summary else "提示语境未提供",
    ]
    if top_action_text:
        key_points.append(f"优先行动 {top_action_text}")
    if evaluable_rows > 0 or usable_feedback > 0:
        key_points.append(
            f"反馈效果 可评估 {evaluable_rows} 行，命中率 {hit_rate:.1%}，平均回报 {avg_return:.1%}"
        )
    if daily_summary_text:
        key_points.append(f"日常总览 {daily_summary_text}")

    risk_note = "保持谨慎，优先看数据和门禁。"
    if gate_status == "pass":
        risk_note = "可正常复核，但仍保留风险提示。"
    elif gate_status == "warn":
        risk_note = "存在降级，先复核再动作。"
    elif gate_status == "block":
        risk_note = "存在阻断，先诊断再继续。"

    return {
        "status": gate_status,
        "summary_text": summary_text,
        "next_step": next_step,
        "risk_note": risk_note,
        "read_order": read_order,
        "key_points": key_points,
        "prompt_rules": prompt_rules,
        "metrics": {
            "usable_feedback": usable_feedback,
            "evaluated_rows": evaluable_rows,
            "hit_rate": hit_rate,
            "avg_return": avg_return,
        },
        "evidence": {
            "production_gate": {
                "status": gate_status,
                "summary": gate_summary,
            },
            "action_list": {
                "summary_text": action_summary,
                "count": len(action_items),
            },
            "run_cadence": {
                "summary_text": cadence_summary,
                "next_step": cadence_next_step,
            },
            "prompt_context": {
                "summary_text": prompt_summary,
            },
        },
    }


def build_schedule_hint(
    *,
    daily_run_status: str | None = None,
    production_gate: dict[str, Any] | None = None,
    run_cadence: dict[str, Any] | None = None,
    prompt_context: dict[str, Any] | None = None,
    review_brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把运行就绪状态收成一份轻量调度准备提示。"""
    production_gate = production_gate if isinstance(production_gate, dict) else {}
    run_cadence = run_cadence if isinstance(run_cadence, dict) else {}
    prompt_context = prompt_context if isinstance(prompt_context, dict) else {}
    review_brief = review_brief if isinstance(review_brief, dict) else {}

    run_status = str(daily_run_status or "").strip() or "unknown"
    gate_status = str(production_gate.get("status", "")).strip() or "unknown"
    gate_summary = str(production_gate.get("summary", "")).strip()
    cadence_status = str(run_cadence.get("status", "")).strip() or "unknown"
    cadence_summary = str(run_cadence.get("summary_text", "")).strip()
    prompt_summary = str(prompt_context.get("summary_text", "")).strip()
    review_status = str(review_brief.get("status", "")).strip() or "unknown"
    review_summary = str(review_brief.get("summary_text", "")).strip()

    blocked_states = {"failed", "block"}
    caution_states = {"degraded", "warn"}

    if run_status in blocked_states or gate_status == "block" or review_status == "block":
        status = "blocked"
        summary_text = "调度准备未就绪：当前有阻断或运行失败，先修复再排下一次自动运行。"
        next_step = "先看门禁、运行输出和数据问题，再决定是否恢复自动推进。"
        next_run_mode = "pause"
        next_run_window = "待门禁恢复后"
    elif run_status in caution_states or gate_status == "warn" or cadence_status == "degraded" or review_status == "warn":
        status = "caution"
        summary_text = "调度准备可继续，但存在降级，建议先复核后再进入下一次自动运行。"
        next_step = "先复核门禁、回看摘要和运行节奏，再决定是否继续自动推进。"
        next_run_mode = "manual_review"
        next_run_window = "下次自动运行前"
    else:
        status = "ready"
        summary_text = "调度准备就绪：可以按日常节奏继续下一次运行。"
        next_step = "继续按固定节奏运行，并保持门禁和回看顺序。"
        next_run_mode = "daily_auto"
        next_run_window = "下一次日常运行时"

    read_order = ["production_gate", "run_cadence", "review_brief", "prompt_context"]
    rules = [
        "schedule_hint 只回答是否适合继续自动推进，不替代 production_gate。",
        "status 为 blocked 时先处理门禁和运行失败，不要直接进入下一次自动运行。",
        "status 为 caution 时保留人工复核，不要把降级当作完全放行。",
        "status 为 ready 时可以按日常节奏继续，但仍保留回看顺序。",
    ]

    return {
        "status": status,
        "summary_text": summary_text,
        "next_step": next_step,
        "next_run_mode": next_run_mode,
        "next_run_window": next_run_window,
        "read_order": read_order,
        "rules": rules,
        "evidence": {
            "daily_run_status": run_status,
            "production_gate": {
                "status": gate_status,
                "summary": gate_summary,
            },
            "run_cadence": {
                "status": cadence_status,
                "summary_text": cadence_summary,
            },
            "prompt_context": {
                "summary_text": prompt_summary,
            },
            "review_brief": {
                "status": review_status,
                "summary_text": review_summary,
            },
        },
    }


def build_daily_collaboration_pack(
    *,
    production_gate: dict[str, Any] | None = None,
    action_list: dict[str, Any] | None = None,
    run_cadence: dict[str, Any] | None = None,
    prompt_context: dict[str, Any] | None = None,
    review_brief: dict[str, Any] | None = None,
    schedule_hint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把日常门禁、行动、节奏、提示语境、回看摘要和运行就绪提示收成协作总包。"""
    production_gate = production_gate if isinstance(production_gate, dict) else {}
    action_list = action_list if isinstance(action_list, dict) else {}
    run_cadence = run_cadence if isinstance(run_cadence, dict) else {}
    prompt_context = prompt_context if isinstance(prompt_context, dict) else {}
    review_brief = review_brief if isinstance(review_brief, dict) else {}
    schedule_hint = schedule_hint if isinstance(schedule_hint, dict) else {}

    gate_status = str(production_gate.get("status", "")).strip() or "unknown"
    action_status = str(action_list.get("status", "")).strip() or gate_status
    cadence_status = str(run_cadence.get("status", "")).strip() or "unknown"
    prompt_status = str(prompt_context.get("status", "")).strip() or gate_status
    review_status = str(review_brief.get("status", "")).strip() or "unknown"
    schedule_status = str(schedule_hint.get("status", "")).strip() or "unknown"

    status_rank = {"blocked": 3, "block": 3, "failed": 3, "caution": 2, "warn": 2, "degraded": 2, "ready": 1, "ok": 1, "pass": 1, "unknown": 0}
    worst_rank = max(
        status_rank.get(gate_status, 0),
        status_rank.get(action_status, 0),
        status_rank.get(cadence_status, 0),
        status_rank.get(prompt_status, 0),
        status_rank.get(review_status, 0),
        status_rank.get(schedule_status, 0),
    )
    if worst_rank >= 3:
        status = "blocked"
    elif worst_rank >= 2:
        status = "caution"
    elif worst_rank >= 1:
        status = "ready"
    else:
        status = "unknown"

    summary_parts = [
        f"门禁 {gate_status or 'unknown'}",
        f"行动 {action_status or 'unknown'}",
        f"节奏 {cadence_status or 'unknown'}",
        f"提示语境 {prompt_status or 'unknown'}",
        f"回看 {review_status or 'unknown'}",
        f"调度准备 {schedule_status or 'unknown'}",
    ]
    summary_text = "协作总包已收拢：" + "；".join(summary_parts) + "。"
    if status == "blocked":
        summary_text += " 当前应先处理阻断和数据问题。"
    elif status == "caution":
        summary_text += " 当前可继续看，但建议先复核再动作。"
    else:
        summary_text += " 当前可按既定日常顺序继续。"

    prompt_text = "\n".join(
        [
            "日常协作总包：",
            f"- 门禁: {gate_status}",
            f"- 行动: {action_status}",
            f"- 节奏: {cadence_status}",
            f"- 提示语境: {prompt_status}",
            f"- 回看: {review_status}",
            f"- 调度准备: {schedule_status}",
            "- 读取顺序: production_gate -> action_list -> run_cadence -> prompt_context -> review_brief -> schedule_hint",
            "- 规则: 先读门禁，再读行动和节奏，最后看回看和调度准备。",
            "- 规则: block / blocked 时只能做诊断、修复数据或等待建议。",
            "- 规则: caution / warn / degraded 时先复核，不要把降级当成完全放行。",
        ]
    )

    read_order = [
        "production_gate",
        "action_list",
        "run_cadence",
        "prompt_context",
        "review_brief",
        "schedule_hint",
    ]
    rules = [
        "协作总包不是新分析，只是把现有协作语境再收一层。",
        "先看 production_gate，再看 action_list，再看 run_cadence。",
        "再看 prompt_context、review_brief 和 schedule_hint，避免重复解释同一组结果。",
        "block / blocked 时只给诊断、修复或等待建议。",
    ]

    return {
        "status": status,
        "summary_text": summary_text,
        "prompt_text": prompt_text,
        "read_order": read_order,
        "rules": rules,
        "evidence": {
            "production_gate": production_gate,
            "action_list": {
                "status": action_status,
                "summary_text": str(action_list.get("summary_text", "")).strip(),
                "count": len(action_list.get("items", [])) if isinstance(action_list.get("items", []), list) else 0,
            },
            "run_cadence": run_cadence,
            "prompt_context": prompt_context,
            "review_brief": review_brief,
            "schedule_hint": schedule_hint,
        },
    }


def build_action_list(
    *,
    decision_items: list[dict[str, Any]],
    health_items: list[dict[str, Any]],
    production_gate: dict[str, Any] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """把日常决策和门禁结果收成可执行的行动清单。"""
    production_gate = production_gate if isinstance(production_gate, dict) else {}
    gate_status = str(production_gate.get("status", "")).strip()
    gate_allowed = production_gate.get("allowed_actions", []) if isinstance(production_gate, dict) else []

    health_index: dict[str, dict[str, Any]] = {}
    for item in health_items:
        if not isinstance(item, dict):
            continue
        stock_code = str(item.get("stock_code", "")).strip()
        if stock_code:
            health_index[stock_code] = item

    actions: list[dict[str, Any]] = []
    for item in decision_items:
        if not isinstance(item, dict):
            continue
        stock_code = str(item.get("stock_code", "")).strip()
        stock_name = str(item.get("name", stock_code or "unknown"))
        group = str(item.get("group", "")).strip()
        position_label = str(item.get("position_label", "")).strip()
        data_confidence = safe_float(item.get("data_confidence"), 0.0)
        confidence = safe_float(item.get("confidence"), 0.0)
        health_item = health_index.get(stock_code, {})
        health_status = str(health_item.get("status", item.get("health_status", "")) or "")
        diagnosis = health_item.get("diagnosis", {}) if isinstance(health_item, dict) else {}

        action = "wait"
        priority = 50
        if group == "重点关注" and confidence >= 0.65 and data_confidence >= 0.6:
            action = "review_now"
            priority = 10
        elif group == "继续观察" and position_label.startswith("已持有"):
            action = "hold_watch"
            priority = 20
        elif group == "继续观察":
            action = "wait"
            priority = 30
        elif group == "暂不行动":
            action = "wait"
            priority = 40
        elif group == "数据不足" or data_confidence < 0.55:
            action = "skip_due_to_data"
            priority = 5 if gate_status == "block" else 15

        if gate_status == "block":
            if action == "review_now":
                action = "diagnose"
                priority = 5
            elif action in {"hold_watch", "wait"}:
                action = "diagnose"
                priority = min(priority, 10)
        elif gate_status == "warn" and action == "review_now":
            priority = 15

        if action == "review_now":
            action_hint = "今天优先复核，先看关键证据和最近变化"
            if position_label.startswith("已持有"):
                action_hint = "优先复核持仓变化，先看关键证据和风险位置"
        elif action == "hold_watch":
            action_hint = "先检查仓位、成本和风险线，确认持有是否仍合理"
        elif action == "wait":
            action_hint = "先不动作，等待下一轮数据或更明确触发条件"
        elif action == "skip_due_to_data":
            action_hint = "先跳过本轮判断，优先排查数据或可信度问题"
        elif action == "diagnose":
            action_hint = "先排查门禁阻断原因，再决定是否恢复后续判断"
        else:
            action_hint = "先维持观察，等更明确的信号"

        reason_parts = [
            f"分组 {group}",
            f"置信度 {format_pct(confidence)}",
            f"可信度 {format_pct(data_confidence)}",
            f"健康状态 {health_status or 'unknown'}",
        ]
        if diagnosis:
            reason_parts.append(str(diagnosis.get("primary_label", "")) or str(diagnosis.get("summary", "")))
        if position_label:
            reason_parts.append(position_label)

        actions.append(
            {
                "stock_code": stock_code,
                "name": stock_name,
                "group": group,
                "action": action,
                "priority": priority,
                "position_label": position_label,
                "confidence": round(confidence, 4),
                "data_confidence": round(data_confidence, 4),
                "health_status": health_status,
                "reason": "；".join(part for part in reason_parts if part),
                "action_hint": action_hint,
                "watch_reason": str(item.get("watch_reason", "") or ""),
                "risk_profile": item.get("risk_profile", ""),
                "latest_price": item.get("latest_price"),
                "target_price": item.get("target_price"),
                "stop_loss": item.get("stop_loss"),
                "position_ratio": item.get("position_ratio"),
                "gate_status": gate_status,
                "gate_allowed": gate_allowed,
            }
        )

    action_groups: dict[str, list[dict[str, Any]]] = {
        "review_now": [],
        "hold_watch": [],
        "wait": [],
        "skip_due_to_data": [],
        "diagnose": [],
    }
    for item in actions:
        action_groups.setdefault(str(item.get("action", "wait")), []).append(item)
    for group_items in action_groups.values():
        group_items.sort(key=lambda item: (int(item.get("priority", 99)), -safe_float(item.get("confidence"), 0.0), item.get("stock_code", "")))

    sorted_actions = sorted(actions, key=lambda item: (int(item.get("priority", 99)), -safe_float(item.get("confidence"), 0.0), item.get("stock_code", "")))
    summary_counts = {key: len(value) for key, value in action_groups.items()}
    summary_lines = [
        f"行动分布: 复核 {summary_counts.get('review_now', 0)}，持有观察 {summary_counts.get('hold_watch', 0)}，等待 {summary_counts.get('wait', 0)}，跳过 {summary_counts.get('skip_due_to_data', 0)}，诊断 {summary_counts.get('diagnose', 0)}",
    ]
    if sorted_actions:
        top_actions = [
            f"{item['stock_code']} {item['name']} [{item['action']}] {item['action_hint']}；{item['reason']}"
            for item in sorted_actions[:limit]
        ]
        summary_lines.append("优先行动: " + "；".join(top_actions))

    return {
        "status": gate_status or "unknown",
        "counts": summary_counts,
        "items": sorted_actions[:limit],
        "groups": action_groups,
        "summary_lines": summary_lines,
        "summary_text": "；".join(summary_lines),
    }


def _build_health_diagnosis(
    *,
    stock_name: str,
    history_source: str,
    fundamental_source: str,
    history_reason: str,
    fundamental_reason: str,
    history_failure_stage: str,
    history_failure_code: str,
    history_fallback_strategy: str,
    history_selected_provider: str,
    history_provider_attempts: list[dict[str, Any]] | list[Any],
    fundamental_failure_stage: str,
    fundamental_failure_code: str,
    fundamental_fallback_strategy: str,
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
    if history_failure_stage or history_failure_code or history_fallback_strategy:
        detail_parts.append(
            "历史失败="
            + "/".join(
                part
                for part in [history_failure_stage, history_failure_code, history_fallback_strategy]
                if part
            )
        )
    if history_selected_provider:
        detail_parts.append(f"历史选择={history_selected_provider}")
    if history_provider_attempts:
        detail_parts.append(f"历史尝试={len(history_provider_attempts)} 次")
    if fundamental_failure_stage or fundamental_failure_code or fundamental_fallback_strategy:
        detail_parts.append(
            "基本面失败="
            + "/".join(
                part
                for part in [fundamental_failure_stage, fundamental_failure_code, fundamental_fallback_strategy]
                if part
            )
        )
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
            "history_failure_stage": history_failure_stage,
            "history_failure_code": history_failure_code,
            "history_fallback_strategy": history_fallback_strategy,
            "history_selected_provider": history_selected_provider,
            "history_provider_attempts": history_provider_attempts,
            "fundamental_failure_stage": fundamental_failure_stage,
            "fundamental_failure_code": fundamental_failure_code,
            "fundamental_fallback_strategy": fundamental_fallback_strategy,
            "history_quality_ok": history_ok,
            "fundamental_quality_ok": fundamental_ok,
        },
    }
