# PRD: "ReadMe" — Local AI Reading Assistant

## 1. Purpose and Vision

ReadMe is a self-hosted reading application that converts digital books and documents (`.pdf`, `.epub`, `.txt`, `.docx`) into natural-sounding speech and intelligent summaries. It is designed for personal, local use — running on your PC — with optional cloud compute on Heroku for resource-intensive AI tasks.

The intent is to build a Speechify-like desktop utility that prioritizes:
- Privacy and ownership of data
- Local responsiveness
- Zero external dependencies except for API calls you explicitly configure

## 2. Functional Overview

| Feature | Description |
|---------|-------------|
| File Input | Open `.pdf`, `.epub`, `.txt`, `.docx` files from local drive |
| Text Extraction | Parse text and structure (pages, chapters, paragraphs) |
| Speech Synthesis | Convert text to speech using AI voices (via local Coqui-TTS or OpenAI API through Heroku) |
| Playback Controls | Play, pause, seek, adjust playback speed, repeat paragraph, or skip |
| Library Management | Maintain local list of previously opened books with reading progress |
| Bookmarks / Notes | Save reading position, annotations, and highlights locally |
| AI Summarization | Summarize selected text or chapters (processed on Heroku) |
| Offline Mode | Fully functional offline reading (except for remote AI services) |
| Minimal Interface | Lightweight desktop GUI with file explorer, playback, and settings panels |

## 3. System Architecture

### Overview

- **Frontend + Local App:** Electron + React (desktop client)
- **Local Backend:** Python FastAPI service running on localhost for parsing, TTS control, and storage
- **Remote Backend (Heroku):** Handles large AI workloads like text summarization, OpenAI TTS, or Whisper transcription

### Architecture Layers

#### A. Local Components

| Layer | Tech | Purpose |
|-------|------|---------|
| Desktop Shell | Electron + React | GUI for book browsing, playback, and settings |
| Local API Server | FastAPI (Python) | Hosts endpoints for local logic and file parsing |
| Database | SQLite | Store library metadata, progress, notes, and settings |
| File Parsing | PyMuPDF / pdfplumber / ebooklib | Extracts text + metadata from documents |
| Local TTS (optional) | Coqui-TTS | Perform on-device text-to-speech when available |
| Audio Engine | PyAudio / Web Audio API | Stream audio to local output |

#### B. Heroku Cloud Components

| Service | Tech | Role |
|---------|------|------|
| Heroku Web App | FastAPI (Python) / Flask | Receives text from local app, returns summarized or TTS-generated audio |
| AI Layer | OpenAI API, Whisper, Transformers | Summarization, translation, advanced speech synthesis |
| Heroku Postgres (optional) | PostgreSQL | Used only for caching API results or analytics if desired |

## 4. Data Flow

### 1. User Opens File
- Electron app reads file metadata and sends to local FastAPI
- FastAPI extracts text and structures it (JSON: `{chapter, page, paragraph}`)

### 2. Speech Generation
- For small jobs → Coqui-TTS locally
- For large jobs → sends text to Heroku FastAPI endpoint (`/generate_audio`)
- Heroku service calls OpenAI TTS or another model, streams back `.wav`/`.mp3`

### 3. Playback
- Local player streams from local disk or directly from Heroku audio stream

### 4. Summarization
- Selected text sent to Heroku `/summarize` endpoint
- Response returned to desktop app and cached locally

### 5. Persistence
- SQLite DB stores:
  - File paths
  - Read progress
  - Bookmarks & annotations
  - TTS cache locations

## 5. Software Stack

### Local (Desktop)

| Category | Tech Stack |
|----------|------------|
| GUI | Electron + React + TailwindCSS |
| Local API | FastAPI (Python 3.12) |
| Parsing | pdfplumber, ebooklib, PyMuPDF, docx2txt |
| TTS (optional local) | Coqui-TTS |
| Storage | SQLite |
| Audio Playback | PyAudio or HTML5 Audio via Electron |
| Environment Management | Poetry / Pipenv |
| Packaging | Electron Builder |

### Heroku (Cloud)

| Layer | Tech |
|-------|------|
| Web Server | FastAPI / Flask |
| Task Queue | Celery + Redis (for longer TTS jobs) |
| AI Libraries | OpenAI API, HuggingFace Transformers, Whisper |
| Storage | Local ephemeral or S3-compatible bucket |
| Deployment | Heroku Pipelines (Staging / Prod) |
| Security | API key authentication (personal key only) |

## 6. Local–Cloud Integration

