#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小 HTTP API 封装。

仅提供统一决策、反馈提交和健康检查三个接口，避免引入额外 Web 框架依赖。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from datetime import datetime, timezone

from .orchestrator import StockOrchestrator


class AgentAPIHandler(BaseHTTPRequestHandler):
    """最小 HTTP API 请求处理器。"""

    server_version = "StockQuantAdvisorAPI/0.1"

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:  # noqa: N802 - HTTP handler signature
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._write_json(
                200,
                {
                    "ok": True,
                    "service": "stock-quant-advisor-api",
                    "status": "ok",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

        if parsed.path == "/decision/stats":
            query = dict()
            if parsed.query:
                from urllib.parse import parse_qs

                query = {k: v[-1] for k, v in parse_qs(parsed.query).items() if v}
            limit = int(query.get("limit", "20") or 20)
            orchestrator = StockOrchestrator()
            result = orchestrator.get_decision_session_stats(limit=limit)
            self._write_json(200, result)
            return

        self._write_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - HTTP handler signature
        parsed = urlparse(self.path)
        payload = self._read_json()
        orchestrator = StockOrchestrator()

        if parsed.path == "/decision":
            user_input = str(payload.get("user_input", "") or "").strip()
            if not user_input:
                self._write_json(400, {"ok": False, "error": "user_input_required"})
                return
            result = orchestrator.answer_decision_request(
                user_input,
                risk_profile=str(payload.get("risk_profile", "moderate") or "moderate"),
            )
            self._write_json(200, result)
            return

        if parsed.path == "/feedback":
            session_id = str(payload.get("session_id", "") or "").strip()
            workflow_id = str(payload.get("workflow_id", "") or "").strip()
            if not session_id:
                self._write_json(400, {"ok": False, "error": "session_id_required"})
                return
            result = orchestrator.submit_decision_feedback(
                session_id=session_id,
                workflow_id=workflow_id,
                accepted=payload.get("accepted"),
                rating=payload.get("rating"),
                reason=str(payload.get("reason", "") or ""),
                correction=str(payload.get("correction", "") or ""),
                comment=str(payload.get("comment", "") or ""),
            )
            self._write_json(200, result)
            return

        self._write_json(404, {"ok": False, "error": "not_found"})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - matching base class
        """关闭默认日志，避免生产输出噪声。"""
        return


def create_agent_api_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """创建最小 HTTP 服务。"""
    return ThreadingHTTPServer((host, port), AgentAPIHandler)


def run_agent_api_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """运行最小 HTTP 服务。"""
    server = create_agent_api_server(host=host, port=port)
    print(f"Agent API server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_agent_api_server()
