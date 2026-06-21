#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常统一流程入口。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.data.eastmoney_api import fetch_stock_hist_governed
from core.data.real_provider import RealDataProvider
from core.orchestrator import create_stock_orchestrator
from examples.watchlist_shared import (
    build_portfolio_index,
    build_position_context,
    format_pct,
    load_portfolio,
    load_watchlist,
    safe_float,
    safe_int,
)


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"
DEFAULT_PORTFOLIO_PATH = ROOT_DIR / "config" / "portfolio.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified daily watchlist pipeline.")
    parser.add_argument("--watchlist", default=str(DEFAULT_WATCHLIST_PATH), help="Watchlist JSON file path.")
    parser.add_argument("--portfolio", default=str(DEFAULT_PORTFOLIO_PATH), help="Portfolio JSON file path.")
    parser.add_argument("--start-date", default="20260601", help="History start date, YYYYMMDD.")
    parser.add_argument("--end-date", default="20260614", help="History end date, YYYYMMDD.")
    parser.add_argument("--risk-profile", default="moderate", choices=("conservative", "moderate", "aggressive"))
    parser.add_argument("--limit", type=int, default=0, help="Limit number of watchlist items. 0 means no limit.")
    parser.add_argument("--output-json", default="", help="Optional JSON output file path.")
    parser.add_argument("--compare-with", default="", help="Optional baseline daily report JSON file path.")
    parser.add_argument(
        "--weekly-reports",
        nargs="*",
        default=[],
        help="Daily report JSON file paths. Accepts space-separated paths or a single comma-separated string.",
    )
    parser.add_argument(
        "--stage-reports",
        nargs="*",
        default=[],
        help="Weekly or daily report JSON file paths for stage report aggregation.",
    )
    parser.add_argument("--archive-package", action="store_true", help="Build a consolidated review archive package.")
    parser.add_argument("--archive-name", default="", help="Optional archive package name.")
    return parser


def _build_history_summary(*, raw: dict[str, Any], stock_code: str, stock_name: str) -> dict[str, Any]:
    if not stock_code:
        return {
            "stock_code": "",
            "name": stock_name,
            "status": "明显降级",
            "history_source": "config_error",
            "fundamental_source": "config_error",
            "history_quality": {"ok": False, "reason": "missing stock_code"},
            "fundamental_quality": {"ok": False, "reason": "missing stock_code"},
            "history_reason": "watchlist 配置缺少 stock_code",
            "fundamental_reason": "watchlist 配置缺少 stock_code",
            "health_score": 0,
            "summary": f"{stock_name} 配置不完整，无法预检。",
            "flags": {"history_degraded": True, "fundamental_degraded": True},
        }

    provider = RealDataProvider()
    try:
        history = fetch_stock_hist_governed(symbol=stock_code, start_date=raw["start_date"], end_date=raw["end_date"])
    except Exception as exc:
        history = {
            "data_source": "error",
            "is_degraded": True,
            "quality": {"ok": False, "reason": str(exc)},
            "reason": str(exc),
        }

    try:
        fundamental = provider.get_financial_indicators_governed(stock_code)
    except Exception as exc:
        fundamental = {
            "data_source": "error",
            "is_degraded": True,
            "quality": {"ok": False, "reason": str(exc)},
            "reason": str(exc),
        }

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

    return {
        "stock_code": stock_code,
        "name": stock_name,
        "status": status,
        "health_score": min(score, 100),
        "history_source": history_source,
        "fundamental_source": fundamental_source,
        "history_quality": history_quality,
        "fundamental_quality": fundamental_quality,
        "history_reason": history_reason,
        "fundamental_reason": fundamental_reason,
        "summary": f"{stock_name} 数据健康状态为{status}，健康分 {min(score, 100)} 分。",
        "flags": {
            "history_degraded": history_degraded,
            "fundamental_degraded": fundamental_degraded,
            "history_quality_ok": bool(history_quality.get("ok", False)),
            "fundamental_quality_ok": bool(fundamental_quality.get("ok", False)),
        },
        "history_rows": safe_int(history.get("quality", {}).get("rows", 0)),
        "fundamental_report_date": str(fundamental.get("payload", {}).get("report_date", "")) if isinstance(fundamental, dict) else "",
        "history_date_range": f"{raw['start_date']} ~ {raw['end_date']}",
    }


