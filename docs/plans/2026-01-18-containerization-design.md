# ReadMeLocal Containerization Design

**Date:** 2026-01-18
**Status:** Approved

## Overview

Containerize ReadMeLocal to run as a background service accessible via web browser at `localhost:5000`, using Colima as the Docker runtime on macOS.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Host (macOS + Colima)             │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │           readmelocal container              │   │
│  │                                              │   │
│  │  ┌────────────────┐  ┌──────────────────┐   │   │
│  │  │  FastAPI       │  │  React Static    │   │   │
│  │  │  Backend       │◄─┤  Files (nginx)   │   │   │
│  │  │  :5000/api/*   │  │  :5000/*         │   │   │
│  │  └───────┬────────┘  └──────────────────┘   │   │
│  │          │                                   │   │
│  │          ▼                                   │   │
│  │  ┌────────────────┐                          │   │
│  │  │  SQLite DB     │ (volume: ./db)           │   │
│  │  └────────────────┘                          │   │
│  └─────────────────────────────────────────────┘   │
│                         │                           │
│    Bind mounts:         │                           │
│    - /path/to/books → /library                      │
│    - ./db → /app/db                                 │
│    - ./cache → /app/cache                           │
│    - ./config → /app/config                         │
└─────────────────────────────────────────────────────┘
```

## Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Access method | Web browser at `localhost:5000` | Simpler than Electron in container |
| Container count | Single container | Nginx + FastAPI via supervisord |
| TTS | Excluded | Keeps image small (~400-500MB vs ~2GB) |
| Library access | Bind mount at runtime | Flexible, no rebuild needed |
| Persistence | Volumes for db, cache, config | Survive container restarts |
| Startup | Manual (`docker compose up -d`) | User preference |
| Base image | `python:3.11-slim` | Small, stable |

## Files to Create

### Dockerfile (multi-stage)

- **Stage 1 (frontend-build)**: Node image builds React to static files
- **Stage 2 (production)**: Python slim + nginx, copies React build + backend

### docker-compose.yml

```yaml
services:
  readmelocal:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./db:/app/db
      - ./cache:/app/cache
      - ./config:/app/config
      - /Volumes/Rich 3TB/books:/library:ro
    environment:
      - LIBRARY_PATH=/library
    restart: "no"
```

### nginx.conf

- Serve React static files on `/`
- Proxy `/api/*` to FastAPI on localhost:8000 (internal)

### .dockerignore

Exclude: `.git`, `node_modules`, `.venv`, `__pycache__`, `.env` files

## Files to Modify

### backend/main.py

- Read `LIBRARY_PATH` from environment variable
- Bind to `0.0.0.0` instead of `127.0.0.1`

### config/settings.yaml

- `library_path: "/library"` (container default)
- `local_api_host: "0.0.0.0"`

### Frontend API calls

- Ensure relative URLs (`/api/...`) not absolute

## Usage

```bash
# Start
colima start
docker compose up -d

# Access
open http://localhost:5000

# Logs
docker compose logs -f

# Stop
docker compose down
```

## Non-Goals

- Electron in container (not practical)
- Local TTS/Coqui (too heavy, add later if needed)
- Auto-restart on boot (manual start preferred)
- Multi-container orchestration (unnecessary complexity)
