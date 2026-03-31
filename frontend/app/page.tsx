"use client";

import dynamic from "next/dynamic";
import { useEffect, useState, useCallback, useMemo } from "react";
import SummaryCards from "./components/SummaryCards";
import RedZoneTable from "./components/RedZoneTable";
import ChartPlaceholder from "./components/ChartPlaceholder";

const BleedBarChart = dynamic(
  () => import("./components/BleedBarChart"),
  { ssr: false, loading: () => <ChartPlaceholder /> }
);

const TrendChart = dynamic(
  () => import("./components/TrendChart"),
  { ssr: false, loading: () => <ChartPlaceholder /> }
);

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

function messageFromUnknown(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "string") return err;
  if (err instanceof Event) return "An unexpected browser event occurred.";
  if (err != null && typeof err === "object" && "message" in err) {
    const m = (err as { message: unknown }).message;
    if (typeof m === "string") return m;
  }
  return "Failed to fetch data";
}

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

function PrinterpixWordmark() {
  return (
    <div className="flex items-baseline gap-0.5 font-bold tracking-tight">
      <span className="text-2xl text-[var(--pp-magenta)]">Printer</span>
      <span className="text-2xl text-[var(--pp-magenta-dark)]">pix</span>
    </div>
  );
}

export default function Dashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [datePreset, setDatePreset] = useState<"7d" | "30d" | "all">("all");
  const [campaign, setCampaign] = useState<string>("all");

  const fetchData = useCallback(async () => {
    if (!API) {
      setError("NEXT_PUBLIC_API_URL is not set. Add it to .env.local.");
      return;
    }
    try {
      const [alertsRes, trendsRes] = await Promise.all([
        fetch(`${API}/alerts?limit=100`),
        fetch(`${API}/trends`),
      ]);

      if (!alertsRes.ok || !trendsRes.ok) {
        throw new Error("API request failed");
      }

      const alertsData = await alertsRes.json();
      const trendsData = await trendsRes.json();

      setAlerts(alertsData);
      setTrends(trendsData);
      setLastUpdated(
        new Date().toLocaleString(undefined, {
          month: "numeric",
          day: "numeric",
          year: "numeric",
          hour: "numeric",
          minute: "2-digit",
          second: "2-digit",
          hour12: true,
        })
      );
      setError(null);
    } catch (err) {
      setError(messageFromUnknown(err));
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const campaignOptions = useMemo(() => {
    const names = new Set(alerts.map((a) => a.campaign_name).filter(Boolean));
    return [...names].sort();
  }, [alerts]);

  const filteredAlerts = useMemo(() => {
    let list = alerts;
    if (campaign !== "all") {
      list = list.filter((a) => a.campaign_name === campaign);
    }
    if (datePreset !== "all") {
      const now = Date.now();
      const ms =
        datePreset === "7d"
          ? 7 * 24 * 60 * 60 * 1000
          : 30 * 24 * 60 * 60 * 1000;
      const cutoff = now - ms;
      list = list.filter((a) => {
        const t = new Date(a.timestamp).getTime();
        return !Number.isNaN(t) && t >= cutoff;
      });
    }
    return list;
  }, [alerts, campaign, datePreset]);

  const filteredTrends = useMemo(() => {
    let list = trends;
    if (campaign !== "all") {
      list = list.filter((t) => t.campaign_name === campaign);
    }
    if (datePreset !== "all") {
      const now = Date.now();
      const ms =
        datePreset === "7d"
          ? 7 * 24 * 60 * 60 * 1000
          : 30 * 24 * 60 * 60 * 1000;
      const cutoff = now - ms;
      list = list.filter((t) => {
        const ts = new Date(t.timestamp).getTime();
        return !Number.isNaN(ts) && ts >= cutoff;
      });
    }
    return list;
  }, [trends, campaign, datePreset]);

  const thresholdUsed = useMemo(() => {
    if (filteredAlerts.length === 0) return 0;
    const sum = filteredAlerts.reduce((s, a) => s + (a.stat_threshold ?? 0), 0);
    return sum / filteredAlerts.length;
  }, [filteredAlerts]);

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-[var(--border-subtle)] bg-white px-4 py-2">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <span className="text-sm font-medium text-[var(--text-muted)]">
            CPC Anomaly Alerts — Red Zone Dashboard
          </span>
          <div className="flex gap-3 text-xs text-[var(--text-muted)]">
            <button
              type="button"
              className="hover:text-[#212121]"
              onClick={() => {
                setDatePreset("all");
                setCampaign("all");
              }}
            >
              Reset
            </button>
            <span className="text-[var(--border-subtle)]">|</span>
            <button type="button" className="hover:text-[#212121]">
              Share
            </button>
            <span className="text-[var(--border-subtle)]">|</span>
            <button type="button" className="hover:text-[#212121]">
              Edit
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        <div className="mb-6 flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-col gap-4">
            <PrinterpixWordmark />
            <h1 className="max-w-3xl text-xl font-bold leading-tight text-[var(--alert-red)] sm:text-2xl md:text-3xl">
              CPC Anomaly Alerts (Red Zone) — Ad Groups Bleeding Money
            </h1>
            <div className="flex flex-wrap gap-3">
              <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
                Select date range
                <select
                  value={datePreset}
                  onChange={(e) =>
                    setDatePreset(e.target.value as "7d" | "30d" | "all")
                  }
                  className="min-w-[180px] rounded border border-[var(--border-subtle)] bg-[var(--filter-bg)] px-3 py-2 text-sm text-[#212121] shadow-sm"
                >
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                  <option value="all">All time</option>
                </select>
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-[var(--text-muted)]">
                Campaign Name
                <select
                  value={campaign}
                  onChange={(e) => setCampaign(e.target.value)}
                  className="min-w-[220px] rounded border border-[var(--border-subtle)] bg-[var(--filter-bg)] px-3 py-2 text-sm text-[#212121] shadow-sm"
                >
                  <option value="all">All campaigns</option>
                  {campaignOptions.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <div className="w-full shrink-0 lg:max-w-md">
            <SummaryCards alerts={filteredAlerts} />
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
            API Error: {error}
          </div>
        )}

        <section className="mt-2">
          <h2 className="mb-3 text-base font-bold text-[var(--alert-red)]">
            CPC Anomaly Alerts — Red Zone
          </h2>
          <RedZoneTable alerts={filteredAlerts} />
        </section>

        <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <BleedBarChart alerts={filteredAlerts} />
          <TrendChart trends={filteredTrends} thresholdUsed={thresholdUsed} />
        </section>

        <footer className="mt-10 border-t border-[var(--border-subtle)] pt-4 text-xs text-[var(--text-muted)]">
          {lastUpdated && (
            <span>Data Last Updated: {lastUpdated}</span>
          )}
          <span className="mx-2">|</span>
          <a
            href="#privacy"
            className="underline hover:text-[#212121]"
            onClick={(e) => e.preventDefault()}
          >
            Privacy Policy
          </a>
        </footer>
      </main>
    </div>
  );
}
