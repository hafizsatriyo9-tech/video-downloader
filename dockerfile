FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir flask gunicorn yt-dlp

# Set workdir
WORKDIR /app

# Copy project
COPY . .

# Railway port
ENV PORT=8080

# Start app
CMD gunicorn app:app --bind 0.0.0.0:$PORT
