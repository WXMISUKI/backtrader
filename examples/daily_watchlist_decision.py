#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常决策清单示例。

用法：
    python examples/daily_watchlist_decision.py
    python examples/daily_watchlist_decision.py --watchlist config/watchlist.json --output-json logs/daily_watchlist.json
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

from core.orchestrator import create_stock_orchestrator


DEFAULT_WATCHLIST_PATH = ROOT_DIR / "config" / "watchlist.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily watchlist decision summary.")
    parser.add_argument(
        "--watchlist",
        default=str(DEFAULT_WATCHLIST_PATH),
        help="Watchlist JSON file path.",
    )
    parser.add_argument(
        "--risk-profile",
        default="moderate",
        choices=("conservative", "moderate", "aggressive"),
        help="Fallback risk profile for watchlist items.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of watchlist items. 0 means no limit.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional JSON output file path.",
    )
    return parser


def _load_watchlist(path: Path) -> list[dict[str, Any]]:
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_pct(value: Any) -> str:
    number = _safe_float(value, default=0.0)
    return f"{number:.1%}"


def _classify_item(*, action: str, confidence: float, is_degraded: bool, data_source: str) -> tuple[str, str, str]:
    action = str(action or "HOLD").upper()
    if is_degraded or data_source == "mock":
        return (
            "数据不足",
            "当前结果来自降级或模拟数据，先补足可信数据再判断。",
            "先检查数据源状态，再决定是否继续跟踪。",
        )

    if action == "BUY" and confidence >= 0.65:
        return (
            "重点关注",
            "买入信号和置信度都达到当前清单的关注阈值。",
            "结合仓位约束，小仓位试探或继续盯盘。",
        )

    if action == "SELL":
        return (
            "暂不行动",
            "当前推荐动作偏向卖出，不适合继续加关注。",
            "先回避风险，等趋势或基本面重新修复。",
        )

    if action == "BUY":
        return (
            "继续观察",
            "出现买入倾向，但置信度还没有到重点关注阈值。",
            "继续观察后续信号变化，再决定是否介入。",
        )

    return (
        "继续观察",
        "当前更适合观察而不是立即行动。",
        "保持跟踪，等更明确的信号再处理。",
    )


def _build_item_summary(item: dict[str, Any], result: dict[str, Any], default_risk_profile: str) -> dict[str, Any]:
    analysis = result.get("data", {}) if isinstance(result, dict) else {}
    recommendation = analysis.get("recommendation", {}) if isinstance(analysis, dict) else {}
    risk = analysis.get("risk", {}) if isinstance(analysis, dict) else {}
    stock = analysis.get("stock", {}) if isinstance(analysis, dict) else {}
    governance = result.get("governance", {}) if isinstance(result, dict) else {}

    stock_code = str(stock.get("code") or item.get("stock_code") or "").strip()
    stock_name = str(stock.get("name") or item.get("name") or stock_code or "unknown")
    action = str(recommendation.get("action", "HOLD")).upper()
    confidence = _safe_float(recommendation.get("confidence"), 0.0)
    data_source = str(result.get("data_source") or analysis.get("data_source") or stock.get("source") or "unknown")
    is_degraded = bool(governance.get("is_degraded")) or data_source == "mock"
    group, group_reason, next_action = _classify_item(
        action=action,
        confidence=confidence,
        is_degraded=is_degraded,
        data_source=data_source,
    )

    latest_price = stock.get("latest_price")
    summary = {
        "stock_code": stock_code,
        "name": stock_name,
        "group": group,
        "结论": f"{stock_name} 进入{group}。",
        "依据": [
            f"推荐动作 {action}",
            f"置信度 {_format_pct(confidence)}",
            f"数据来源 {data_source}",
            f"配置风险 {item.get('risk_profile', default_risk_profile)}",
            *( [f"推荐原因 {recommendation.get('reason')}"] if recommendation.get("reason") else [] ),
        ],
        "风险": _build_risk_text(
            group=group,
            group_reason=group_reason,
            risk=risk,
            data_source=data_source,
            is_degraded=is_degraded,
        ),
        "下一步动作": next_action,
        "action": action,
        "confidence": round(confidence, 4),
        "data_source": data_source,
        "risk_level": risk.get("risk_level", ""),
        "reason": str(recommendation.get("reason", "")),
        "watch_reason": str(item.get("reason", "")),
        "tags": item.get("tags", []),
        "risk_profile": item.get("risk_profile", default_risk_profile),
        "latest_price": latest_price,
        "target_price": recommendation.get("target_price"),
        "stop_loss": recommendation.get("stop_loss"),
        "position_ratio": recommendation.get("position_ratio"),
        "max_drawdown": risk.get("max_drawdown"),
        "volatility": risk.get("volatility"),
        "degraded": is_degraded,
    }
    return summary


