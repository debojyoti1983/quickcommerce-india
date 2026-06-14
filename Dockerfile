# Python 3.12 base — avoids the 3.14 wheel-build issue; pins work on 3.11–3.14.
FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# auth.db lives here; mount a persistent disk at /app/data in production and set
# QC_AUTH_DB_PATH=/app/data/auth.db so accounts survive restarts/redeploys.
ENV QC_AUTH_DB_PATH=/app/auth.db

EXPOSE 8000

# Single web process: the OTP/order/session stores are in-memory, so a second
# worker wouldn't share them. Move those to Redis before scaling out.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
