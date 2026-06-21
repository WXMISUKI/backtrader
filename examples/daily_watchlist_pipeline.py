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


def main() -> int:
    args = build_parser().parse_args()
    watchlist_path = Path(args.watchlist)
    portfolio_path = Path(args.portfolio)
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
