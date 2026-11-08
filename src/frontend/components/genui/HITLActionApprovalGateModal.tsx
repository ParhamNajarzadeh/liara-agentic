"use client";

import React from "react";

export interface HITLActionApprovalGateModalProps {
  project_name: string;
  action: string;
  plan_id?: string;
  target_release_id?: string;
  monthly_cost_tomans?: number;
  remaining_credit_tomans?: number;
  onDecision: (status: "approved" | "rejected") => void;
}

export const HITLActionApprovalGateModal: React.FC<
  HITLActionApprovalGateModalProps
> = ({
  project_name,
  action,
  plan_id,
  target_release_id,
  monthly_cost_tomans = 0,
  remaining_credit_tomans = 2000000,
  onDecision,
}) => {
  return (
    <div
      dir="rtl"
      className="rounded-2xl border-2 border-amber-500/60 bg-slate-900 p-6 shadow-2xl space-y-4"
    >
      <div className="flex items-center justify-between">
        <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-bold text-amber-300">
          دروازه توقف و تأیید انسانی (Anti-Fatigue HITL — فقط تصمیمات مالی و پروداکشن)
        </span>
        <code className="text-xs text-slate-400">interrupt() active</code>
      </div>

      <h3 className="text-lg font-bold text-white">
        درخواست مجوز اجرای عملیات حساس: <code className="text-amber-300">{action}</code> روی پروژه{" "}
        <code className="text-sky-400">{project_name}</code>
      </h3>

      <div className="rounded-xl bg-slate-950 p-4 border border-slate-800 text-xs text-slate-300 space-y-1.5">
        {plan_id && <div>پلن هدف: <code>{plan_id}</code></div>}
        {target_release_id && <div>بازگشت (Rollback) به ریلیز سالم: <code>{target_release_id}</code></div>}
        <div>
          بار مالی ماهانه:{" "}
          <strong className="text-amber-300">
            {monthly_cost_tomans.toLocaleString("fa-IR")} تومان
          </strong>{" "}
          | اعتبار باقیمانده هکاتون:{" "}
          <strong className="text-emerald-400">
            {remaining_credit_tomans.toLocaleString("fa-IR")} تومان
          </strong>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          onClick={() => onDecision("rejected")}
          className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700"
        >
          انصراف و لغو عملیات
        </button>
        <button
          onClick={() => onDecision("approved")}
          className="rounded-xl bg-amber-500 px-5 py-2 text-xs font-bold text-slate-950 hover:bg-amber-400"
        >
          تأیید نهایی و اجرای امن در لیارا
        </button>
      </div>
    </div>
  );
};
