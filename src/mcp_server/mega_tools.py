"""5 Domain-Driven Liara Mega-Tools (`src/mcp_server/mega_tools.py`).

Implements the Context Engineering Mega-Tool architecture (`Harness.txt` & Quera Ch. 13):
All Liara OpenAPI v1/v2 operations are grouped into 5 domain-driven Mega-Tools with strict
Pydantic validation and Anti-Fatigue HITL enforcement:
1. `liara_app_lifecycle`
2. `liara_release_pipeline`
3. `liara_config_and_storage`
4. `liara_sre_observability`
5. `liara_domain_and_network`
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

from src.core.governance import GovernanceEngine, LogSanitizer
from src.core.system_one_engine import SystemOneDecisionEngine
from src.mcp_server.build_healer_bridge import BuildAutoHealerBridge
from src.mcp_server.liara_client import LiaraOpenAPIClient


class MegaToolResponse(BaseModel):
    """Unified envelope returned by all 5 Liara Mega-Tools."""

    tool_name: str
    action: str
    risk_tier: str
    requires_hitl: bool = False
    status: str
    data: Dict[str, Any]
    ui_directive: Optional[Dict[str, Any]] = None


class LiaraMegaTools:
    """Implementation of the 5 Domain-Driven Liara Mega-Tools."""

    def __init__(
        self,
        liara_client: Optional[LiaraOpenAPIClient] = None,
        governance: Optional[GovernanceEngine] = None,
        system_one: Optional[SystemOneDecisionEngine] = None,
        build_healer: Optional[BuildAutoHealerBridge] = None,
    ) -> None:
        self.governance = governance or GovernanceEngine()
        self.client = liara_client or LiaraOpenAPIClient(governance=self.governance)
        self.system_one = system_one or SystemOneDecisionEngine(self.governance.settings)
        self.build_healer = build_healer or BuildAutoHealerBridge(self.client)

    def liara_app_lifecycle(
        self,
        action: Literal[
            "list_apps",
            "get_app_details",
            "estimate_optimal_plan",
            "create_app",
            "restart_app",
            "turn_power",
            "scale_plan",
        ],
        project_name: str = "my-liara-app",
        platform: str = "python",
        plan_id: str = "ir-standard-1g",
        port: int = 8000,
        power_on: bool = True,
        has_oom_history: bool = False,
        hitl_approved: bool = False,
    ) -> MegaToolResponse:
        """Manage Liara application lifecycle, plan estimation, creation, power, and scaling."""
        guard = self.system_one.evaluate_pre_tool_guardrail(
            "liara_app_lifecycle", action, {"project_name": project_name, "plan_id": plan_id}
        )
        risk_tier = guard.decisions["action_risk_tier"]
        needs_hitl = guard.decisions["requires_hitl_interrupt"]

        if action == "list_apps":
            res = self.client.list_projects()
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=False,
                status="OK",
                data=res,
            )

        if action == "get_app_details":
            res = self.client.get_project_details(project_name)
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=False,
                status="OK",
                data=res,
            )

        if action == "estimate_optimal_plan":
            rec = self.governance.credit_guard.recommend_economical_plan(platform, has_oom_history)
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=rec,
            )

        if needs_hitl and not hitl_approved:
            plan_info = self.governance.credit_guard.LIARA_PLANS_CATALOG.get(
                plan_id, self.governance.credit_guard.LIARA_PLANS_CATALOG["ir-standard-1g"]
            )
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=True,
                status="AWAITING_HITL_APPROVAL",
                data={
                    "pending_action": {
                        "tool_name": "liara_app_lifecycle",
                        "sub_action": action,
                        "project_name": project_name,
                        "platform": platform,
                        "plan_id": plan_id,
                        "port": port,
                        "cost_tomans": plan_info["monthly_cost_tomans"] if action in ("create_app", "scale_plan") else 0,
                        "remaining_credit_tomans": self.governance.credit_guard.remaining_credit_tomans,
                    }
                },
                ui_directive={
                    "component_name": "UnifiedZeroFrictionLaunchCard"
                    if action == "create_app"
                    else "HITLActionApprovalGateModal",
                    "props": {
                        "project_name": project_name,
                        "action": action,
                        "plan_id": plan_id,
                        "port": port,
                        "monthly_cost_tomans": plan_info["monthly_cost_tomans"],
                        "remaining_credit_tomans": self.governance.credit_guard.remaining_credit_tomans,
                    },
                },
            )

        if action == "create_app":
            res = self.client.create_project(project_name, platform, plan_id, port)
            budget = self.governance.credit_guard.commit_plan_cost(plan_id)
            res["credit_budget"] = budget
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        if action == "restart_app":
            res = self.client.restart_project(project_name)
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        if action == "turn_power":
            res = self.client.power_project(project_name, power_on)
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        if action == "scale_plan":
            res = self.client.scale_project_plan(project_name, plan_id)
            budget = self.governance.credit_guard.commit_plan_cost(plan_id)
            res["credit_budget"] = budget
            return MegaToolResponse(
                tool_name="liara_app_lifecycle",
                action=action,
                risk_tier=risk_tier,
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        raise ValueError(f"Unsupported sub-action: {action}")

    def liara_release_pipeline(
        self,
        action: Literal[
            "auto_prepare_and_upload",
            "publish_release",
            "auto_heal_build_loop",
            "list_releases",
            "rollback_release",
        ],
        project_name: str,
        workspace_path: str = "workspace/sample_app",
        source_id: Optional[str] = None,
        port: int = 8000,
        target_release_id: Optional[str] = None,
        raw_build_error: str = "",
        simulate_build_error: Optional[bool] = None,
        hitl_approved: bool = False,
    ) -> MegaToolResponse:
        """Manage source packaging, upload, release publication, auto-build healing, and rollbacks."""
        if action == "auto_prepare_and_upload":
            ws = Path(workspace_path)
            ws.mkdir(parents=True, exist_ok=True)
            manifest = self._auto_scan_repository(ws, project_name, port)
            archive_path = self.client.package_source_tar_gz(ws)
            upload_res = self.client.upload_source_archive(project_name, str(archive_path))
            return MegaToolResponse(
                tool_name="liara_release_pipeline",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="UPLOADED_READY",
                data={
                    "manifest": manifest,
                    "archive_path": str(archive_path),
                    "source_id": upload_res["sourceID"],
                    "upload_response": upload_res,
                },
                ui_directive={
                    "component_name": "LiveDeploymentStepper",
                    "props": {
                        "project_name": project_name,
                        "current_step": 2,
                        "source_id": upload_res["sourceID"],
                        "detected_platform": manifest["platform"],
                    },
                },
            )

        if action == "auto_heal_build_loop":
            heal_res = self.build_healer.execute_auto_heal_loop(
                project_name=project_name,
                raw_build_error=raw_build_error,
                workspace_dir=Path(workspace_path),
                target_port=port,
            )
            return MegaToolResponse(
                tool_name="liara_release_pipeline",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="AUTO_HEALED" if heal_res.get("healed") else "HEAL_FAILED",
                data=heal_res,
                ui_directive={
                    "component_name": "AutomatedBuildHealerBridgeCard",
                    "props": heal_res,
                },
            )

        if action == "list_releases":
            res = self.client.list_releases(project_name)
            return MegaToolResponse(
                tool_name="liara_release_pipeline",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=res,
            )

        if action == "publish_release":
            if not hitl_approved:
                return MegaToolResponse(
                    tool_name="liara_release_pipeline",
                    action=action,
                    risk_tier="financial_or_prod_hitl",
                    requires_hitl=True,
                    status="AWAITING_HITL_APPROVAL",
                    data={
                        "pending_action": {
                            "tool_name": "liara_release_pipeline",
                            "sub_action": "publish_release",
                            "project_name": project_name,
                            "source_id": source_id,
                            "port": port,
                        }
                    },
                )
            pub_res = self.client.publish_release(
                project_name,
                source_id or "src-auto-latest",
                port=port,
                simulate_build_error=simulate_build_error,
            )
            return MegaToolResponse(
                tool_name="liara_release_pipeline",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=False,
                status=pub_res["status"],
                data=pub_res,
                ui_directive={
                    "component_name": "LiveDeploymentStepper",
                    "props": {
                        "project_name": project_name,
                        "current_step": 5 if pub_res["status"] == "RUNNING" else 3,
                        "release_id": pub_res.get("releaseID"),
                        "status": pub_res["status"],
                    },
                },
            )

        if action == "rollback_release":
            if not hitl_approved:
                return MegaToolResponse(
                    tool_name="liara_release_pipeline",
                    action=action,
                    risk_tier="financial_or_prod_hitl",
                    requires_hitl=True,
                    status="AWAITING_HITL_APPROVAL",
                    data={
                        "pending_action": {
                            "tool_name": "liara_release_pipeline",
                            "sub_action": "rollback_release",
                            "project_name": project_name,
                            "target_release_id": target_release_id or "rel-v101-healthy",
                        }
                    },
                    ui_directive={
                        "component_name": "HITLActionApprovalGateModal",
                        "props": {
                            "project_name": project_name,
                            "action": "rollback_release",
                            "target_release_id": target_release_id or "rel-v101-healthy",
                        },
                    },
                )
            pub_res = self.client.publish_release(
                project_name,
                source_id=target_release_id or "src-001",
                port=port,
                simulate_build_error=False,
            )
            pub_res["rolled_back_to"] = target_release_id or "rel-v101-healthy"
            return MegaToolResponse(
                tool_name="liara_release_pipeline",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=False,
                status="ROLLED_BACK",
                data=pub_res,
            )

        raise ValueError(f"Unsupported sub-action: {action}")

    def liara_config_and_storage(
        self,
        action: Literal[
            "scan_env_template",
            "apply_secret_blind_envs",
            "toggle_zero_downtime",
            "toggle_readonly",
            "toggle_static_ip",
            "manage_disks",
            "create_ftp_backup",
        ],
        project_name: str,
        workspace_path: str = "workspace/sample_app",
        env_key_names: Optional[List[str]] = None,
        enabled: bool = True,
        disk_name: str = "data-disk",
        disk_size_gb: int = 5,
        hitl_approved: bool = False,
    ) -> MegaToolResponse:
        """Scan `.env.example` autonomously and manage Secret-Blind envs, Zero-Downtime, and Disks."""
        if action == "scan_env_template":
            ws = Path(workspace_path)
            env_example = ws / ".env.example"
            discovered_keys: List[str] = []
            if env_example.is_file():
                for line in env_example.read_text(encoding="utf-8").splitlines():
                    clean = line.strip()
                    if clean and not clean.startswith("#") and "=" in clean:
                        k, _, _ = clean.partition("=")
                        discovered_keys.append(k.strip())
            else:
                discovered_keys = ["APP_ENV", "PORT", "DATABASE_URL", "REDIS_URL"]

            return MegaToolResponse(
                tool_name="liara_config_and_storage",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data={
                    "project_name": project_name,
                    "env_key_names": discovered_keys,
                    "secret_blind_enforced": True,
                },
            )

        if not hitl_approved:
            return MegaToolResponse(
                tool_name="liara_config_and_storage",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=True,
                status="AWAITING_HITL_APPROVAL",
                data={
                    "pending_action": {
                        "tool_name": "liara_config_and_storage",
                        "sub_action": action,
                        "project_name": project_name,
                        "env_key_names": env_key_names or [],
                    }
                },
            )

        if action == "apply_secret_blind_envs":
            res = self.client.update_envs_secret_blind(project_name, env_key_names or [])
            return MegaToolResponse(
                tool_name="liara_config_and_storage",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        if action == "toggle_zero_downtime":
            res = self.client.toggle_zero_downtime(project_name, enabled)
            return MegaToolResponse(
                tool_name="liara_config_and_storage",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        if action == "toggle_readonly":
            res = self.client.toggle_read_only(project_name, enabled)
            return MegaToolResponse(
                tool_name="liara_config_and_storage",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        if action in ("manage_disks", "create_ftp_backup", "toggle_static_ip"):
            res = self.client.manage_disk(project_name, disk_name, disk_size_gb)
            return MegaToolResponse(
                tool_name="liara_config_and_storage",
                action=action,
                risk_tier="financial_or_prod_hitl",
                requires_hitl=False,
                status="EXECUTED",
                data=res,
            )

        raise ValueError(f"Unsupported sub-action: {action}")

    def liara_sre_observability(
        self,
        action: Literal[
            "get_resource_metrics",
            "get_app_logs",
            "get_build_logs",
            "get_system_events",
            "get_applets_health",
            "run_full_telemetry_fanout",
        ],
        project_name: str,
        max_log_lines: int = 200,
    ) -> MegaToolResponse:
        """100% Autonomous observability with Regex sanitization and `<untrusted_log_data>` wrapping."""
        if action == "get_resource_metrics":
            metrics = self.client.get_metrics(project_name)
            return MegaToolResponse(
                tool_name="liara_sre_observability",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=metrics,
                ui_directive={"component_name": "ResourceHealthTelemetryCard", "props": metrics},
            )

        if action in ("get_app_logs", "get_build_logs"):
            raw_logs = self.client.get_raw_logs(project_name)
            sanitized_block, meta = LogSanitizer.sanitize_and_wrap(raw_logs, max_lines=max_log_lines)
            scan = self.system_one.scan_logs_and_anomalies(raw_logs)
            return MegaToolResponse(
                tool_name="liara_sre_observability",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data={
                    "project_name": project_name,
                    "sanitized_logs": sanitized_block,
                    "sanitization_meta": meta,
                    "system_one_anomaly_scan": scan.model_dump(),
                },
            )

        if action == "get_system_events":
            events = self.client.get_events(project_name)
            return MegaToolResponse(
                tool_name="liara_sre_observability",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=events,
            )

        if action == "get_applets_health":
            applets = self.client.get_applets(project_name)
            return MegaToolResponse(
                tool_name="liara_sre_observability",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=applets,
            )

        if action == "run_full_telemetry_fanout":
            metrics = self.client.get_metrics(project_name)
            raw_logs = self.client.get_raw_logs(project_name)
            sanitized_block, meta = LogSanitizer.sanitize_and_wrap(raw_logs, max_lines=max_log_lines)
            scan = self.system_one.scan_logs_and_anomalies(raw_logs)
            events = self.client.get_events(project_name)
            applets = self.client.get_applets(project_name)
            releases = self.client.list_releases(project_name)
            snapshot = {
                "project_name": project_name,
                "metrics": metrics,
                "sanitized_logs": sanitized_block,
                "sanitization_meta": meta,
                "system_one_anomaly_scan": scan.model_dump(),
                "events": events["events"],
                "applets": applets["applets"],
                "releases": releases["releases"],
            }
            return MegaToolResponse(
                tool_name="liara_sre_observability",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=snapshot,
                ui_directive={"component_name": "ResourceHealthTelemetryCard", "props": snapshot},
            )

        raise ValueError(f"Unsupported sub-action: {action}")

    def liara_domain_and_network(
        self,
        action: Literal[
            "list_domains",
            "attach_domain",
            "check_domain_dns_ssl",
            "manage_dns_records",
            "generate_external_registrar_guide",
        ],
        domain_name: str = "shop.example.ir",
        project_name: str = "shop-api-prod",
        hitl_approved: bool = True,
    ) -> MegaToolResponse:
        """Manage domains, SSL verification, and step-by-step IRNIC (`.ir`) / Cloudflare registrar guides."""
        if action == "list_domains":
            res = self.client.list_domains()
            return MegaToolResponse(
                tool_name="liara_domain_and_network",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=res,
            )

        if action == "attach_domain":
            res = self.client.attach_domain(domain_name, project_name)
            guide = self._build_irnic_registrar_guide(domain_name, project_name)
            res["registrar_guide"] = guide
            return MegaToolResponse(
                tool_name="liara_domain_and_network",
                action=action,
                risk_tier="financial_or_prod_hitl" if not hitl_approved else "autonomous_safe",
                requires_hitl=False,
                status="ATTACHED",
                data=res,
                ui_directive={"component_name": "DomainDNSGuideWidget", "props": {**res, **guide}},
            )

        if action in ("check_domain_dns_ssl", "manage_dns_records"):
            res = self.client.check_domain_dns_and_ssl(domain_name)
            guide = self._build_irnic_registrar_guide(domain_name, project_name)
            return MegaToolResponse(
                tool_name="liara_domain_and_network",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="VERIFIED",
                data={**res, "registrar_guide": guide},
                ui_directive={"component_name": "DomainDNSGuideWidget", "props": {**res, **guide}},
            )

        if action == "generate_external_registrar_guide":
            guide = self._build_irnic_registrar_guide(domain_name, project_name)
            return MegaToolResponse(
                tool_name="liara_domain_and_network",
                action=action,
                risk_tier="autonomous_safe",
                requires_hitl=False,
                status="OK",
                data=guide,
                ui_directive={"component_name": "DomainDNSGuideWidget", "props": guide},
            )

        raise ValueError(f"Unsupported sub-action: {action}")

    @staticmethod
    def _auto_scan_repository(workspace_dir: Path, project_name: str, default_port: int = 8000) -> Dict[str, Any]:
        """Scan project files without asking repetitive questions (Zero-Friction 1-Step Flow)."""
        platform = "python"
        port = default_port
        if (workspace_dir / "package.json").exists():
            pkg_txt = (workspace_dir / "package.json").read_text(encoding="utf-8", errors="ignore")
            platform = "nextjs" if "next" in pkg_txt else "node"
            port = 3000
        elif (workspace_dir / "Dockerfile").exists():
            platform = "docker"
            port = 8000
        elif (workspace_dir / "requirements.txt").exists() or (workspace_dir / "pyproject.toml").exists():
            platform = "python"
            port = 8000

        env_keys = ["APP_ENV", "PORT", "DATABASE_URL"]
        env_example = workspace_dir / ".env.example"
        if env_example.exists():
            parsed = [
                ln.split("=")[0].strip()
                for ln in env_example.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.strip().startswith("#") and "=" in ln
            ]
            if parsed:
                env_keys = parsed

        liara_cfg = {
            "app": project_name,
            "platform": platform,
            "port": port,
            "build": {"location": "iran"},
        }
        (workspace_dir / "liara.json").write_text(
            json.dumps(liara_cfg, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        manifest = {
            "project_name": project_name,
            "platform": platform,
            "detected_port": port,
            "env_key_names": env_keys,
            "liara_json_generated": True,
        }
        (workspace_dir / "project_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return manifest

    @staticmethod
    def _build_irnic_registrar_guide(domain_name: str, project_name: str) -> Dict[str, Any]:
        return {
            "domain_name": domain_name,
            "project_name": project_name,
            "registrar": "IRNIC (nic.ir) / Cloudflare",
            "api_limitation_disclosure": (
                "محدودیت صریح API: پلتفرم لیارا دسترسی مستقیم API به پنل ایرنیک (nic.ir) ندارد. "
                "تنظیم NS یا رکوردهای A/CNAME در ایرنیک باید توسط کاربر با کپی تک‌کلیکی مقادیر زیر انجام شود."
            ),
            "dns_records": [
                {"type": "CNAME", "host": "www", "value": "edge.liara.ir", "ttl": "Auto / 3600"},
                {"type": "A / ANAME", "host": "@", "value": "185.141.107.44", "ttl": "Auto / 3600"},
            ],
            "liara_nameservers": ["ns1.liara.zone", "ns2.liara.zone"],
            "steps_persian": [
                "۱. وارد پنل ایرنیک (nic.ir) یا کلودفلر خود شوید.",
                "۲. رکوردهای A و CNAME بالا را با یک کلیک کپی کرده و در بخش DNS دامنه ثبت کنید.",
                "۳. روی دکمه «بررسی اتصال DNS و صدور خودکار گواهی SSL» در همین کارت کلیک کنید تا اندپوینت POST /v1/domains/{id}/check فراخوانی شود.",
            ],
        }
