"""
CPC Guardrail API — reads anomaly alerts from BigQuery table
  printerpix-general.GA_Avanish.CPC_Alerts_Updated

Schema matches GA_Avanish.CPC_Alerts_Updated: base columns plus Average_CPC,
CPC_vs_Threshold, CPC_Spike_Percent, CTR, Money_Bleeding, Record_Count (exposed as snake_case JSON).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import os
from datetime import datetime, timezone
from typing import Optional

app = FastAPI(title="Printerpix CPC Guardrail API")


@app.get("/")
async def root():
    """Railway smoke test — if this 404s, this public URL is not running this FastAPI app."""
    return {
        "service": "printerpix-cpc-guardrail-api",
        "build": "2026-04-01-cpc-alerts-updated",
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "alerts": "/alerts",
            "docs": "/docs",
        },
    }


# --- BigQuery table: printerpix-general.GA_Avanish.CPC_Alerts_Updated ---
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

def _alerts_sql(full_table: str) -> str:
    # SELECT * keeps the API aligned with CPC_Alerts_Updated as you add materialized fields.
    return f"""
        SELECT *
        FROM `{full_table}`
        ORDER BY run_timestamp DESC, current_cpc DESC
        LIMIT @limit
    """


def get_bq_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        fid = resolve_full_table_id()
        project = PROJECT_ID or (fid.split(".", 1)[0] if fid else None)
        _bq_client = bigquery.Client(project=project)
    return _bq_client


@app.get("/version")
async def version():
    """Use this to verify Railway/Vercel are hitting the API you think."""
    return {
        "api": "cpc-guardrail",
        "build": "2026-04-01-diagnostic-cpc-alerts-updated",
        "git_commit": os.getenv("RAILWAY_GIT_COMMIT_SHA", ""),
        "git_branch": os.getenv("RAILWAY_GIT_BRANCH", ""),
        "resolved_bq_table": resolve_full_table_id(),
        "alerts_query": "SELECT * … ORDER BY run_timestamp DESC, current_cpc DESC",
    }


def _normalize_alert_row(d: dict) -> dict:
    """Map BigQuery row → stable JSON for the dashboard (snake_case API keys)."""
    d = dict(d)
    d["alert_reason"] = d.get("notes")
    d["timestamp"] = d.get("run_timestamp")
    d["stat_threshold"] = d.get("threshold_used")

    # CPC_Alerts_Updated uses Looker-style names in BigQuery
    bq_to_api = (
        ("Average_CPC", "average_cpc"),
        ("CPC_vs_Threshold", "cpc_vs_threshold"),
        ("CPC_Spike_Percent", "cpc_spike_percent"),
        ("CTR", "ctr"),
        ("Money_Bleeding", "money_bleeding"),
        ("Record_Count", "record_count"),
    )
    for bq_key, api_key in bq_to_api:
        if bq_key in d:
            val = d.pop(bq_key)
            if val is not None:
                d[api_key] = val

    for redundant in ("notes", "run_timestamp", "threshold_used"):
        d.pop(redundant, None)

    optional = (
        "baseline_mean",
        "max_allowable_cpc",
        "dynamic_conv_rate",
        "percent_above_baseline",
        "average_cpc",
        "cpc_vs_threshold",
        "cpc_spike_percent",
        "ctr",
        "money_bleeding",
        "record_count",
    )
    for key in optional:
        if key in d and d.get(key) is None:
            del d[key]

    return d


@app.get("/alerts")
async def get_red_zone_alerts(limit: int = Query(default=10, ge=1, le=100)):
    full_table = resolve_full_table_id()
    if not full_table:
        raise HTTPException(
            status_code=503,
            detail=(
                "BigQuery table not configured. Set BIGQUERY_TABLE="
                "printerpix-general.GA_Avanish.CPC_Alerts_Updated "
                "or PROJECT_ID + TABLE."
            ),
        )

    query = _alerts_sql(full_table)
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
