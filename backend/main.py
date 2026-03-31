"""
CPC Guardrail API — reads anomaly alerts from BigQuery table
  printerpix-general.GA_Avanish.CPC_Anomaly_Alerts

Table schema (see BigQuery console): run_timestamp, alert_date, alert_hour,
campaign_id, campaign_name, ad_group_id, ad_group_name, current_cpc,
threshold_used, cost, clicks, impressions, notes
(no baseline_mean / percent_above_baseline columns — derived in API).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import os
from datetime import datetime, timezone
from typing import Optional

app = FastAPI(title="Printerpix CPC Guardrail API")

# --- BigQuery table: printerpix-general.GA_Avanish.CPC_Anomaly_Alerts ---
PROJECT_ID = os.getenv("PROJECT_ID", "").strip()
TABLE = os.getenv("TABLE", "").strip()
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "").strip()


def resolve_full_table_id() -> Optional[str]:
    if BIGQUERY_TABLE:
        return BIGQUERY_TABLE
    if PROJECT_ID and TABLE:
        return f"{PROJECT_ID}.{TABLE}"
    return None


def _cors_origins() -> list[str]:
    origins = ["http://localhost:3000"]
    raw = os.getenv("FRONTEND_URL", "")
    for url in raw.split(","):
        u = url.strip().rstrip("/")
        if u:
            origins.append(u)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https://.*\.vercel.app",
    allow_methods=["GET"],
    allow_headers=["*"],
)

creds_json = os.getenv("GOOGLE_CREDENTIALS")
if creds_json:
    with open("/tmp/credentials.json", "w", encoding="utf-8") as f:
        f.write(creds_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"

_bq_client: Optional[bigquery.Client] = None


def get_bq_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        fid = resolve_full_table_id()
        project = PROJECT_ID or (fid.split(".", 1)[0] if fid else None)
        _bq_client = bigquery.Client(project=project)
    return _bq_client


def _spike_pct_vs_threshold(current_cpc: object, threshold_used: object) -> Optional[float]:
    """% above threshold_used (UI field still named percent_above_baseline)."""
    if current_cpc is None or threshold_used is None:
        return None
    try:
        c = float(current_cpc)
        t = float(threshold_used)
        if t > 0:
            return round((c - t) / t * 100, 1)
    except (TypeError, ValueError):
        pass
    return None


@app.get("/version")
async def version():
    return {"api": "cpc-guardrail", "build": "2026-03-31-bq-schema-v5"}


def _normalize_alert_row(d: dict) -> dict:
    """Map BigQuery row → frontend Alert shape."""
    d = dict(d)
    d["alert_reason"] = d.get("notes")
    d["timestamp"] = d.get("run_timestamp")
    # Table column is threshold_used; dashboard expects stat_threshold
    d["stat_threshold"] = d.get("threshold_used")
    d["baseline_mean"] = None
    d["max_allowable_cpc"] = None
    d["dynamic_conv_rate"] = None
    d["percent_above_baseline"] = _spike_pct_vs_threshold(
        d.get("current_cpc"), d.get("threshold_used")
    )
    return d


@app.get("/alerts")
async def get_red_zone_alerts(limit: int = Query(default=10, ge=1, le=100)):
    full_table = resolve_full_table_id()
    if not full_table:
        raise HTTPException(
            status_code=503,
            detail=(
                "BigQuery table not configured. Set BIGQUERY_TABLE="
                "printerpix-general.GA_Avanish.CPC_Anomaly_Alerts "
                "or PROJECT_ID + TABLE."
            ),
        )

    # Columns must match physical table (see BigQuery Schema tab)
    query = f"""
        SELECT
            run_timestamp,
            alert_date,
            alert_hour,
            campaign_id,
            campaign_name,
            ad_group_id,
            ad_group_name,
            current_cpc,
            threshold_used,
            cost,
            clicks,
            impressions,
            notes
        FROM `{full_table}`
        ORDER BY run_timestamp DESC, current_cpc DESC
        LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)]
    )
    try:
        rows = list(get_bq_client().query(query, job_config=job_config))
        return [_normalize_alert_row(dict(row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/trends")
async def get_cpc_trends():
    full_table = resolve_full_table_id()
    if not full_table:
        raise HTTPException(
            status_code=503,
            detail="BigQuery table not configured.",
        )

    query = f"""
        SELECT
            campaign_name,
            ad_group_name,
            current_cpc,
            run_timestamp AS `timestamp`
        FROM `{full_table}`
        WHERE run_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        ORDER BY run_timestamp DESC
    """
    try:
        rows = list(get_bq_client().query(query))
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health():
    configured = resolve_full_table_id() is not None
    return {
        "status": "healthy",
        "time": datetime.now(timezone.utc).isoformat(),
        "bigquery_table_configured": configured,
        "table": resolve_full_table_id() if configured else None,
    }