### Local Endpoint

```json
POST /api/tts
{
  "text": "...",
  "voice": "rich-voice-1",
  "mode": "cloud" | "local"
}
```

### Cloud Endpoint (Heroku)

```json
POST /api/v1/tts
{
  "text": "...",
  "model": "gpt-4o-tts",
  "voice": "alloy"
}
```

### Heroku Returns
- Streamed or pre-generated `.mp3`
- Response metadata (duration, sample_rate, voice_used)

## 7. Security Model

- Local FastAPI only binds to `localhost:5000` (not exposed publicly)
- All cloud interactions use HTTPS with personal bearer token
- No third-party user accounts or telemetry
- Heroku stores no user data — ephemeral compute only

## 8. Performance and Scalability

| Operation | Location | Target Performance |
|-----------|----------|-------------------|
| Parsing a 200-page PDF | Local | < 5 seconds |
| Local TTS (Coqui) | Local | 1x real-time |
| Cloud TTS (Heroku) | Remote | < 2 sec latency |
| Summarization (GPT-4o) | Remote | < 8 sec per chapter |
| DB read/write | Local SQLite | Instantaneous |

## 9. Deployment & DevOps

| Area | Tool |
|------|------|
| Local App Packaging | Electron Builder |
| Backend Hosting | Heroku Standard Dyno |
| Database Migration | Alembic (for Heroku Postgres if used) |
| Version Control | Git + GitHub |
| CI/CD | GitHub Actions → Auto-deploy to Heroku |
| Local Runtime | Docker Compose (optional) |
| Logs & Monitoring | Heroku Logs + Sentry (local + cloud) |

## 10. Roadmap

| Phase | Deliverables |
|-------|-------------|
| Phase 1 (MVP) | Electron app + local FastAPI + PDF/EPUB parsing + basic playback |
| Phase 2 | Integrate Heroku TTS + caching + voice selector |
| Phase 3 | Add summarization endpoint + local note system |
| Phase 4 | Coqui-TTS local fallback + offline speech synthesis |
| Phase 5 | UI polish + exportable audio + hotkey navigation |

## 11. Directory Layout (Proposed)

```
readme-app/
├── frontend/                  # Electron + React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── store/
│   └── package.json
├── backend/
│   ├── main.py               # FastAPI local API
│   ├── tts/
│   │   ├── coqui.py
│   │   └── openai_cloud.py
│   └── parsers/
│       ├── pdf_parser.py
│       ├── epub_parser.py
│       └── doc_parser.py
├── cloud/
│   ├── app.py                # Heroku FastAPI entry
│   ├── summarize.py
│   ├── tts_openai.py
│   └── requirements.txt
├── db/
│   └── readme.db
└── config/
    ├── settings.yaml
    └── secrets.env
```

## 12. Technologies Summary

| Layer | Stack |
|-------|-------|
| Frontend | Electron + React + TailwindCSS |
| Backend (Local) | FastAPI, PyMuPDF, pdfplumber, Coqui-TTS, SQLite |
| Backend (Heroku) | FastAPI, OpenAI API, Celery, Redis |
| Infrastructure | Docker, GitHub Actions, Heroku Dynos |
| Security | API key, localhost-only exposure, TLS |
| Audio Pipeline | Local caching, async streaming |

---

# Technical Specification (TS): "ReadMe" – Local AI Reading Assistant

## 1. System Topology

### Architecture Overview
- **Desktop Layer:** Electron + React (UI) communicates via REST/WebSocket
- **Local Backend:** FastAPI + SQLite + Coqui-TTS
- **Cloud Compute:** Heroku Dyno (FastAPI / Celery) + OpenAI TTS / GPT Summarizer

## 2. Core Data Structures

### 2.1 Book Metadata

```python
class Book(BaseModel):
    id: str                          # UUID
    title: str
    author: Optional[str]
    filepath: str                    # Absolute local path
    filetype: str                    # pdf | epub | txt | docx
    total_pages: int
    last_read_page: int = 0
    last_accessed: datetime
    cover_image_path: Optional[str]
    text_cache_path: Optional[str]
```

### 2.2 Annotation / Note

```python
class Annotation(BaseModel):
    id: str
    book_id: str
    page_number: int
    selection_text: str
    note_text: str
    timestamp: datetime
```

### 2.3 Audio Job (Local/Remote)

```python
class AudioJob(BaseModel):
    id: str
    book_id: str
    chapter: str
    status: str                      # queued | processing | done | failed
    engine: str                      # local | cloud
    voice: str
    text_path: str
    audio_path: Optional[str]
    created_at: datetime
```

