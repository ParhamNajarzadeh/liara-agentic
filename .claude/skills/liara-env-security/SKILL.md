---
name: liara-env-security
description: Use when scanning .env.example templates, injecting production environment variables into Liara via Secret-Blind Vault, or auditing repositories for zero hardcoded API keys.
allowed-tools:
  - liara_config_and_storage
---

# `liara-env-security` — Secret-Blind Environment Configuration & Zero-Hardcoded-Key Skill

## Instructions
1. **Autonomous Template Discovery:** Read only variable key names (`DATABASE_URL`, `REDIS_URL`, `APP_ENV`) from `.env.example` using `liara_config_and_storage(action="scan_env_template")`.
2. **Enforce Secret-Blind Vaulting (Breaking the Lethal Trifecta):** When the user enters sensitive secret values in the frontend UI (`UnifiedZeroFrictionLaunchCard`), route them directly to `SecretBlindVault` (`POST /api/vault/secrets`) so raw values never pass through the LLM context window.
3. **Inject via Liara OpenAPI:** Resolve secret values strictly inside the deterministic HTTP client layer when calling `POST /v1/projects/{id}/update-envs`.
4. **Zero Hardcoded Keys Audit:** Ensure all application code loads `METIS_API_KEY` and `LIARA_API_TOKEN` exclusively from environment variables via `src/core/config.py`.

## Examples
- **User:** «متغیرهای محیطی دیتابیس رو به صورت امن روی پروژه ست کن.»
- **Agent Action:** Scans `.env.example` key names, collects secret values via the Secret-Blind UI input directly into the backend vault, and updates Liara envs after HITL confirmation.

## Constraints
- NEVER ask the user to paste raw production passwords or API tokens in plain chat messages.
- NEVER hardcode any API key (`tpsg-`, `sk-`, `Bearer`) in source files.
