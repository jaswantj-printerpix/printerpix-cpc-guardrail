"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import type { TrendPoint } from "../page";

const COLORS = [
  "#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6",
  "#8b5cf6", "#ec4899", "#14b8a6", "#f43f5e", "#6366f1",
];

export default function TrendChart({ trends }: { trends: TrendPoint[] }) {
  if (trends.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
        No trend data in the last 24 hours.
      </div>
    );
  }

  // Group by ad group and pivot into chart-friendly format
  // Each timestamp becomes a row, each ad group becomes a column
  const adGroups = [...new Set(trends.map((t) => t.ad_group_name))];

  const timeMap = new Map<string, Record<string, number | string>>();

  for (const t of trends) {
    const timeKey = new Date(t.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    if (!timeMap.has(timeKey)) {
      timeMap.set(timeKey, { time: timeKey });
    }
    timeMap.get(timeKey)![t.ad_group_name] = t.current_cpc;
  }

  const chartData = [...timeMap.values()].reverse(); // oldest first

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="time"
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
          />
          <YAxis
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            tickFormatter={(v: number) => `$${v.toFixed(2)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#111827",
              border: "1px solid #374151",
              borderRadius: "8px",
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, ""]}
          />
          <Legend />
          {adGroups.slice(0, 10).map((ag, i) => (
            <Line
              key={ag}
              type="monotone"
              dataKey={ag}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