def _build_risk_text(*, group: str, group_reason: str, risk: dict[str, Any], data_source: str, is_degraded: bool) -> str:
    parts = [group_reason]
    risk_level = risk.get("risk_level")
    if risk_level:
        parts.append(f"风险等级 {risk_level}")
    volatility = risk.get("volatility")
    if volatility is not None:
        parts.append(f"波动率 {_format_pct(volatility)}")
    max_drawdown = risk.get("max_drawdown")
    if max_drawdown is not None:
        parts.append(f"最大回撤 {_format_pct(abs(_safe_float(max_drawdown, 0.0)))}")
    if is_degraded or data_source == "mock":
        parts.append("数据处于降级状态")
    if group == "数据不足":
        parts.append("当前结果不适合作为直接行动依据")
    return "；".join(parts)


def _print_item(summary: dict[str, Any]) -> None:
    print(f"- {summary['stock_code']} {summary['name']} [{summary['group']}]")
    print(f"  结论: {summary['结论']}")
    print(f"  依据: {summary['依据']}")
    print(f"  风险: {summary['风险']}")
    print(f"  下一步动作: {summary['下一步动作']}")
    extra = []
    if summary.get("latest_price") is not None:
        extra.append(f"最新价 {summary['latest_price']:.2f}")
    extra.append(f"动作 {summary['action']}")
    extra.append(f"置信度 {_format_pct(summary['confidence'])}")
    extra.append(f"数据 {summary['data_source']}")
    print(f"  详情: {' | '.join(extra)}")


def _print_group(title: str, items: list[dict[str, Any]]) -> None:
    print(f"\n== {title} ({len(items)}) ==")
    if not items:
        print("  无")
        return
    for item in items:
        _print_item(item)


def main() -> int:
    args = build_parser().parse_args()
    watchlist_path = Path(args.watchlist)
    orchestrator = create_stock_orchestrator()

    try:
        watchlist = _load_watchlist(watchlist_path)
    except Exception as exc:
        print(f"读取 watchlist 失败: {exc}")
        return 1

    if args.limit and args.limit > 0:
        watchlist = watchlist[: args.limit]

    if not watchlist:
        print("watchlist 为空，未执行分析。")
        return 1

    print("== 自选股日常决策清单 ==")
    print(f"生成时间: {datetime.now().isoformat(timespec='seconds')}")
    print(f"watchlist: {watchlist_path}")
    print(f"默认风险: {args.risk_profile}")

    items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for item in watchlist:
        stock_code = str(item.get("stock_code", "")).strip()
        stock_name = str(item.get("name", stock_code or "unknown"))
        risk_profile = str(item.get("risk_profile", args.risk_profile) or args.risk_profile)
        if not stock_code:
            errors.append(
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
                }
            )
            continue

        try:
            result = orchestrator.analyze(stock_code, risk_profile=risk_profile)
            summary = _build_item_summary(item, result, args.risk_profile)
            items.append(summary)
        except Exception as exc:
            errors.append(
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
                }
            )

    items.extend(errors)
    items.sort(key=lambda x: (_group_order(str(x.get("group", ""))), -_safe_float(x.get("confidence"), 0.0), str(x.get("stock_code", ""))))

    groups = {
        "重点关注": [item for item in items if item.get("group") == "重点关注"],
        "继续观察": [item for item in items if item.get("group") == "继续观察"],
        "暂不行动": [item for item in items if item.get("group") == "暂不行动"],
        "数据不足": [item for item in items if item.get("group") == "数据不足"],
    }

    total = len(items)
    counts = {key: len(value) for key, value in groups.items()}
    print(f"\n总计: {total} 只，重点关注 {counts['重点关注']}，继续观察 {counts['继续观察']}，暂不行动 {counts['暂不行动']}，数据不足 {counts['数据不足']}")

    _print_group("重点关注", groups["重点关注"])
    _print_group("继续观察", groups["继续观察"])
    _print_group("暂不行动", groups["暂不行动"])
    _print_group("数据不足", groups["数据不足"])

    output_path = Path(args.output_json) if args.output_json else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "watchlist_path": str(watchlist_path),
            "default_risk_profile": args.risk_profile,
            "counts": counts,
            "items": items,
            "groups": groups,
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n已导出: {output_path}")

    return 0


def _group_order(group: str) -> int:
    order = {
        "重点关注": 0,
        "继续观察": 1,
        "暂不行动": 2,
        "数据不足": 3,
    }
    return order.get(group, 99)


if __name__ == "__main__":
    raise SystemExit(main())
