/** CPC vs stat threshold (from API: BQ threshold_used), not stored in BigQuery. */
export function cpcSpikeVsThresholdPercent(a: {
  current_cpc?: number | null;
  stat_threshold?: number | null;
}): number | null {
  const t = a.stat_threshold;
  const c = a.current_cpc;
  if (t == null || c == null || Number(t) <= 0) return null;
  return Math.round(((Number(c) - Number(t)) / Number(t)) * 1000) / 10;
}
