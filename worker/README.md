# CPC_Alerts_Jas — hourly worker (Railway Cron)

Runs the **Google Ads → anomaly logic → BigQuery** pipeline that used to run on your VM:

```cron
5 * * * * flock -n /tmp/CPC_Alerts_Jas.lock -c "source .../.venv/bin/activate && python .../CPC_Alerts_Jas.py"
```

Script: `CPC_Alerts_Jas.py` (same behaviour as your original, adapted for Railway env vars).

## Railway setup

`worker/railway.json` sets **`cronSchedule`: `5 * * * *`** (UTC) and the Docker build. Config-as-code overrides dashboard defaults on deploy.

1. In the same Railway project as the API, **Add service** → this repo.
2. **Settings → Build**
   - **Root directory**: `worker`  
   - **Dockerfile path**: `Dockerfile` (under `worker/`)
3. **Cron** should show **`5 * * * *`** from `railway.json` after deploy. If not, set it manually to match.

### Deploy from your machine (CLI)

```bash
cd worker
npx @railway/cli login
npx @railway/cli link          # pick project + this worker service
npx @railway/cli up            # deploy current code
```

Or push to GitHub if the service has **auto-deploy on push** enabled.
4. **Variables** (use **Shared Variables** where possible):

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CREDENTIALS` | Service account **JSON** (for BigQuery `insert_rows_json`). Same as API. |
| `BIGQUERY_TABLE` | Default `printerpix-general.GA_Avanish.CPC_Anomaly_Alerts` |
| **Google Ads auth (one of)** | See below |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads customer id (default `5176633302`) |

### Google Ads client config (pick one)

- **`GOOGLE_ADS_YAML`** — paste the **full** contents of your `google-ads.yaml` (Railway “secret” / multiline).
- **`GOOGLE_ADS_CONFIG_JSON`** — minified JSON accepted by `GoogleAdsClient.load_from_dict` (alternative to YAML).
- **`GOOGLE_ADS_YAML_PATH`** — local path only (e.g. laptop); not used on Railway unless you mount a file.

BigQuery and Google Ads use **different** credentials: OAuth via yaml/JSON for Ads, service account JSON for BigQuery.

### Optional tuning (defaults match your script)

| Variable | Default |
|----------|---------|
| `MARKETING_ALLOWABLE_PER_SALE` | `20.0` |
| `CPC_ANOMALY_MULTIPLIER` | `2.0` |
| `MIN_COST_FOR_ALERT` | `15.0` |
| `MIN_CLICKS_FOR_ALERT` | `5` |
| `DAYS_FOR_BASELINE` | `1` |
| `CPC_ALERTS_LOCK_PATH` | `/tmp/CPC_Alerts_Jas.lock` |

Railway skips overlapping cron runs; the script still uses `flock` for manual runs.

## Timezone

Cron is **UTC**. Adjust `5 * * * *` if you need a specific local wall time.
