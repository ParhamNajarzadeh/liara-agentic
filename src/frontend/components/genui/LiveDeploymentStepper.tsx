"use client";

import React, { useState } from "react";

export interface LiveDeploymentStepperProps {
  project_name: string;
  current_step: number;
  source_id?: string;
  release_id?: string;
  status?: string;
  build_logs?: string;
}

const STEPS = [
  "۱. تشخیص خودکار فریم‌ورک و تولید liara.json",
  "۲. فشرده‌سازی .tar.gz و آپلود سورس (v2/sources)",
  "۳. تزریق Secret-Blind متغیرها و ساخت ریلیز (v2/releases)",
  "۴. راه‌اندازی کانتینر و بررسی رویدادهای بیلد",
  "۵. تست سلامت نهایی (HTTP 200 Probe)",
];

export const LiveDeploymentStepper: React.FC<LiveDeploymentStepperProps> = ({
  project_name,
  current_step = 5,
  source_id,
  release_id,
  status = "RUNNING",
  build_logs,
}) => {
  const [logsOpen, setLogsOpen] = useState(false);

  return (
    <div
      dir="rtl"
      className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl space-y-4"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">
          استپر زنده پیشرفت دیپلوی: <code className="text-sky-400">{project_name}</code>
        </h3>
        <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-bold text-emerald-300">
          {status}
        </span>
      </div>

      <div className="space-y-2.5">
        {STEPS.map((label, idx) => {
          const stepNum = idx + 1;
          const done = stepNum <= current_step;
          return (
            <div
              key={label}
              className={`flex items-center justify-between rounded-xl px-4 py-2.5 border ${
                done
                  ? "border-emerald-500/40 bg-emerald-950/30 text-emerald-200"
                  : "border-slate-800 bg-slate-950/50 text-slate-500"
              }`}
            >
              <span className="text-sm font-medium">{label}</span>
              <span className="text-xs font-mono">
                {done ? "✓ تکمیل شد" : "در انتظار..."}
              </span>
            </div>
          );
        })}
      </div>

      <div className="pt-2">
        <button
          onClick={() => setLogsOpen(!logsOpen)}
          className="text-xs text-sky-400 hover:underline"
        >
          {logsOpen ? "▲ بستن لاگ آکاردئونی بیلد" : "▼ مشاهده لاگ زنده بیلد و شناسه‌های استقرار"}
        </button>
        {logsOpen && (
          <pre
            dir="ltr"
            className="mt-2 rounded-xl bg-black/80 p-3 font-mono text-xs text-slate-300 border border-slate-800"
          >
            {build_logs ||
              `[INFO] Source ID: ${source_id || "src-auto"}\n[INFO] Release ID: ${
                release_id || "rel-auto"
              }\n[SUCCESS] Container listening on port 8000 -> Status: ${status}`}
          </pre>
        )}
      </div>
    </div>
  );
};
