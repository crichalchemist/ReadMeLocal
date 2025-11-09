# Project Overview — ReadMe: Local AI Reading Assistant

Last updated: 2025-11-06 04:14

## Purpose and Vision
ReadMe is a self‑hosted desktop application that converts digital books and documents (`.pdf`, `.epub`, `.txt`, `.docx`) into natural‑sounding speech and provides intelligent summaries. It prioritizes privacy (all files stay local), responsiveness, and optional cloud compute on Heroku for heavier AI tasks (e.g., OpenAI TTS, summarization, Whisper transcription).

## Core Features
- File input: open `.pdf`, `.epub`, `.txt`, `.docx`
- Text extraction: structured into chapters, pages, paragraphs
- Speech synthesis: local Coqui‑TTS or cloud (OpenAI via Heroku)
- Playback controls: play/pause, seek, speed, repeat/skip paragraph
- Library management: local list, progress tracking
- Bookmarks and notes: annotations stored locally
- AI summarization: selected passages or chapters (via cloud)
- Offline mode: fully functional locally (except remote AI calls)
- Minimal interface: lightweight Electron + React UI

## System Architecture (Three Layers)
1) Desktop client (Electron + React)
2) Local backend (FastAPI + SQLite + optional Coqui‑TTS)
3) Cloud backend on Heroku (FastAPI/Celery + OpenAI/Whisper)

### Local Components
- Desktop Shell: Electron + React UI
- Local API Server: FastAPI (Python 3.12) — parsing, orchestration, storage
- Database: SQLite — books, progress, annotations, audio jobs
- File Parsing: PyMuPDF / pdfplumber / ebooklib / docx2txt
- Local TTS (optional): Coqui‑TTS
- Audio Engine: PyAudio or HTML5 Audio (Electron)

### Cloud Components (Heroku)
- Web App: FastAPI/Flask for TTS and summarization endpoints
- AI Layer: OpenAI API (TTS & GPT‑4o summarization), Whisper, Transformers
- Queue: Celery + Redis (for longer jobs)
- Storage: Ephemeral or S3‑compatible bucket
- Security: Personal bearer token; no user data retained

## Data Flow
1) Open file in Electron → send to local FastAPI
2) Parse text → structure `{chapter, page, paragraph}` and cache JSON
3) TTS:
   - Local mode: Coqui‑TTS produces audio into cache
   - Cloud mode: Local FastAPI posts text to Heroku → OpenAI TTS → returns audio URL/bytes → cached locally
4) Playback: Stream from local disk or cloud response
5) Summarization: Local FastAPI forwards selected text to Heroku; results cached
6) Persistence: SQLite tracks files, progress, annotations, audio jobs

## Key Data Models (conceptual)
- Book: id, title, author, filepath, filetype, total_pages, last_read_page, last_accessed, cover_image_path, text_cache_path
- Annotation: id, book_id, page_number, selection_text, note_text, timestamp
- AudioJob: id, book_id, chapter, status, engine, voice, text_path, audio_path, created_at

## Local API (FastAPI, localhost:5000)
- POST `/api/books/import` — upload/parse file → metadata
- GET `/api/books` — list all books
- GET `/api/books/{id}` — book details + cached content
- POST `/api/books/{id}/parse` — re‑parse a file
- POST `/api/tts` — generate audio (`mode: local|cloud`)
- GET `/api/audio/{id}/stream` — stream cached audio
- POST `/api/annotate` — add note/bookmark
- GET `/api/annotations/{book_id}` — get notes
- POST `/api/summarize` — forward text to cloud summarizer
- GET `/api/settings` — read config
- PUT `/api/settings` — update preferences

Example local TTS request:
```http
POST /api/tts
Content-Type: application/json

{
  "text": "...",
  "voice": "rich-voice-1",
  "mode": "cloud"
}
```

## Cloud API (Heroku)
Base URL: `https://readme-ai.herokuapp.com`
- POST `/api/v1/tts` — text → audio (OpenAI TTS)
- POST `/api/v1/summarize` — summarize paragraph/chapter
- POST `/api/v1/translate` — optional translation
- GET `/api/v1/health` — health check

Example cloud TTS request:
```http
POST /api/v1/tts
Content-Type: application/json

{
  "text": "Chapter one begins...",
  "model": "gpt-4o-tts",
  "voice": "alloy"
}
```

Example response:
```json
{
  "job_id": "a2b1f...",
  "duration": 32.6,
  "sample_rate": 44100,
  "audio_url": "https://readme-ai.herokuapp.com/files/a2b1f.mp3"
}
```

## Repository Layouts

This repo (local app):
```
readme-app/
├── frontend/                  # Electron + React
│   ├── src/
│   ├── public/
│   └── electron/
├── backend/
│   ├── main.py               # FastAPI local API
│   ├── tts/
│   └── parsers/
├── config/
│   ├── settings.yaml
│   └── secrets.env(.template)
├── db/                       # SQLite (runtime)
└── .junie/
    └── guidelines.md         # This file
```

Cloud repo (separate):
```
readme-cloud/
├── app.py
├── settings.py
├── auth.py
├── routers/
│   ├── tts.py
│   └── summarize.py
├── services/
│   ├── openai_tts.py
│   └── openai_summarize.py
├── tests/
│   ├── test_tts.py
│   └── test_summarize.py
├── requirements.txt
├── Procfile
└── runtime.txt
```

## Configuration & Secrets
`config/settings.yaml`
```yaml
tts_default: "local"
voices:
  - "coqui_en"
  - "openai_alloy"
heroku_api_url: "https://readme-ai.herokuapp.com"
api_key: !ENV ${HEROKU_API_KEY}
cache_dir: "./cache"
```
`config/secrets.env`
```
OPENAI_API_KEY=sk-...
HEROKU_API_KEY=...
```

## Security Model
- Local FastAPI binds to `localhost:5000` only
- HTTPS for all cloud calls with personal bearer token
- No third‑party accounts or telemetry; Heroku stores no user data
- Optional encrypted storage for annotations/cache (SQLCipher)

## Performance Targets
- Parse 200‑page PDF: < 5 sec
- Local TTS (Coqui): ≈ 1× realtime
- Cloud TTS round‑trip: < 2 sec
- Summarization: < 8 sec per chapter
- App cold start: < 3 sec; Memory: < 600 MB

## Error Handling
- Heroku offline → fallback to local TTS
- Parsing error → retry with alternate parser
- API timeout → queue and retry (async)
- Disk full → alert and clear cache
- DB locked → rollback + backoff

## Setup (Dev)
Local app:
```bash
git clone readme-app
cd backend && poetry install
poetry run uvicorn main:app --reload
cd ../frontend && npm install && npm run electron-dev
```

Heroku (cloud):
```bash
heroku create readme-ai
git push heroku main
heroku config:set OPENAI_API_KEY=sk-...
heroku ps:scale web=1 worker=1
```

## Roadmap (Phases)
1) MVP: Electron app + local FastAPI + PDF/EPUB parsing + basic playback
2) Heroku TTS integration + caching + voice selector
3) Summarization endpoint + local notes system
4) Local fallback TTS with Coqui (offline)
5) UI polish + exportable audio + hotkeys

## Notes
- Use OpenAI Audio API `audio/speech` (e.g., `gpt-4o-mini-tts`) for TTS
- Track OpenAI changelog and Responses API guidance to avoid breaking changes

---
This overview summarizes the Product Requirements and Technical Specification for quick onboarding and alignment. Refer to the full PRD PDF and source files for details.