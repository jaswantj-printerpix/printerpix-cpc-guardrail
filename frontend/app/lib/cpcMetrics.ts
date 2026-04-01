/** CPC vs stat threshold (from API: BQ threshold_used). */
export function cpcSpikeVsThresholdPercent(a: {
  current_cpc?: number | null;
  stat_threshold?: number | null;
}): number | null {
  const t = a.stat_threshold;
  const c = a.current_cpc;
  if (t == null || c == null || Number(t) <= 0) return null;
  return Math.round(((Number(c) - Number(t)) / Number(t)) * 1000) / 10;
}

/** Prefer BQ `CPC_Spike_Percent` (`cpc_spike_percent`); else legacy `percent_above_baseline`; else derived. */
export function displayCpcSpikePercent(a: {
  cpc_spike_percent?: number | null;
  percent_above_baseline?: number | null;
  current_cpc?: number | null;
  stat_threshold?: number | null;
}): number | null {
  for (const raw of [a.cpc_spike_percent, a.percent_above_baseline]) {
    if (raw != null && Number.isFinite(Number(raw))) {
      return Math.round(Number(raw) * 1000) / 1000;
    }
  }
  return cpcSpikeVsThresholdPercent(a);
}

/** Prefer BQ `Money_Bleeding`; else `cost`. */
export function moneyBleedingAmount(a: {
  money_bleeding?: number | null;
  cost?: number | null;
}): number {
  const m = a.money_bleeding;
  if (m != null && Number.isFinite(Number(m))) return Number(m);
  return Number(a.cost ?? 0);
}
