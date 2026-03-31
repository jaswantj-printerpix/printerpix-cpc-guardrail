"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import type { Alert } from "../page";

function heatColor(t: number): string {
  const r = Math.round(34 + t * (220 - 34));
  const g = Math.round(120 + t * (40 - 120));
  const b = Math.round(50 + t * (40 - 50));
  return `rgb(${r},${g},${b})`;
}

export default function BleedBarChart({ alerts }: { alerts: Alert[] }) {
  const byCampaign = new Map<string, number>();
  for (const a of alerts) {
    const c = a.campaign_name ?? "";
    byCampaign.set(c, (byCampaign.get(c) ?? 0) + (a.cost ?? 0));
  }
  const rows = [...byCampaign.entries()]
    .map(([name, bleed]) => ({ name, bleed }))
    .sort((a, b) => b.bleed - a.bleed)
    .slice(0, 12);

  if (rows.length === 0) {
    return (
      <div className="rounded border border-[var(--border-subtle)] bg-[var(--card-bg)] p-8 text-center text-[var(--text-muted)]">
        No campaign bleed data.
      </div>
    );
  }

  const maxBleed = Math.max(...rows.map((r) => r.bleed), 1);
  const minBleed = Math.min(...rows.map((r) => r.bleed), 0);

  return (
    <div className="rounded border border-[var(--border-subtle)] bg-white p-4">
      <h3 className="mb-3 text-sm font-bold text-[var(--alert-red)]">
        Top Campaigns by Bleed
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={rows}
          margin={{ top: 8, right: 8, left: 0, bottom: 48 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="name"
            stroke="#616161"
            tick={{ fontSize: 10 }}
            interval={0}
            angle={-45}
            textAnchor="end"
            height={70}
          />
          <YAxis
            stroke="#616161"
            tick={{ fontSize: 11 }}
            tickFormatter={(v) =>
              typeof v === "number" && !Number.isNaN(v)
                ? `£${v.toFixed(0)}`
                : ""
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #e0e0e0",
              borderRadius: 4,
            }}
            formatter={(value: unknown) => {
              const n = typeof value === "number" ? value : Number(value);
              return [
                Number.isFinite(n) ? `£${n.toFixed(2)}` : "—",
                "Bleed",
              ];
            }}
          />
          <Bar dataKey="bleed" radius={[2, 2, 0, 0]}>
            {rows.map((entry, index) => {
              const t =
                maxBleed === minBleed
                  ? 0.5
                  : (entry.bleed - minBleed) / (maxBleed - minBleed);
              return <Cell key={`cell-${index}`} fill={heatColor(t)} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
