"""
CPC Guardrail API — reads anomaly alerts from BigQuery table
  printerpix-general.GA_Avanish.CPC_Anomaly_Alerts

Configure via BIGQUERY_TABLE (full id) or PROJECT_ID + TABLE (dataset.table).
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
# dataset.table, e.g. GA_Avanish.CPC_Anomaly_Alerts
TABLE = os.getenv("TABLE", "").strip()
# Optional: full "project.dataset.table" — overrides PROJECT_ID + TABLE if set
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "").strip()


def resolve_full_table_id() -> Optional[str]:
    """Return project.dataset.table for CPC_Anomaly_Alerts."""
    if BIGQUERY_TABLE:
        return BIGQUERY_TABLE
    if PROJECT_ID and TABLE:
        return f"{PROJECT_ID}.{TABLE}"
    return None


# CORS — localhost + Railway/Vercel URLs from env
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
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Load GCP credentials from Railway / local env (JSON string)
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


def _percent_above_baseline(baseline_mean: object, current_cpc: object) -> Optional[float]:
    """Spike % vs baseline — computed in API so BigQuery never references missing columns."""
    if baseline_mean is None or current_cpc is None:
        return None
    try:
        b = float(baseline_mean)
        c = float(current_cpc)
        if b > 0:
            return round((c - b) / b * 100, 1)
    except (TypeError, ValueError):
        pass
    return None


@app.get("/version")
async def version():
    """Bump when changing /alerts query — use to confirm Railway deployed latest."""
    return {"api": "cpc-guardrail", "build": "2026-03-31-pct-in-python"}


@app.get("/alerts")
async def get_red_zone_alerts(limit: int = Query(default=10, ge=1, le=100)):
    """Top CPC anomalies — the Red Zone (CPC_Anomaly_Alerts)."""
    full_table = resolve_full_table_id()
    if not full_table:
        raise HTTPException(
            status_code=503,
            detail=(
                "BigQuery table not configured. Set BIGQUERY_TABLE="
                "printerpix-general.GA_Avanish.CPC_Anomaly_Alerts "
                "or PROJECT_ID + TABLE (e.g. TABLE=GA_Avanish.CPC_Anomaly_Alerts)."
            ),
        )

    # Spike % is computed in Python — BigQuery must never see the name percent_above_baseline
    # (older deployed images / schema drift caused invalidQuery on that identifier).
    query = f"""
        SELECT
            campaign_name,
            ad_group_name,
            current_cpc,
            notes AS alert_reason,
            run_timestamp AS `timestamp`,
            cost,
            clicks,
            baseline_mean,
            stat_threshold,
            max_allowable_cpc,
            dynamic_conv_rate
        FROM `{full_table}`
        ORDER BY run_timestamp DESC, current_cpc DESC
        LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)]
    )
    try:
        rows = list(get_bq_client().query(query, job_config=job_config))
        out: list[dict] = []
        for row in rows:
            d = dict(row)
            d["percent_above_baseline"] = _percent_above_baseline(
                d.get("baseline_mean"), d.get("current_cpc")
            )
            out.append(d)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/trends")
async def get_cpc_trends():
    """24-hour CPC trend data for charts (same BigQuery table)."""
    full_table = resolve_full_table_id()
    if not full_table:
        raise HTTPException(
            status_code=503,
            detail="BigQuery table not configured. See /alerts error detail.",
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
