# Printerpix CPC Guardrail Dashboard

**Production Full-Stack CPC Anomaly Detection System**  
Replaces the old Looker Studio static dashboard with a real-time, interactive web application.

---

## 🎯 Objective
Real-time monitoring of Google Ads CPC spikes that threaten Contribution Margin (CM).  
Alerts are generated hourly and displayed instantly in the "Red Zone".

---

## 🏗️ Architecture

- **Backend** → FastAPI (Railway)  
  - Securely queries `printerpix-general.GA_Avanish.CPC_Anomaly_Alerts`  
  - Endpoints: `/alerts`, `/trends`, `/health`

- **Frontend** → Next.js 15 (Vercel)  
  - Live Red Zone table + 24-hour CPC trend visualisation  
  - Auto-refreshes every 60 seconds

- **Hourly worker** → `worker/CPC_Alerts_Jas.py` on **Railway Cron** (`5 * * * *` UTC), same env as the API — replaces the old `flock` + venv cron on a VM

---

## 🚀 Live URLs

- **Backend API** (Railway): `https://<your-railway-url>.up.railway.app`  
- **Frontend Dashboard** (Vercel): `https://<your-vercel-url>.vercel.app`

---

## BigQuery & API configuration

Alerts are read from **`printerpix-general.GA_Avanish.CPC_Anomaly_Alerts`**.

### Backend (Railway or local)

1. Copy `backend/.env.example` and set credentials.
2. **Either** set **`BIGQUERY_TABLE=printerpix-general.GA_Avanish.CPC_Anomaly_Alerts`**  
   **or** set **`PROJECT_ID=printerpix-general`** and **`TABLE=GA_Avanish.CPC_Anomaly_Alerts`**.
3. Set **`GOOGLE_CREDENTIALS`** to the full JSON of a service account that can read that table (BigQuery Data Viewer on the dataset or project).
4. Set **`FRONTEND_URL`** to your Vercel URL (e.g. `https://your-app.vercel.app`) so the browser can call the API.

Endpoints:

- `GET /alerts?limit=100` — rows from `CPC_Anomaly_Alerts`, newest first  
- `GET /trends` — last 24 hours for charts  
- `GET /health` — includes whether the table id is configured  

### Frontend (Vercel)

Set **`NEXT_PUBLIC_API_URL`** to your public API base URL (no trailing slash), e.g. `https://your-api.up.railway.app`.

After changing env vars, redeploy backend and frontend so the new values apply.

---

## Project layout

- `backend/` — FastAPI API; queries BigQuery `CPC_Anomaly_Alerts`  
- `frontend/` — Next.js dashboard (calls `NEXT_PUBLIC_API_URL`)  
- `worker/` — hourly `CPC_Alerts_Jas.py` job for Railway Cron (see `worker/README.md`)

---

## Hourly CPC job (Railway Cron)

Your old schedule:

`5 * * * * flock -n /tmp/CPC_Alerts_Jas.lock -c "…/activate && python …/CPC_Alerts_Jas.py"`

**On Railway:**

1. Add a **second service** from this repo with **root directory** `worker` (or Dockerfile `worker/Dockerfile`).
2. **Settings → Cron schedule:** `5 * * * *` (UTC — same five-field crontab as before; adjust if you need a non-UTC wall clock).
3. Reuse the same **GCP / BigQuery variables** as the API (Railway **Shared Variables** / **Reference**), so the job writes or refreshes the same table the API reads.
4. Configure **Google Ads** (`GOOGLE_ADS_YAML` or `GOOGLE_ADS_CONFIG_JSON`) plus **`GOOGLE_CREDENTIALS`** for BigQuery — see **`worker/README.md`**. The full `CPC_Alerts_Jas.py` pipeline is already in `worker/CPC_Alerts_Jas.py`.
