from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import examples.daily_watchlist_pipeline as pipeline
from examples.watchlist_shared import build_production_gate
from examples.daily_watchlist_pipeline import _build_history_provider_overview
from examples.daily_watchlist_pipeline import _write_daily_artifacts


def test_history_provider_overview_handles_visible_items() -> None:
    overview = _build_history_provider_overview(
        [
            {
                "stock_code": "000001",
                "name": "平安银行",
                "history_selected_provider": "eastmoney_direct",
                "history_provider_summary": "历史 provider eastmoney_direct；尝试 1 次",
            }
        ]
    )

    assert overview["visible_count"] == 1
    assert overview["summary_text"]
    assert overview["selected_providers"] == ["eastmoney_direct"]


def test_write_daily_artifacts_copies_latest_markdown(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    source_json_path = tmp_path / "source" / "pipeline.json"
    payload = {
        "daily_summary": {"status": "需要谨慎"},
        "portfolio_summary": {"count": 2, "market_value": 76520.0, "total_assets": 1000000.0},
        "daily_report": {"report_text": "日报正文"},
        "daily_comparison": {"summary_text": "暂无变化"},
        "weekly_report": {"report_text": ""},
        "stage_report": {"report_text": ""},
        "archive_package": {"report_text": "留档包正文"},
    }

    archive_info = _write_daily_artifacts(
        archive_dir=archive_dir,
        generated_at="2026-06-27T15:23:31",
        payload=payload,
        export_markdown=True,
        write_latest=True,
        source_json_path=source_json_path,
    )

    latest_json = archive_dir / "latest.json"
    latest_md = archive_dir / "latest.md"

    assert latest_json.exists()
    assert latest_md.exists()
    assert source_json_path.exists()
    assert "日报正文" in latest_md.read_text(encoding="utf-8")
    assert "留档包正文" in latest_md.read_text(encoding="utf-8")
    assert archive_info["markdown_path"]


def test_build_history_summary_keeps_confidence_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline,
        "fetch_stock_hist_governed",
        lambda **kwargs: {"data_source": "real", "quality": {"ok": True, "rows": 10}},
    )
    monkeypatch.setattr(
        pipeline,
        "RealDataProvider",
        lambda: SimpleNamespace(
            get_financial_indicators_governed=lambda stock_code: {
                "data_source": "real",
                "quality": {"ok": True},
                "payload": {"report_date": "2026-06-27"},
            }
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "build_data_health_summary",
        lambda **kwargs: {
            "status": "完全可用",
            "health_score": 100,
            "data_confidence": 0.96,
            "confidence_level": "high",
            "confidence_breakdown": {"history": {"score": 0.96}, "fundamental": {"score": 0.96}},
            "history_source": "real",
            "fundamental_source": "real",
            "history_quality": {"ok": True},
            "fundamental_quality": {"ok": True},
            "history_reason": "",
            "fundamental_reason": "",
            "summary": "测试股票 数据健康状态为完全可用，健康分 100 分。",
            "diagnosis": {"primary_cause": "healthy"},
            "flags": {"history_degraded": False, "fundamental_degraded": False},
        },
    )

    summary = pipeline._build_history_summary(
        raw={"start_date": "20260601", "end_date": "20260614"},
        stock_code="000001",
        stock_name="平安银行",
    )

    assert summary["data_confidence"] == 0.96
    assert summary["confidence_level"] == "high"
    assert summary["confidence_breakdown"]["history"]["score"] == 0.96


def test_build_production_gate_ignores_pending_acceptance_when_core_data_is_strong() -> None:
    gate = build_production_gate(
        daily_summary={
            "status": "平稳",
            "diagnosis_counts": {},
            "confidence_counts": {"high": 5, "medium": 0, "low": 0},
            "average_confidence": 1.0,
        },
        diagnosis_evidence={"top_causes": []},
        acceptance={"status": "unknown"},
        health_items=[
            {
                "status": "完全可用",
                "data_confidence": 0.96,
                "diagnosis": {"primary_cause": "healthy", "severity": "ok"},
            }
        ],
        daily_run_status="ok",
    )

    assert gate["status"] == "pass"
    assert "acceptance_pending" in gate["reasons"]
