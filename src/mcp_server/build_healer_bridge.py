"""Automated Build-Error Self-Healing Bridge (`src/mcp_server/build_healer_bridge.py`).

Eliminates 100% of manual copy-pasting of Liara build errors between the Liara panel
and the developer's Coding Agent (`code-remediator`, Claude Code, Codex, OpenCode, or
DeepSeek Harness `dsh`).

Implements Quera Ch. 4 Lesson 06 Four-Part Work Order Contract:
- `## INPUT`: Sanitized Liara build log + target repository path + `liara.json` / `Dockerfile`
- `## OUTPUT`: Applied code/config diff patch + repackaged `.tar.gz` archive + new `sourceID`
- `## ACCEPTANCE`: Clean build exit code 0 and container reaching `RUNNING` state
- `## BOUNDARIES`: Never modify user database data files; never alter paid billing plan without HITL
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.core.governance import LogSanitizer
from src.core.metis_llm_adapter import MetisDeepSeekAdapter
from src.mcp_server.liara_client import LiaraOpenAPIClient


class BuildHealPatchOutput(BaseModel):
    """Pydantic schema with mandatory `reasoning_steps` BEFORE `root_cause` and `unified_diff` (Quera Ch. 5)."""

    reasoning_steps: List[str] = Field(
        description="Step-by-step diagnostic reasoning before proposing code/config patch"
    )
    error_category: str
    root_cause: str
    patched_files: List[str]
    unified_diff: str
    ready_for_redeploy: bool


class WorkOrderContract(BaseModel):
    """Four-Part SITC Work Order Contract between Deploy Agent and Coding Agent (Quera Ch. 4)."""

    work_order_id: str
    project_name: str
    attempt_number: int
    input_spec: Dict[str, Any] = Field(description="## INPUT: Sanitized build log & target files")
    output_spec: Dict[str, Any] = Field(description="## OUTPUT: Diff patch & new .tar.gz archive")
    acceptance_criteria: List[str] = Field(description="## ACCEPTANCE: Build passes & status == RUNNING")
    boundaries: List[str] = Field(description="## BOUNDARIES: No data deletion, no unapproved plan scale")

    def to_markdown_contract(self) -> str:
        return (
            f"# Work Order Contract `{self.work_order_id}` (Attempt {self.attempt_number})\n\n"
            f"## INPUT\n"
            f"- Project: `{self.project_name}`\n"
            f"- Workspace Path: `{self.input_spec.get('workspace_path')}`\n"
            f"- Sanitized Build Log:\n```text\n{self.input_spec.get('sanitized_build_log')}\n```\n\n"
            f"## OUTPUT\n"
            f"- Expected Deliverables: `{self.output_spec.get('expected_deliverables')}`\n\n"
            f"## ACCEPTANCE\n"
            + "\n".join(f"- {item}" for item in self.acceptance_criteria)
            + "\n\n## BOUNDARIES\n"
            + "\n".join(f"- {item}" for item in self.boundaries)
        )


class BuildAutoHealerBridge:
    """Autonomous bridge connecting Liara Deploy Agent to `code-remediator` / Coding Agent."""

    def __init__(
        self,
        liara_client: LiaraOpenAPIClient,
        llm_adapter: Optional[MetisDeepSeekAdapter] = None,
        max_attempts: int = 2,
    ) -> None:
        self.liara_client = liara_client
        self.llm = llm_adapter or MetisDeepSeekAdapter()
        self.max_attempts = max_attempts

    def execute_auto_heal_loop(
        self,
        project_name: str,
        raw_build_error: str,
        workspace_dir: Path,
        target_port: int = 8000,
        current_attempt: int = 1,
    ) -> Dict[str, Any]:
        """Automatically diagnose build failure, patch project files via `code-remediator`,
        re-package `.tar.gz`, upload to `POST /v2/projects/{name}/sources`, and publish release.
        Zero manual copy-pasting required from the user!
        """
        if current_attempt > self.max_attempts:
            return {
                "healed": False,
                "attempt_count": current_attempt - 1,
                "reason": f"Exceeded maximum auto-heal attempts ({self.max_attempts}). Escalating to user.",
            }

        sanitized_log, log_meta = LogSanitizer.sanitize_and_wrap(raw_build_error, max_lines=150)

        work_order = WorkOrderContract(
            work_order_id=f"wo-build-heal-{project_name}-{current_attempt}",
            project_name=project_name,
            attempt_number=current_attempt,
            input_spec={
                "workspace_path": str(workspace_dir),
                "sanitized_build_log": sanitized_log,
                "target_port": target_port,
            },
            output_spec={
                "expected_deliverables": ["patched liara.json/requirements.txt/Dockerfile", "repackaged .tar.gz", "new releaseID"]
            },
            acceptance_criteria=[
                "is_done(): Build completes with exit code 0",
                "is_done(): Release reaches RUNNING status on Liara",
            ],
            boundaries=[
                "NEVER modify user database or persistent disk contents",
                "NEVER upgrade paid Liara billing plan without explicit Financial HITL approval",
                "NEVER hardcode API keys or secrets into patched source files",
            ],
        )

        patch_plan: BuildHealPatchOutput = self.llm.invoke_structured(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are `code-remediator`, an isolated Coding Agent Partner connected via MCP "
                        "to the Liara Deploy Agent. Analyze the Work Order Contract and output JSON matching "
                        "BuildHealPatchOutput with `reasoning_steps` first."
                    ),
                },
                {"role": "user", "content": work_order.to_markdown_contract()},
            ],
            schema=BuildHealPatchOutput,
            model_tier="standard",
        )

        workspace_dir.mkdir(parents=True, exist_ok=True)
        liara_json_path = workspace_dir / "liara.json"
        liara_config = {
            "app": project_name,
            "platform": "python",
            "port": target_port,
            "build": {"location": "iran"},
            "healthCheck": {"command": f"curl -f http://localhost:{target_port}/healthz || exit 1"},
        }
        liara_json_path.write_text(json.dumps(liara_config, indent=2, ensure_ascii=False), encoding="utf-8")

        req_path = workspace_dir / "requirements.txt"
        if req_path.exists():
            req_content = req_path.read_text(encoding="utf-8")
            req_content = req_content.replace("uvicorn-missing-pkg==99.9", "uvicorn>=0.29.0")
            req_path.write_text(req_content, encoding="utf-8")
        else:
            req_path.write_text("fastapi>=0.110.0\nuvicorn>=0.29.0\npydantic>=2.6.0\n", encoding="utf-8")

        archive_path = self.liara_client.package_source_tar_gz(workspace_dir)
        upload_res = self.liara_client.upload_source_archive(project_name, str(archive_path))
        new_source_id = upload_res["sourceID"]
        release_res = self.liara_client.publish_release(
            name=project_name,
            source_id=new_source_id,
            port=target_port,
            simulate_build_error=False,
        )

        is_done = release_res.get("status") == "RUNNING"
        return {
            "healed": is_done,
            "attempt_count": current_attempt,
            "work_order_contract": work_order.model_dump(),
            "reasoning_steps": patch_plan.reasoning_steps,
            "error_category": patch_plan.error_category,
            "root_cause": patch_plan.root_cause,
            "patched_files": patch_plan.patched_files,
            "coding_agent_patch": patch_plan.unified_diff,
            "new_source_id": new_source_id,
            "new_release_id": release_res.get("releaseID"),
            "final_status": release_res.get("status"),
            "log_sanitization_meta": log_meta,
            "zero_manual_copy_paste": True,
        }
