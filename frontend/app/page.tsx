"use client";

import { useEffect, useState, useCallback } from "react";
import SummaryCards from "./components/SummaryCards";
import RedZoneTable from "./components/RedZoneTable";
import TrendChart from "./components/TrendChart";

const API = process.env.NEXT_PUBLIC_API_URL;

export interface Alert {
  campaign_name: string;
  ad_group_name: string;
  current_cpc: number;
  alert_reason: string;
  timestamp: string;
  cost: number;
  clicks: number;
  percent_above_baseline: number;
  baseline_mean: number;
  stat_threshold: number;
  max_allowable_cpc: number;
  dynamic_conv_rate: number;
}

export interface TrendPoint {
  campaign_name: string;
  ad_group_name: string;
  current_cpc: number;
  timestamp: string;
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [alertsRes, trendsRes] = await Promise.all([
        fetch(`${API}/alerts?limit=10`),
        fetch(`${API}/trends`),
      ]);

      if (!alertsRes.ok || !trendsRes.ok) {
        throw new Error("API request failed");
      }

      const alertsData = await alertsRes.json();
      const trendsData = await trendsRes.json();

      setAlerts(alertsData);
      setTrends(trendsData);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60_000); // auto-refresh every 60s
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            CPC Guardrail Dashboard
          </h1>
          <p className="text-gray-400 mt-1">
            Printerpix — Real-time CPC anomaly detection
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          {lastUpdated && <p>Last updated: {lastUpdated}</p>}
          <p className="text-xs">Auto-refreshes every 60s</p>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg mb-6">
          API Error: {error}
        </div>
      )}

      {/* Summary Cards */}
      <SummaryCards alerts={alerts} />

      {/* Red Zone Table */}
      <section className="mt-8">
        <h2 className="text-xl font-semibold mb-4 text-red-400">
          Red Zone — Top Ad Groups Bleeding Money
        </h2>
        <RedZoneTable alerts={alerts} />
      </section>

      {/* Trend Chart */}
      <section className="mt-8">
        <h2 className="text-xl font-semibold mb-4">
          CPC Trends — Last 24 Hours
        </h2>
        <TrendChart trends={trends} />
      </section>
    </main>
  );
}
