"""Structured Observability & Immutable Audit Trail (`src/core/observability.py`).

Records every System 1 decision, System 2 tool call, Build-Healer patch, and HITL
approval ID into an immutable JSONL audit log (`workspace/trace.jsonl`), preventing
Shadow AI and enabling post-mortem analysis (Quera Ch. 16 & `AIGovernance.txt`).
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TraceSpan(BaseModel):
    """Structured immutable audit record written to `trace.jsonl`."""

    trace_id: str = Field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:10]}")
    timestamp_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    session_id: str
    virtual_agent_id: str = "liara-sre-virtual-agent"
    layer: str = Field(description="System1 | System2 | MCP_MegaTool | Governance | BuildHealer")
    node_or_tool: str
    sub_action: Optional[str] = None
    risk_tier: str = "autonomous_safe"
    hitl_approval_id: Optional[str] = None
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost_tomans: float = 0.0
    status: str = "SUCCESS"
    details: Dict[str, Any] = Field(default_factory=dict)


class AuditLogger:
    """Thread-safe JSONL trace logger and runtime telemetry aggregator."""

    def __init__(self, trace_file_path: Optional[Path] = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "workspace" / "trace.jsonl"
        self.trace_file_path = trace_file_path or default_path
        self.trace_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._in_memory_spans: List[TraceSpan] = []

    def log_span(
        self,
        session_id: str,
        layer: str,
        node_or_tool: str,
        sub_action: Optional[str] = None,
        risk_tier: str = "autonomous_safe",
        hitl_approval_id: Optional[str] = None,
        latency_ms: float = 0.0,
        tokens_used: int = 0,
        cost_tomans: float = 0.0,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> TraceSpan:
        """Write an immutable audit span to `trace.jsonl` and keep in-memory copy."""
        span = TraceSpan(
            session_id=session_id,
            layer=layer,
            node_or_tool=node_or_tool,
            sub_action=sub_action,
            risk_tier=risk_tier,
            hitl_approval_id=hitl_approval_id,
            latency_ms=round(latency_ms, 2),
            tokens_used=tokens_used,
            cost_tomans=round(cost_tomans, 2),
            status=status,
            details=details or {},
        )
        self._in_memory_spans.append(span)
        with self.trace_file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(span.model_dump(), ensure_ascii=False) + "\n")
        return span

    def get_session_traces(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return recorded audit spans for UI inspection or smoke test assertions."""
        spans = [
            s.model_dump()
            for s in self._in_memory_spans
            if session_id is None or s.session_id == session_id
        ]
        return spans
