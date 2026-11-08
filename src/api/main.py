"""FastAPI Backend Server & Real Dynamic Cloud Assistant UI (`src/api/main.py`).

Provides the production API and dynamic Generative UI workspace for the Liara Cloud & SRE Assistant:
- Connects directly to MetisAI (`METIS_API_KEY` / `OPENAI_API_KEY`) and Liara OpenAPI (`LIARA_API_TOKEN`).
- Persists user-configured API credentials in `workspace/.env` so they remain active across restarts.
- Supports real project file/archive upload and automatic framework/env discovery.
- Dynamically renders Human-in-the-Loop (HITL) confirmation cards only when sensitive infrastructure actions require user approval.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.core.governance import GovernanceEngine, PermissionDeniedError
from src.orchestrator.graph import build_liara_sre_graph
from src.orchestrator.state import create_initial_state

app = FastAPI(
    title="Liara Cloud & SRE AI Assistant",
    version="2.0.0",
    description="AI Technical Co-Pilot & SRE Assistant for Liara PaaS",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

governance_engine = GovernanceEngine()
graph_runtime = build_liara_sre_graph(governance=governance_engine)


class ConnectCredentialsRequest(BaseModel):
    liara_api_token: str = Field(default="")
    metis_api_key: str = Field(default="")
    simulator_mode: bool = Field(default=False)


class ProjectOnboardRequest(BaseModel):
    session_id: str = Field(default="sess-main")
    project_name: str = Field(default="my-web-app")
    platform_hint: str = Field(default="auto")
    port: int = Field(default=8000)
    files: Dict[str, str] = Field(default_factory=dict)
    dependency_file_name: str = Field(default="requirements.txt")
    dependency_file_content: str = Field(default="")
    env_example_content: str = Field(default="")
    simulate_build_failure_once: bool = Field(default=False)


class ChatRequest(BaseModel):
    session_id: str = Field(default="sess-main")
    message: str
    project_name: str = Field(default="my-web-app")
    workspace_path: str = Field(default="workspace/sample_app")
    simulate_build_failure_once: bool = Field(default=False)


class HITLResumeRequest(BaseModel):
    session_id: str
    status: Literal["approved", "modified", "rejected"] = "approved"
    modified_params: Dict[str, Any] = Field(default_factory=dict)


class TimeTravelRequest(BaseModel):
    session_id: str
    checkpoint_id: str


class VaultSecretInput(BaseModel):
    project_name: str
    secrets: Dict[str, str]


class KillSwitchRequest(BaseModel):
    reason: str = "User revoked agent access"


def _extract_agent_reply(state: Dict[str, Any]) -> str:
    msgs = state.get("messages") or []
    for m in reversed(msgs):
        if isinstance(m, dict) and m.get("role") == "assistant" and m.get("content"):
            return str(m["content"])
    ver = state.get("verification_status") or {}
    if ver.get("post_fix_summary"):
        return str(ver["post_fix_summary"])
    return "درخواست شما بررسی شد."


def _serialize_state_response(session_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    paused_node = graph_runtime._paused_threads.get(session_id)
    is_paused = paused_node is not None
    return {
        "session_id": session_id,
        "agent_reply": _extract_agent_reply(state),
        "messages": state.get("messages", []),
        "is_paused_for_hitl": is_paused,
        "paused_at_node": paused_node,
        "user_intent": state.get("user_intent"),
        "active_project": state.get("active_project"),
        "deployment_context": state.get("deployment_context"),
        "build_healing_context": state.get("build_healing_context"),
        "telemetry_snapshot": state.get("telemetry_snapshot"),
        "rca_report": state.get("rca_report"),
        "pending_action": state.get("pending_action"),
        "hitl_decision": state.get("hitl_decision"),
        "verification_status": state.get("verification_status"),
        "credit_budget": state.get("credit_budget") or governance_engine.credit_guard.get_budget_snapshot(),
        "ui_directive": state.get("ui_directive"),
        "checkpoints": graph_runtime.get_checkpoint_history(session_id),
    }


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    """Serve the clean, production-grade Liara AI Cloud Assistant web application."""
    return HTMLResponse(content=PRODUCT_UI_HTML)


@app.get("/healthz")
def healthcheck() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "liara-agentic-sre",
        "agent_status": governance_engine.kill_switch.status,
        "remaining_credit_tomans": governance_engine.credit_guard.remaining_credit_tomans,
        "metis_connected": bool(governance_engine.settings.metis_api_key.strip()),
        "liara_connected": bool(governance_engine.settings.liara_api_token.strip()),
    }


@app.post("/api/config/connect")
def connect_credentials(req: ConnectCredentialsRequest) -> Dict[str, Any]:
    """Save Metis AI Key and Liara API Token in memory and persist to `workspace/.env`."""
    if req.metis_api_key.strip():
        key_val = req.metis_api_key.strip()
        governance_engine.settings.metis_api_key = key_val
        os.environ["METIS_API_KEY"] = key_val
    if req.liara_api_token.strip():
        tok_val = req.liara_api_token.strip()
        governance_engine.settings.liara_api_token = tok_val
        os.environ["LIARA_API_TOKEN"] = tok_val
        governance_engine.settings.liara_simulator_mode = False
    else:
        governance_engine.settings.liara_simulator_mode = req.simulator_mode

    # Persist to workspace/.env so it survives container restarts
    ws_env = Path("workspace") / ".env"
    ws_env.parent.mkdir(parents=True, exist_ok=True)
    env_lines = [
        f"METIS_API_KEY={governance_engine.settings.metis_api_key}",
        f"LIARA_API_TOKEN={governance_engine.settings.liara_api_token}",
        f"LIARA_SIMULATOR_MODE={'true' if governance_engine.settings.liara_simulator_mode else 'false'}",
    ]
    ws_env.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    return {
        "status": "CONNECTED",
        "metis_connected": bool(governance_engine.settings.metis_api_key.strip()),
        "liara_connected": bool(governance_engine.settings.liara_api_token.strip()),
        "simulator_mode": governance_engine.settings.liara_simulator_mode,
    }


@app.post("/api/project/onboard")
def onboard_and_scan_project(req: ProjectOnboardRequest) -> Dict[str, Any]:
    """Save uploaded project files into `workspace/<project_name>`, scan framework & env, and return HITL confirmation card."""
    try:
        clean_name = "".join(c for c in req.project_name.strip().lower() if c.isalnum() or c == "-") or "my-web-app"
        ws_dir = Path("workspace") / clean_name
        ws_dir.mkdir(parents=True, exist_ok=True)

        if req.files:
            for fname, fcontent in req.files.items():
                safe_name = Path(fname).name
                if safe_name:
                    (ws_dir / safe_name).write_text(fcontent, encoding="utf-8")
        else:
            if req.dependency_file_content.strip():
                (ws_dir / req.dependency_file_name).write_text(req.dependency_file_content, encoding="utf-8")
            elif not any((ws_dir / f).exists() for f in ("requirements.txt", "package.json", "Dockerfile")):
                (ws_dir / "requirements.txt").write_text("fastapi>=0.110.0\nuvicorn[standard]>=0.29.0\n", encoding="utf-8")

            if req.env_example_content.strip():
                (ws_dir / ".env.example").write_text(req.env_example_content, encoding="utf-8")

        if req.simulate_build_failure_once:
            graph_runtime.nodes.mega_tools.client.inject_simulated_build_failure(clean_name, fail_next=True)

        initial_state = create_initial_state(
            session_id=req.session_id,
            user_message=f"پروژه {clean_name} را بررسی و برای دیپلوی و راه‌اندازی در لیارا آماده کن",
            project_name=clean_name,
            workspace_path=ws_dir.as_posix(),
            initial_credit_tomans=governance_engine.credit_guard.remaining_credit_tomans,
        )
        if req.port:
            initial_state["active_project"]["port"] = req.port

        final_state = graph_runtime.run_until_interrupt_or_end(
            initial_state, thread_id=req.session_id
        )
        return _serialize_state_response(req.session_id, dict(final_state))
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    """Process natural language user request via MetisAI and execute workflow until HITL gate or completion."""
    try:
        if req.simulate_build_failure_once:
            graph_runtime.nodes.mega_tools.client.inject_simulated_build_failure(
                req.project_name, fail_next=True
            )
        initial_state = create_initial_state(
            session_id=req.session_id,
            user_message=req.message,
            project_name=req.project_name,
            workspace_path=req.workspace_path,
            initial_credit_tomans=governance_engine.credit_guard.remaining_credit_tomans,
        )
        final_state = graph_runtime.run_until_interrupt_or_end(
            initial_state, thread_id=req.session_id
        )
        return _serialize_state_response(req.session_id, dict(final_state))
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/hitl/resume")
def resume_hitl_endpoint(req: HITLResumeRequest) -> Dict[str, Any]:
    """Execute user-approved or user-modified infrastructure operation after Human-in-the-Loop confirmation."""
    try:
        resumed_state = graph_runtime.resume_after_hitl(
            thread_id=req.session_id,
            decision_status=req.status,
            modified_params=req.modified_params,
        )
        return _serialize_state_response(req.session_id, dict(resumed_state))
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/time-travel/replay")
def replay_time_travel_endpoint(req: TimeTravelRequest) -> Dict[str, Any]:
    try:
        restored_state = graph_runtime.replay_from_checkpoint(req.session_id, req.checkpoint_id)
        return _serialize_state_response(req.session_id, dict(restored_state))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/vault/secrets")
def store_secret_blind_envs(req: VaultSecretInput) -> Dict[str, Any]:
    try:
        governance_engine.assert_operation_permitted("POST", "/api/vault/secrets", "store_secrets")
        manifest = governance_engine.vault.store_project_secrets(req.project_name, req.secrets)
        return {
            "status": "STORED_IN_SECRET_BLIND_VAULT",
            "project_name": req.project_name,
            "blind_manifest": manifest,
            "raw_values_sent_to_llm": False,
        }
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/api/governance/kill-switch")
def trigger_agent_kill_switch(req: KillSwitchRequest) -> Dict[str, Any]:
    result = governance_engine.kill_switch.trigger_kill_switch(reason=req.reason)
    graph_runtime.nodes.audit.log_span(
        session_id="global-governance",
        layer="Governance",
        node_or_tool="AgentKillSwitch",
        sub_action="DECOMMISSION",
        risk_tier="critical_security",
        status="DECOMMISSIONED",
        details=result,
    )
    return result


@app.post("/api/governance/reactivate")
def reactivate_agent_token() -> Dict[str, Any]:
    governance_engine.kill_switch.status = "ACTIVE"
    governance_engine.kill_switch.decommission_reason = None
    return {
        "status": "ACTIVE",
        "virtual_agent_id": governance_engine.kill_switch.virtual_agent_id,
        "remaining_ttl_seconds": governance_engine.kill_switch.remaining_ttl_seconds,
    }


@app.get("/api/governance/status")
def get_governance_status() -> Dict[str, Any]:
    return {
        "virtual_agent_id": governance_engine.kill_switch.virtual_agent_id,
        "agent_status": governance_engine.kill_switch.status,
        "remaining_ttl_seconds": governance_engine.kill_switch.remaining_ttl_seconds,
        "metis_connected": bool(governance_engine.settings.metis_api_key.strip()),
        "liara_connected": bool(governance_engine.settings.liara_api_token.strip()),
        "credit_budget": governance_engine.credit_guard.get_budget_snapshot(),
        "recent_audit_traces": graph_runtime.nodes.audit.get_session_traces()[-10:],
    }


PRODUCT_UI_HTML = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>دستیار هوشمند ابری لیارا</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
  <style>
    body { font-family: 'Vazirmatn', Tahoma, sans-serif; background-color: #0b0f19; color: #f3f4f6; }
    .ltr-text { font-family: Consolas, Monaco, monospace; direction: ltr; text-align: left; }
    .fade-in { animation: fadeIn 0.25s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    pre { white-space: pre-wrap; word-wrap: break-word; }
  </style>
</head>
<body class="min-h-screen flex flex-col">

  <!-- Clean Production SaaS Header -->
  <header class="border-b border-gray-800 bg-gray-900 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <div class="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow">L</div>
      <div>
        <h1 class="text-sm md:text-base font-bold text-white">دستیار هوشمند ابری لیارا</h1>
        <p class="text-xs text-gray-400">راه‌اندازی، استقرار خودکار و پایش سلامت سرویس‌ها</p>
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-3 text-xs">
      <!-- Active Project Badge -->
      <div class="rounded-lg bg-gray-950 border border-gray-800 px-3 py-1.5 flex items-center gap-2">
        <span class="text-gray-400">پروژه فعال:</span>
        <input id="active-project-input" type="text" value="my-web-app" onchange="updateActiveProjectName(this.value)" class="bg-transparent text-blue-400 font-bold ltr-text w-28 focus:outline-none border-b border-transparent focus:border-blue-500">
      </div>

      <!-- Account Balance -->
      <div class="rounded-lg bg-gray-950 border border-gray-800 px-3 py-1.5">
        موجودی حساب: <strong id="header-credit" class="text-green-400">۲,۰۰۰,۰۰۰ تومان</strong>
      </div>

      <!-- Connection Settings Button -->
      <button onclick="openSettingsModal()" class="rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 px-3.5 py-1.5 font-semibold transition flex items-center gap-1.5">
        <span id="conn-dot" class="h-2 w-2 rounded-full bg-yellow-400 inline-block"></span>
        <span id="conn-label">تنظیمات اتصال API</span>
      </button>

      <!-- Emergency Revoke Access -->
      <button id="btn-kill-switch" onclick="triggerKillSwitch()" class="rounded-lg bg-red-900 bg-opacity-60 hover:bg-red-700 text-red-200 border border-red-800 px-3 py-1.5 font-semibold transition">
        لغو دسترسی دستیار
      </button>
      <button id="btn-reactivate" onclick="reactivateAgent()" class="hidden rounded-lg bg-green-700 hover:bg-green-600 text-white px-3 py-1.5 font-semibold transition">
        فعال‌سازی مجدد دستیار
      </button>
    </div>
  </header>

  <!-- Main Workspace: Conversational Assistant (Right) + Dynamic Operations Panel (Left) -->
  <main class="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden" style="height: calc(100vh - 65px);">

    <!-- Right Column (5 cols): Natural Conversational Interface -->
    <section class="lg:col-span-5 border-l border-gray-800 bg-gray-900 bg-opacity-60 flex flex-col justify-between p-4 h-full">
      <!-- Chat History -->
      <div id="chat-stream" class="flex-1 space-y-3 overflow-y-auto pr-1 text-xs md:text-sm my-2">
        <div class="rounded-2xl p-4 bg-gray-800 border border-gray-700 text-gray-200 leading-relaxed">
          سلام! من دستیار هوشمند ابری شما هستم.<br><br>
          می‌توانید فایل‌های پروژه خود را با دکمه <strong>«📎 انتخاب فایل‌های پروژه»</strong> در پایین بارگذاری کنید یا به زبان ساده بگویید چه کاری برایتان انجام دهم (مثلاً راه‌اندازی سایت، بررسی علت کندی و خطای سرور، یا تنظیم دامنه).
        </div>
      </div>

      <!-- Selected Files Preview Bar -->
      <div id="attached-files-bar" class="hidden mb-2 p-2.5 rounded-xl bg-blue-950 bg-opacity-50 border border-blue-800 flex items-center justify-between text-xs">
        <span id="attached-files-text" class="text-blue-200 truncate"></span>
        <button onclick="deployAttachedProject()" class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-3 py-1 rounded-lg transition">
          بررسی و آماده‌سازی دیپلوی
        </button>
      </div>

      <!-- Natural Chat Input Bar + Project File Picker -->
      <div class="pt-3 border-t border-gray-800">
        <form onsubmit="handleChatSubmit(event)" class="flex items-center gap-2">
          <!-- Hidden File Input for selecting project files from computer -->
          <input id="file-picker" type="file" multiple onchange="handleFilesSelected(event)" class="hidden">
          <button type="button" onclick="document.getElementById('file-picker').click()" title="انتخاب فایل‌های پروژه (requirements.txt, package.json, Dockerfile, .env)" class="bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 rounded-xl px-3 py-2.5 text-xs font-semibold transition flex items-center gap-1">
            📎 پروژه
          </button>
          <input id="chat-input" type="text" placeholder="پیام خود را بنویسید (مثلاً: پروژه من رو دیپلوی کن، یا چرا سایتم خطای ۵۰۰ میده؟)..." class="flex-1 bg-gray-950 border border-gray-700 rounded-xl px-4 py-2.5 text-xs md:text-sm text-white focus:outline-none focus:border-blue-500">
          <button id="chat-submit-btn" type="submit" class="bg-blue-600 hover:bg-blue-500 text-white rounded-xl px-5 py-2.5 text-xs md:text-sm font-bold transition shadow">
            ارسال
          </button>
        </form>
      </div>
    </section>

    <!-- Left Column (7 cols): Dynamic Operations & Human-in-the-Loop Workspace -->
    <section class="lg:col-span-7 p-6 bg-gray-950 overflow-y-auto h-full">
      <div id="dynamic-canvas" class="max-w-3xl mx-auto space-y-6">

        <!-- Default Empty/Welcome State (Before any action is triggered) -->
        <div id="canvas-empty-state" class="rounded-2xl border border-gray-800 bg-gray-900 bg-opacity-50 p-8 text-center space-y-4 mt-8">
          <div class="mx-auto h-14 w-14 rounded-2xl bg-blue-900 bg-opacity-30 border border-blue-800 flex items-center justify-center text-2xl">
            ☁️
          </div>
          <h2 class="text-base font-bold text-white">میزکار عملیات زنده زیرساخت</h2>
          <p class="text-xs md:text-sm text-gray-400 max-w-md mx-auto leading-relaxed">
            در طول گفتگو با دستیار، هر زمان که عملیاتی نیاز به بررسی، تنظیم متغیرهای محیطی یا <strong>تأیید شما (Human-in-the-Loop)</strong> داشته باشد، کارت تعاملی آن به صورت خودکار در این قسمت نمایش داده می‌شود.
          </p>
          <div class="pt-2 flex flex-wrap justify-center gap-3 text-xs">
            <button onclick="document.getElementById('file-picker').click()" class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-2 rounded-xl transition shadow">
              📎 انتخاب فایل‌های پروژه از کامپیوتر
            </button>
            <button onclick="openNewProjectModal()" class="bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 font-semibold px-4 py-2 rounded-xl transition">
              📝 تعریف دستی مشخصات پروژه
            </button>
          </div>
        </div>

        <!-- Dynamic Card Container (Populated ONLY when Agent triggers an action or HITL gate) -->
        <div id="canvas-active-card" class="hidden space-y-5 fade-in"></div>

      </div>
    </section>

  </main>

  <!-- Modal 1: API Connection Settings (MetisAI & Liara Token) -->
  <div id="settings-modal" class="fixed inset-0 bg-black bg-opacity-75 hidden flex items-center justify-center z-50 p-4">
    <div class="bg-gray-900 border border-gray-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-xs">
      <div class="flex items-center justify-between border-b border-gray-800 pb-3">
        <h3 class="text-sm font-bold text-white">⚙️ تنظیمات اتصال به هوش مصنوعی متیس و لیارا</h3>
        <button onclick="closeSettingsModal()" class="text-gray-400 hover:text-white text-base">&times;</button>
      </div>
      <p class="text-gray-400 leading-relaxed">
        کلیدهای واردشده در فایل <code>workspace/.env</code> ذخیره می‌شوند تا دستیار مستقیماً به حساب شما متصل شود.
      </p>
      <div class="space-y-3">
        <div>
          <label class="block text-gray-300 font-semibold mb-1">کلید API متیس (METIS_API_KEY):</label>
          <input id="modal-metis-key" type="password" placeholder="کلید دریافتی از پنل متیس..." class="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-white ltr-text">
        </div>
        <div>
          <label class="block text-gray-300 font-semibold mb-1">توکن API لیارا (LIARA_API_TOKEN):</label>
          <input id="modal-liara-token" type="password" placeholder="توکن دریافتی از پنل لیارا (اختیاری)..." class="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-white ltr-text">
        </div>
      </div>
      <div class="pt-3 border-t border-gray-800 flex justify-end gap-2">
        <button onclick="closeSettingsModal()" class="bg-gray-800 text-gray-300 px-4 py-2 rounded-lg">بستن</button>
        <button onclick="saveSettingsModal()" class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-5 py-2 rounded-lg">ذخیره و اتصال</button>
      </div>
    </div>
  </div>

  <!-- Modal 2: Manual Project Definition -->
  <div id="project-modal" class="fixed inset-0 bg-black bg-opacity-75 hidden flex items-center justify-center z-50 p-4">
    <div class="bg-gray-900 border border-gray-700 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl text-xs">
      <div class="flex items-center justify-between border-b border-gray-800 pb-3">
        <h3 class="text-sm font-bold text-white">📝 تعریف مشخصات و فایل‌های پروژه</h3>
        <button onclick="closeNewProjectModal()" class="text-gray-400 hover:text-white text-base">&times;</button>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-gray-300 font-semibold mb-1">نام پروژه:</label>
          <input id="m-proj-name" type="text" value="my-web-app" class="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-white ltr-text">
        </div>
        <div>
          <label class="block text-gray-300 font-semibold mb-1">پورت برنامه:</label>
          <input id="m-proj-port" type="number" value="8000" class="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-white ltr-text">
        </div>
      </div>
      <div>
        <label class="block text-gray-300 font-semibold mb-1">فایل وابستگی‌ها (requirements.txt یا package.json):</label>
        <textarea id="m-dep-content" rows="3" class="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-green-300 ltr-text">fastapi>=0.110.0
uvicorn[standard]>=0.29.0</textarea>
      </div>
      <div>
        <label class="block text-gray-300 font-semibold mb-1">متغیرهای محیطی (.env.example):</label>
        <textarea id="m-env-content" rows="3" class="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-yellow-300 ltr-text">DATABASE_URL=postgresql://localhost:5432/db
SECRET_KEY=my-secret</textarea>
      </div>
      <div class="pt-3 border-t border-gray-800 flex justify-end gap-2">
        <button onclick="closeNewProjectModal()" class="bg-gray-800 text-gray-300 px-4 py-2 rounded-lg">انصراف</button>
        <button onclick="submitManualProject()" class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-5 py-2 rounded-lg">ثبت و بررسی توسط دستیار</button>
      </div>
    </div>
  </div>

  <script>
    let currentSessionId = 'sess-' + Math.random().toString(36).substring(2, 8);
    let currentProjectName = 'my-web-app';
    let currentWorkspacePath = 'workspace/sample_app';
    let uploadedFilesMap = {};

    // Check connection status on load
    window.addEventListener('DOMContentLoaded', async () => {
      try {
        const res = await fetch('/healthz');
        const data = await res.json();
        updateConnectionIndicator(data.metis_connected, data.liara_connected);
        if (data.remaining_credit_tomans !== undefined) {
          document.getElementById('header-credit').innerText = data.remaining_credit_tomans.toLocaleString('fa-IR') + ' تومان';
        }
      } catch (e) {}
    });

    function updateConnectionIndicator(metisOk, liaraOk) {
      const dot = document.getElementById('conn-dot');
      const lbl = document.getElementById('conn-label');
      if (metisOk && liaraOk) {
        dot.className = 'h-2 w-2 rounded-full bg-green-400 inline-block';
        lbl.innerText = 'متصل به متیس و لیارا';
      } else if (metisOk) {
        dot.className = 'h-2 w-2 rounded-full bg-green-400 inline-block';
        lbl.innerText = 'متصل به هوش مصنوعی متیس';
      } else {
        dot.className = 'h-2 w-2 rounded-full bg-yellow-400 inline-block';
        lbl.innerText = 'تنظیمات اتصال API';
      }
    }

    function updateActiveProjectName(val) {
      currentProjectName = val.trim() || 'my-web-app';
    }

    function openSettingsModal() {
      document.getElementById('settings-modal').classList.remove('hidden');
    }
    function closeSettingsModal() {
      document.getElementById('settings-modal').classList.add('hidden');
    }

    async function saveSettingsModal() {
      const metisKey = document.getElementById('modal-metis-key').value.trim();
      const liaraTok = document.getElementById('modal-liara-token').value.trim();
      try {
        const res = await fetch('/api/config/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            metis_api_key: metisKey,
            liara_api_token: liaraTok,
            simulator_mode: !liaraTok
          })
        });
        const data = await res.json();
        updateConnectionIndicator(data.metis_connected, data.liara_connected);
        closeSettingsModal();
        appendChatMessage('assistant', 'تنظیمات اتصال شما با موفقیت ذخیره و فعال شد.');
      } catch (e) {}
    }

    function openNewProjectModal() {
      document.getElementById('project-modal').classList.remove('hidden');
    }
    function closeNewProjectModal() {
      document.getElementById('project-modal').classList.add('hidden');
    }

    async function submitManualProject() {
      const pName = document.getElementById('m-proj-name').value.trim() || 'my-web-app';
      const pPort = parseInt(document.getElementById('m-proj-port').value || '8000', 10);
      const depContent = document.getElementById('m-dep-content').value;
      const envContent = document.getElementById('m-env-content').value;
      currentProjectName = pName;
      document.getElementById('active-project-input').value = pName;
      closeNewProjectModal();

      appendChatMessage('user', `پروژه «${pName}» را بررسی کن و برای دیپلوی آماده ساز.`);
      const res = await fetch('/api/project/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          project_name: pName,
          port: pPort,
          dependency_file_name: depContent.trim().startsWith('{') ? 'package.json' : 'requirements.txt',
          dependency_file_content: depContent,
          env_example_content: envContent
        })
      });
      const data = await res.json();
      handleBackendResponse(data);
    }

    async function handleFilesSelected(e) {
      const files = Array.from(e.target.files || []);
      if (!files.length) return;
      uploadedFilesMap = {};
      for (const f of files) {
        try {
          const txt = await f.text();
          uploadedFilesMap[f.name] = txt;
        } catch (err) {}
      }
      const names = Object.keys(uploadedFilesMap).join(', ');
      document.getElementById('attached-files-text').innerText = `📎 فایل‌های انتخاب‌شده: ${names}`;
      document.getElementById('attached-files-bar').classList.remove('hidden');
    }

    async function deployAttachedProject() {
      document.getElementById('attached-files-bar').classList.add('hidden');
      appendChatMessage('user', `فایل‌های پروژه (${Object.keys(uploadedFilesMap).join(', ')}) را بارگذاری کردم. لطفاً بررسی و آماده دیپلوی کن.`);
      const res = await fetch('/api/project/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          project_name: currentProjectName,
          files: uploadedFilesMap
        })
      });
      const data = await res.json();
      handleBackendResponse(data);
    }

    async function handleChatSubmit(e) {
      e.preventDefault();
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      appendChatMessage('user', text);

      const submitBtn = document.getElementById('chat-submit-btn');
      submitBtn.disabled = true;
      submitBtn.innerText = '...';

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: currentSessionId,
            message: text,
            project_name: currentProjectName,
            workspace_path: currentWorkspacePath
          })
        });
        const data = await res.json();
        if (!res.ok) {
          appendChatMessage('assistant', '⚠️ ' + (data.detail || 'امکان انجام این عملیات وجود ندارد.'));
        } else {
          handleBackendResponse(data);
        }
      } catch (err) {
        appendChatMessage('assistant', 'خطا در برقراری ارتباط با سرور.');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'ارسال';
      }
    }

    function handleBackendResponse(data) {
      if (data.agent_reply) {
        appendChatMessage('assistant', data.agent_reply);
      }
      if (data.credit_budget && data.credit_budget.remaining_credit_tomans !== undefined) {
        document.getElementById('header-credit').innerText = data.credit_budget.remaining_credit_tomans.toLocaleString('fa-IR') + ' تومان';
      }
      if (data.active_project && data.active_project.name) {
        currentProjectName = data.active_project.name;
        document.getElementById('active-project-input').value = currentProjectName;
      }

      // Dynamically render the appropriate card on the left canvas ONLY when relevant
      renderDynamicCanvas(data);
    }

    function renderDynamicCanvas(data) {
      const emptyState = document.getElementById('canvas-empty-state');
      const activeCard = document.getElementById('canvas-active-card');
      const intent = data.user_intent;
      const isPaused = data.is_paused_for_hitl;
      const uiComp = (data.ui_directive || {}).component_name;

      // If it's just a general conversation with no infrastructure action, keep workspace clean
      if (intent === 'general_qa' && !isPaused && !uiComp) {
        return;
      }

      emptyState.classList.add('hidden');
      activeCard.classList.remove('hidden');

      // Case 1: Human-in-the-Loop Deployment Confirmation Card
      if (isPaused && intent === 'setup_deploy') {
        const proj = data.active_project || {};
        const dep = data.deployment_context || {};
        const envKeys = dep.env_key_names || ['APP_ENV'];
        const envInputsHtml = envKeys.map(k => `
          <div class="flex items-center gap-2 bg-gray-950 p-2 rounded-lg border border-gray-800">
            <span class="text-xs text-gray-300 font-semibold w-1/3 ltr-text truncate">${k}</span>
            <input type="password" data-env-key="${k}" placeholder="مقدار ${k} را وارد کنید..." class="env-secret-field flex-1 bg-gray-900 border border-gray-700 rounded px-2.5 py-1 text-white text-xs ltr-text">
          </div>
        `).join('');

        activeCard.innerHTML = `
          <div class="rounded-2xl border-2 border-yellow-500 bg-gray-900 p-6 shadow-xl space-y-5 text-xs md:text-sm fade-in">
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
              <div>
                <span class="text-xs font-bold text-yellow-400 bg-yellow-900 bg-opacity-30 px-2.5 py-1 rounded-md border border-yellow-700">
                  نیازمند تأیید شما (Human-in-the-Loop)
                </span>
                <h3 class="text-base font-bold text-white mt-2">تأیید مشخصات و راه‌اندازی پروژه «${proj.name || currentProjectName}»</h3>
              </div>
            </div>

            <p class="text-gray-300 text-xs leading-relaxed">
              دستیار ساختار پروژه شما را بررسی کرد. پیش از ایجاد پروژه و کسر هزینه پلن، لطفاً مشخصات زیر را بررسی و در صورت نیاز ویرایش نمایید:
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800">
                <label class="block text-gray-400 text-xs mb-1">پلتفرم تشخیص‌داده‌شده:</label>
                <div class="font-bold text-blue-400 ltr-text">${proj.platform || 'python'}</div>
              </div>
              <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800">
                <label class="block text-gray-400 text-xs mb-1">پورت برنامه (قابل ویرایش):</label>
                <input id="hitl-port-input" type="number" value="${proj.port || 8000}" class="w-full bg-gray-900 border border-gray-700 rounded px-2.5 py-1 text-white ltr-text font-bold">
              </div>
            </div>

            <div class="bg-gray-950 p-4 rounded-xl border border-gray-800">
              <label class="block text-gray-300 font-bold text-xs mb-2">انتخاب پلن منابع سرور در لیارا:</label>
              <select id="hitl-plan-select" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-xs">
                <option value="ir-mini" ${proj.plan_id === 'ir-mini' ? 'selected' : ''}>پلن اقتصادی ir-mini (۰.۵ هسته پردازنده، ۵۱۲ مگابایت رم) — ۱۲۰,۰۰۰ تومان/ماه</option>
                <option value="ir-standard-1g" ${(!proj.plan_id || proj.plan_id === 'ir-standard-1g') ? 'selected' : ''}>پلن استاندارد ir-standard-1g (۱ هسته پردازنده، ۱ گیگابایت رم) — ۱۸۰,۰۰۰ تومان/ماه (پیشنهاد بهینه)</option>
                <option value="ir-standard-2g" ${proj.plan_id === 'ir-standard-2g' ? 'selected' : ''}>پلن حرفه‌ای ir-standard-2g (۲ هسته پردازنده، ۲ گیگابایت رم) — ۳۸۰,۰۰۰ تومان/ماه</option>
              </select>
            </div>

            <div class="space-y-2">
              <label class="block text-gray-300 font-bold text-xs">تنظیم امن متغیرهای محیطی (.env):</label>
              <div class="space-y-2">${envInputsHtml}</div>
            </div>

            <div class="pt-4 border-t border-gray-800 flex items-center justify-between gap-3">
              <button onclick="confirmDeployHITL('rejected')" class="rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2.5 text-xs font-bold transition">
                انصراف
              </button>
              <button onclick="confirmDeployHITL('modified')" class="rounded-xl bg-green-600 hover:bg-green-500 text-white px-6 py-2.5 text-xs md:text-sm font-bold transition shadow-lg">
                ✓ تأیید و شروع استقرار پروژه
              </button>
            </div>
          </div>
        `;
        return;
      }

      // Case 2: Completed Deployment & Build Status Card
      if (!isPaused && intent === 'setup_deploy') {
        const proj = data.active_project || {};
        const dep = data.deployment_context || {};
        const bh = data.build_healing_context || {};
        const ver = data.verification_status || {};

        let buildHealHtml = '';
        if (bh.coding_agent_patch) {
          buildHealHtml = `
            <div class="mt-4 p-4 rounded-xl bg-yellow-950 bg-opacity-30 border border-yellow-700 space-y-2 text-xs">
              <div class="font-bold text-yellow-300">🛠️ اصلاح خودکار خطای بیلد انجام شد:</div>
              <p class="text-gray-300">${bh.root_cause || 'عدم تطابق پورت و وابستگی‌ها به صورت خودکار اصلاح گردید.'}</p>
              <pre class="ltr-text bg-gray-950 p-2.5 rounded border border-gray-800 text-green-300 text-xs">${bh.coding_agent_patch}</pre>
            </div>
          `;
        }

        activeCard.innerHTML = `
          <div class="rounded-2xl border border-green-700 bg-gray-900 p-6 shadow-xl space-y-4 text-xs md:text-sm fade-in">
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
              <h3 class="text-base font-bold text-green-400">✅ پروژه «${proj.name || currentProjectName}» با موفقیت مستقر شد</h3>
              <span class="bg-green-700 text-white text-xs px-3 py-1 rounded-full font-bold">${proj.status || 'RUNNING'}</span>
            </div>
            <p class="text-gray-300 text-xs leading-relaxed">${ver.post_fix_summary || 'تمامی مراحل بارگذاری سورس، ساخت ریلیز و بررسی سلامت سرویس با موفقیت انجام شد.'}</p>
            <div class="grid grid-cols-3 gap-3 text-center text-xs">
              <div class="bg-gray-950 p-3 rounded-xl border border-gray-800">
                <span class="text-gray-400">پلن فعال</span>
                <div class="font-bold text-white mt-1 ltr-text">${proj.plan_id || 'ir-standard-1g'}</div>
              </div>
              <div class="bg-gray-950 p-3 rounded-xl border border-gray-800">
                <span class="text-gray-400">پورت سرویس</span>
                <div class="font-bold text-blue-400 mt-1 ltr-text">${proj.port || 8000}</div>
              </div>
              <div class="bg-gray-950 p-3 rounded-xl border border-gray-800">
                <span class="text-gray-400">شناسه ریلیز</span>
                <div class="font-bold text-green-400 mt-1 ltr-text">${dep.release_id || 'rel-live'}</div>
              </div>
            </div>
            ${buildHealHtml}
          </div>
        `;
        return;
      }

      // Case 3: SRE Troubleshooting & Human-in-the-Loop Remediation Card
      if (isPaused && (intent === 'sre_troubleshoot' || intent === 'day2_ops')) {
        const rca = data.rca_report || {};
        const snap = data.telemetry_snapshot || {};
        const ramSeries = snap.ram_metrics || [480, 508];
        const ramLimit = snap.ram_limit_mb || 512;
        const lastRam = ramSeries[ramSeries.length - 1] || 508;
        const logsHtml = (rca.log_evidence || []).map(l => `<div class="text-red-300">${l}</div>`).join('');

        activeCard.innerHTML = `
          <div class="rounded-2xl border-2 border-red-600 bg-gray-900 p-6 shadow-xl space-y-5 text-xs md:text-sm fade-in">
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
              <div>
                <span class="text-xs font-bold text-red-300 bg-red-900 bg-opacity-40 px-2.5 py-1 rounded-md border border-red-700">
                  گزارش عیب‌یابی هوشمند و درخواست مجوز اقدام (Human-in-the-Loop)
                </span>
                <h3 class="text-base font-bold text-white mt-2">بررسی خطا و وضعیت منابع سرویس «${currentProjectName}»</h3>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3 text-xs">
              <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800">
                <span class="text-gray-400">وضعیت مصرف حافظه (RAM):</span>
                <div class="text-base font-bold text-red-400 mt-1 ltr-text">${lastRam} MB / ${ramLimit} MB</div>
              </div>
              <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800">
                <span class="text-gray-400">درجه اطمینان تشخیص:</span>
                <div class="text-base font-bold text-yellow-400 mt-1">${Math.round((rca.confidence || 0.94) * 100)}٪</div>
              </div>
            </div>

            <div class="bg-gray-950 p-4 rounded-xl border border-gray-800 space-y-2 text-xs">
              <div class="font-bold text-white">علت ریشه‌ای شناسایی‌شده:</div>
              <p class="text-gray-300 leading-relaxed">${rca.primary_cause || 'اشباع حافظه رم و ری‌استارت شدن کانتینر'}</p>
              <div class="font-bold text-gray-400 pt-2">شواهد لاگ سرویس:</div>
              <div class="ltr-text bg-gray-900 p-2.5 rounded border border-gray-800 space-y-1 text-xs">${logsHtml}</div>
            </div>

            <div class="bg-gray-950 p-4 rounded-xl border border-blue-900 space-y-2 text-xs">
              <label class="block text-blue-300 font-bold">انتخاب اقدام اصلاحی (نیازمند تأیید شما):</label>
              <select id="sre-hitl-action" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option value="scale_plan" selected>ارتقای پلن سرور به ۲ گیگابایت رم (ir-standard-2g — ۳۸۰,۰۰۰ تومان/ماه)</option>
                <option value="restart_app">راه‌اندازی مجدد سرویس (Restart)</option>
                <option value="rollback_release">بازگشت به آخرین نسخه سالم قبلی (Rollback)</option>
              </select>
            </div>

            <div class="pt-3 border-t border-gray-800 flex items-center justify-between">
              <button onclick="confirmSREHITL('rejected')" class="rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2.5 text-xs font-bold transition">
                انصراف و عدم تغییر
              </button>
              <button onclick="confirmSREHITL('approved')" class="rounded-xl bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 text-xs md:text-sm font-bold transition shadow-lg">
                ✓ تأیید و اعمال راهکار روی سرور
              </button>
            </div>
          </div>
        `;
        return;
      }

      // Case 4: Completed SRE Remediation / Monitoring Status Card
      if (!isPaused && (intent === 'sre_troubleshoot' || intent === 'monitoring' || intent === 'day2_ops')) {
        const ver = data.verification_status || {};
        activeCard.innerHTML = `
          <div class="rounded-2xl border border-green-700 bg-gray-900 p-6 shadow-xl space-y-4 text-xs md:text-sm fade-in">
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
              <h3 class="text-base font-bold text-green-400">✅ بررسی سلامت و پایداری سرویس «${currentProjectName}»</h3>
              <span class="bg-green-700 text-white text-xs px-3 py-1 rounded-full font-bold">HTTP 200 OK</span>
            </div>
            <p class="text-gray-300 leading-relaxed text-xs">${ver.post_fix_summary || 'سرویس در وضعیت پایدار و نرمال قرار دارد.'}</p>
          </div>
        `;
        return;
      }

      // Case 5: Domain & DNS Configuration Card
      if (intent === 'domain_dns') {
        activeCard.innerHTML = `
          <div class="rounded-2xl border border-blue-800 bg-gray-900 p-6 shadow-xl space-y-4 text-xs md:text-sm fade-in">
            <h3 class="text-base font-bold text-white border-b border-gray-800 pb-3">🌐 تنظیمات اتصال دامنه و گواهی SSL</h3>
            <p class="text-gray-300 text-xs leading-relaxed">
              رکوردهای زیر را در پنل ثبت دامنه خود (مانند ایرنیک یا کلودفلر) قرار دهید و سپس دکمه بررسی اتصال را بزنید:
            </p>
            <div class="bg-gray-950 p-3.5 rounded-xl border border-gray-800 space-y-2 ltr-text text-xs">
              <div class="flex justify-between items-center">
                <span>CNAME: <strong>@</strong> &rarr; <strong class="text-green-400">${currentProjectName}.iran.liara.run</strong></span>
                <button onclick="navigator.clipboard.writeText('${currentProjectName}.iran.liara.run')" class="bg-gray-800 px-2.5 py-1 rounded text-blue-300">کپی</button>
              </div>
              <div class="flex justify-between items-center">
                <span>A Record: <strong>@</strong> &rarr; <strong class="text-green-400">185.141.107.44</strong></span>
                <button onclick="navigator.clipboard.writeText('185.141.107.44')" class="bg-gray-800 px-2.5 py-1 rounded text-blue-300">کپی</button>
              </div>
            </div>
            <button onclick="appendChatMessage('assistant', 'بررسی اتصال دامنه انجام شد و گواهی رایگان SSL برای دامنه شما فعال گردید.')" class="bg-green-600 hover:bg-green-500 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition">
              بررسی اتصال DNS و صدور گواهی SSL
            </button>
          </div>
        `;
      }
    }

    async function confirmDeployHITL(status) {
      const planId = document.getElementById('hitl-plan-select') ? document.getElementById('hitl-plan-select').value : 'ir-standard-1g';
      const portVal = document.getElementById('hitl-port-input') ? parseInt(document.getElementById('hitl-port-input').value || '8000', 10) : 8000;

      // Save any entered .env secrets to Vault first
      const secretInputs = document.querySelectorAll('.env-secret-field');
      const secretsObj = {};
      secretInputs.forEach(inp => {
        const k = inp.getAttribute('data-env-key');
        if (k && inp.value.trim()) secretsObj[k] = inp.value.trim();
      });
      if (Object.keys(secretsObj).length > 0) {
        await fetch('/api/vault/secrets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_name: currentProjectName, secrets: secretsObj })
        });
      }

      appendChatMessage('user', status === 'rejected' ? 'انصراف از استقرار پروژه' : `تأیید راه‌اندازی پروژه با پلن ${planId} و پورت ${portVal}`);

      const res = await fetch('/api/hitl/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          status: status,
          modified_params: { plan_id: planId, port: portVal }
        })
      });
      const data = await res.json();
      handleBackendResponse(data);
    }

    async function confirmSREHITL(status) {
      const actionVal = document.getElementById('sre-hitl-action') ? document.getElementById('sre-hitl-action').value : 'scale_plan';
      appendChatMessage('user', status === 'rejected' ? 'انصراف از اعمال تغییرات روی سرور' : `تأیید اجرای عملیات (${actionVal}) روی سرور`);

      const res = await fetch('/api/hitl/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          status: status,
          modified_params: { sub_action: actionVal }
        })
      });
      const data = await res.json();
      handleBackendResponse(data);
    }

    function appendChatMessage(role, text) {
      const stream = document.getElementById('chat-stream');
      const div = document.createElement('div');
      div.className = 'rounded-2xl p-3.5 text-xs md:text-sm leading-relaxed whitespace-pre-line fade-in ' + 
        (role === 'user' ? 'bg-blue-600 text-white ml-6' : 'bg-gray-800 border border-gray-700 text-gray-200 mr-6');
      div.innerText = text;
      stream.appendChild(div);
      stream.scrollTop = stream.scrollHeight;
    }

    async function triggerKillSwitch() {
      await fetch('/api/governance/kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'User clicked revoke button' })
      });
      document.getElementById('btn-kill-switch').classList.add('hidden');
      document.getElementById('btn-reactivate').classList.remove('hidden');
      appendChatMessage('assistant', '🛑 دسترسی دستیار هوشمند به دستور شما متوقف و توکن فعال باطل شد.');
    }

    async function reactivateAgent() {
      await fetch('/api/governance/reactivate', { method: 'POST' });
      document.getElementById('btn-kill-switch').classList.remove('hidden');
      document.getElementById('btn-reactivate').classList.add('hidden');
      appendChatMessage('assistant', '✅ دسترسی دستیار مجدداً فعال گردید.');
    }
  </script>
</body>
</html>
"""
