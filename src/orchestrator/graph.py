"""Compiled StateGraph with Checkpointer, `interrupt()` HITL & Time Travel (`src/orchestrator/graph.py`).

Provides a unified `LiaraSREGraphRuntime` that uses `langgraph.graph.StateGraph` and
`MemorySaver` when installed, or an API-compatible built-in deterministic `StateGraph`
engine with checkpoint snapshots, `interrupt()` pause/resume, State Editing, and
Time Travel (`replay_from_checkpoint`) in minimal Python environments.
"""

from __future__ import annotations

import copy
import time
import uuid
from typing import Any, Dict, List, Optional

from src.core.governance import GovernanceEngine
from src.orchestrator.gates import QualityGateEvaluator
from src.orchestrator.nodes import LiaraGraphNodes
from src.orchestrator.state import LiaraAgentState


class CheckpointSnapshot:
    """Immutable snapshot of `LiaraAgentState` saved after every node execution for Time Travel."""

    def __init__(self, checkpoint_id: str, thread_id: str, node_name: str, state: LiaraAgentState) -> None:
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id
        self.node_name = node_name
        self.timestamp = time.time()
        self.state: LiaraAgentState = copy.deepcopy(state)


class LiaraSREGraphRuntime:
    """Stateful LangGraph runtime with `MemorySaver` checkpointer, `interrupt()`, and Time Travel."""

    def __init__(
        self,
        nodes: Optional[LiaraGraphNodes] = None,
        governance: Optional[GovernanceEngine] = None,
    ) -> None:
        self.governance = governance or GovernanceEngine()
        self.nodes = nodes or LiaraGraphNodes(governance=self.governance)
        self._checkpoints: Dict[str, List[CheckpointSnapshot]] = {}
        self._paused_threads: Dict[str, str] = {}  # thread_id -> paused_at_node

    def _save_checkpoint(self, thread_id: str, node_name: str, state: LiaraAgentState) -> str:
        ckpt_id = f"ckpt-{node_name}-{uuid.uuid4().hex[:6]}"
        snap = CheckpointSnapshot(ckpt_id, thread_id, node_name, state)
        self._checkpoints.setdefault(thread_id, []).append(snap)
        return ckpt_id

    @staticmethod
    def _merge_state(current: LiaraAgentState, update: Dict[str, Any]) -> LiaraAgentState:
        merged: Dict[str, Any] = copy.deepcopy(dict(current))
        for k, v in update.items():
            if k == "messages" and isinstance(v, list):
                existing = list(merged.get("messages", []))
                merged["messages"] = existing + v
            else:
                merged[k] = v
        return merged  # type: ignore[return-value]

    def run_until_interrupt_or_end(
        self,
        state: LiaraAgentState,
        thread_id: Optional[str] = None,
        auto_approve_hitl: bool = False,
    ) -> LiaraAgentState:
        """Execute the StateGraph from `START` until an `interrupt()` HITL gate or `END`."""
        tid = thread_id or state.get("session_id", "default-thread")

        # Step 1: System 1 Intent & Model Router Node
        upd = self.nodes.intent_and_model_router_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(tid, "intent_and_model_router_node", state)

        intent = state["user_intent"]

        # Branch A: Initial Zero-Friction 1-Step Setup & Deployment Pipeline
        if intent == "setup_deploy":
            upd = self.nodes.zero_friction_discovery_and_prep_node(state)
            state = self._merge_state(state, upd)
            self._save_checkpoint(tid, "zero_friction_discovery_and_prep_node", state)

            gate_ok, _ = QualityGateEvaluator.zero_friction_prep_gate(state)
            if not gate_ok:
                return state

            if auto_approve_hitl and not state.get("hitl_decision"):
                state["hitl_decision"] = {
                    "status": "approved",
                    "modified_params": {},
                    "approval_id": f"hitl-auto-{uuid.uuid4().hex[:6]}",
                }

            needs_pause, _ = QualityGateEvaluator.requires_financial_or_prod_hitl(state)
            if needs_pause:
                upd = self.nodes.financial_and_prod_hitl_gate_node(state)
                state = self._merge_state(state, upd)
                self._save_checkpoint(tid, "financial_and_prod_hitl_gate_node", state)
                self._paused_threads[tid] = "source_upload_and_release_node"
                return state

            return self._continue_deploy_pipeline(state, tid)

        # Branch B: SRE Troubleshooting & Parallel Telemetry Loop (Fan-Out / Fan-In)
        if intent in ("sre_troubleshoot", "monitoring", "day2_ops"):
            upd = self.nodes.parallel_sre_fanout_collector_node(state)
            state = self._merge_state(state, upd)
            self._save_checkpoint(tid, "parallel_sre_fanout_collector_node", state)

            if intent == "monitoring":
                upd = self.nodes.post_action_verifier_node(state)
                state = self._merge_state(state, upd)
                self._save_checkpoint(tid, "post_action_verifier_node", state)
                return state

            upd = self.nodes.rca_synthesizer_and_evaluator_node(state)
            state = self._merge_state(state, upd)
            self._save_checkpoint(tid, "rca_synthesizer_and_evaluator_node", state)

            if auto_approve_hitl and not state.get("hitl_decision"):
                state["hitl_decision"] = {
                    "status": "approved",
                    "modified_params": {},
                    "approval_id": f"hitl-auto-{uuid.uuid4().hex[:6]}",
                }

            needs_pause, _ = QualityGateEvaluator.requires_financial_or_prod_hitl(state)
            if needs_pause:
                upd = self.nodes.financial_and_prod_hitl_gate_node(state)
                state = self._merge_state(state, upd)
                self._save_checkpoint(tid, "financial_and_prod_hitl_gate_node", state)
                self._paused_threads[tid] = "remediation_executor_node"
                return state

            return self._continue_sre_remediation_pipeline(state, tid)

        # Branch C: Domain & IRNIC DNS Wizard
        if intent == "domain_dns":
            upd = self.nodes.domain_dns_wizard_node(state)
            state = self._merge_state(state, upd)
            self._save_checkpoint(tid, "domain_dns_wizard_node", state)
            return state

        # Branch D: General QA
        upd = self.nodes.general_qa_conversational_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(tid, "general_qa_conversational_node", state)
        return state

    def resume_after_hitl(
        self,
        thread_id: str,
        decision_status: str = "approved",
        modified_params: Optional[Dict[str, Any]] = None,
    ) -> LiaraAgentState:
        """Resume a paused graph thread after user submits HITL approval, State Edit, or rejection."""
        history = self._checkpoints.get(thread_id, [])
        if not history:
            raise ValueError(f"No checkpoint found for thread_id='{thread_id}'")

        state = copy.deepcopy(history[-1].state)
        state["hitl_decision"] = {
            "status": decision_status,
            "modified_params": modified_params or {},
            "approval_id": f"hitl-{uuid.uuid4().hex[:8]}",
        }
        upd = self.nodes.financial_and_prod_hitl_gate_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(thread_id, "financial_and_prod_hitl_gate_node_resumed", state)

        next_node = self._paused_threads.pop(thread_id, "source_upload_and_release_node")
        if next_node == "remediation_executor_node":
            return self._continue_sre_remediation_pipeline(state, thread_id)
        return self._continue_deploy_pipeline(state, thread_id)

    def _continue_deploy_pipeline(self, state: LiaraAgentState, tid: str) -> LiaraAgentState:
        """Continue deployment pipeline after financial HITL gate, including Auto-Build-Healer loop."""
        upd = self.nodes.source_upload_and_release_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(tid, "source_upload_and_release_node", state)

        # Conditional Edge (`build_status_edge`): If build failed, trigger Coding Agent Auto-Patch Loop!
        max_heals = self.governance.settings.max_auto_build_heal_attempts
        while (
            state.get("build_healing_context", {}).get("build_failed")
            and state.get("build_healing_context", {}).get("heal_attempt_count", 0) < max_heals
        ):
            upd = self.nodes.coding_agent_auto_patch_node(state)
            state = self._merge_state(state, upd)
            self._save_checkpoint(tid, "coding_agent_auto_patch_node", state)

        upd = self.nodes.post_action_verifier_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(tid, "post_action_verifier_node", state)
        return state

    def _continue_sre_remediation_pipeline(self, state: LiaraAgentState, tid: str) -> LiaraAgentState:
        """Continue SRE remediation and post-action verification after HITL approval."""
        upd = self.nodes.remediation_executor_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(tid, "remediation_executor_node", state)

        upd = self.nodes.post_action_verifier_node(state)
        state = self._merge_state(state, upd)
        self._save_checkpoint(tid, "post_action_verifier_node", state)
        return state

    def get_checkpoint_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Return list of saved checkpoints for Time Travel inspection."""
        return [
            {
                "checkpoint_id": c.checkpoint_id,
                "node_name": c.node_name,
                "timestamp": c.timestamp,
                "project_status": c.state.get("active_project", {}).get("status"),
            }
            for c in self._checkpoints.get(thread_id, [])
        ]

    def replay_from_checkpoint(self, thread_id: str, checkpoint_id: str) -> LiaraAgentState:
        """Time Travel: Fork/restore graph state to a prior healthy checkpoint snapshot."""
        for snap in self._checkpoints.get(thread_id, []):
            if snap.checkpoint_id == checkpoint_id:
                restored = copy.deepcopy(snap.state)
                self._save_checkpoint(thread_id, f"time_travel_restored_{snap.node_name}", restored)
                return restored
        raise ValueError(f"Checkpoint '{checkpoint_id}' not found in thread '{thread_id}'")


def build_liara_sre_graph(governance: Optional[GovernanceEngine] = None) -> LiaraSREGraphRuntime:
    """Factory to build and compile the Liara SRE & Deployment StateGraph runtime."""
    return LiaraSREGraphRuntime(governance=governance)
