#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据治理层

为行情、财务和市场数据提供统一的缓存、质量检查与来源追踪。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional


@dataclass
class DataSnapshot:
    """一次数据获取的统一快照。"""

    name: str
    source: str
    payload: Any
    data_source: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_degraded: bool = False
    cache_hit: bool = False
    reason: str = ""
    quality: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "data_source": self.data_source or self.source,
            "fetched_at": self.fetched_at,
            "is_degraded": self.is_degraded,
            "cache_hit": self.cache_hit,
            "reason": self.reason,
            "quality": self.quality or {},
            "meta": self.meta,
            "payload": self.payload,
        }


class CacheManager:
    """轻量内存缓存管理器。"""

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._expires_at: Dict[str, float] = {}

    def get(self, key: str) -> Any:
        expires_at = self._expires_at.get(key)
        if expires_at is not None and time.time() > expires_at:
            self._cache.pop(key, None)
            self._expires_at.pop(key, None)
            return None
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self._cache[key] = value
        self._expires_at[key] = time.time() + ttl

    def clear(self) -> None:
        self._cache.clear()
        self._expires_at.clear()


class DataQualityChecker:
    """数据质量检查器。"""

    def check_dataframe(self, df) -> dict:
        if df is None:
            return {"ok": False, "reason": "dataframe is None", "rows": 0, "columns": []}

        rows = int(getattr(df, "shape", [0])[0] or 0)
        columns = list(getattr(df, "columns", []))

        if rows == 0:
            return {"ok": False, "reason": "dataframe is empty", "rows": 0, "columns": columns}

        return {"ok": True, "reason": "ok", "rows": rows, "columns": columns}

    def check_ohlcv_dataframe(self, df) -> dict:
        """检查行情 DataFrame 是否满足基础 OHLCV 要求。"""
        result = self.check_dataframe(df)
        if not result.get("ok"):
            return result

        required = ["open", "high", "low", "close", "volume"]
        columns = list(getattr(df, "columns", []))
        missing = [col for col in required if col not in columns]
        if missing:
            return {
                "ok": False,
                "reason": f"missing columns: {missing}",
                "rows": int(getattr(df, "shape", [0])[0] or 0),
                "columns": columns,
                "missing": missing,
            }

        return {
            "ok": True,
            "reason": "ok",
            "rows": int(getattr(df, "shape", [0])[0] or 0),
            "columns": columns,
            "missing": [],
        }

    def check_dict(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return {"ok": False, "reason": "not a dict", "keys": []}
        if not data:
            return {"ok": False, "reason": "dict is empty", "keys": []}
        return {"ok": True, "reason": "ok", "keys": list(data.keys())}


def build_snapshot(
    name: str,
    payload: Any,
    source: str,
    *,
    degraded: bool = False,
    cache_hit: bool = False,
    reason: str = "",
) -> DataSnapshot:
    """创建统一数据快照。"""
    return DataSnapshot(
        name=name,
        source=source,
        payload=payload,
        is_degraded=degraded,
        cache_hit=cache_hit,
        reason=reason,
    )
