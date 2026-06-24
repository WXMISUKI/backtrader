#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日常入口共享的环境门禁工具。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_EXPECTED_ENV = "quant"


def detect_active_conda_env() -> str:
    env_name = str(os.environ.get("CONDA_DEFAULT_ENV", "") or "").strip()
    if env_name:
        return env_name
    prefix = str(os.environ.get("CONDA_PREFIX", "") or "").strip()
    if prefix:
        return Path(prefix).name
    return "unknown"


def build_env_guard(expected_env: str = DEFAULT_EXPECTED_ENV) -> dict[str, Any]:
    active_env = detect_active_conda_env()
    expected_env = str(expected_env or DEFAULT_EXPECTED_ENV).strip() or DEFAULT_EXPECTED_ENV
    python_version = sys.version.split()[0]
    status = "ok" if active_env == expected_env else "warn"
    summary_text = (
        f"当前环境 {active_env}，建议环境 {expected_env}。"
        if active_env != expected_env
        else f"当前环境 {active_env}，符合开发规范。"
    )
    return {
        "status": status,
        "summary_text": summary_text,
        "active_env": active_env,
        "expected_env": expected_env,
        "python_version": python_version,
        "is_expected": active_env == expected_env,
        "rules": [
            f"Python 相关验证优先切换到 {expected_env}。",
            "不要默认使用 base 作为主验证环境。",
            "如果环境不一致，先切换环境，再做回归判断。",
        ],
    }
