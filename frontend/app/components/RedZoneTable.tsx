"use client";

import type { CSSProperties } from "react";
import type { Alert } from "../page";

function heatMapStyle(cost: number, min: number, max: number): CSSProperties {
  if (max === min) {
    return { backgroundColor: "rgb(34, 139, 34)", color: "#fff" };
  }
  const t = (cost - min) / (max - min);
  const r = Math.round(34 + t * (220 - 34));
  const g = Math.round(120 + t * (40 - 120));
  const b = Math.round(50 + t * (40 - 50));
  return {
    backgroundColor: `rgb(${r},${g},${b})`,
    color: t > 0.55 ? "#fff" : "#0d1f0d",
    fontWeight: 600,
  };
}

export default function RedZoneTable({ alerts }: { alerts: Alert[] }) {
  const costs = alerts.map((a) => a.cost ?? 0);
  const minCost = costs.length ? Math.min(...costs) : 0;
  const maxCost = costs.length ? Math.max(...costs) : 0;

  if (alerts.length === 0) {
    return (
      <div className="rounded border border-[var(--border-subtle)] bg-[var(--card-bg)] p-8 text-center text-[var(--text-muted)]">
        No alerts — all CPCs within thresholds.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded border border-[var(--border-subtle)]">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="bg-[var(--table-header)] text-left text-[#212121]">
            <th className="px-3 py-2.5 font-bold">#</th>
            <th className="px-3 py-2.5 font-bold">Campaign Name</th>
            <th className="px-3 py-2.5 font-bold">Ad Group</th>
            <th className="px-3 py-2.5 text-right font-bold">Money Bleeding</th>
            <th className="px-3 py-2.5 text-right font-bold">CPC Spike %</th>
            <th className="px-3 py-2.5 text-right font-bold">Current CPC</th>
            <th className="px-3 py-2.5 text-right font-bold">Cost</th>
            <th className="px-3 py-2.5 text-right font-bold">Clicks</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((a, i) => (
            <tr
              key={`${a.campaign_name}-${a.ad_group_name}-${i}`}
              className={i % 2 === 0 ? "bg-white" : "bg-[#fafafa]"}
            >
              <td className="border-t border-[var(--border-subtle)] px-3 py-2 text-[var(--text-muted)]">
                {i + 1}
              </td>
              <td className="border-t border-[var(--border-subtle)] px-3 py-2 font-medium">
                {a.campaign_name}
              </td>
              <td className="border-t border-[var(--border-subtle)] px-3 py-2">
                {a.ad_group_name}
              </td>
              <td
                className="border-t border-[var(--border-subtle)] px-3 py-2 text-right tabular-nums"
                style={heatMapStyle(a.cost ?? 0, minCost, maxCost)}
              >
                £{(a.cost ?? 0).toFixed(2)}
              </td>
              <td className="border-t border-[var(--border-subtle)] px-3 py-2 text-right tabular-nums">
                {(a.percent_above_baseline ?? 0).toFixed(2)}%
              </td>
              <td className="border-t border-[var(--border-subtle)] px-3 py-2 text-right tabular-nums">
                £{(a.current_cpc ?? 0).toFixed(2)}
              </td>
              <td className="border-t border-[var(--border-subtle)] px-3 py-2 text-right tabular-nums">
                £{(a.cost ?? 0).toFixed(2)}
              </td>
              <td className="border-t border-[var(--border-subtle)] px-3 py-2 text-right tabular-nums">
                {a.clicks}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
