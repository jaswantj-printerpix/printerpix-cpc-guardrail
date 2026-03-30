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

- **Background Task** → Hourly anomaly script running natively on Railway (no SSH cron needed)

---

## 🚀 Live URLs

- **Backend API** (Railway): `https://<your-railway-url>.up.railway.app`  
- **Frontend Dashboard** (Vercel): `https://<your-vercel-url>.vercel.app`

---

## 📁 Project Structure