def _build_decision_summary(
    *,
    item: dict[str, Any],
    result: dict[str, Any],
    default_risk_profile: str,
    position_context: dict[str, Any],
) -> dict[str, Any]:
    analysis = result.get("data", {}) if isinstance(result, dict) else {}
    recommendation = analysis.get("recommendation", {}) if isinstance(analysis, dict) else {}
    risk = analysis.get("risk", {}) if isinstance(analysis, dict) else {}
    stock = analysis.get("stock", {}) if isinstance(analysis, dict) else {}
    governance = result.get("governance", {}) if isinstance(result, dict) else {}

    stock_code = str(stock.get("code") or item.get("stock_code") or "").strip()
    stock_name = str(stock.get("name") or item.get("name") or stock_code or "unknown")
    action = str(recommendation.get("action", "HOLD")).upper()
    confidence = safe_float(recommendation.get("confidence"), 0.0)
    data_source = str(result.get("data_source") or analysis.get("data_source") or stock.get("source") or "unknown")
    is_degraded = bool(governance.get("is_degraded")) or data_source == "mock"
    group = "继续观察"
    if is_degraded or data_source == "mock":
        group = "数据不足"
    elif action == "BUY" and confidence >= 0.65:
        group = "重点关注"
    elif action == "SELL":
        group = "暂不行动"

    return {
        "stock_code": stock_code,
        "name": stock_name,
        "group": group,
        "结论": f"{stock_name} 进入{group}。",
        "依据": [
            f"推荐动作 {action}",
            f"置信度 {format_pct(confidence)}",
            f"数据来源 {data_source}",
            f"配置风险 {item.get('risk_profile', default_risk_profile)}",
            *([f"推荐原因 {recommendation.get('reason')}"] if recommendation.get("reason") else []),
        ],
        "风险": str(risk.get("risk_level", "")),
        "下一步动作": "保持跟踪，等更明确的信号再处理。",
        "action": action,
        "confidence": round(confidence, 4),
        "data_source": data_source,
        "risk_level": risk.get("risk_level", ""),
        "reason": str(recommendation.get("reason", "")),
        "watch_reason": str(item.get("reason", "")),
        "tags": item.get("tags", []),
        "risk_profile": item.get("risk_profile", default_risk_profile),
        "latest_price": stock.get("latest_price"),
        "target_price": recommendation.get("target_price"),
        "stop_loss": recommendation.get("stop_loss"),
        "position_ratio": recommendation.get("position_ratio"),
        "max_drawdown": risk.get("max_drawdown"),
        "volatility": risk.get("volatility"),
        "degraded": is_degraded,
        **position_context,
    }


