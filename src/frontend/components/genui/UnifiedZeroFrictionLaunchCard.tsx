"use client";

import React, { useState } from "react";

export interface UnifiedZeroFrictionLaunchCardProps {
  project_name: string;
  detected_platform: string;
  detected_port: number;
  env_key_names: string[];
  recommended_plan: {
    plan_id: string;
    ram_gb: number;
    cpu_cores: number;
    disk_gb: number;
    monthly_cost_tomans: number;
    remaining_credit_tomans: number;
    estimated_runway_months: number;
    tier_label: string;
  };
  source_id: string;
  onApproveLaunch: (modifiedParams: {
    plan_id: string;
    port: number;
    secret_values: Record<string, string>;
  }) => void;
}

export const UnifiedZeroFrictionLaunchCard: React.FC<
  UnifiedZeroFrictionLaunchCardProps
> = ({
  project_name,
  detected_platform,
  detected_port,
  env_key_names,
  recommended_plan,
  source_id,
  onApproveLaunch,
}) => {
  const [selectedPlan, setSelectedPlan] = useState(recommended_plan.plan_id);
  const [port, setPort] = useState(detected_port);
  const [secretValues, setSecretValues] = useState<Record<string, string>>({});

  return (
    <div
      dir="rtl"
      className="rounded-2xl border border-sky-500/40 bg-slate-900/90 p-6 shadow-2xl space-y-5"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <span className="inline-block rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300 mb-1">
            جایگزین ۵ مرحله سنتی پنل لیارا ← ۱ گام هوشمند (Zero-Friction 1-Step)
          </span>
          <h3 className="text-xl font-bold text-white">
            کارت تجمیعی راه‌اندازی خودکار پروژه: <code className="text-sky-400">{project_name}</code>
          </h3>
        </div>
        <div className="text-left text-xs text-slate-400">
          <div>بسته سورس آماده و آپلود شده:</div>
          <code className="text-emerald-400 font-mono">{source_id}</code>
        </div>
      </div>

      {/* 1. Auto-detected Stack & Port (State Editable) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950/70 p-4 rounded-xl border border-slate-800">
        <div>
          <label className="block text-xs text-slate-400 mb-1">
            پلتفرم تشخیص‌داده‌شده (خودکار)
          </label>
          <div className="font-mono text-sm font-bold text-sky-300 uppercase">
            {detected_platform} (liara.json آماده)
          </div>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">
            پورت برنامه (قابل ویرایش در State)
          </label>
          <input
            type="number"
            value={port}
            onChange={(e) => setPort(Number(e.target.value))}
            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-1.5 text-sm text-white font-mono"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">
            انتخاب پلن زیرساخت (محافظت از شارژ ۲ میلیون تومانی)
          </label>
          <select
            value={selectedPlan}
            onChange={(e) => setSelectedPlan(e.target.value)}
            className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-1.5 text-sm text-white"
          >
            <option value="ir-mini">ir-mini (۰.۵GB RAM - ۱۲۰,۰۰۰ تومان/ماه)</option>
            <option value="ir-standard-1g">
              ir-standard-1g (۱GB RAM - ۲۲۰,۰۰۰ تومان/ماه - پیشنهادی)
            </option>
            <option value="ir-standard-2g">
              ir-standard-2g (۲GB RAM - ۳۸۰,۰۰۰ تومان/ماه)
            </option>
          </select>
        </div>
      </div>

      {/* 2. Secret-Blind Environment Variables Input */}
      <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-amber-300">
            متغیرهای استخراج‌شده از <code>.env.example</code> (معماری Secret-Blind: مقادیر خام وارد LLM نمی‌شوند)
          </span>
          <span className="text-xs text-slate-400">تزریق مستقیم به Vault رمزنگاری‌شده</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {env_key_names.map((key) => (
            <div key={key} className="flex items-center gap-2">
              <span className="w-40 truncate font-mono text-xs text-slate-300">{key}=</span>
              <input
                type="password"
                placeholder="مقدار محرمانه (مستقیم به Vault)..."
                onChange={(e) =>
                  setSecretValues((prev) => ({ ...prev, [key]: e.target.value }))
                }
                className="flex-1 rounded-lg bg-slate-900 border border-slate-700 px-2.5 py-1 text-xs text-white"
              />
            </div>
          ))}
        </div>
      </div>

      {/* 3. Financial Summary & Single Consolidated Confirmation Button */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-2">
        <div className="text-xs text-slate-300 space-y-1">
          <div>
            هزینه ماهانه پلن انتخابی:{" "}
            <strong className="text-emerald-400">
              {recommended_plan.monthly_cost_tomans.toLocaleString("fa-IR")} تومان
            </strong>{" "}
            | باقیمانده اعتبار هکاتون:{" "}
            <strong className="text-sky-400">
              {recommended_plan.remaining_credit_tomans.toLocaleString("fa-IR")} تومان
            </strong>{" "}
            (تضمین آنلاین ماندن تا {recommended_plan.estimated_runway_months} ماه)
          </div>
          <div className="text-slate-400">
            محدودیت شفاف API: شارژ کیف پول از طریق درگاه بانکی خارج از API لیارا است و در صورت کسری، لینک پنل ارائه می‌شود.
          </div>
        </div>
        <button
          onClick={() =>
            onApproveLaunch({
              plan_id: selectedPlan,
              port,
              secret_values: secretValues,
            })
          }
          className="rounded-xl bg-gradient-to-l from-sky-500 to-emerald-500 px-6 py-3 text-sm font-bold text-slate-950 shadow-lg hover:opacity-95 transition"
        >
          تأیید پلن مالی و شروع دیپلوی خودکار (۱ کلیک)
        </button>
      </div>
    </div>
  );
};
