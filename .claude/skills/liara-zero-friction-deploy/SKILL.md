---
name: liara-zero-friction-deploy
description: Use when setting up or deploying an application on Liara PaaS for the first time to collapse the traditional 5-step manual panel flow into a single-click Zero-Friction launch card.
allowed-tools:
  - liara_app_lifecycle
  - liara_release_pipeline
  - liara_config_and_storage
---

# `liara-zero-friction-deploy` — 1-Step Zero-Friction Deployment Skill

## Instructions
1. **Autonomous Stack & Port Detection:** Inspect `package.json`, `requirements.txt`, `pyproject.toml`, or `Dockerfile` via `repo-scanner` to identify the platform (`nextjs`, `node`, `python`, `django`, `fastapi`, `docker`, `static`) and default port without asking the user.
2. **Autonomous Secret-Blind `.env.example` Scan:** Call `liara_config_and_storage(action="scan_env_template")` to extract required variable key names without exposing raw secrets to the LLM.
3. **Autonomous Source Packaging & Upload:** Generate `liara.json`, package the project into `.tar.gz` (excluding `.git`, `node_modules`, `.env`), and upload to `POST /v2/projects/{name}/sources` to obtain `sourceID`.
4. **Economical Plan Estimation (2,000,000 Tomans Guard):** Call `liara_app_lifecycle(action="estimate_optimal_plan")` to select the most cost-effective Liara plan (`ir-mini` or `ir-standard-1g`) that keeps the app online through judging.
5. **Single Consolidated Financial HITL Gate:** Render `UnifiedZeroFrictionLaunchCard` and pause at `interrupt()` ONCE so the user can approve (or edit plan/port) before `POST /v1/projects` and `POST /v2/projects/{name}/releases` execute.

## Examples
- **User:** «پروژه پایتون من رو روی لیارا دیپلوی کن.»
- **Agent Action:** Runs steps 1–4 silently with zero popups, then presents `UnifiedZeroFrictionLaunchCard` for a single financial confirmation click.

## Constraints
- NEVER ask the user separate confirmation questions for framework detection, `.env.example` reading, `liara.json` creation, or `.tar.gz` upload (Anti-Fatigue HITL).
- ALWAYS pause at `interrupt()` before creating a paid Liara project that deducts from the 2,000,000 Tomans hackathon credit.
