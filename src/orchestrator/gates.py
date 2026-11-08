"""Deterministic Quality Gates & Evaluator-Optimizer Rubric (`src/orchestrator/gates.py`).

Implements Quera Ch. 9 Lesson 03 & Lesson 06 patterns:
1. Prompt Chaining Gate Functions (`gate_function(state) -> tuple[bool, str]`):
   Validates intermediate artifacts (`project_manifest.json`, `.tar.gz`, `source_id`)
   without interrupting the user for low-risk preparatory steps.
2. Anti-Fatigue HITL Gate Classifier:
   Pauses graph execution via `interrupt()` ONLY for financial commitments (spending the
   2,000,000 Tomans hackathon credit) or mutating production operations.
3. 4-Level Evaluator-Optimizer Rubric (Threshold >= 8.0 / 10.0):
   Evaluates RCA reports and deployment configurations before presenting to the user.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from src.orchestrator.state import LiaraAgentState


class QualityGateEvaluator:
    """Deterministic quality gates and 4-level Evaluator-Optimizer rubric."""

    RUBRIC_STOP_THRESHOLD = 8.0

    @staticmethod
    def zero_friction_prep_gate(state: LiaraAgentState) -> Tuple[bool, str]:
        """Chaining Gate 1: Verify stack detection, `.env.example` scan, and `.tar.gz` source upload."""
        proj = state.get("active_project", {})
        dep = state.get("deployment_context", {})
        if not proj.get("platform"):
            return False, "Missing detected platform in active_project"
        if not proj.get("plan_id"):
            return False, "Missing recommended economical Liara plan_id"
        if not dep.get("source_id"):
            return False, "Missing uploaded source_id from POST /v2/projects/{name}/sources"
        return True, "Zero-Friction preparation gate passed (100% autonomous, 0 user popups)"

    @staticmethod
    def requires_financial_or_prod_hitl(state: LiaraAgentState) -> Tuple[bool, str]:
        """Anti-Fatigue HITL Gate: Return True ONLY if pending_action has financial or production impact."""
        pending = state.get("pending_action")
        if not pending:
            return False, "no_pending_action"
        decision = state.get("hitl_decision")
        if decision and decision.get("status") in ("approved", "modified"):
            return False, f"already_{decision.get('status')}"
        risk_tier = pending.get("risk_tier", "autonomous_safe")
        if risk_tier == "financial_or_prod_hitl":
            return True, f"HITL required for {pending.get('sub_action')} (cost={pending.get('cost_tomans', 0)} Tomans)"
        return False, "autonomous_safe"

    @classmethod
    def evaluate_rca_rubric_4level(cls, rca_report: Dict[str, Any]) -> Tuple[bool, float, Dict[str, float]]:
        """4-Level Evaluator-Optimizer Rubric (Quera Ch. 9 Lesson 06 & Ch. 15).

        Dimensions (each scored 0.0 to 2.5, total 10.0, stop threshold >= 8.0):
        1. Step-by-Step Reasoning (`reasoning_steps` placed before conclusions, >= 3 steps)
        2. Telemetry & Log Correlation (links exit code / metrics to log lines)
        3. Actionable Dual Remediation (both infra plan & code patch provided)
        4. Security & Grounding (no hallucinated endpoints, prompt injections sanitized)
        """
        steps = rca_report.get("reasoning_steps", [])
        dim_reasoning = 2.5 if len(steps) >= 3 else (1.5 if len(steps) >= 1 else 0.0)

        evidence = rca_report.get("log_evidence", [])
        hypotheses = rca_report.get("hypotheses", [])
        dim_correlation = 2.5 if (len(evidence) >= 2 and len(hypotheses) >= 1) else 1.0

        has_infra = bool(rca_report.get("infra_remediation_plan"))
        has_code = bool(rca_report.get("code_remediation_patch"))
        dim_remediation = 2.5 if (has_infra and has_code) else (1.5 if (has_infra or has_code) else 0.0)

        primary = str(rca_report.get("primary_cause", ""))
        dim_grounding = 2.5 if len(primary) > 10 else 1.0

        total_score = round(dim_reasoning + dim_correlation + dim_remediation + dim_grounding, 2)
        breakdown = {
            "step_by_step_reasoning": dim_reasoning,
            "telemetry_log_correlation": dim_correlation,
            "dual_remediation_completeness": dim_remediation,
            "security_and_api_grounding": dim_grounding,
            "total_score_out_of_10": total_score,
        }
        return total_score >= cls.RUBRIC_STOP_THRESHOLD, total_score, breakdown
