# Phase 13 最小 CLI 启动脚本归档

---

## 1. 归档结论

Phase 13 已完成最小闭环：项目可以通过单一 CLI 命令启动最小 HTTP API。

---

## 2. 已完成内容

- 新增 Phase 13 规格草案
- 新增包内 CLI 启动入口 `core/cli.py`
- 新增脚本入口 `tools/agent-api.py`
- 注册安装后命令 `stock-agent-api`
- 继续复用 Phase 12 的最小 HTTP API 实现

---

## 3. 当前收口边界

本阶段只补启动方式，不扩展 Web 框架、不增加复杂命令参数，也不做额外运维系统。

---

## 4. 轻量验证要求

建议验证：

1. CLI 可以正常解析 `--host` 和 `--port`
2. 可以启动 `run_agent_api_server()`
3. 安装后命令可用

---

## 5. 后续建议

下一阶段最值得继续推进的是：

1. 为统一输出补一个最小 API 使用示例
2. 在真实环境验证 `/decision` 和 `/feedback`
3. 再考虑最简配置文件或部署脚本
