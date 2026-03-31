"use client";

import type { Alert } from "../page";

export default function SummaryCards({ alerts }: { alerts: Alert[] }) {
  const totalAlerts = alerts.length;

  const highestSpike = alerts.reduce(
    (max, a) => Math.max(max, a.percent_above_baseline ?? 0),
    0
  );

  const totalWastedSpend = alerts.reduce((sum, a) => sum + (a.cost ?? 0), 0);

  const avgCpc =
    alerts.length > 0
      ? alerts.reduce((sum, a) => sum + (a.current_cpc ?? 0), 0) / alerts.length
      : 0;

  const cards = [
    {
      label: "Active Alerts",
      value: totalAlerts,
      color: "text-red-400",
      bg: "bg-red-950/40 border-red-900/50",
    },
    {
      label: "Highest CPC Spike",
      value: `${highestSpike.toFixed(1)}%`,
      sub: "above baseline",
      color: "text-orange-400",
      bg: "bg-orange-950/40 border-orange-900/50",
    },
    {
      label: "Total Flagged Spend",
      value: `$${totalWastedSpend.toFixed(2)}`,
      color: "text-yellow-400",
      bg: "bg-yellow-950/40 border-yellow-900/50",
    },
    {
      label: "Avg Flagged CPC",
      value: `$${avgCpc.toFixed(2)}`,
      color: "text-blue-400",
      bg: "bg-blue-950/40 border-blue-900/50",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-xl border p-5 ${card.bg}`}
        >
          <p className="text-sm text-gray-400">{card.label}</p>
          <p className={`text-3xl font-bold mt-1 ${card.color}`}>
            {card.value}
          </p>
          {card.sub && (
            <p className="text-xs text-gray-500 mt-1">{card.sub}</p>
          )}
        </div>
      ))}
    </div>
  );
}
