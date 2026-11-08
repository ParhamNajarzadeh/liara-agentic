"use client";

import React, { useState } from "react";
import { UnifiedZeroFrictionLaunchCard } from "../components/genui/UnifiedZeroFrictionLaunchCard";
import { AutomatedBuildHealerBridgeCard } from "../components/genui/AutomatedBuildHealerBridgeCard";
import { LiveDeploymentStepper } from "../components/genui/LiveDeploymentStepper";
import { ResourceHealthTelemetryCard } from "../components/genui/ResourceHealthTelemetryCard";
import { IncidentRCADiagnosticCard } from "../components/genui/IncidentRCADiagnosticCard";
import { HITLActionApprovalGateModal } from "../components/genui/HITLActionApprovalGateModal";
import { DomainDNSGuideWidget } from "../components/genui/DomainDNSGuideWidget";

export default function LiaraAgenticSREPage() {
  const [activeTab, setActiveTab] = useState<
    "launch" | "build_healer" | "sre_rca" | "domain_dns"
  >("launch");
  const [agentStatus, setAgentStatus] = useState<"ACTIVE" | "DECOMMISSIONED">("ACTIVE");
  const [remainingCredit, setRemainingCredit] = useState<number>(2000000);
  const [chatLog, setChatLog] = useState<Array<{ role: string; text: string }>>([
    {
      role: "assistant",
      text: "سلام! من دستیار هوشمند زیرساخت و مهندس قابلیت اطمینان (SRE) لیارا هستم. پروژه شما به صورت خودکار اسکن شد و کارت راه‌اندازی تک‌کلیکی آماده است.",
    },
  ]);
  const [inputMsg, setInputMsg] = useState("");

  const handleKillSwitch = () => {
    setAgentStatus("DECOMMISSIONED");
    setChatLog((prev) => [
      ...prev,
      {
        role: "system",
        text: "🛑 کلید اضطراری Kill-Switch فعال شد: توکن مجازی ایجنت (liara-sre-virtual-agent) باطل گردید و وضعیت به DECOMMISSIONED تغییر یافت.",
      },
    ]);
  };

  return (
    <div dir="rtl" className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Governance, Hackathon Credit & Kill-Switch Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="h-3 w-3 rounded-full bg-emerald-400 animate-pulse" />
          <h1 className="text-base font-bold text-white">
            دستیار هوشمند زیرساخت و SRE لیارا (Liara Agentic Co-Pilot)
          </h1>
          <span className="rounded-md bg-slate-800 px-2.5 py-1 text-xs font-mono text-sky-300">
            System 2: deepseek-v4.1-flash | System 1: Jev / Mizan-4B (ECE=0.064)
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5">
            اعتبار هکاتون:{" "}
            <strong className="text-emerald-400">
              {remainingCredit.toLocaleString("fa-IR")} تومان
            </strong>
          </div>
          <div className="rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5">
            وضعیت هویت مجازی:{" "}
            <strong
              className={
                agentStatus === "ACTIVE" ? "text-emerald-400" : "text-rose-400"
              }
            >
              {agentStatus} (TTL: 59m)
            </strong>
          </div>
          <button
            onClick={handleKillSwitch}
            disabled={agentStatus === "DECOMMISSIONED"}
            className="rounded-lg bg-rose-600 px-3.5 py-1.5 font-bold text-white hover:bg-rose-500 disabled:opacity-40 transition"
          >
            بازنشستگی و قطع اضطراری دسترسی ایجنت (Kill-Switch)
          </button>
        </div>
      </header>

      {/* Dual Chat Plus Layout: 35% RTL Persian Chat Panel (Right) + 65% Live Infrastructure Canvas (Left) */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Right Panel: 35% (4 cols) Conversational Co-Pilot */}
        <section className="lg:col-span-4 border-l border-slate-800 bg-slate-900/50 p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-3 overflow-y-auto max-h-[72vh]">
            <div className="text-xs font-semibold text-slate-400">
              پنل گفتگوی هوشمند (۳۵٪ عرض — بدون لاگ‌های متنی شلوغ)
            </div>
            {chatLog.map((msg, idx) => (
              <div
                key={idx}
                className={`rounded-xl p-3.5 text-xs leading-relaxed ${
                  msg.role === "user"
                    ? "bg-sky-600/20 border border-sky-500/30 text-sky-100"
                    : msg.role === "system"
                    ? "bg-rose-950/60 border border-rose-500/40 text-rose-200"
                    : "bg-slate-800/80 border border-slate-700 text-slate-200"
                }`}
              >
                {msg.text}
              </div>
            ))}
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMsg}
                onChange={(e) => setInputMsg(e.target.value)}
                placeholder="درخواست خود را به زبان ساده بنویسید (مثلاً: سایت خطای ۵۰۰ میده)..."
                className="flex-1 rounded-xl bg-slate-950 border border-slate-700 px-3.5 py-2 text-xs text-white"
              />
              <button
                onClick={() => {
                  if (!inputMsg.trim()) return;
                  setChatLog((prev) => [
                    ...prev,
                    { role: "user", text: inputMsg },
                    {
                      role: "assistant",
                      text: "درخواست شما در کمتر از ۲۵ میلی‌ثانیه توسط روتر System 1 مسیریابی شد و کامپوننت تعاملی در بوم سمت چپ به‌روزرسانی گردید.",
                    },
                  ]);
                  setInputMsg("");
                }}
                className="rounded-xl bg-sky-500 px-4 py-2 text-xs font-bold text-slate-950"
              >
                ارسال
              </button>
            </div>
          </div>
        </section>

        {/* Left Panel: 65% (8 cols) Live Infrastructure Canvas (Static GenUI) */}
        <section className="lg:col-span-8 p-6 overflow-y-auto space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <span className="text-sm font-bold text-sky-400">
              بوم زنده عملیات زیرساخت (Live Infrastructure Canvas — ۶۵٪ عرض | Static GenUI)
            </span>
            <div className="flex gap-2 text-xs">
              <button
                onClick={() => setActiveTab("launch")}
                className={`rounded-lg px-3 py-1.5 font-semibold ${
                  activeTab === "launch"
                    ? "bg-sky-500 text-slate-950"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                ۱. دیپلوی تک‌کلیکی (Zero-Friction)
              </button>
              <button
                onClick={() => setActiveTab("build_healer")}
                className={`rounded-lg px-3 py-1.5 font-semibold ${
                  activeTab === "build_healer"
                    ? "bg-amber-500 text-slate-950"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                ۲. خودترمیم‌گر بیلد (Auto-Build-Healer)
              </button>
              <button
                onClick={() => setActiveTab("sre_rca")}
                className={`rounded-lg px-3 py-1.5 font-semibold ${
                  activeTab === "sre_rca"
                    ? "bg-rose-500 text-white"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                ۳. میز کار SRE و خطای 500
              </button>
              <button
                onClick={() => setActiveTab("domain_dns")}
                className={`rounded-lg px-3 py-1.5 font-semibold ${
                  activeTab === "domain_dns"
                    ? "bg-emerald-500 text-slate-950"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                ۴. دامنه و ایرنیک (.ir)
              </button>
            </div>
          </div>

          {activeTab === "launch" && (
            <div className="space-y-6">
              <UnifiedZeroFrictionLaunchCard
                project_name="shop-api-prod"
                detected_platform="python"
                detected_port={8000}
                env_key_names={["APP_ENV", "PORT", "DATABASE_URL", "REDIS_URL"]}
                recommended_plan={{
                  plan_id: "ir-standard-1g",
                  ram_gb: 1.0,
                  cpu_cores: 1.0,
                  disk_gb: 10,
                  monthly_cost_tomans: 220000,
                  remaining_credit_tomans: remainingCredit,
                  estimated_runway_months: 9.1,
                  tier_label: "استاندارد ۱ گیگابایت",
                }}
                source_id="src-98f1a20c"
                onApproveLaunch={({ plan_id, port }) => {
                  setRemainingCredit((c) => c - 55000);
                  setChatLog((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      text: `پلن مالی (${plan_id}) روی پورت ${port} تأیید شد. دیپلوی خودکار انجام و سرویس به وضعیت RUNNING رسید.`,
                    },
                  ]);
                }}
              />
              <LiveDeploymentStepper
                project_name="shop-api-prod"
                current_step={5}
                source_id="src-98f1a20c"
                release_id="rel-77b41e09"
                status="RUNNING"
              />
            </div>
          )}

          {activeTab === "build_healer" && (
            <AutomatedBuildHealerBridgeCard
              healed={true}
              heal_attempt_count={1}
              root_cause="عدم تطابق پورت EXPOSE در liara.json (3000 به جای 8000) و پکیج ناقص در requirements.txt"
              patched_files={["liara.json", "requirements.txt", "Dockerfile"]}
              coding_agent_patch={
                '--- a/liara.json\n+++ b/liara.json\n@@ -1,4 +1,4 @@\n-  "port": 3000\n+  "port": 8000\n--- a/requirements.txt\n+++ b/requirements.txt\n+uvicorn[standard]>=0.29.0'
              }
              reasoning_steps={[
                "گام ۱: دریافت خودکار لاگ خطای بیلد از GET /v1/projects/shop-api-prod/events بدون دخالت کاربر.",
                "گام ۲: ارسال قرارداد کار چهاربخشی (Work Order Contract) از طریق MCP به ساب‌ایجنت code-remediator.",
                "گام ۳: اصلاح خودکار پورت 8000 در liara.json و پکیج uvicorn در requirements.txt.",
                "گام ۴: بسته‌بندی مجدد .tar.gz، آپلود به v2/sources و انتشار ریلیز سالم (RUNNING).",
              ]}
              new_source_id="src-healed-8821"
              new_release_id="rel-healed-9902"
            />
          )}

          {activeTab === "sre_rca" && (
            <div className="space-y-6">
              <ResourceHealthTelemetryCard
                project_name="shop-api-prod"
                cpu_metrics={[42, 58.5, 76, 88.2]}
                ram_metrics={[380, 445, 498, 508]}
                ram_limit_mb={512}
                memory_leak_slope_detected={true}
                applets={[
                  {
                    applet_id: "app-shop-api-prod-01",
                    state: "CrashLoopBackOff (Exit 137 - OOMKilled)",
                    restarts: 4,
                    http_probe_status: 500,
                  },
                ]}
              />
              <IncidentRCADiagnosticCard
                project_name="shop-api-prod"
                rca_report={{
                  reasoning_steps: [
                    "گام ۱: پاکسازی لاگ‌ها در تگ <untrusted_log_data> و خنثی‌سازی تلاش تزریق پرامپت (Prompt Injection).",
                    "گام ۲: تطبیق رویداد OOMKilled (Exit Code 137) با اشباع ۹۹.۲٪ حافظه RAM (۵۰۸MB از ۵۱۲MB).",
                    "گام ۳: تدوین برنامه دوگانه ارتقای پلن به ir-standard-2g و اصلاح اندازه استخر اتصالات دیتابیس.",
                  ],
                  hypotheses: [
                    {
                      cause_id: "OOM_MEMORY_EXHAUSTION",
                      title: "اشباع حافظه RAM و قتل کانتینر توسط کرنل (OOMKilled - Exit Code 137)",
                      confidence: 0.94,
                      evidence: "RAM peaked at 508MB/512MB; Container exited with code 137",
                    },
                  ],
                  primary_cause: "اشباع حافظه RAM (OOMKilled 137) به همراه نشت کانکشن دیتابیس",
                  confidence: 0.94,
                  log_evidence: [
                    "[ERROR] HTTP 500 Internal Server Error on GET /api/v1/checkout",
                    "[ERROR] Kernel invoked oom-killer: gfp_mask=0x140cca",
                    "[CRITICAL] Container applet-main exited with status 137 (OOMKilled)",
                  ],
                  code_remediation_patch:
                    "-engine = create_async_engine(DB_URL, pool_size=50)\n+engine = create_async_engine(DB_URL, pool_size=10, pool_recycle=1800)",
                  rubric_score: 9.5,
                }}
                pending_action={{
                  sub_action: "scale_plan (ir-standard-2g)",
                  cost_tomans: 380000,
                  params: { plan_id: "ir-standard-2g" },
                }}
                onApproveRemediation={() => {
                  setRemainingCredit((c) => c - 95000);
                  setChatLog((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      text: "ارتقای پلن به ir-standard-2g تأیید و اجرا شد. راستی‌آزمایی پس از اقدام: وضعیت سرویس RUNNING و کد پاسخ HTTP 200 پایدار است.",
                    },
                  ]);
                }}
              />
              <HITLActionApprovalGateModal
                project_name="shop-api-prod"
                action="scale_plan -> ir-standard-2g"
                plan_id="ir-standard-2g"
                monthly_cost_tomans={380000}
                remaining_credit_tomans={remainingCredit}
                onDecision={(st) => {
                  setChatLog((prev) => [
                    ...prev,
                    { role: "assistant", text: `تصمیم گیت HITL ثبت شد: ${st}` },
                  ]);
                }}
              />
            </div>
          )}

          {activeTab === "domain_dns" && (
            <DomainDNSGuideWidget
              domain_name="shop.example.ir"
              project_name="shop-api-prod"
              api_limitation_disclosure="محدودیت ذاتی API: ثبت رکورد در پنل ایرنیک (nic.ir) خارج از دسترسی مستقیم API لیارا است؛ مقادیر زیر را کپی و در پنل ایرنیک وارد کنید."
              dns_records={[
                { type: "CNAME", host: "www", value: "edge.liara.ir", ttl: "3600" },
                { type: "A / ANAME", host: "@", value: "185.141.107.44", ttl: "3600" },
              ]}
              steps_persian={[
                "۱. وارد پنل ایرنیک (nic.ir) یا کلودفلر شوید.",
                "۲. رکوردهای A و CNAME جدول بالا را با یک کلیک کپی و ثبت نمایید.",
                "۳. دکمه زیر را بزنید تا اندپوینت POST /v1/domains/{id}/check وضعیت DNS و گواهی SSL را تأیید کند.",
              ]}
              ssl_status="ISSUED_LETS_ENCRYPT"
              onVerifyDnsSsl={() => {
                setChatLog((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    text: "بررسی DNS و گواهی Let's Encrypt SSL با موفقیت از طریق اندپوینت POST /v1/domains/{id}/check انجام شد.",
                  },
                ]);
              }}
            />
          )}
        </section>
      </main>
    </div>
  );
}
