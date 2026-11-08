---
name: liara-day2-rollback
description: Use when managing Day-2 production operations on Liara, including Zero-Downtime deployments, Read-Only mode, persistent Disks, FTP backups, and instant Rollback to a healthy releaseID.
allowed-tools:
  - liara_release_pipeline
  - liara_config_and_storage
  - liara_sre_observability
---

# `liara-day2-rollback` — Day-2 Operations, Zero-Downtime & Instant Rollback Skill

## Instructions
1. **Pre-Release Safety Checks:** Verify `zero-downtime` status (`POST /v1/projects/{id}/zero-downtime`) and persistent disk health (`GET /v1/projects/{id}/disks`) before publishing a Day-2 release.
2. **Release History Inspection:** Call `liara_release_pipeline(action="list_releases")` (`GET /v1/projects/{name}/releases`) to identify the last known healthy `releaseID` (e.g., `rel-v101-healthy`).
3. **HITL-Gated Instant Rollback & Time Travel:** When a newly deployed release causes production degradation, present `HITLActionApprovalGateModal` with the target healthy `releaseID`. Upon approval, redeploy the healthy release and restore the corresponding LangGraph checkpoint snapshot.
4. **Post-Rollback Verification:** Poll `GET /v1/projects/{name}/applets` and `GET /v1/projects/{name}/events` to confirm zero-downtime traffic restoration.

## Examples
- **User:** «نسخه جدیدی که دیپلوی شد مشکل داره، سریع به آخرین ریلیز سالم قبلی برگرد (Rollback).»
- **Agent Action:** Lists releases, selects `rel-v101-healthy`, requests production HITL confirmation, executes rollback, and verifies `HTTP 200` health.

## Constraints
- ALWAYS require user confirmation (`interrupt()`) before rolling back or modifying live production settings (`read-only`, `disks`).
- NEVER delete persistent disks (`DELETE` is hard-blocked in `GovernanceEngine`).
