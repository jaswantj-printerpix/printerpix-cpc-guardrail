"use client";

import type { Alert } from "../page";
import { displayCpcSpikePercent, moneyBleedingAmount } from "../lib/cpcMetrics";

export default function SummaryCards({ alerts }: { alerts: Alert[] }) {
  const totalAlerts = alerts.length;

  const spikeValues = alerts
    .map((a) => displayCpcSpikePercent(a))
    .filter((v): v is number => v != null && !Number.isNaN(v));
  const avgSpike =
    spikeValues.length > 0
      ? spikeValues.reduce((s, v) => s + v, 0) / spikeValues.length
      : 0;

  const totalMoneyBleeding = alerts.reduce(
    (sum, a) => sum + moneyBleedingAmount(a),
    0
  );

  const campaignsAffected = new Set(
    alerts.map((a) => a.campaign_name).filter(Boolean)
  ).size;

  const cards = [
    {
      label: "Total Money Bleeding",
      value: `£${totalMoneyBleeding.toFixed(2)}`,
      labelClass: "text-[var(--alert-red)]",
    },
    {
      label: "Avg. CPC Spike %",
      value: `${avgSpike.toFixed(2)}%`,
      labelClass: "text-[var(--alert-red)]",
    },
    {
      label: "No. of Active Alerts",
      value: String(totalAlerts),
      labelClass: "text-[var(--kpi-blue)]",
    },
    {
      label: "Campaigns Affected",
      value: String(campaignsAffected),
      labelClass: "text-[var(--kpi-blue)]",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded border border-[var(--border-subtle)] bg-[var(--card-bg)] px-4 py-3 sm:px-5 sm:py-4"
        >
          <p
            className={`text-xs font-medium leading-tight sm:text-sm ${card.labelClass}`}
          >
            {card.label}
          </p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-[#212121] sm:text-3xl">
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
}
