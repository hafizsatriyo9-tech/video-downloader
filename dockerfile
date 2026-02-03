FROM python:3.11-slim

# ===== System deps =====
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    ca-certificates \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# ===== Install curl-impersonate (ARM64 – RAILWAY) =====
RUN wget -q https://github.com/lwthiker/curl-impersonate/releases/download/v0.6.1/curl-impersonate-chrome-linux-arm64.tar.gz \
    && tar -xzf curl-impersonate-chrome-linux-arm64.tar.gz \
    && mv curl-impersonate-chrome /usr/local/bin/ \
    && chmod +x /usr/local/bin/curl-impersonate-chrome \
    && rm curl-impersonate-chrome-linux-arm64.tar.gz

# ===== Python deps =====
RUN pip install --no-cache-dir flask gunicorn yt-dlp

WORKDIR /app
COPY . .

ENV PORT=8080
CMD gunicorn app:app --bind 0.0.0.0:$PORT