def _build_daily_summary(
    *,
    health_groups: dict[str, list[dict[str, Any]]],
    decision_groups: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    health_counts = {key: len(value) for key, value in health_groups.items()}
    decision_counts = {key: len(value) for key, value in decision_groups.items()}
    top_focus = [item["stock_code"] + " " + item["name"] for item in decision_groups.get("重点关注", [])[:3]]
    watch_list = [item["stock_code"] + " " + item["name"] for item in decision_groups.get("继续观察", [])[:3]]
    held_alerts = [
        item["stock_code"] + " " + item["name"]
        for item in decision_groups.get("继续观察", [])
        if str(item.get("position_label", "")).startswith("已持有")
    ][:3]
    status = "平稳"
    if health_counts.get("明显降级", 0) > 0 or decision_counts.get("数据不足", 0) > 0:
        status = "需要谨慎"
    elif decision_counts.get("重点关注", 0) > 0:
        status = "出现重点关注"

    lines = [
        f"今日总览: {status}",
        f"健康状态: 完全可用 {health_counts.get('完全可用', 0)}，部分降级 {health_counts.get('部分降级', 0)}，明显降级 {health_counts.get('明显降级', 0)}",
        f"决策分布: 重点关注 {decision_counts.get('重点关注', 0)}，继续观察 {decision_counts.get('继续观察', 0)}，暂不行动 {decision_counts.get('暂不行动', 0)}，数据不足 {decision_counts.get('数据不足', 0)}",
    ]
    if top_focus:
        lines.append(f"重点关注: {'，'.join(top_focus)}")
    if watch_list:
        lines.append(f"继续观察: {'，'.join(watch_list)}")
    if held_alerts:
        lines.append(f"持仓留意: {'，'.join(held_alerts)}")

    return {
        "status": status,
        "health_counts": health_counts,
        "decision_counts": decision_counts,
        "highlights": {
            "top_focus": top_focus,
            "watch_list": watch_list,
            "held_alerts": held_alerts,
        },
        "summary_lines": lines,
        "summary_text": "；".join(lines),
    }


def _build_daily_report(
    *,
    generated_at: str,
    watchlist_path: Path,
    portfolio_path: Path,
    health_groups: dict[str, list[dict[str, Any]]],
    decision_groups: dict[str, list[dict[str, Any]]],
    daily_summary: dict[str, Any],
    portfolio_count: int,
    portfolio_value: float,
    total_assets: float,
) -> dict[str, Any]:
    health_counts = daily_summary["health_counts"]
    decision_counts = daily_summary["decision_counts"]
    headline = f"今日总览：{daily_summary['status']}"
    overview = daily_summary["summary_text"]
    health_summary = (
        f"健康状态：完全可用 {health_counts.get('完全可用', 0)}，部分降级 {health_counts.get('部分降级', 0)}，"
        f"明显降级 {health_counts.get('明显降级', 0)}"
    )
    portfolio_summary = f"持仓数量 {portfolio_count}，持仓市值 {portfolio_value:.2f}，总资产 {total_assets:.2f}"
    watchlist_summary = (
        f"决策分布：重点关注 {decision_counts.get('重点关注', 0)}，继续观察 {decision_counts.get('继续观察', 0)}，"
        f"暂不行动 {decision_counts.get('暂不行动', 0)}，数据不足 {decision_counts.get('数据不足', 0)}"
    )
    highlights = {
        "重点关注": daily_summary["highlights"]["top_focus"],
        "继续观察": daily_summary["highlights"]["watch_list"],
        "持仓留意": daily_summary["highlights"]["held_alerts"],
    }
    report_lines = [
        headline,
        overview,
        health_summary,
        portfolio_summary,
        watchlist_summary,
    ]
    if highlights["重点关注"]:
        report_lines.append(f"重点关注：{'，'.join(highlights['重点关注'])}")
    if highlights["继续观察"]:
        report_lines.append(f"继续观察：{'，'.join(highlights['继续观察'])}")
    if highlights["持仓留意"]:
        report_lines.append(f"持仓留意：{'，'.join(highlights['持仓留意'])}")

    return {
        "headline": headline,
        "overview": overview,
        "health_summary": health_summary,
        "portfolio_summary": portfolio_summary,
        "watchlist_summary": watchlist_summary,
        "highlights": highlights,
        "report_lines": report_lines,
        "report_text": "\n".join(report_lines),
        "generated_at": generated_at,
        "watchlist_path": str(watchlist_path),
        "portfolio_path": str(portfolio_path),
    }


def _load_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload if isinstance(payload, dict) else {}


def _build_daily_comparison(current_report: dict[str, Any], baseline_report: dict[str, Any]) -> dict[str, Any]:
    if not baseline_report:
        return {
            "baseline_path": "",
            "changed_sections": [],
            "summary_text": "",
            "delta_items": {},
        }

    changed_sections: list[str] = []
    delta_items: dict[str, Any] = {}

    for key in ("headline", "health_summary", "portfolio_summary", "watchlist_summary"):
        current_value = str(current_report.get(key, ""))
        baseline_value = str(baseline_report.get(key, ""))
        if current_value != baseline_value:
            changed_sections.append(key)
            delta_items[key] = {
                "current": current_value,
                "baseline": baseline_value,
            }

    current_highlights = current_report.get("highlights", {}) if isinstance(current_report, dict) else {}
    baseline_highlights = baseline_report.get("highlights", {}) if isinstance(baseline_report, dict) else {}
    for key in ("重点关注", "继续观察", "持仓留意"):
        current_items = current_highlights.get(key, []) if isinstance(current_highlights, dict) else []
        baseline_items = baseline_highlights.get(key, []) if isinstance(baseline_highlights, dict) else []
        if current_items != baseline_items:
            changed_sections.append(f"highlights.{key}")
            delta_items[f"highlights.{key}"] = {
                "current": current_items,
                "baseline": baseline_items,
            }

    summary_text = "；".join(changed_sections) if changed_sections else "与基线报告相比暂无变化"
    return {
        "baseline_path": str(baseline_report.get("_source_path", "")),
        "changed_sections": changed_sections,
        "summary_text": summary_text,
        "delta_items": delta_items,
    }


def _load_report_list(raw_paths: list[str]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    flattened: list[str] = []
    for raw in raw_paths:
        flattened.extend(part.strip() for part in raw.split(",") if part.strip())
    for path_text in flattened:
        report_path = Path(path_text)
        payload = _load_json_payload(report_path)
        if payload:
            daily_report = payload.get("daily_report", {}) if isinstance(payload, dict) else {}
            if isinstance(daily_report, dict):
                daily_report = dict(daily_report)
                daily_report["_source_path"] = str(report_path)
                daily_report["_payload"] = payload
                reports.append(daily_report)
    return reports


def _build_weekly_report(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not reports:
        return {
            "period": "",
            "headline": "",
            "summary": "",
            "health_trend": {},
            "decision_trend": {},
            "portfolio_trend": {},
            "highlights": {},
            "report_lines": [],
            "report_text": "",
        }

    start = reports[0].get("generated_at", "")
    end = reports[-1].get("generated_at", "")
    period = f"{start} ~ {end}" if start and end else ""

    health_trend = {
        "完全可用": [r.get("health_summary", "") for r in reports],
        "变化次数": len({r.get("health_summary", "") for r in reports}),
    }
    decision_trend = {
        "日报数量": len(reports),
        "变化次数": len({r.get("watchlist_summary", "") for r in reports}),
    }
    portfolio_trend = {
        "持仓变化次数": len({r.get("portfolio_summary", "") for r in reports}),
    }

    first = reports[0]
    last = reports[-1]
    headline = "周报总览：日报保持稳定"
    if first.get("headline") != last.get("headline"):
        headline = "周报总览：出现变化"

    highlights = {
        "最近日报": last.get("headline", ""),
        "重点关注": last.get("highlights", {}).get("重点关注", []) if isinstance(last.get("highlights", {}), dict) else [],
        "继续观察": last.get("highlights", {}).get("继续观察", []) if isinstance(last.get("highlights", {}), dict) else [],
    }
    summary = f"本周汇总 {len(reports)} 份日报，最后一份日期 {end or 'unknown'}。"
    report_lines = [
        headline,
        summary,
        f"周期：{period}",
        f"健康趋势：变化次数 {health_trend['变化次数']}",
        f"决策趋势：日报数量 {decision_trend['日报数量']}，变化次数 {decision_trend['变化次数']}",
        f"持仓趋势：变化次数 {portfolio_trend['持仓变化次数']}",
    ]
    if highlights["重点关注"]:
        report_lines.append(f"重点关注：{'，'.join(highlights['重点关注'])}")
    if highlights["继续观察"]:
        report_lines.append(f"继续观察：{'，'.join(highlights['继续观察'])}")

    return {
        "period": period,
        "headline": headline,
        "summary": summary,
        "health_trend": health_trend,
        "decision_trend": decision_trend,
        "portfolio_trend": portfolio_trend,
        "highlights": highlights,
        "report_lines": report_lines,
        "report_text": "\n".join(report_lines),
        "report_count": len(reports),
    }


def _load_stage_reports(raw_paths: list[str]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    flattened: list[str] = []
    for raw in raw_paths:
        flattened.extend(part.strip() for part in raw.split(",") if part.strip())
    for path_text in flattened:
        report_path = Path(path_text)
        payload = _load_json_payload(report_path)
        if not payload:
            continue
        if isinstance(payload.get("stage_report"), dict):
            stage_report = dict(payload["stage_report"])
            stage_report["_source_path"] = str(report_path)
            reports.append(stage_report)
            continue
        if isinstance(payload.get("weekly_report"), dict):
            weekly_report = dict(payload["weekly_report"])
            weekly_report["_source_path"] = str(report_path)
            reports.append(weekly_report)
            continue
        if isinstance(payload.get("daily_report"), dict):
            daily_report = dict(payload["daily_report"])
            daily_report["_source_path"] = str(report_path)
            reports.append(daily_report)
    return reports


def _build_stage_report(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not reports:
        return {
            "period": "",
            "headline": "",
            "summary": "",
            "health_summary": "",
            "decision_summary": "",
            "portfolio_summary": "",
            "trend_summary": "",
            "highlights": {},
            "report_lines": [],
            "report_text": "",
            "report_count": 0,
        }

    start = reports[0].get("generated_at", reports[0].get("period", ""))
    end = reports[-1].get("generated_at", reports[-1].get("period", ""))
    period = f"{start} ~ {end}" if start and end else ""
    report_count = len(reports)

    headline = "阶段总览：整体保持稳定"
    if str(reports[0].get("headline", "")) != str(reports[-1].get("headline", "")):
        headline = "阶段总览：出现变化"

    health_summary = f"健康趋势：共 {report_count} 份报告"
    decision_summary = f"决策趋势：共 {report_count} 份报告"
    portfolio_summary = f"持仓趋势：共 {report_count} 份报告"
    trend_summary = f"本阶段累计 {report_count} 份报告，覆盖从 {start or 'unknown'} 到 {end or 'unknown'}。"

    highlights = {
        "最新报告": reports[-1].get("headline", ""),
        "阶段重点关注": reports[-1].get("highlights", {}).get("重点关注", []) if isinstance(reports[-1].get("highlights", {}), dict) else [],
        "阶段继续观察": reports[-1].get("highlights", {}).get("继续观察", []) if isinstance(reports[-1].get("highlights", {}), dict) else [],
    }
    report_lines = [
        headline,
        trend_summary,
        health_summary,
        decision_summary,
        portfolio_summary,
    ]
    if highlights["阶段重点关注"]:
        report_lines.append(f"阶段重点关注：{'，'.join(highlights['阶段重点关注'])}")
    if highlights["阶段继续观察"]:
        report_lines.append(f"阶段继续观察：{'，'.join(highlights['阶段继续观察'])}")

    return {
        "period": period,
        "headline": headline,
        "summary": trend_summary,
        "health_summary": health_summary,
        "decision_summary": decision_summary,
        "portfolio_summary": portfolio_summary,
        "trend_summary": trend_summary,
        "highlights": highlights,
        "report_lines": report_lines,
        "report_text": "\n".join(report_lines),
        "report_count": report_count,
    }


def _build_archive_package(
    *,
    archive_name: str,
    daily_report: dict[str, Any],
    daily_comparison: dict[str, Any],
    weekly_report: dict[str, Any],
    stage_report: dict[str, Any],
    portfolio_summary: dict[str, Any],
) -> dict[str, Any]:
    name = archive_name or "自选股复盘留档包"
    title = name
    sections = [
        {
            "title": "复盘总览",
            "summary": "留档包已汇总当前日报、对比、周报与阶段报告。",
            "text": daily_report.get("report_text", ""),
        },
        {
            "title": "当日日报",
            "summary": daily_report.get("headline", ""),
            "text": daily_report.get("report_text", ""),
        },
        {
            "title": "日报对比",
            "summary": daily_comparison.get("summary_text", "") or "暂无变化",
            "text": daily_comparison.get("summary_text", "") or "暂无变化",
        },
        {
            "title": "周报模板",
            "summary": weekly_report.get("headline", "") or "未提供",
            "text": weekly_report.get("report_text", "") or "未提供",
        },
        {
            "title": "阶段报告",
            "summary": stage_report.get("headline", "") or "未提供",
            "text": stage_report.get("report_text", "") or "未提供",
        },
        {
            "title": "持仓语境",
            "summary": f"{portfolio_summary.get('count', 0)} 只，市值 {portfolio_summary.get('market_value', 0.0):.2f}",
            "text": f"持仓数量 {portfolio_summary.get('count', 0)}，持仓市值 {portfolio_summary.get('market_value', 0.0):.2f}，总资产 {portfolio_summary.get('total_assets', 0.0):.2f}",
        },
    ]
    summary = "；".join(section["summary"] for section in sections if section.get("summary"))
    report_lines = [
        f"留档包：{name}",
        f"总览：{summary or '暂无摘要'}",
        *[f"{section['title']}：{section['summary']}" for section in sections],
    ]
    return {
        "title": title,
        "name": name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "sections": sections,
        "daily_report": daily_report,
        "daily_comparison": daily_comparison,
        "weekly_report": weekly_report,
        "stage_report": stage_report,
        "portfolio_summary": portfolio_summary,
        "report_lines": report_lines,
        "report_text": "\n".join(report_lines),
    }


def main() -> int:
    args = build_parser().parse_args()
    watchlist_path = Path(args.watchlist)
    portfolio_path = Path(args.portfolio)
    compare_path = Path(args.compare_with) if args.compare_with else None
    weekly_reports = _load_report_list(args.weekly_reports) if args.weekly_reports else []
    stage_reports = _load_stage_reports(args.stage_reports) if args.stage_reports else []
    orchestrator = create_stock_orchestrator()

    try:
        watchlist = load_watchlist(watchlist_path)
    except Exception as exc:
        print(f"读取 watchlist 失败: {exc}")
        return 1

    if args.limit and args.limit > 0:
        watchlist = watchlist[: args.limit]

    if not watchlist:
        print("watchlist 为空，未执行流程。")
        return 1

    portfolio_items, total_assets = load_portfolio(portfolio_path)
    portfolio_index = build_portfolio_index(portfolio_items)
    portfolio_count = len(portfolio_index)
    portfolio_value = sum(
        safe_float(item.get("market_price"), 0.0) * safe_float(item.get("size"), 0.0)
        for item in portfolio_items
    )

    print("== 自选股日常统一流程 ==")
    print(f"生成时间: {datetime.now().isoformat(timespec='seconds')}")
    print(f"watchlist: {watchlist_path}")
    print(f"portfolio: {portfolio_path}")
    print(f"历史区间: {args.start_date} ~ {args.end_date}")
    print(f"默认风险: {args.risk_profile}")
    print(f"持仓数量: {portfolio_count}，持仓市值: {portfolio_value:.2f}，总资产: {total_assets:.2f}")

    health_items: list[dict[str, Any]] = []
    decision_items: list[dict[str, Any]] = []
    for raw in watchlist:
        stock_code = str(raw.get("stock_code", "")).strip()
        stock_name = str(raw.get("name", stock_code or "unknown"))
        if not stock_code:
            health_items.append(_build_history_summary(raw={"start_date": args.start_date, "end_date": args.end_date}, stock_code="", stock_name=stock_name))
            decision_items.append(
                {
                    "stock_code": "",
                    "name": stock_name,
                    "group": "数据不足",
                    "结论": f"{stock_name} 缺少股票代码，无法分析。",
                    "依据": ["watchlist 配置缺少 stock_code"],
                    "风险": "请补充股票代码后再运行。",
                    "下一步动作": "修正配置，再重新执行。",
                    "action": "ERROR",
                    "confidence": 0.0,
                    "data_source": "config_error",
                    "degraded": True,
                    **build_position_context(
                        stock_code="",
                        stock_name=stock_name,
                        portfolio_index=portfolio_index,
                        total_assets=total_assets,
                    ),
                }
            )
            continue

        health_item = _build_history_summary(
            raw={"start_date": args.start_date, "end_date": args.end_date},
            stock_code=stock_code,
            stock_name=stock_name,
        )
        health_items.append(health_item)

        risk_profile = str(raw.get("risk_profile", args.risk_profile) or args.risk_profile)
        try:
            result = orchestrator.analyze(stock_code, risk_profile=risk_profile)
            decision_items.append(
                _build_decision_summary(
                    item=raw,
                    result=result,
                    default_risk_profile=args.risk_profile,
                    position_context=build_position_context(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        portfolio_index=portfolio_index,
                        total_assets=total_assets,
                    ),
                )
            )
        except Exception as exc:
            decision_items.append(
                {
                    "stock_code": stock_code,
                    "name": stock_name,
                    "group": "数据不足",
                    "结论": f"{stock_name} 分析失败。",
                    "依据": [f"异常: {exc}"],
                    "风险": "这次结果不可用，先排查数据源或分析链路。",
                    "下一步动作": "稍后重试或切换数据源。",
                    "action": "ERROR",
                    "confidence": 0.0,
                    "data_source": "error",
                    "degraded": True,
                    **build_position_context(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        portfolio_index=portfolio_index,
                        total_assets=total_assets,
                    ),
                }
            )

    health_groups = {
        "完全可用": [item for item in health_items if item.get("status") == "完全可用"],
        "部分降级": [item for item in health_items if item.get("status") == "部分降级"],
        "明显降级": [item for item in health_items if item.get("status") == "明显降级"],
    }
    decision_groups = {
        "重点关注": [item for item in decision_items if item.get("group") == "重点关注"],
        "继续观察": [item for item in decision_items if item.get("group") == "继续观察"],
        "暂不行动": [item for item in decision_items if item.get("group") == "暂不行动"],
        "数据不足": [item for item in decision_items if item.get("group") == "数据不足"],
    }
    daily_summary = _build_daily_summary(health_groups=health_groups, decision_groups=decision_groups)
    daily_report = _build_daily_report(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        watchlist_path=watchlist_path,
        portfolio_path=portfolio_path,
        health_groups=health_groups,
        decision_groups=decision_groups,
        daily_summary=daily_summary,
        portfolio_count=portfolio_count,
        portfolio_value=portfolio_value,
        total_assets=total_assets,
    )
    baseline_payload = _load_json_payload(compare_path) if compare_path is not None else {}
    if baseline_payload:
        baseline_report = baseline_payload.get("daily_report", {}) if isinstance(baseline_payload, dict) else {}
        if isinstance(baseline_report, dict):
            baseline_report = dict(baseline_report)
            baseline_report["_source_path"] = str(compare_path)
        daily_comparison = _build_daily_comparison(daily_report, baseline_report)
    else:
        daily_comparison = {
            "baseline_path": "",
            "changed_sections": [],
            "summary_text": "",
            "delta_items": {},
        }

    print("\n== 日更报告 ==")
    for line in daily_report["report_lines"]:
        print(f"- {line}")

    if daily_comparison["changed_sections"]:
        print("\n== 日报对比 ==")
        print(f"- 对比基线: {daily_comparison['baseline_path']}")
        print(f"- 变化摘要: {daily_comparison['summary_text']}")

    weekly_report = _build_weekly_report(weekly_reports)
    if weekly_reports:
        print("\n== 周报模板 ==")
        for line in weekly_report["report_lines"]:
            print(f"- {line}")

    stage_report = _build_stage_report(stage_reports)
    if stage_reports:
        print("\n== 阶段报告模板 ==")
        for line in stage_report["report_lines"]:
            print(f"- {line}")

    archive_package = {}
    if args.archive_package:
        archive_package = _build_archive_package(
            archive_name=args.archive_name,
            daily_report=daily_report,
            daily_comparison=daily_comparison,
            weekly_report=weekly_report,
            stage_report=stage_report,
            portfolio_summary={
                "count": portfolio_count,
                "market_value": round(portfolio_value, 2),
                "total_assets": round(total_assets, 2),
            },
        )
        print("\n== 复盘留档包 ==")
        for line in archive_package["report_lines"]:
            print(f"- {line}")

    print("\n== 数据健康预检 ==")
    print(f"总计: {len(health_items)} 只，完全可用 {len(health_groups['完全可用'])}，部分降级 {len(health_groups['部分降级'])}，明显降级 {len(health_groups['明显降级'])}")
    for title, items in health_groups.items():
        print(f"\n-- {title} ({len(items)}) --")
        for item in items[:5]:
            print(f"- {item['stock_code']} {item['name']} [{item['status']}] {item['summary']}")

    print("\n== 日常决策清单 ==")
    print(f"总计: {len(decision_items)} 只，重点关注 {len(decision_groups['重点关注'])}，继续观察 {len(decision_groups['继续观察'])}，暂不行动 {len(decision_groups['暂不行动'])}，数据不足 {len(decision_groups['数据不足'])}")
    for title, items in decision_groups.items():
        print(f"\n-- {title} ({len(items)}) --")
        for item in items:
            print(f"- {item['stock_code']} {item['name']} [{item['group']}] {item['结论']}")
            print(f"  持仓: {item.get('position_summary', '')}")

    output_path = Path(args.output_json) if args.output_json else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "watchlist_path": str(watchlist_path),
            "portfolio_path": str(portfolio_path),
            "history_start_date": args.start_date,
            "history_end_date": args.end_date,
            "counts": {
                "health": {key: len(value) for key, value in health_groups.items()},
                "decision": {key: len(value) for key, value in decision_groups.items()},
            },
            "health": {"items": health_items, "groups": health_groups},
            "decision": {"items": decision_items, "groups": decision_groups},
            "daily_summary": daily_summary,
            "daily_report": daily_report,
            "daily_comparison": daily_comparison,
            "weekly_report": weekly_report,
            "stage_report": stage_report,
            "archive_package": archive_package,
            "portfolio_summary": {
                "count": portfolio_count,
                "market_value": round(portfolio_value, 2),
                "total_assets": round(total_assets, 2),
            },
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n已导出: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
