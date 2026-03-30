from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
import os
from datetime import datetime

app = FastAPI(title="Printerpix CPC Guardrail API")

# Load credentials from Railway secret
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/credentials.json"
with open("/tmp/credentials.json", "w") as f:
    f.write(os.getenv("GOOGLE_CREDENTIALS"))

client = bigquery.Client(project=os.getenv("PROJECT_ID"))

@app.get("/alerts")
async def get_red_zone_alerts(limit: int = 10):
    """Returns the latest CPC anomalies exactly as your CPC_Alerts_Jas.py inserts them"""
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
        FROM `{os.getenv('PROJECT_ID')}.{os.getenv('TABLE')}`
        ORDER BY run_timestamp DESC, current_cpc DESC
        LIMIT {limit}
    """
    try:
        rows = list(client.query(query))
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends")
async def get_cpc_trends():
    query = f"""
        SELECT 
            campaign_name,
            ad_group_name,
            current_cpc,
            run_timestamp AS timestamp
        FROM `{os.getenv('PROJECT_ID')}.{os.getenv('TABLE')}`
        WHERE run_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        ORDER BY run_timestamp DESC
    """
    rows = list(client.query(query))
    return [dict(row) for row in rows]

@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.utcnow().isoformat()}
