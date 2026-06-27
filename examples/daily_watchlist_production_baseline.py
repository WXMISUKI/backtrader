#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常投产实跑基线。

用法：
    python examples/daily_watchlist_production_baseline.py
    python examples/daily_watchlist_production_baseline.py --archive-dir logs/daily_watchlist_archive
    python examples/daily_watchlist_production_baseline.py --show-json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from examples.env_guard import build_env_guard
from examples.watchlist_shared import build_feedback_effect_brief, build_regression_gate


DEFAULT_ARCHIVE_DIR = ROOT_DIR / "logs" / "daily_watchlist_archive"
DEFAULT_RUN_STATUS = ROOT_DIR / "logs" / "daily_watchlist_run_status.json"
DEFAULT_FLOW_JSON = ROOT_DIR / "logs" / "daily_watchlist_flow.json"
DEFAULT_ACCEPTANCE_JSON = ROOT_DIR / "logs" / "daily_watchlist_acceptance.json"
DEFAULT_PIPELINE_JSON = ROOT_DIR / "logs" / "daily_watchlist_pipeline.json"
DEFAULT_FEEDBACK_JSON = ROOT_DIR / "logs" / "daily_watchlist_feedback_effects.json"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "logs" / "daily_watchlist_production_baseline.json"
DEFAULT_HISTORY_JSON = ROOT_DIR / "logs" / "daily_watchlist_production_baseline_history.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily production baseline for watchlist workflow.")
    parser.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR), help="Archive directory for daily artifacts.")
    parser.add_argument("--run-status", default=str(DEFAULT_RUN_STATUS), help="Run status JSON path.")
    parser.add_argument("--flow-json", default=str(DEFAULT_FLOW_JSON), help="Flow JSON path.")
    parser.add_argument("--acceptance-json", default=str(DEFAULT_ACCEPTANCE_JSON), help="Acceptance JSON path.")
    parser.add_argument("--pipeline-json", default=str(DEFAULT_PIPELINE_JSON), help="Pipeline JSON path.")
    parser.add_argument("--feedback-json", default=str(DEFAULT_FEEDBACK_JSON), help="Feedback effects JSON path.")
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON), help="Baseline JSON output path.")
    parser.add_argument("--history-json", default=str(DEFAULT_HISTORY_JSON), help="Baseline history JSON path.")
    parser.add_argument("--show-json", action="store_true", help="Print JSON payload.")
    return parser


def _load_json_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _exists_and_nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _load_history_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _build_recent_run_record(
    *,
    status: str,
    failed_stage: str,
    failure_class: str,
    checks: dict[str, bool],
) -> dict[str, Any]:
    missing_required_checks = [
        key
        for key in ("run_status", "pipeline_json", "latest_json", "acceptance_json", "production_gate", "daily_execution_brief", "feedback_effect_brief")
        if not checks.get(key, False)
    ]
    missing_optional_checks = [
        key
        for key in ("latest_md", "review_brief", "schedule_hint", "history_provider_visible")
        if not checks.get(key, False)
    ]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "failed_stage": failed_stage,
        "failure_class": failure_class,
        "missing_required_checks": missing_required_checks,
        "missing_optional_checks": missing_optional_checks,
        "history_provider_visible": bool(checks.get("history_provider_visible", False)),
    }


