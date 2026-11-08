"""Standard Model Context Protocol (MCP) Server for Liara (`src/mcp_server/server.py`).

Exposes the 5 Liara Mega-Tools, Resources (`liara://projects`, `liara://credit-budget`), and Prompts
over JSON-RPC / stdio or in-process calls so external coding agents (`Claude Code`, `Codex`,
`OpenCode`, `DeepSeek Harness / dsh`) can autonomously deploy and heal builds on Liara
without manual user copy-pasting.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from src.mcp_server.mega_tools import LiaraMegaTools


class LiaraMCPServer:
    """MCP-compliant server exposing Liara Mega-Tools, Resources, and Prompts."""

    SERVER_NAME = "liara-mcp-server"
    SERVER_VERSION = "1.0.0"

    def __init__(self, mega_tools: Optional[LiaraMegaTools] = None) -> None:
        self.mega_tools = mega_tools or LiaraMegaTools()

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return compact M+N tool schemas for the 5 domain-driven Mega-Tools."""
        return [
            {
                "name": "liara_app_lifecycle",
                "description": (
                    "Manage Liara PaaS app lifecycle: list_apps, get_app_details, estimate_optimal_plan "
                    "(autonomous), and create_app, restart_app, turn_power, scale_plan (Financial/Prod HITL)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "list_apps",
                                "get_app_details",
                                "estimate_optimal_plan",
                                "create_app",
                                "restart_app",
                                "turn_power",
                                "scale_plan",
                            ],
                        },
                        "project_name": {"type": "string"},
                        "platform": {"type": "string"},
                        "plan_id": {"type": "string"},
                        "port": {"type": "integer"},
                        "hitl_approved": {"type": "boolean"},
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "liara_release_pipeline",
                "description": (
                    "Manage Liara deployment & automated build-fix loop with Coding Agent: "
                    "auto_prepare_and_upload, auto_heal_build_loop, list_releases (autonomous), "
                    "and publish_release, rollback_release (HITL)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "auto_prepare_and_upload",
                                "publish_release",
                                "auto_heal_build_loop",
                                "list_releases",
                                "rollback_release",
                            ],
                        },
                        "project_name": {"type": "string"},
                        "workspace_path": {"type": "string"},
                        "source_id": {"type": "string"},
                        "port": {"type": "integer"},
                        "raw_build_error": {"type": "string"},
                        "hitl_approved": {"type": "boolean"},
                    },
                    "required": ["action", "project_name"],
                },
            },
            {
                "name": "liara_config_and_storage",
                "description": (
                    "Manage Liara environment variables (Secret-Blind Vault), Zero-Downtime, Read-Only, "
                    "Static IP, and persistent Disks."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "scan_env_template",
                                "apply_secret_blind_envs",
                                "toggle_zero_downtime",
                                "toggle_readonly",
                                "toggle_static_ip",
                                "manage_disks",
                                "create_ftp_backup",
                            ],
                        },
                        "project_name": {"type": "string"},
                        "env_key_names": {"type": "array", "items": {"type": "string"}},
                        "enabled": {"type": "boolean"},
                        "hitl_approved": {"type": "boolean"},
                    },
                    "required": ["action", "project_name"],
                },
            },
            {
                "name": "liara_sre_observability",
                "description": (
                    "100% Autonomous SRE telemetry & log forensics with Regex sanitization and "
                    "<untrusted_log_data> prompt-injection defense."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "get_resource_metrics",
                                "get_app_logs",
                                "get_build_logs",
                                "get_system_events",
                                "get_applets_health",
                                "run_full_telemetry_fanout",
                            ],
                        },
                        "project_name": {"type": "string"},
                        "max_log_lines": {"type": "integer"},
                    },
                    "required": ["action", "project_name"],
                },
            },
            {
                "name": "liara_domain_and_network",
                "description": (
                    "Manage Liara custom domains, DNS records, Let's Encrypt SSL check, and "
                    "guided IRNIC (.ir) external registrar wizard."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "list_domains",
                                "attach_domain",
                                "check_domain_dns_ssl",
                                "manage_dns_records",
                                "generate_external_registrar_guide",
                            ],
                        },
                        "domain_name": {"type": "string"},
                        "project_name": {"type": "string"},
                    },
                    "required": ["action"],
                },
            },
        ]

    def list_resources(self) -> List[Dict[str, str]]:
        return [
            {
                "uri": "liara://credit-budget",
                "name": "Liara 2,000,000 Tomans Hackathon Credit Budget",
                "mimeType": "application/json",
            },
            {
                "uri": "liara://projects",
                "name": "Active Liara PaaS Projects",
                "mimeType": "application/json",
            },
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch an MCP tool call to the corresponding Mega-Tool handler."""
        if not hasattr(self.mega_tools, name):
            raise ValueError(f"Unknown MCP Mega-Tool: {name}")
        handler = getattr(self.mega_tools, name)
        result = handler(**arguments)
        return result.model_dump()

    def handle_jsonrpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process standard MCP JSON-RPC 2.0 messages."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        try:
            if method == "initialize":
                res = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": self.SERVER_NAME, "version": self.SERVER_VERSION},
                    "capabilities": {"tools": {}, "resources": {}},
                }
            elif method == "tools/list":
                res = {"tools": self.list_tools()}
            elif method == "resources/list":
                res = {"resources": self.list_resources()}
            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                output = self.call_tool(tool_name, tool_args)
                res = {
                    "content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}],
                    "isError": False,
                }
            else:
                res = {"status": "acknowledged", "method": method}
            return {"jsonrpc": "2.0", "id": req_id, "result": res}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(exc)},
            }


def main() -> None:
    """Run MCP server over stdio for Claude Code / OpenCode / DeepSeek Harness (`dsh`)."""
    server = LiaraMCPServer()
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        req = json.loads(raw)
        resp = server.handle_jsonrpc(req)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
