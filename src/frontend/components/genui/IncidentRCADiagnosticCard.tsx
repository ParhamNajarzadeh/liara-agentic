"use client";

import React from "react";

export interface IncidentRCADiagnosticCardProps {
  project_name: string;
  rca_report: {
    reasoning_steps: string[];
    hypotheses: Array<{
      cause_id: string;
      title: string;
      confidence: number;
      evidence: string;
    }>;
    primary_cause: string;
    confidence: number;
    log_evidence: string[];
    code_remediation_patch: string;
    rubric_score: number;
  };
  pending_action?: {
    sub_action: string;
    cost_tomans: number;
    params: Record<string, unknown>;
  };
  onApproveRemediation: () => void;
}

export const IncidentRCADiagnosticCard: React.FC<
  IncidentRCADiagnosticCardProps
> = ({ project_name, rca_report, pending_action, onApproveRemediation }) => {
  return (
    <div
      dir="rtl"
      className="rounded-2xl border border-rose-500/40 bg-slate-900/95 p-6 shadow-2xl space-y-5"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <span className="inline-block rounded-full bg-rose-500/20 px-3 py-1 text-xs font-semibold text-rose-300 mb-1">
            میز کار ریشه‌یابی هوشمند خطای HTTP 500 (MTTR &lt; 30s | امتیاز روبریک: {rca_report.rubric_score}/10)
          </span>
          <h3 className="text-lg font-bold text-white">
            علت اصلی شناسایی‌شده: <span className="text-rose-300">{rca_report.primary_cause}</span>
          </h3>
        </div>
        <div className="text-left">
          <div className="text-xs text-slate-400">درجه اطمینان کالیبره‌شده</div>
          <div className="text-xl font-bold text-emerald-400">
            {Math.round((rca_report.confidence || 0.94) * 100)}%
          </div>
        </div>
      </div>

      {/* Reasoning Steps First (Quera Ch. 5 Lesson 05) */}
      <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1.5">
        <div className="text-xs font-bold text-sky-400">
          استدلال گام‌به‌گام مهندس قابلیت اطمینان (SRE Reasoning Steps):
        </div>
        <ol className="list-decimal list-inside text-xs text-slate-300 space-y-1">
          {(rca_report.reasoning_steps || []).map((step, idx) => (
            <li key={idx}>{step}</li>
          ))}
        </ol>
      </div>

      {/* Prioritized Hypotheses */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-400">
          فرضیه‌های اولویت‌بندی‌شده (RCA Hypotheses):
        </div>
        {(rca_report.hypotheses || []).map((h) => (
          <div
            key={h.cause_id}
            className="rounded-xl bg-slate-950 p-3.5 border border-slate-800 flex items-center justify-between"
          >
            <div>
              <div className="text-sm font-bold text-white">{h.title}</div>
              <div className="text-xs text-slate-400 font-mono mt-0.5" dir="ltr">
                {h.evidence}
              </div>
            </div>
            <span className="rounded-lg bg-sky-500/20 px-3 py-1 text-xs font-bold text-sky-300">
              {Math.round(h.confidence * 100)}%
            </span>
          </div>
        ))}
      </div>

      {/* Sanitized Log Evidence & Code Patch */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-slate-400 mb-1">
            ۳ خط کلیدی لاگ (پاکسازی‌شده در <code>&lt;untrusted_log_data&gt;</code>):
          </div>
          <pre
            dir="ltr"
            className="rounded-xl bg-black/80 p-3 font-mono text-[11px] text-rose-300 border border-slate-800 overflow-x-auto"
          >
            {(rca_report.log_evidence || []).join("\n")}
          </pre>
        </div>
        <div>
          <div className="text-xs text-slate-400 mb-1">
            پچ پیشنهادی کد برای Coding Agent (<code>code-remediator</code>):
          </div>
          <pre
            dir="ltr"
            className="rounded-xl bg-black/80 p-3 font-mono text-[11px] text-emerald-300 border border-slate-800 overflow-x-auto"
          >
            {rca_report.code_remediation_patch}
          </pre>
        </div>
      </div>

      {/* HITL Action Gate Button */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800">
        <div className="text-xs text-slate-300">
          اقدام زیرساختی پیشنهادی:{" "}
          <code className="text-amber-300">{pending_action?.sub_action || "scale_plan"}</code>{" "}
          (هزینه ماهانه: {(pending_action?.cost_tomans || 380000).toLocaleString("fa-IR")} تومان)
        </div>
        <button
          onClick={onApproveRemediation}
          className="rounded-xl bg-emerald-500 px-5 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 transition"
        >
          تأیید HITL و اجرای عملیات ترمیم زیرساخت
        </button>
      </div>
    </div>
  );
};