def _build_baseline_observation(
    *,
    history_entries: list[dict[str, Any]],
    current_record: dict[str, Any],
    history_path: Path,
    limit: int = 5,
) -> dict[str, Any]:
    recent_runs = (history_entries + [current_record])[-limit:]
    failure_counts = Counter()
    missing_counts = Counter()
    provider_visible_count = 0

    for item in recent_runs:
        failure_class = str(item.get("failure_class", "") or "unknown")
        failure_counts[failure_class] += 1
        for key in item.get("missing_required_checks", []) or []:
            missing_counts[str(key)] += 1
        for key in item.get("missing_optional_checks", []) or []:
            missing_counts[str(key)] += 1
        if bool(item.get("history_provider_visible", False)):
            provider_visible_count += 1

    total_runs = len(recent_runs)
    provider_visibility_rate = round(provider_visible_count / total_runs, 4) if total_runs else 0.0
    top_missing_checks = [key for key, _ in missing_counts.most_common(5)]
    failure_class_counts = dict(failure_counts.most_common())
    if failure_class_counts:
        recommended_fix_order = list(failure_class_counts.keys())
    else:
        recommended_fix_order = ["maintain_current_state"]

    if total_runs == 0:
        summary_text = "暂无历史基线记录，先从第一次运行开始观察。"
    else:
        top_failure_class = next(iter(failure_class_counts), "none")
        summary_text = (
            f"最近 {total_runs} 次基线中，最常见失败类是 {top_failure_class}，"
            f"provider 可见性为 {provider_visibility_rate:.0%}。"
        )

    return {
        "summary_text": summary_text,
        "recent_runs": recent_runs,
        "failure_class_counts": failure_class_counts,
        "top_missing_checks": top_missing_checks,
        "provider_visibility_rate": provider_visibility_rate,
        "recommended_fix_order": recommended_fix_order,
        "history_path": str(history_path),
    }


