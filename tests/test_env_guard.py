from __future__ import annotations

from examples import env_guard


def test_build_env_guard_contains_expected_fields() -> None:
    guard = env_guard.build_env_guard(expected_env="quant")

    assert guard["expected_env"] == "quant"
    assert guard["summary_text"]
    assert "active_env" in guard
    assert "python_version" in guard
    assert isinstance(guard["rules"], list)
    assert isinstance(guard["is_expected"], bool)
