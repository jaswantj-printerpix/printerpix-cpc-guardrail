FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY CPC_Alerts_Jas.py .

# Railway Cron runs this start command on schedule; process must exit when done.
CMD ["python", "CPC_Alerts_Jas.py"]