## 3. Database Schema (SQLite)

```sql
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT,
    author TEXT,
    filepath TEXT,
    filetype TEXT,
    total_pages INTEGER,
    last_read_page INTEGER,
    last_accessed DATETIME,
    cover_image_path TEXT,
    text_cache_path TEXT
);

CREATE TABLE annotations (
    id TEXT PRIMARY KEY,
    book_id TEXT,
    page_number INTEGER,
    selection_text TEXT,
    note_text TEXT,
    timestamp DATETIME,
    FOREIGN KEY(book_id) REFERENCES books(id)
);

CREATE TABLE audio_jobs (
    id TEXT PRIMARY KEY,
    book_id TEXT,
    chapter TEXT,
    status TEXT,
    engine TEXT,
    voice TEXT,
    text_path TEXT,
    audio_path TEXT,
    created_at DATETIME,
    FOREIGN KEY(book_id) REFERENCES books(id)
);
```

## 4. API Specification

### 4.1 Local FastAPI (localhost:5000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/books/import` | Upload & parse `.pdf`, `.epub`, etc. Returns metadata |
| GET | `/api/books` | List all local books with metadata |
| GET | `/api/books/{id}` | Get details, progress, and cached content |
| POST | `/api/books/{id}/parse` | Force re-parse a file |
| POST | `/api/tts` | Generate audio (mode: local or cloud) |
| GET | `/api/audio/{id}/stream` | Stream cached `.wav`/`.mp3` to player |
| POST | `/api/annotate` | Add a note/bookmark |
| GET | `/api/annotations/{book_id}` | Retrieve annotations |
| POST | `/api/summarize` | Send selected text to Heroku summarization service |
| GET | `/api/settings` | Retrieve system config (voices, cache paths) |
| PUT | `/api/settings` | Update local preferences |

### 4.2 Cloud Heroku FastAPI

**Base URL:** `https://readme-ai.herokuapp.com`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tts` | Convert text → audio using OpenAI TTS or another engine |
| POST | `/api/v1/summarize` | Summarize a paragraph or chapter |
| POST | `/api/v1/translate` | (Optional) Translate selected text |
| GET | `/api/v1/health` | Health check |

### 4.3 Example Payloads

#### Local → Cloud TTS Request

```json
POST /api/v1/tts
{
  "text": "Chapter one begins...",
  "model": "gpt-4o-tts",
  "voice": "alloy"
}
```

#### Response

```json
{
  "job_id": "a2b1f...",
  "duration": 32.6,
  "sample_rate": 44100,
  "audio_url": "https://readme-ai.herokuapp.com/files/a2b1f.mp3"
}
```

## 5. Processing Pipelines

### 5.1 File Parsing (Local)
1. Electron selects file → POST `/api/books/import`
2. FastAPI determines parser based on file extension
3. Extracted text stored in JSON cache: `cache/books/<book_id>/text.json`
4. DB entry created

### 5.2 Text-to-Speech
- **Local Mode:** Coqui-TTS engine generates audio to cache directory
- **Cloud Mode:** Text sent to Heroku → processed via OpenAI API → audio URL returned → downloaded + cached locally

### 5.3 Summarization
1. Electron highlights passage → POST `/api/summarize`
2. FastAPI forwards to Heroku `/api/v1/summarize`
3. GPT-4o generates abstract → result cached in SQLite

## 6. Heroku Cloud Services

### 6.1 Heroku App Structure

```
cloud/
├── app.py
├── routers/
│   ├── tts.py
│   └── summarize.py
├── services/
│   ├── openai_client.py
│   └── audio_utils.py
└── Procfile
```

### 6.2 Example Heroku Procfile

```
web: gunicorn app:app --workers=1 --timeout 120
worker: celery -A tasks.celery_app worker --loglevel=info
```

### 6.3 Celery Task Example

```python
@app.task
def generate_audio_task(text, voice="alloy"):
    audio = openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text
    )
    filename = f"{uuid.uuid4()}.mp3"
    with open(f"/tmp/{filename}", "wb") as f:
        f.write(audio.read())
    return f"/tmp/{filename}"
