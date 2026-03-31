"use client";

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import type { TrendPoint } from "../page";

export default function TrendChart({
  trends,
  thresholdUsed,
}: {
  trends: TrendPoint[];
  thresholdUsed: number;
}) {
  if (trends.length === 0) {
    return (
      <div className="rounded border border-[var(--border-subtle)] bg-[var(--card-bg)] p-8 text-center text-[var(--text-muted)]">
        No trend data in the last 24 hours.
      </div>
    );
  }

  const timeMap = new Map<
    string,
    { sum: number; count: number; time: string }
  >();

  for (const t of trends) {
    const timeKey = new Date(t.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    const prev = timeMap.get(timeKey);
    const cpc = t.current_cpc ?? 0;
    if (!prev) {
      timeMap.set(timeKey, { sum: cpc, count: 1, time: timeKey });
    } else {
      prev.sum += cpc;
      prev.count += 1;
    }
  }

  const chartData = [...timeMap.values()]
    .map((row) => ({
      time: row.time,
      avgCpc: row.sum / row.count,
      threshold_used: thresholdUsed > 0 ? thresholdUsed : row.sum / row.count,
    }))
    .sort(
      (a, b) =>
        new Date(`1970-01-01 ${a.time}`).getTime() -
        new Date(`1970-01-01 ${b.time}`).getTime()
    );

  return (
    <div className="rounded border border-[var(--border-subtle)] bg-white p-4">
      <h3 className="mb-3 text-sm font-bold text-[var(--alert-red)]">
        CPC Trend / Volatility
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis dataKey="time" stroke="#616161" tick={{ fontSize: 11 }} />
          <YAxis
            yAxisId="left"
            stroke="#616161"
            tick={{ fontSize: 11 }}
            tickFormatter={(v) =>
              typeof v === "number" && Number.isFinite(v)
                ? `£${v.toFixed(2)}`
                : ""
            }
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#616161"
            tick={{ fontSize: 11 }}
            tickFormatter={(v) =>
              typeof v === "number" && Number.isFinite(v)
                ? `£${v.toFixed(2)}`
                : ""
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #e0e0e0",
              borderRadius: 4,
            }}
            formatter={(value: unknown, name: unknown) => {
              const n = typeof value === "number" ? value : Number(value);
              const label =
                name === "avgCpc" ? "Average_CPC" : "threshold_used";
              return [
                Number.isFinite(n) ? `£${n.toFixed(2)}` : "—",
                label,
              ];
            }}
          />
          <Legend
            formatter={(value: unknown) =>
              value === "avgCpc" ? "Average_CPC" : "threshold_used"
            }
          />
          <Bar
            yAxisId="right"
            dataKey="threshold_used"
            fill="#fb923c"
            name="threshold_used"
            radius={[2, 2, 0, 0]}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="avgCpc"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            name="avgCpc"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
