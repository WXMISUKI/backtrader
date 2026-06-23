#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富 cookie 解析与标准化工具。
"""

from __future__ import annotations

from pathlib import Path


def parse_cookie_blob(cookie_blob: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    text = (cookie_blob or "").strip()
    if not text:
        return cookies

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for chunk in line.split(";"):
            part = chunk.strip()
            if not part:
                continue
            if "\t" in part:
                columns = [col.strip() for col in part.split("\t")]
                if len(columns) >= 2 and columns[0] and columns[1]:
                    cookies[columns[0]] = columns[1]
                    continue
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    cookies[key] = value

    return cookies


def format_cookie_string(cookies: dict[str, str]) -> str:
    ordered = []
    for key, value in cookies.items():
        if key and value:
            ordered.append(f"{key}={value}")
    return "; ".join(ordered)


def load_cookie_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"cookie file not found: {p}")
    return p.read_text(encoding="utf-8").strip()
