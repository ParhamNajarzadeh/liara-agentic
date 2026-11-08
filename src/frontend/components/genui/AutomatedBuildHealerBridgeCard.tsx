"use client";

import React from "react";

export interface AutomatedBuildHealerBridgeCardProps {
  healed?: boolean;
  heal_attempt_count: number;
  root_cause: string;
  patched_files: string[];
  coding_agent_patch: string;
  reasoning_steps: string[];
  new_source_id?: string;
  new_release_id?: string;
}

export const AutomatedBuildHealerBridgeCard: React.FC<
  AutomatedBuildHealerBridgeCardProps
> = ({
  heal_attempt_count,
  root_cause,
  patched_files,
  coding_agent_patch,
  reasoning_steps,
  new_source_id,
  new_release_id,
}) => {
  return (
    <div
      dir="rtl"
      className="rounded-2xl border border-amber-500/40 bg-slate-900/95 p-6 shadow-2xl space-y-4"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <span className="inline-block rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-300 mb-1">
            پل خودترمیم‌گر بیلد (Deploy Agent ↔ MCP ↔ Coding Agent) — حذف ۱۰۰٪ کپی-پیست دستی
          </span>
          <h3 className="text-lg font-bold text-white">
            اصلاح خودکار خطای بیلد و انتشار مجدد (تلاش #{heal_attempt_count})
          </h3>
        </div>
        <span className="rounded-lg bg-emerald-500/20 px-3 py-1.5 text-xs font-bold text-emerald-300">
          وضعیت نهایی: RUNNING
        </span>
      </div>

      <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
        <div className="text-xs font-bold text-sky-400">
          زنجیره استدلال گام‌به‌گام (Step-by-Step Reasoning پیش از پچ):
        </div>
        <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
          {(reasoning_steps || []).map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ul>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">علت ریشه‌ای شکست بیلد:</div>
          <div className="text-sm font-medium text-amber-200">{root_cause}</div>
        </div>
        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
          <div className="text-xs text-slate-400 mb-1">
            فایل‌های اصلاح‌شده توسط ساب‌ایجنت <code>code-remediator</code>:
          </div>
          <div className="flex flex-wrap gap-2 mt-1">
            {(patched_files || []).map((f) => (
              <span
                key={f}
                className="rounded bg-slate-800 px-2.5 py-1 font-mono text-xs text-sky-300"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div>
        <div className="text-xs text-slate-400 mb-1">
          پیش‌نمایش پچ اعمال‌شده (Unified Diff Preview):
        </div>
        <pre
          dir="ltr"
          className="overflow-x-auto rounded-xl bg-black/80 p-4 font-mono text-xs text-emerald-300 border border-slate-800"
        >
          {coding_agent_patch}
        </pre>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
        <span>
          شناسه سورس جدید: <code className="text-sky-400">{new_source_id || "src-healed"}</code>
        </span>
        <span>
          شناسه ریلیز سالم: <code className="text-emerald-400">{new_release_id || "rel-healed"}</code>
        </span>
      </div>
    </div>
  );
};
