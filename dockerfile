FROM python:3.11-slim

# Install system deps + impersonation
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    curl \
    curl-impersonate \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir flask gunicorn yt-dlp

WORKDIR /app
COPY . .

ENV PORT=8080

CMD gunicorn app:app --bind 0.0.0.0:$PORT
