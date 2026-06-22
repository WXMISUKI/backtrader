#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富会话路由回归测试。

目标：
- 默认会继承环境代理
- 可通过显式参数关闭环境继承
- 可通过环境变量控制默认行为
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eastmoney_config as ec


def test_get_eastmoney_session_defaults_to_trust_env(monkeypatch):
    monkeypatch.delenv("EASTMONEY_TRUST_ENV", raising=False)

    session = ec.get_eastmoney_session()

    assert session.trust_env is True


def test_get_eastmoney_session_can_disable_trust_env_explicitly():
    session = ec.get_eastmoney_session(trust_env=False)

    assert session.trust_env is False


def test_get_eastmoney_session_respects_env_override(monkeypatch):
    monkeypatch.setenv("EASTMONEY_TRUST_ENV", "0")

    session = ec.get_eastmoney_session()
    meta = ec.get_eastmoney_session_meta()

    assert session.trust_env is False
    assert meta["session_trust_env"] is False
    assert meta["session_mode"] == "ignore_env"

