---
name: liara-build-auto-healer
description: Use when a Liara release build fails during deployment (Dockerfile error, missing package in requirements.txt/package.json, TypeScript/Python syntax error, or port mismatch) to automatically patch code via the Coding Agent and redeploy without user copy-pasting.
allowed-tools:
  - liara_release_pipeline
  - liara_sre_observability
---

# `liara-build-auto-healer` — Automated Deploy Agent ↔ Coding Agent Bridge Skill

## Instructions
1. **Detect Build Failure Automatically:** Monitor release status from `POST /v2/projects/{name}/releases` and `GET /v1/projects/{name}/events`.
2. **Sanitize Build Logs:** Pass the raw build error log through `LogSanitizer.sanitize_and_wrap` (`<untrusted_log_data>`) and System 1 anomaly scanner (`is_build_error_fixable_by_coding_agent`).
3. **Issue 4-Part Work Order Contract:** Dispatch a structured SITC Work Order Contract (`## INPUT`, `## OUTPUT`, `## ACCEPTANCE`, `## BOUNDARIES`) to `code-remediator` (or connected Claude Code / OpenCode / DeepSeek Harness `dsh` via MCP).
4. **Apply Patch & Redeploy Autonomously:** Apply the unified diff to `liara.json`, `Dockerfile`, or dependency manifests, repackage `.tar.gz`, upload a new `sourceID` to `POST /v2/projects/{name}/sources`, and publish a new release (up to 2 automatic attempts).
5. **Render Live Bridge UI:** Display `AutomatedBuildHealerBridgeCard` showing the live handoff, unified diff preview, and final `RUNNING` state.

## Examples
- **Scenario:** Release `rel-01` fails because `liara.json` specifies port `3000` while FastAPI binds to `8000` and `requirements.txt` has a broken package pin.
- **Agent Action:** Automatically invokes `liara_release_pipeline(action="auto_heal_build_loop")`, patches `liara.json` and `requirements.txt`, uploads new `.tar.gz`, and reaches `RUNNING` with zero manual copy-paste.

## Constraints
- NEVER ask the user to manually copy-paste build logs from Liara to their IDE/Coding Agent.
- NEVER exceed `max_auto_build_heal_attempts = 2` without escalating to the user.
- NEVER modify user database contents or upgrade billing plans inside the build-healing loop.