def _build_repair_priority(
    *,
    baseline_observation: dict[str, Any],
    status: str,
    failed_stage: str,
    failure_class: str,
) -> dict[str, Any]:
    failure_class_counts = baseline_observation.get("failure_class_counts", {})
    top_missing_checks = baseline_observation.get("top_missing_checks", [])
    provider_visibility_rate = float(baseline_observation.get("provider_visibility_rate", 0.0) or 0.0)
    recommended_fix_order = list(baseline_observation.get("recommended_fix_order", []) or [])

    items: list[dict[str, Any]] = []

    def add_item(
        *,
        target: str,
        matched_failure_class: str,
        priority: int,
        reason: str,
        command_hint: str,
        verify_hint: str,
    ) -> None:
        items.append(
            {
                "target": target,
                "failure_class": matched_failure_class,
                "priority": priority,
                "reason": reason,
                "command_hint": command_hint,
                "verify_hint": verify_hint,
            }
        )

    if status == "ready":
        add_item(
            target="maintain_current_state",
            matched_failure_class="none",
            priority=1,
            reason="当前链路已可稳定参考，优先保持现状并继续观察。",
            command_hint="继续按日常节奏运行基线入口。",
            verify_hint="下次运行确认仍然是 ready，且 baseline_observation 没有新增高频缺口。",
        )
    else:
        priority_map = {
            "gate_missing": 1,
            "execution_missing": 1,
            "provider_visibility_missing": 1,
            "acceptance_missing": 2,
            "execution_brief_missing": 2,
            "feedback_brief_missing": 2,
            "archive_missing": 3,
            "precheck_missing": 3,
            "partial_artifacts": 4,
            "degraded_but_runnable": 5,
        }
        target_map = {
            "gate_missing": "production_gate",
            "execution_missing": "pipeline_outputs",
            "provider_visibility_missing": "history_selected_provider",
            "acceptance_missing": "acceptance_json",
            "execution_brief_missing": "daily_execution_brief",
            "feedback_brief_missing": "feedback_effect_brief",
            "archive_missing": "latest_json",
            "precheck_missing": "run_status",
            "partial_artifacts": "optional_artifacts",
            "degraded_but_runnable": "review_and_observe",
        }
        reason_map = {
            "gate_missing": "门禁缺失会直接阻断日常参考，应优先修复。",
            "execution_missing": "执行产物缺失说明主链路没有完整产出，应先修复执行层。",
            "provider_visibility_missing": "provider 透传缺失会影响数据可追踪性，应优先修复。",
            "acceptance_missing": "验收产物缺失会影响闭环判断，但通常次于门禁和执行层。",
            "execution_brief_missing": "执行简报缺失会削弱第一屏判断，但不一定阻断主链路。",
            "feedback_brief_missing": "反馈效果缺失会影响闭环评估，通常次于执行层。",
            "archive_missing": "留档缺失会影响回看，不一定阻断本次执行。",
            "precheck_missing": "预检缺失会影响运行前判断，但优先级通常低于门禁和执行层。",
            "partial_artifacts": "当前主要是非阻断产物缺失，先补齐常用摘要。",
            "degraded_but_runnable": "链路可跑但仍存在降级，先观察高频缺口。",
        }
        command_map = {
            "gate_missing": "先检查 daily_watchlist_flow.py 输出是否包含 production_gate。",
            "execution_missing": "先检查 daily_watchlist_daily_run.py 和 latest.json 是否已写入执行结果。",
            "provider_visibility_missing": "先检查健康摘要和 latest.json 是否透传 history_selected_provider。",
            "acceptance_missing": "先重新生成 acceptance JSON。",
            "execution_brief_missing": "先补齐 daily_execution_brief 的生成与透传。",
            "feedback_brief_missing": "先补齐 feedback_effect_brief 的生成与透传。",
            "archive_missing": "先检查 archive/latest.json 是否成功落盘。",
            "precheck_missing": "先检查 run_status 是否成功生成。",
            "partial_artifacts": "先补齐缺失的非阻断摘要，再决定是否继续参考。",
            "degraded_but_runnable": "先复核高频缺口，不要把降级结果当成强信号。",
        }
        verify_map = {
            "gate_missing": "重新运行基线入口，确认 production_gate 变为存在。",
            "execution_missing": "重新运行日常流程，确认 latest.json 中有执行产物。",
            "provider_visibility_missing": "重新运行健康预检，确认 history_selected_provider 可见。",
            "acceptance_missing": "重新运行验收，确认 acceptance JSON 存在。",
            "execution_brief_missing": "重新运行日常运行，确认 daily_execution_brief 存在。",
            "feedback_brief_missing": "重新运行反馈效果链路，确认 feedback_effect_brief 存在。",
            "archive_missing": "重新运行归档后，确认 latest.json 已写入。",
            "precheck_missing": "重新运行预检，确认 run_status 存在。",
            "partial_artifacts": "确认补齐后的摘要字段已进入 baseline_observation。",
            "degraded_but_runnable": "确认高频缺口数下降，且最近 N 次没有持续同类失败。",
        }

        ordered_classes = list(dict.fromkeys(
            [failure_class] + list(recommended_fix_order)
        ))
        seen_targets = set()
        for idx, cls in enumerate(ordered_classes, start=1):
            if cls in seen_targets or cls == "none":
                continue
            seen_targets.add(cls)
            base_priority = priority_map.get(cls, 9)
            if cls == failure_class:
                base_priority = 0
            elif cls in failure_class_counts and failure_class_counts.get(cls, 0) > failure_class_counts.get(failure_class, 0):
                base_priority = max(1, base_priority - 1)
            if cls == "provider_visibility_missing" and provider_visibility_rate < 0.5:
                base_priority = 1
            add_item(
                target=target_map.get(cls, cls),
                matched_failure_class=cls,
                priority=base_priority,
                reason=reason_map.get(cls, "根据最近观测结果调整优先级。"),
                command_hint=command_map.get(cls, "先按当前基线入口检查对应产物。"),
                verify_hint=verify_map.get(cls, "重新运行基线入口确认该项已恢复。"),
            )

        if not items:
            add_item(
                target="review_and_observe",
                matched_failure_class=failure_class or "unknown",
                priority=1,
                reason="当前没有可排序的明确修复项，先保持观察。",
                command_hint="先检查最近一次运行结果和缺失项摘要。",
                verify_hint="确认下一次运行没有新增阻断。",
            )

    items = sorted(
        items,
        key=lambda item: (
            int(item.get("priority", 9)),
            0 if item.get("failure_class") == failure_class else 1,
            str(item.get("target", "")),
        ),
    )
    top_target = str(items[0].get("target", "unknown")) if items else "unknown"
    summary_text = f"当前优先修复 {top_target}，再按优先级顺序处理其余缺口。"
    return {
        "summary_text": summary_text,
        "items": items,
        "top_target": top_target,
        "history_path": str(baseline_observation.get("history_path", "")),
    }