```

## 7. Desktop Application (Electron + React)

### 7.1 UI Layout

| Component | Purpose |
|-----------|---------|
| Sidebar | Library (Book list, progress bar) |
| Reader Pane | Paginated text view, highlighting, annotations |
| Player Bar | Play/pause, speed, seek, voice selector |
| Settings Panel | Choose local vs cloud mode, manage voices |
| Console Panel (Dev) | Display FastAPI logs, status updates |

### 7.2 IPC Communication

Electron bridges frontend ↔ Python backend:

```javascript
ipcRenderer.invoke('fetch-books')
ipcRenderer.invoke('start-tts', { text, mode: 'local' })
ipcRenderer.invoke('summarize-text', { text })
```

Electron executes Python server using:

```javascript
const pyProc = spawn('python', ['backend/main.py'])
```

## 8. Data Flow Diagram

```
┌───────────────┐     ┌──────────────┐     ┌─────────────┐
│ Electron UI   │────►│ Local FastAPI│────►│ Heroku Cloud│
└───────────────┘     └──────────────┘     └─────────────┘
        ▲                     │                     │
        │                     │                     │
        │                     ▼                     ▼
        │            Coqui-TTS / SQLite    OpenAI API / GPT-4o
        │
        └── Playback, Notes, and Rendering
```

## 9. Configuration and Secrets

### `config/settings.yaml`

```yaml
tts_default: "local"
voices:
  - "coqui_en"
  - "openai_alloy"
heroku_api_url: "https://readme-ai.herokuapp.com"
api_key: !ENV ${HEROKU_API_KEY}
cache_dir: "./cache"
```

### `config/secrets.env`

```
OPENAI_API_KEY=sk-...
HEROKU_API_KEY=...
```

## 10. Performance Targets

| Function | Target |
|----------|--------|
| PDF parse (200 pages) | < 5 sec |
| Local TTS latency | < 1.5x realtime |
| Cloud TTS round-trip | < 2 sec |
| Summarization response | < 8 sec |
| App cold start | < 3 sec |
| Memory footprint | < 600 MB |

## 11. Error Handling and Recovery

| Scenario | Mitigation |
|----------|------------|
| Heroku offline | Fallback to local TTS |
| Parsing error | Retry with alternate parser |
| API timeout | Queue and retry async |
| Disk full | Alert and clear cache |
| DB locked | Rollback + exponential backoff |

## 12. Testing Strategy

| Level | Tools | Purpose |
|-------|-------|---------|
| Unit Tests | Pytest, Jest | Core parsing, API endpoints |
| Integration | Postman, pytest-asyncio | Local ↔ Heroku endpoints |
| UI Tests | Cypress | GUI behavior |
| Load Tests | Locust | Parsing + TTS concurrency |
| E2E | Electron Test Kit | Full pipeline validation |

## 13. Deployment Guide Summary

### Local Setup

```bash
git clone readme-app
cd backend && poetry install
poetry run uvicorn main:app --reload
cd ../frontend && npm install && npm run electron-dev
```

### Heroku Setup

```bash
heroku create readme-ai
git push heroku main
heroku config:set OPENAI_API_KEY=sk-...
heroku ps:scale web=1 worker=1
```

## 14. Security Summary

- Localhost-only backend access
- Cloud auth via static bearer key (personal)
- Encrypted storage for annotations and cache (SQLCipher optional)
- All external calls HTTPS-only
- No analytics / telemetry / external tracking

## 15. Optional Enhancements

| Feature | Description |
|---------|-------------|
| Voice Cloning | Train voice using Coqui-VC and store locally |
| Web Scraper | Import articles directly from URLs |
| AI Q&A Mode | Ask contextual questions about chapters using GPT-4o |
| Batch Export | Generate audiobook MP3 for entire book |
| CLI Interface | Lightweight terminal mode for TTS playback |

---

# Cloud Repository Layout

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

## Environment Variables (Heroku)

```bash
OPENAI_API_KEY=...
API_BEARER=some-long-random-token        # Your personal bearer for cloud auth
AUDIO_FORMAT=mp3                         # mp3 | wav | ogg (optional)
OPENAI_TTS_MODEL=gpt-4o-mini-tts        # Default TTS model
OPENAI_SUMMARY_MODEL=gpt-4.1-mini       # Or another lightweight text model
```

## Notes

- The Audio API `audio/speech` endpoint with models like `gpt-4o-mini-tts` is the current OpenAI path for TTS
- Keep an eye on OpenAI's changelog/deprecations and the newer Responses API guidance for text to avoid breaking changes

## Reference

[PRD_ "ReadMe" — Local AI Reading Assistant.pdf](../PRD_%20%E2%80%9CReadMe%E2%80%9D%20%E2%80%94%20Local%20AI%20Reading%20Assistant.pdf)