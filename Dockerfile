# ReadMeLocal Container
# Multi-stage build: Node for frontend, Python for backend + nginx for serving

# =============================================================================
# Stage 1: Build React frontend
# =============================================================================
FROM node:20-slim AS frontend-build

WORKDIR /build

# Copy package files first for better caching
COPY frontend/package*.json ./
RUN npm ci --only=production=false

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# =============================================================================
# Stage 2: Production image with Python + nginx
# =============================================================================
FROM python:3.11-slim AS production

# Install nginx, supervisor, and curl (for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy Python requirements (excluding TTS for smaller image)
COPY backend/requirements.txt ./requirements-full.txt

# Create filtered requirements without Coqui TTS
RUN grep -v "^TTS==" requirements-full.txt > requirements.txt \
    && rm requirements-full.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built React frontend
COPY --from=frontend-build /build/build /app/static

# Copy config directory structure
COPY config/ ./config/

# Copy nginx and supervisor configs
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create required directories
RUN mkdir -p /app/db /app/cache /library \
    && chown -R www-data:www-data /app/static

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    README_LIBRARY_PATH=/library \
    README_HOST=0.0.0.0 \
    README_PORT=8000

# Expose the single port (nginx handles routing)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start supervisor (manages nginx + uvicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