def _derive_status(checks: dict[str, bool]) -> str:
    required_failed = [
        "run_status",
        "pipeline_json",
        "latest_json",
        "production_gate",
        "daily_execution_brief",
        "acceptance_json",
    ]
    if any(not checks.get(key, False) for key in required_failed):
        return "failed"
    if not all(checks.get(key, False) for key in checks):
        return "caution"
    return "ready"


def _derive_failure_stage(checks: dict[str, bool]) -> str:
    if not checks.get("run_status", False):
        return "run_status"
    if not checks.get("pipeline_json", False):
        return "pipeline"
    if not checks.get("latest_json", False):
        return "archive"
    if not checks.get("acceptance_json", False):
        return "acceptance"
    if not checks.get("production_gate", False):
        return "production_gate"
    if not checks.get("daily_execution_brief", False):
        return "daily_execution_brief"
    if not checks.get("feedback_effect_brief", False):
        return "feedback_effect_brief"
    if not checks.get("history_provider_visible", False):
        return "history_provider_visible"
    return "none"


def _derive_failure_class(checks: dict[str, bool], status: str, failed_stage: str) -> str:
    if status == "ready":
        return "none"
    if failed_stage == "run_status":
        return "precheck_missing"
    if failed_stage == "pipeline":
        return "execution_missing"
    if failed_stage == "archive":
        return "archive_missing"
    if failed_stage == "acceptance":
        return "acceptance_missing"
    if failed_stage == "production_gate":
        return "gate_missing"
    if failed_stage == "daily_execution_brief":
        return "execution_brief_missing"
    if failed_stage == "feedback_effect_brief":
        return "feedback_brief_missing"
    if failed_stage == "history_provider_visible":
        return "provider_visibility_missing"
    if status == "caution":
        missing_optional = [
            key
            for key in ("latest_md", "review_brief", "schedule_hint")
            if not checks.get(key, False)
        ]
        if missing_optional:
            return "partial_artifacts"
        return "degraded_but_runnable"
    return "unknown_failure"


def _build_repair_hint(failure_class: str, failed_stage: str) -> str:
    repair_map = {
        "precheck_missing": "先补齐预检状态，再重新跑基线。",
        "execution_missing": "先补齐执行产物，再重新跑基线。",
        "archive_missing": "先检查归档目录是否写入完成，再重新跑基线。",
        "acceptance_missing": "先补齐验收 JSON，再重新跑基线。",
        "gate_missing": "先修复 production_gate，再重新跑基线。",
        "execution_brief_missing": "先补齐 daily_execution_brief，再重新跑基线。",
        "feedback_brief_missing": "先补齐 feedback_effect_brief，再重新跑基线。",
        "provider_visibility_missing": "先确认历史 provider 是否已写入健康摘要，再重新跑基线。",
        "partial_artifacts": "先补齐缺失的非阻断产物，再决定是否继续参考。",
        "degraded_but_runnable": "链路可跑但存在降级，先复核后再动作。",
    }
    if failure_class in repair_map:
        return repair_map[failure_class]
    if failed_stage == "none":
        return "当前无需修复，继续按日常节奏运行。"
    return "先定位失败阶段，再逐层修复。"


def _build_evidence_summary(checks: dict[str, bool], status: str, failed_stage: str, failure_class: str) -> dict[str, object]:
    priority_read_order = [
        "production_gate",
        "daily_execution_brief",
        "feedback_effect_brief",
        "schedule_hint",
        "history_selected_provider",
        "review_brief",
        "latest_json",
        "acceptance_json",
    ]
    missing_required_checks = [
        key
        for key in ("run_status", "pipeline_json", "latest_json", "acceptance_json", "production_gate", "daily_execution_brief", "feedback_effect_brief")
        if not checks.get(key, False)
    ]
    missing_optional_checks = [
        key
        for key in ("latest_md", "review_brief", "schedule_hint", "history_provider_visible")
        if not checks.get(key, False)
    ]
    key_evidence_items = []
    for key in priority_read_order:
        if checks.get(key, False):
            key_evidence_items.append(key)
    if failed_stage != "none":
        key_evidence_items.insert(0, f"failed_stage:{failed_stage}")
    if failure_class != "none":
        key_evidence_items.insert(1 if key_evidence_items else 0, f"failure_class:{failure_class}")
    summary_text = f"status={status}; failed_stage={failed_stage}; failure_class={failure_class}; required_missing={len(missing_required_checks)}; optional_missing={len(missing_optional_checks)}"
    return {
        "summary_text": summary_text,
        "priority_read_order": priority_read_order,
        "missing_required_checks": missing_required_checks,
        "missing_optional_checks": missing_optional_checks,
        "key_evidence_items": key_evidence_items,
    }


