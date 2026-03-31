"use client";

import type { Alert } from "../page";

function severityColor(pct: number): string {
  if (pct >= 50) return "bg-red-900/60 text-red-200";
  if (pct >= 25) return "bg-orange-900/40 text-orange-200";
  return "bg-yellow-900/30 text-yellow-200";
}

function severityBadge(pct: number): string {
  if (pct >= 50) return "CRITICAL";
  if (pct >= 25) return "HIGH";
  return "ELEVATED";
}

export default function RedZoneTable({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
        No alerts — all CPCs within thresholds.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead className="bg-gray-900 text-gray-400 text-left">
          <tr>
            <th className="px-4 py-3">Severity</th>
            <th className="px-4 py-3">Campaign</th>
            <th className="px-4 py-3">Ad Group</th>
            <th className="px-4 py-3 text-right">CPC</th>
            <th className="px-4 py-3 text-right">Baseline</th>
            <th className="px-4 py-3 text-right">% Above</th>
            <th className="px-4 py-3 text-right">Max Allowable</th>
            <th className="px-4 py-3 text-right">Cost</th>
            <th className="px-4 py-3 text-right">Clicks</th>
            <th className="px-4 py-3">Alert Reason</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((a, i) => (
            <tr
              key={`${a.campaign_name}-${a.ad_group_name}-${i}`}
              className={`border-t border-gray-800 ${severityColor(a.percent_above_baseline)} hover:brightness-110 transition-all`}
            >
              <td className="px-4 py-3">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                    a.percent_above_baseline >= 50
                      ? "bg-red-600 text-white"
                      : a.percent_above_baseline >= 25
                        ? "bg-orange-600 text-white"
                        : "bg-yellow-600 text-black"
                  }`}
                >
                  {severityBadge(a.percent_above_baseline)}
                </span>
              </td>
              <td className="px-4 py-3 font-medium max-w-48 truncate">
                {a.campaign_name}
              </td>
              <td className="px-4 py-3 max-w-40 truncate">
                {a.ad_group_name}
              </td>
              <td className="px-4 py-3 text-right font-mono font-bold">
                ${a.current_cpc?.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right font-mono text-gray-400">
                ${a.baseline_mean?.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right font-mono font-bold">
                {a.percent_above_baseline?.toFixed(1)}%
              </td>
              <td className="px-4 py-3 text-right font-mono text-gray-400">
                ${a.max_allowable_cpc?.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right font-mono">
                ${a.cost?.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right font-mono">
                {a.clicks}
              </td>
              <td className="px-4 py-3 text-xs text-gray-400 max-w-56 truncate">
                {a.alert_reason}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
