from __future__ import annotations

from examples.watchlist_shared import build_feedback_effect_brief


def test_feedback_effect_brief_ready() -> None:
    payload = build_feedback_effect_brief(
        feedback_effects={
            "overall": {
                "usable_feedback": 6,
                "evaluated_rows": 6,
                "hit_rate": 0.6667,
                "avg_return": 0.0123,
            },
            "windows": {
                "1": {"evaluable": 2, "positive": 2, "negative": 0, "flat": 0, "avg_return": 0.02, "hit_count": 2, "hit_rate": 1.0, "sample_count": 2},
                "3": {"evaluable": 2, "positive": 1, "negative": 1, "flat": 0, "avg_return": 0.01, "hit_count": 1, "hit_rate": 0.5, "sample_count": 2},
                "5": {"evaluable": 2, "positive": 1, "negative": 0, "flat": 1, "avg_return": 0.005, "hit_count": 1, "hit_rate": 0.5, "sample_count": 2},
            },
            "samples": [{"stock_code": "000001"}],
        }
    )

    assert payload["status"] == "ready"
    assert payload["summary_text"]
    assert payload["read_order"] == ["production_gate", "action_list", "review_brief", "daily_execution_brief"]
    assert payload["window_summary"]["1"]["evaluable"] == 2


def test_feedback_effect_brief_blocked() -> None:
    payload = build_feedback_effect_brief(feedback_effects={})

    assert payload["status"] == "blocked"
    assert "usable_feedback_zero" in payload["excluded_reasons"]
    assert "evaluated_rows_zero" in payload["excluded_reasons"]


def test_feedback_effect_brief_skewed_coverage_demotes_ready() -> None:
    payload = build_feedback_effect_brief(
        feedback_effects={
            "overall": {
                "usable_feedback": 6,
                "evaluated_rows": 6,
                "hit_rate": 0.75,
                "avg_return": 0.015,
            },
            "windows": {
                "1": {"evaluable": 6, "positive": 4, "negative": 1, "flat": 1, "avg_return": 0.03, "hit_count": 4, "hit_rate": 0.6667, "sample_count": 6},
                "3": {"evaluable": 1, "positive": 1, "negative": 0, "flat": 0, "avg_return": 0.01, "hit_count": 1, "hit_rate": 1.0, "sample_count": 1},
                "5": {"evaluable": 1, "positive": 1, "negative": 0, "flat": 0, "avg_return": 0.005, "hit_count": 1, "hit_rate": 1.0, "sample_count": 1},
            },
            "samples": [{"stock_code": "000001"}],
        }
    )

    assert payload["status"] == "caution"
    assert "coverage_skewed" in payload["stability_flags"]
    assert "偏斜" in payload["coverage_summary"]
