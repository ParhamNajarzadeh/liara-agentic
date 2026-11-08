"use client";

import React from "react";

export interface DomainDNSGuideWidgetProps {
  domain_name: string;
  project_name: string;
  api_limitation_disclosure: string;
  dns_records: Array<{ type: string; host: string; value: string; ttl: string }>;
  steps_persian: string[];
  ssl_status?: string;
  onVerifyDnsSsl: () => void;
}

export const DomainDNSGuideWidget: React.FC<DomainDNSGuideWidgetProps> = ({
  domain_name = "shop.example.ir",
  project_name = "shop-api-prod",
  api_limitation_disclosure,
  dns_records = [],
  steps_persian = [],
  ssl_status = "ISSUED_LETS_ENCRYPT",
  onVerifyDnsSsl,
}) => {
  return (
    <div
      dir="rtl"
      className="rounded-2xl border border-sky-500/40 bg-slate-900/90 p-6 shadow-xl space-y-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">
            راهنمای تعاملی اتصال دامنه و ایرنیک (<code>{domain_name}</code> ← <code>{project_name}</code>)
          </h3>
          <p className="text-xs text-amber-300 mt-1">{api_limitation_disclosure}</p>
        </div>
        <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-bold text-emerald-300">
          SSL: {ssl_status}
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950">
        <table className="w-full text-right text-xs">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="p-3">نوع رکورد (Type)</th>
              <th className="p-3">نام میزبان (Host)</th>
              <th className="p-3">مقدار هدف در لیارا (Value)</th>
              <th className="p-3">TTL</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 font-mono text-slate-200">
            {dns_records.map((rec, i) => (
              <tr key={i}>
                <td className="p-3 text-sky-400 font-bold">{rec.type}</td>
                <td className="p-3">{rec.host}</td>
                <td className="p-3 text-emerald-300">{rec.value}</td>
                <td className="p-3">{rec.ttl}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
        {steps_persian.map((s, idx) => (
          <li key={idx}>{s}</li>
        ))}
      </ul>

      <div className="flex justify-end">
        <button
          onClick={onVerifyDnsSsl}
          className="rounded-xl bg-sky-500 px-5 py-2 text-xs font-bold text-slate-950 hover:bg-sky-400"
        >
          بررسی مجدد اتصال DNS و صدور SSL (POST /v1/domains/check)
        </button>
      </div>
    </div>
  );
};
