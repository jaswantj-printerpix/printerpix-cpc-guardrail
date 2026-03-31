#!/usr/bin/env python3
"""
Hourly CPC anomaly job — Google Ads → BigQuery `CPC_Anomaly_Alerts`.

Replaces:
  5 * * * * flock -n /tmp/CPC_Alerts_Jas.lock -c \\
    "source .../.venv/bin/activate && python .../CPC_Alerts_Jas.py"

Railway: separate service, Cron `5 * * * *` (UTC), same env pattern as the API.
"""

from __future__ import annotations

import fcntl
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.cloud import bigquery

LOCK_PATH = os.getenv("CPC_ALERTS_LOCK_PATH", "/tmp/CPC_Alerts_Jas.lock")

# --- BigQuery target (must match API reader) ---
BIGQUERY_TABLE = os.getenv(
    "BIGQUERY_TABLE", "printerpix-general.GA_Avanish.CPC_Anomaly_Alerts"
).strip()
PROJECT_ID = os.getenv("PROJECT_ID", "printerpix-general").strip()

# --- Google Ads ---
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "5176633302").strip()

# --- Alert tuning (env overrides) ---
MARKETING_ALLOWABLE_PER_SALE = float(
    os.getenv("MARKETING_ALLOWABLE_PER_SALE", "20.0")
)
CPC_ANOMALY_MULTIPLIER = float(os.getenv("CPC_ANOMALY_MULTIPLIER", "2.0"))
MIN_COST_FOR_ALERT = float(os.getenv("MIN_COST_FOR_ALERT", "15.0"))
MIN_CLICKS_FOR_ALERT = int(os.getenv("MIN_CLICKS_FOR_ALERT", "5"))
DAYS_FOR_BASELINE = int(os.getenv("DAYS_FOR_BASELINE", "1"))


def _load_gcp_credentials() -> None:
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        Path("/tmp/credentials.json").write_text(creds_json, encoding="utf-8")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"


def _google_ads_client() -> GoogleAdsClient:
    """
    Railway: set one of:
      GOOGLE_ADS_YAML — full contents of google-ads.yaml (multiline secret)
      GOOGLE_ADS_CONFIG_JSON — JSON dict accepted by GoogleAdsClient.load_from_dict
    Local: GOOGLE_ADS_YAML_PATH — path to google-ads.yaml
    """
    yaml_path = os.getenv("GOOGLE_ADS_YAML_PATH", "").strip()
    if yaml_path and Path(yaml_path).is_file():
        return GoogleAdsClient.load_from_storage(yaml_path)

    yaml_content = os.getenv("GOOGLE_ADS_YAML", "").strip()
    if yaml_content:
        p = Path("/tmp/google-ads.yaml")
        p.write_text(yaml_content, encoding="utf-8")
        return GoogleAdsClient.load_from_storage(str(p))

    cfg_json = os.getenv("GOOGLE_ADS_CONFIG_JSON", "").strip()
    if cfg_json:
        cfg = json.loads(cfg_json)
        return GoogleAdsClient.load_from_dict(cfg)

    raise RuntimeError(
        "Set GOOGLE_ADS_YAML, GOOGLE_ADS_CONFIG_JSON, or GOOGLE_ADS_YAML_PATH "
        "for Google Ads API client config."
    )


def _bq_project() -> str:
    if BIGQUERY_TABLE and "." in BIGQUERY_TABLE:
        return BIGQUERY_TABLE.split(".", 1)[0]
    return PROJECT_ID


def _acquire_lock():
    lockf = open(LOCK_PATH, "w", encoding="utf-8")
    try:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(
            "CPC_Alerts_Jas: lock held — skipping (another run active).",
            file=sys.stderr,
            flush=True,
        )
        lockf.close()
        sys.exit(0)
    return lockf


def get_previous_hour_range():
    now = datetime.now(timezone.utc)
    prev_hour = now - timedelta(hours=1)
    prev_hour = prev_hour.replace(minute=0, second=0, microsecond=0)

    date_str = prev_hour.strftime("%Y-%m-%d")
    hour_int = prev_hour.hour
    return date_str, hour_int


def fetch_historical_data(client: GoogleAdsClient, date_str: str, hour_int: int):
    ga_service = client.get_service("GoogleAdsService")

    start_date = (
        datetime.now(timezone.utc) - timedelta(days=DAYS_FOR_BASELINE + 1)
    ).strftime("%Y-%m-%d")

    query = f"""
    SELECT
      metrics.average_cpc,
      metrics.clicks,
      metrics.conversions,
      segments.hour
    FROM ad_group
    WHERE segments.date BETWEEN '{start_date}' AND '{date_str}'
      AND segments.hour = {hour_int}
      AND metrics.clicks > 0
    """

    search_request = client.get_type("SearchGoogleAdsRequest")
    search_request.customer_id = GOOGLE_ADS_CUSTOMER_ID
    search_request.query = query

    cpc_values = []
    total_clicks = 0
    total_conversions = 0.0

    for row in ga_service.search(search_request):
        avg_cpc = row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0.0
        clicks = row.metrics.clicks
        conversions = row.metrics.conversions if row.metrics.conversions else 0.0

        if avg_cpc > 0:
            cpc_values.append(avg_cpc)

        total_clicks += clicks
        total_conversions += conversions

    return cpc_values, total_clicks, total_conversions


