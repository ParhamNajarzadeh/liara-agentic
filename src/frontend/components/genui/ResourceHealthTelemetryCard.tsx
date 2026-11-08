"use client";

import React from "react";

export interface ResourceHealthTelemetryCardProps {
  project_name: string;
  cpu_metrics?: number[];
  ram_metrics?: number[];
  ram_limit_mb?: number;
  memory_leak_slope_detected?: boolean;
  applets?: Array<{
    applet_id: string;
    state: string;
    restarts: number;
    http_probe_status: number;
  }>;
}

export const ResourceHealthTelemetryCard: React.FC<
  ResourceHealthTelemetryCardProps
> = ({
  project_name,
  cpu_metrics = [42, 58, 76, 88],
  ram_metrics = [380, 445, 498, 508],
  ram_limit_mb = 512,
  memory_leak_slope_detected = true,
  applets = [],
}) => {
  const latestRam = ram_metrics[ram_metrics.length - 1] || 0;
  const ramPct = Math.min(100, Math.round((latestRam / ram_limit_mb) * 100));
  const latestCpu = cpu_metrics[cpu_metrics.length - 1] || 0;

  return (
    <div
      dir="rtl"
      className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl space-y-5"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">
            داشبورد تلمتری و سلامت منابع: <code className="text-sky-400">{project_name}</code>
          </h3>
          <p className="text-xs text-slate-400">
            واکشی موازی از اندپوینت‌های <code>/v1/projects/{project_name}/metrics</code> و <code>/applets</code>
          </p>
        </div>
        {memory_leak_slope_detected && (
          <span className="rounded-full bg-rose-500/20 border border-rose-500/40 px-3 py-1 text-xs font-bold text-rose-300">
            ⚠ هشدار نشت حافظه (Memory Leak / OOM Risk)
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-950 p-4 border border-slate-800 space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">مصرف حافظه RAM</span>
            <span className="font-mono font-bold text-rose-400">
              {latestRam} MB / {ram_limit_mb} MB ({ramPct}%)
            </span>
          </div>
          <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${ramPct > 85 ? "bg-rose-500" : "bg-emerald-500"}`}
              style={{ width: `${ramPct}%` }}
            />
          </div>
          <div className="text-[11px] text-slate-500 font-mono" dir="ltr">
            Series: [{ram_metrics.join("MB -> ")}MB]
          </div>
        </div>

        <div className="rounded-xl bg-slate-950 p-4 border border-slate-800 space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">مصرف پردازنده CPU</span>
            <span className="font-mono font-bold text-amber-400">{latestCpu}%</span>
          </div>
          <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500"
              style={{ width: `${Math.min(100, latestCpu)}%` }}
            />
          </div>
          <div className="text-[11px] text-slate-500 font-mono" dir="ltr">
            Series: [{cpu_metrics.join("% -> ")}%]
          </div>
        </div>
      </div>

      {applets.length > 0 && (
        <div className="rounded-xl bg-slate-950 p-3.5 border border-slate-800 text-xs flex items-center justify-between">
          <span>
            وضعیت آپلت: <code className="text-amber-300">{applets[0].state}</code>
          </span>
          <span>تعداد ری‌استارت: {applets[0].restarts}</span>
          <span>کد وضعیت HTTP: {applets[0].http_probe_status}</span>
        </div>
      )}
    </div>
  );
};
