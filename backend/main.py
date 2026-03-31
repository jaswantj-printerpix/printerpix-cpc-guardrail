from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import os
import json
from datetime import datetime

app = FastAPI(title="Printerpix CPC Guardrail API")

# CORS — allow your Vercel frontend (and localhost for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),  # set this in Railway env vars
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Load GCP credentials from Railway environment variable
creds_json = os.getenv("GOOGLE_CREDENTIALS")
if creds_json:
    with open("/tmp/credentials.json", "w") as f:
        f.write(creds_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"

PROJECT_ID = os.getenv("PROJECT_ID")
TABLE = os.getenv("TABLE")  # e.g. GA_Avanish.CPC_Anomaly_Alerts

client = bigquery.Client(project=PROJECT_ID)


@app.get("/alerts")
async def get_red_zone_alerts(limit: int = Query(default=10, ge=1, le=100)):
    """Top CPC anomalies — the Red Zone."""
    query = f"""
        SELECT
            campaign_name,
            ad_group_name,
            current_cpc,
            notes AS alert_reason,
            run_timestamp AS timestamp,
            cost,
            clicks,
            percent_above_baseline,
            baseline_mean,
            stat_threshold,
            max_allowable_cpc,
            dynamic_conv_rate
        FROM `{PROJECT_ID}.{TABLE}`
        ORDER BY run_timestamp DESC, current_cpc DESC
        LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)]
    )
    try:
        rows = list(client.query(query, job_config=job_config))
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trends")
async def get_cpc_trends():
    """24-hour CPC trend data for charts."""
    query = f"""
        SELECT
            campaign_name,
            ad_group_name,
            current_cpc,
            run_timestamp AS timestamp
        FROM `{PROJECT_ID}.{TABLE}`
        WHERE run_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        ORDER BY run_timestamp DESC
    """
    try:
        rows = list(client.query(query))
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.utcnow().isoformat()}
