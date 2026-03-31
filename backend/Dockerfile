FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main app (bump comment to invalidate Docker layer cache on Railway)
# build: 2026-03-31-select-star-v4
COPY main.py .

# Run the FastAPI app
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
