#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能体配置加载

读取项目根目录 `.env`，并提供 Ark / OpenAI-compatible 接入参数。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Optional

try:
    dotenv_values = None
except ImportError:  # pragma: no cover
    dotenv_values = None


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AgentSettings:
    """智能体运行配置。"""

    api_key: str
    base_url: str
    responses_model: str
    chat_model: str
    temperature: float
    max_tokens: int
    timeout: int
    enable_agent: bool
    enable_stream: bool
    default_risk_profile: str
    data_cache_ttl: int
    eastmoney_cookie: str

    @property
    def has_api_key(self) -> bool:
        """判断是否已配置 API Key。"""
        return bool(self.api_key.strip())


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(env_path: Optional[str] = None) -> None:
    path = Path(env_path) if env_path else _find_env_file()
    if path.exists():
        # 直接解析文件并写入当前进程环境，避免依赖第三方 dotenv 包
        for key, value in _parse_env_file(path).items():
            os.environ[key] = value


def _parse_env_file(path: Path) -> dict:
    """解析 .env 文件。"""
    values: dict = {}
    content = path.read_text(encoding="utf-8")

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        values[key] = value

    return values


def _find_env_file() -> Path:
    """
    查找 .env 文件。

    优先级：
    1. 当前工作目录及其父目录
    2. 项目根目录
    """
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        env_file = candidate / ".env"
        if env_file.exists():
            return env_file
    return _PROJECT_ROOT / ".env"


def load_agent_settings(env_path: Optional[str] = None) -> AgentSettings:
    """
    加载智能体配置。

    默认读取项目根目录 `.env`，也可以通过 env_path 指定其他路径。
    """
    _load_dotenv(env_path)

    return AgentSettings(
        api_key=os.getenv("ARK_API_KEY", "").strip(),
        base_url=os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").strip(),
        responses_model=os.getenv("ARK_RESPONSES_MODEL", "doubao-seed-2-0-lite-260428").strip(),
        chat_model=os.getenv("ARK_CHAT_MODEL", "doubao-seed-2-0-lite-260215").strip(),
        temperature=float(os.getenv("ARK_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("ARK_MAX_TOKENS", "4096")),
        timeout=int(os.getenv("ARK_TIMEOUT", "60")),
        enable_agent=_env_bool("ENABLE_AGENT", True),
        enable_stream=_env_bool("ENABLE_STREAM", True),
        default_risk_profile=os.getenv("DEFAULT_RISK_PROFILE", "moderate").strip(),
        data_cache_ttl=int(os.getenv("DATA_CACHE_TTL", "3600")),
        eastmoney_cookie=os.getenv("EASTMONEY_COOKIE", "").strip(),
    )
