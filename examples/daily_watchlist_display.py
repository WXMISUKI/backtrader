#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自选股日常显示辅助工具。
"""

from __future__ import annotations

from typing import Any, Iterable


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def print_kv_pairs(items: Iterable[tuple[str, Any]]) -> None:
    for key, value in items:
        print(f"{key}: {value}")


def print_bullets(items: Iterable[str]) -> None:
    for item in items:
        print(f"- {item}")


def print_block(title: str, lines: list[str]) -> None:
    print_section(title)
    for line in lines:
        print(line)