def run_pipeline() -> None:
    _load_gcp_credentials()
    client = _google_ads_client()
    bq_client = bigquery.Client(project=_bq_project())

    try:
        ga_service = client.get_service("GoogleAdsService")

        date_str, hour_int = get_previous_hour_range()
        print(
            f"Running CPC Alert Engine for previous hour: {date_str} "
            f"hour {hour_int:02d}:00 UTC",
            flush=True,
        )

        current_query = f"""
        SELECT
          campaign.id,
          campaign.name,
          ad_group.id,
          ad_group.name,
          metrics.cost_micros,
          metrics.average_cpc,
          metrics.clicks,
          metrics.impressions,
          segments.date,
          segments.hour
        FROM ad_group
        WHERE segments.date = '{date_str}'
          AND segments.hour = {hour_int}
        ORDER BY metrics.cost_micros DESC
        """

        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = GOOGLE_ADS_CUSTOMER_ID
        search_request.query = current_query

        results = []
        for row in ga_service.search(search_request):
            cost = row.metrics.cost_micros / 1_000_000
            avg_cpc = (
                row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0.0
            )

            record = {
                "run_timestamp": datetime.now(timezone.utc).isoformat(),
                "date": date_str,
                "hour": hour_int,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "cost": round(cost, 2),
                "average_cpc": round(avg_cpc, 4),
                "clicks": row.metrics.clicks,
                "impressions": row.metrics.impressions,
            }
            results.append(record)

        print(f"Fetched {len(results)} ad group rows", flush=True)

        campaign_top = {}
        for r in results:
            cid = r["campaign_id"]
            if cid not in campaign_top or r["cost"] > campaign_top[cid]["cost"]:
                campaign_top[cid] = r

        top_adgroups = list(campaign_top.values())
        print(f"Analyzing {len(top_adgroups)} top ad groups", flush=True)

        historical_cpcs, hist_clicks, hist_conversions = fetch_historical_data(
            client, date_str, hour_int
        )

        if len(historical_cpcs) < 3:
            print(
                "Not enough historical data for reliable baseline.",
                flush=True,
            )
            rolling_mean = 0.0
            rolling_std = 0.0
            conv_rate = 0.0
        else:
            rolling_mean = statistics.mean(historical_cpcs)
            rolling_std = (
                statistics.stdev(historical_cpcs)
                if len(historical_cpcs) > 1
                else 0.0
            )
            conv_rate = (hist_conversions / hist_clicks) if hist_clicks > 0 else 0.0
            print(
                f"24h Baseline: Mean CPC £{rolling_mean:.4f} | Std £{rolling_std:.4f} "
                f"| Conv Rate {conv_rate * 100:.2f}%",
                flush=True,
            )

        max_allowable_cpc = MARKETING_ALLOWABLE_PER_SALE * conv_rate
        print(f"Max Allowable CPC (dynamic): £{max_allowable_cpc:.4f}", flush=True)

        alerts = []
        for r in top_adgroups:
            current_cpc = r["average_cpc"]
            cost = r["cost"]
            clicks = r["clicks"]

            if (
                current_cpc <= 0
                or cost < MIN_COST_FOR_ALERT
                or clicks < MIN_CLICKS_FOR_ALERT
            ):
                continue

            stat_threshold = CPC_ANOMALY_MULTIPLIER * (rolling_mean + rolling_std)
            is_statistical_anomaly = current_cpc > stat_threshold
            is_unprofitable = current_cpc > max_allowable_cpc

            if is_statistical_anomaly and is_unprofitable:
                percent_above = (
                    ((current_cpc - rolling_mean) / rolling_mean * 100)
                    if rolling_mean > 0
                    else 0
                )

                # Row shape must match BigQuery table schema (GA_Avanish.CPC_Anomaly_Alerts)
                alert_record = {
                    "run_timestamp": datetime.now(timezone.utc).isoformat(),
                    "alert_date": date_str,
                    "alert_hour": hour_int,
                    "campaign_id": r["campaign_id"],
                    "campaign_name": r["campaign_name"],
                    "ad_group_id": r["ad_group_id"],
                    "ad_group_name": r["ad_group_name"],
                    "current_cpc": round(current_cpc, 4),
                    "threshold_used": round(stat_threshold, 4),
                    "cost": round(cost, 2),
                    "clicks": clicks,
                    "impressions": r["impressions"],
                    "notes": (
                        f"CPC > {CPC_ANOMALY_MULTIPLIER}×(mean+std) AND exceeds "
                        f"dynamic max £{max_allowable_cpc:.4f}; "
                        f"spike vs baseline {percent_above:.1f}%"
                    ),
                }
                alerts.append(alert_record)

                print(
                    f"ALERT: {r['campaign_name']} | {r['ad_group_name']} → "
                    f"CPC £{current_cpc:.4f} (stat threshold £{stat_threshold:.4f}, "
                    f"max allowable £{max_allowable_cpc:.4f})",
                    flush=True,
                )

        if alerts:
            errors = bq_client.insert_rows_json(BIGQUERY_TABLE, alerts)
            if errors:
                print(f"Error inserting alerts: {errors}", file=sys.stderr, flush=True)
                sys.exit(1)
            print(
                f"{len(alerts)} CPC Anomaly Alert(s) successfully logged to {BIGQUERY_TABLE}",
                flush=True,
            )
        else:
            print("No CPC anomalies detected this hour.", flush=True)

    except GoogleAdsException as ex:
        print(f"Google Ads API error: {ex}", file=sys.stderr, flush=True)
        for error in ex.failure.errors:
            print(f"   - {error.error_code}: {error.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr, flush=True)
        raise


def main() -> None:
    lockf = _acquire_lock()
    try:
        run_pipeline()
    finally:
        try:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
        finally:
            lockf.close()


if __name__ == "__main__":
    main()
