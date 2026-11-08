"""Context Engineering, Token Budgeting, JIT Retrieval & Compaction (`src/core/context_manager.py`).

Implements Quera Agentic AI Course Ch. 6 & Ch. 10 principles:
1. 4-Share Token Budget (`count_tokens`): System Prompt + Mega-Tool Schemas + `CLAUDE.md` + History.
2. Three Automatic Compaction Triggers (`should_compact` - Ch. 10 Lesson 04):
   - Trigger 1: Window utilization >= 70% (`usage / window >= 0.70`)
   - Trigger 2: Conversation turn count >= 40 (`len(history) >= 40`)
   - Trigger 3: Explicit topic shift (`/clear`) while preserving key reference IDs
     (`project_name`, `source_id`, `release_id`, `remaining_credit_tomans`).
3. 4-Step Just-In-Time (JIT) File Retrieval (`decide -> glob/grep -> slice read -> answer` - Ch. 10 Lesson 05).
4. Persistent 4-Part `MEMORY.md` synchronization (`User Preferences`, `Project Topology`,
   `Build & Incident Learnings`, `Reference IDs`).
"""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ContextBudgetManager:
    """Manages token counting, 4-share allocation, and non-destructive context compaction."""

    def __init__(
        self,
        window_limit: int = 128_000,
        compaction_threshold: float = 0.70,
        max_turns: int = 40,
    ) -> None:
        self.window_limit = window_limit
        self.compaction_threshold = compaction_threshold
        self.max_turns = max_turns
        self.compaction_count = 0

    @staticmethod
    def count_tokens(text: str) -> int:
        """Fast deterministic token estimator for Persian + English + code (~3.6 chars/token)."""
        if not text:
            return 0
        return max(1, int(len(text) / 3.6))

    def compute_budget_breakdown(
        self,
        system_prompt: str,
        mega_tool_schemas: str,
        claude_md_content: str,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate the 4 token shares and current utilization percentage."""
        sys_tokens = self.count_tokens(system_prompt)
        tool_tokens = self.count_tokens(mega_tool_schemas)
        claude_tokens = self.count_tokens(claude_md_content)
        hist_tokens = sum(self.count_tokens(str(m.get("content", ""))) for m in messages)
        total_input = sys_tokens + tool_tokens + claude_tokens + hist_tokens
        utilization = round(total_input / max(1, self.window_limit), 4)
        return {
            "system_prompt_tokens": sys_tokens,
            "mega_tool_schema_tokens": tool_tokens,
            "claude_md_tokens": claude_tokens,
            "history_tokens": hist_tokens,
            "input_tokens": total_input,
            "output_tokens": 0,
            "window_limit": self.window_limit,
            "window_utilization_pct": round(utilization * 100.0, 2),
            "compaction_count": self.compaction_count,
        }

    def should_compact(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int,
        topic_shifted: bool = False,
    ) -> Tuple[bool, str]:
        """Evaluate the 3 automatic compaction triggers (Quera Ch. 10 Lesson 04)."""
        utilization = current_tokens / max(1, self.window_limit)
        if topic_shifted:
            return True, "topic_shift_clear"
        if utilization >= self.compaction_threshold:
            return True, f"window_utilization_exceeded ({utilization:.1%} >= {self.compaction_threshold:.0%})"
        if len(messages) >= self.max_turns:
            return True, f"turn_count_exceeded ({len(messages)} >= {self.max_turns})"
        return False, "within_budget"

    def compact_history(
        self,
        messages: List[Dict[str, Any]],
        preserved_state_anchors: Dict[str, Any],
        keep_recent: int = 4,
    ) -> List[Dict[str, Any]]:
        """Compress older turns into a high-signal anchor block while preserving key IDs and recent messages."""
        self.compaction_count += 1
        anchor_summary = (
            "[COMPACTED_SESSION_MEMORY_ANCHOR]\n"
            f"- Active Project: {preserved_state_anchors.get('project_name', 'unknown')}\n"
            f"- Platform & Plan: {preserved_state_anchors.get('platform', 'unknown')} / {preserved_state_anchors.get('plan_id', 'unknown')}\n"
            f"- Latest Source ID: {preserved_state_anchors.get('source_id', 'none')}\n"
            f"- Latest Release ID: {preserved_state_anchors.get('release_id', 'none')}\n"
            f"- Remaining Hackathon Credit (Tomans): {preserved_state_anchors.get('remaining_credit_tomans', 2_000_000)}\n"
            f"- Last RCA Cause: {preserved_state_anchors.get('primary_cause', 'none')}"
        )
        recent_slice = messages[-keep_recent:] if len(messages) > keep_recent else messages
        return [{"role": "system", "content": anchor_summary}] + list(recent_slice)


class JITFileRetriever:
    """4-Step Just-In-Time (JIT) Retrieval Loop (`decide -> glob/grep -> slice read -> synthesize`).

    Prevents Context Rot by inspecting only targeted file slices instead of eager-loading
    entire repositories into the main orchestrator context.
    """

    IGNORED_DIRS = {".git", "node_modules", ".next", "__pycache__", ".venv", "venv", "dist", "build"}

    @classmethod
    def glob_files(cls, root_dir: Path, pattern: str = "*") -> List[str]:
        """Step 2a: Lightweight file tree discovery excluding heavy build artifacts."""
        matches: List[str] = []
        if not root_dir.exists():
            return matches
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in cls.IGNORED_DIRS]
            for fname in filenames:
                if fnmatch.fnmatch(fname, pattern):
                    rel = os.path.relpath(os.path.join(dirpath, fname), root_dir)
                    matches.append(rel)
        return sorted(matches)

    @classmethod
    def grep_pattern(cls, root_dir: Path, regex_pattern: str, max_hits: int = 20) -> List[Dict[str, Any]]:
        """Step 2b: Search for specific symbols/ports/configs across repository files."""
        rx = re.compile(regex_pattern, re.IGNORECASE)
        hits: List[Dict[str, Any]] = []
        for rel_path in cls.glob_files(root_dir, "*"):
            full_path = root_dir / rel_path
            try:
                text = full_path.read_text(encoding="utf-8", errors="ignore")
                for idx, line in enumerate(text.splitlines(), start=1):
                    if rx.search(line):
                        hits.append({"file": rel_path, "line": idx, "snippet": line.strip()[:160]})
                        if len(hits) >= max_hits:
                            return hits
            except Exception:
                continue
        return hits

    @classmethod
    def read_slice(cls, file_path: Path, offset_line: int = 1, limit_lines: int = 60) -> str:
        """Step 3: Read bounded line slice (`offset`/`limit`) to preserve context budget."""
        if not file_path.is_file():
            return ""
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        start = max(0, offset_line - 1)
        end = min(len(lines), start + limit_lines)
        sliced = [f"{i + 1}: {lines[i]}" for i in range(start, end)]
        return "\n".join(sliced)

    @staticmethod
    def update_episodic_memory_file(
        memory_md_path: Path,
        section_header: str,
        bullet_entry: str,
    ) -> None:
        """Append new operational learning or reference ID into the 4-part `MEMORY.md` file."""
        if not memory_md_path.exists():
            return
        content = memory_md_path.read_text(encoding="utf-8")
        if bullet_entry in content:
            return
        if section_header in content:
            parts = content.split(section_header, 1)
            updated = f"{parts[0]}{section_header}\n- {bullet_entry}{parts[1]}"
            memory_md_path.write_text(updated, encoding="utf-8")
        else:
            memory_md_path.write_text(f"{content.rstrip()}\n\n{section_header}\n- {bullet_entry}\n", encoding="utf-8")