def main() -> int:
    args = build_parser().parse_args()
    archive_dir = Path(args.archive_dir)
    run_status_path = Path(args.run_status)
    flow_path = Path(args.flow_json)
    acceptance_path = Path(args.acceptance_json)
    pipeline_path = Path(args.pipeline_json)
    feedback_path = Path(args.feedback_json)
    output_path = Path(args.output_json)
    env_guard = build_env_guard()

    run_status_payload = _load_json_payload(run_status_path)
    flow_payload = _load_json_payload(flow_path)
    acceptance_payload = _load_json_payload(acceptance_path)
    pipeline_payload = _load_json_payload(pipeline_path)
    feedback_payload = _load_json_payload(feedback_path)
    history_path = Path(args.history_json)
    history_entries = _load_history_entries(history_path)

    latest_json = archive_dir / "latest.json"
    latest_md = archive_dir / "latest.md"
    latest_payload = _load_json_payload(latest_json)
    if not latest_payload and isinstance(pipeline_payload, dict):
        latest_payload = pipeline_payload

    production_gate = latest_payload.get("production_gate", {}) if isinstance(latest_payload, dict) else {}
    daily_execution_brief = latest_payload.get("daily_execution_brief", {}) if isinstance(latest_payload, dict) else {}
    review_brief = latest_payload.get("review_brief", {}) if isinstance(latest_payload, dict) else {}
    schedule_hint = latest_payload.get("schedule_hint", {}) if isinstance(latest_payload, dict) else {}
    regression_gate = latest_payload.get("regression_gate", {}) if isinstance(latest_payload, dict) else {}
    feedback_effect_brief = feedback_payload.get("feedback_effect_brief", {}) if isinstance(feedback_payload, dict) else {}
    if not isinstance(feedback_effect_brief, dict) or not feedback_effect_brief:
        feedback_effect_brief = build_feedback_effect_brief(feedback_effects=feedback_payload if isinstance(feedback_payload, dict) else {})
    if not isinstance(regression_gate, dict) or not regression_gate:
        regression_gate = build_regression_gate(
            daily_run_status=str(run_status_payload.get("status", "unknown")) if isinstance(run_status_payload, dict) else "unknown",
            acceptance=acceptance_payload if isinstance(acceptance_payload, dict) else {},
            baseline={},
            regression_gate=_ensure_dict(latest_payload.get("regression_gate", {}) if isinstance(latest_payload, dict) else {}),
        )

    checks = {
        "run_status": _exists_and_nonempty(run_status_path),
        "pipeline_json": _exists_and_nonempty(pipeline_path),
        "latest_json": _exists_and_nonempty(latest_json),
        "latest_md": _exists_and_nonempty(latest_md),
        "acceptance_json": _exists_and_nonempty(acceptance_path),
        "production_gate": bool(isinstance(production_gate, dict) and production_gate.get("status", "")),
        "daily_execution_brief": bool(isinstance(daily_execution_brief, dict) and daily_execution_brief.get("summary_text", "")),
        "review_brief": bool(isinstance(review_brief, dict) and review_brief.get("summary_text", "")),
        "schedule_hint": bool(isinstance(schedule_hint, dict) and schedule_hint.get("summary_text", "")),
        "feedback_effect_brief": bool(isinstance(feedback_effect_brief, dict) and feedback_effect_brief.get("summary_text", "")),
        "regression_gate": bool(isinstance(regression_gate, dict) and regression_gate.get("summary_text", "")),
        "history_provider_visible": any(
            isinstance(item, dict) and bool(item.get("history_selected_provider"))
            for item in (latest_payload.get("health", {}).get("items", []) if isinstance(latest_payload, dict) else [])
        ),
        "env_guard": bool(env_guard.get("summary_text", "")),
    }
    status = _derive_status(checks)
    failed_stage = _derive_failure_stage(checks)
    failure_class = _derive_failure_class(checks, status, failed_stage)
    repair_hint = _build_repair_hint(failure_class, failed_stage)
    evidence_summary = _build_evidence_summary(checks, status, failed_stage, failure_class)
    current_record = _build_recent_run_record(
        status=status,
        failed_stage=failed_stage,
        failure_class=failure_class,
        checks=checks,
    )
    baseline_observation = _build_baseline_observation(
        history_entries=history_entries,
        current_record=current_record,
        history_path=history_path,
    )
    repair_priority = _build_repair_priority(
        baseline_observation=baseline_observation,
        status=status,
        failed_stage=failed_stage,
        failure_class=failure_class,
    )

    if status == "ready":
        summary_text = "日常投产基线通过，主链路可完整参考。"
        next_action = "继续按日常节奏运行，并保持现有门禁顺序。"
    elif status == "caution":
        summary_text = "日常投产基线可用，但存在部分非阻断缺口。"
        next_action = "先复核缺失入口，再决定是否继续参考。"
    else:
        summary_text = f"日常投产基线失败（{failure_class}），当前不建议直接参考。"
        next_action = "先修复失败阶段，再重新跑基线。"

    evidence = {
        "run_status": run_status_payload,
        "flow": flow_payload,
        "acceptance": acceptance_payload,
        "pipeline": pipeline_payload,
        "latest_payload": latest_payload,
        "production_gate": production_gate,
        "daily_execution_brief": daily_execution_brief,
        "review_brief": review_brief,
        "schedule_hint": schedule_hint,
        "feedback_effect_brief": feedback_effect_brief,
        "regression_gate": regression_gate,
        "env_guard": env_guard,
        "baseline_observation_history": history_entries,
    }

    payload = {
        "status": status,
        "summary_text": summary_text,
        "failed_stage": failed_stage,
        "failure_class": failure_class,
        "repair_hint": repair_hint,
        "evidence_summary": evidence_summary,
        "next_action": next_action,
        "checks": checks,
        "evidence": evidence,
        "baseline_observation": baseline_observation,
        "repair_priority": repair_priority,
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    history_entries = (history_entries + [current_record])[-30:]
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("w", encoding="utf-8") as f:
        json.dump(history_entries, f, ensure_ascii=False, indent=2, default=str)

    print("== 自选股日常投产基线 ==")
    print(f"状态: {status}")
    print(f"结论: {summary_text}")
    print(f"失败阶段: {failed_stage}")
    print(f"失败分类: {failure_class}")
    print(f"修复提示: {repair_hint}")
    print(f"摘要: {evidence_summary['summary_text']}")
    print(f"下一步: {next_action}")
    print(f"production_gate: {'存在' if checks['production_gate'] else '缺失'}")
    print(f"daily_execution_brief: {'存在' if checks['daily_execution_brief'] else '缺失'}")
    print(f"feedback_effect_brief: {'存在' if checks['feedback_effect_brief'] else '缺失'}")
    print(f"regression_gate: {'存在' if checks['regression_gate'] else '缺失'}")
    print(f"history_provider_visible: {'存在' if checks['history_provider_visible'] else '缺失'}")
    print(f"env_guard: {'存在' if checks['env_guard'] else '缺失'}")
    print(f"baseline_observation: {baseline_observation['summary_text']}")
    print(f"repair_priority: {repair_priority['summary_text']}")
    print(f"验收JSON: {'存在' if checks['acceptance_json'] else '缺失'}")
    print(f"输出JSON: {output_path}")

    if args.show_json:
        print("\n== baseline.json ==")
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))

    return 0 if status in {"ready", "caution"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
