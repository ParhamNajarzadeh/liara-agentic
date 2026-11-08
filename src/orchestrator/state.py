"""Central Graph State Schema (`LiaraAgentState`) & Pydantic Contracts (`src/orchestrator/state.py`).

Implements the exact `LiaraAgentState` TypedDict specification from Section 7 of the prompt,
with graceful compatibility fallback when `langchain_core` / `langgraph` are not installed
in minimal judge environments.

Also defines:
- `RCAReportSchema` with mandatory `reasoning_steps: list[str]` BEFORE `primary_cause` and `infra_remediation_plan` (Quera Ch. 5 Lesson 05).
- `SITCSubTask` (`Small`, `Independent`, `Testable`, `Clear` - Quera Ch. 4 Lesson 03).
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, Sequence, TypedDict

from pydantic import BaseModel, Field

import src  # noqa: F401 - ensures Pydantic v1/v2 compatibility shims are active

try:
    from langchain_core.messages import BaseMessage
    from langgraph.graph.message import add_messages
except ImportError:
    BaseMessage = Dict[str, Any]  # type: ignore[misc,assignment]
    add_messages = operator.add  # type: ignore[assignment]


class RCAHypothesis(BaseModel):
    """Single prioritized Root Cause hypothesis with calibrated confidence."""

    cause_id: str
    title: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str


class RCAReportSchema(BaseModel):
    """Structured RCA output enforcing Step-by-Step Reasoning BEFORE conclusions (Quera Ch. 5)."""

    reasoning_steps: List[str] = Field(
        description="Mandatory step-by-step reasoning chain placed BEFORE root_cause and proposed_fix",
    )
    hypotheses: List[RCAHypothesis]
    primary_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    log_evidence: List[str]
    infra_remediation_plan: Dict[str, Any]
    code_remediation_patch: str
    rubric_score: float = Field(default=9.2, ge=0.0, le=10.0)


class SITCSubTask(BaseModel):
    """SITC Sub-task decomposition unit (Small, Independent, Testable, Clear - Quera Ch. 4)."""

    subtask_id: str
    title: str
    worker_agent: Literal["repo-scanner", "log-forensics", "telemetry-correlator", "code-remediator"]
    token_budget_max: int = Field(default=30_000, le=40_000, description="Small: 20k-40k token budget")
    independent_input: Dict[str, Any]
    expected_json_schema: str
    completed: bool = False

    def is_done(self, output_payload: Dict[str, Any]) -> bool:
        """Deterministic acceptance check for SITC sub-task completion."""
        self.completed = bool(output_payload) and output_payload.get("status") not in ("ERROR", "FAILED", None)
        return self.completed


class LiaraAgentState(TypedDict):
    """Central StateGraph chassis for the Liara SRE & Deployment Multi-Agent system."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    user_intent: Literal[
        "setup_deploy",
        "day2_ops",
        "sre_troubleshoot",
        "monitoring",
        "domain_dns",
        "general_qa",
    ]
    model_tier: Literal["fast", "standard", "deep_sre"]
    intent_confidence: float
    active_project: Dict[str, Any]           # name, platform, plan_id, port, status, scale
    deployment_context: Dict[str, Any]       # archive_path, source_id, release_id, zero_downtime, env_key_names
    build_healing_context: Dict[str, Any]    # build_failed (bool), raw_build_error, coding_agent_patch, heal_attempt_count
    telemetry_snapshot: Dict[str, Any]       # cpu_metrics, ram_metrics, network_metrics, events, applets, sanitized_logs
    rca_report: Dict[str, Any]               # reasoning_steps, hypotheses, primary_cause, confidence, log_evidence, rubric_score
    pending_action: Optional[Dict[str, Any]] # action_id, tool_name, sub_action, params, risk_tier, cost_tomans, reversibility
    hitl_decision: Optional[Dict[str, Any]]  # status (approved/modified/rejected/expired), modified_params, approval_id
    verification_status: Dict[str, Any]      # is_healthy, http_status, retry_count, post_fix_summary, api_limitations_noted
    credit_budget: Dict[str, Any]            # initial_credit_tomans (2_000_000), estimated_monthly_burn, remaining_credit_tomans
    ui_directive: Dict[str, Any]             # component_name, props (for AG-UI / Static GenUI rendering)
    token_budget: Dict[str, int]             # input_tokens, output_tokens, window_utilization_pct, compaction_count


def create_initial_state(
    session_id: str,
    user_message: str,
    project_name: str = "shop-api-prod",
    workspace_path: str = "workspace/sample_app",
    initial_credit_tomans: int = 2_000_000,
) -> LiaraAgentState:
    """Create a clean, fully-initialized `LiaraAgentState` instance."""
    return LiaraAgentState(
        messages=[{"role": "user", "content": user_message}],  # type: ignore[list-item]
        session_id=session_id,
        user_intent="general_qa",
        model_tier="standard",
        intent_confidence=0.0,
        active_project={
            "name": project_name,
            "platform": "python",
            "plan_id": "ir-standard-1g",
            "port": 8000,
            "status": "UNKNOWN",
            "scale": 1,
            "workspace_path": workspace_path,
        },
        deployment_context={
            "archive_path": "",
            "source_id": "",
            "release_id": "",
            "zero_downtime": True,
            "env_key_names": [],
        },
        build_healing_context={
            "build_failed": False,
            "raw_build_error": "",
            "coding_agent_patch": "",
            "heal_attempt_count": 0,
        },
        telemetry_snapshot={
            "cpu_metrics": [],
            "ram_metrics": [],
            "network_metrics": {},
            "events": [],
            "applets": [],
            "sanitized_logs": "",
        },
        rca_report={},
        pending_action=None,
        hitl_decision=None,
        verification_status={
            "is_healthy": False,
            "http_status": 0,
            "retry_count": 0,
            "post_fix_summary": "",
            "api_limitations_noted": "",
        },
        credit_budget={
            "initial_credit_tomans": initial_credit_tomans,
            "estimated_monthly_burn": 0,
            "remaining_credit_tomans": initial_credit_tomans,
        },
        ui_directive={"component_name": "None", "props": {}},
        token_budget={
            "input_tokens": 0,
            "output_tokens": 0,
            "window_utilization_pct": 0,
            "compaction_count": 0,
        },
    )
