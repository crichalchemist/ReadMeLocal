# ReadMe Local - Architecture Documentation

## System Overview

ReadMe Local is a self-hosted, privacy-first desktop application that converts digital books into natural-sounding speech with word-by-word RSVP (Rapid Serial Visual Presentation) reading. The application is built with a strict separation between frontend (Electron + React) and backend (FastAPI + Python), communicating exclusively over localhost.

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Main Process                     │
│              (Window Management, Subprocess Mgmt)            │
│                  (frontend/electron/main.js)                 │
└────────────────────┬────────────────────────────────────────┘
                     │ spawns Python subprocess
                     │ port 5000 (localhost only)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           FastAPI Backend (backend/main.py)                 │
│                     Port 5000                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ REST API Endpoints (CORS restricted to localhost)   │  │
│  │ - Document import & parsing                         │  │
│  │ - Playback state management                         │  │
│  │ - TTS generation (Google Cloud)                     │  │
│  │ - Annotation CRUD & export                          │  │
│  │ - Library scanning                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                       ▲                                      │
│                       │ HTTP (localhost)                    │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Core Modules                                         │  │
│  │ - Parser Registry (PDF, EPUB, DOCX, TXT, MD)        │  │
│  │ - RSVP Tokenization (rsvp_tokens.py)                │  │
│  │ - Content Filter (frontmatter, headers, footnotes)  │  │
│  │ - TTS Service (Google Cloud)                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                       ▲                                      │
│                       │ read/write                          │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ SQLite Database (./db/readme.db)                    │  │
│  │ - CurrentBook (id=1, content JSON)                 │  │
│  │ - PlaybackState (id=1, position, speed, sync)      │  │
│  │ - Annotation (paragraph-level notes)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ File Storage                                         │  │
│  │ - ./cache/audio/ (generated TTS files)              │  │
│  │ - config/settings.yaml (app configuration)          │  │
│  │ - config/secrets.env (API keys, git-ignored)        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                     ▲ HTTP responses
                     │ (localhost:5000)
                     │
┌────────────────────┴────────────────────────────────────────┐
│              React UI (frontend/src/)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ App.js (Main Component)                              │  │
│  │ - Book library browser                              │  │
│  │ - RSVP playback loop (word-by-word highlighting)    │  │
│  │ - Playback controls (play, pause, speed, position)  │  │
│  │ - TTS integration                                   │  │
│  │ - Annotation modal                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ rsvp/timing.js                                       │  │
│  │ - WPM → millisecond calculations                    │  │
│  │ - Word timing & punctuation pauses                  │  │
│  │ - Sentence sync calculations                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. Electron Main Process (`frontend/electron/main.js`)

**Purpose:** Window lifecycle management, subprocess orchestration, and desktop integration.

**Key Responsibilities:**
- Create and manage the main application window
- Launch Python backend as a child process (port 5000)
- Handle window events (close, minimize, focus)
- Manage app lifecycle (quit, relaunch)
- Enforce security constraints (`contextIsolation: true`, `nodeIntegration: false`)
- Handle OS-level file drag-and-drop (if implemented)

**Security Constraints:**
- Runs with limited Node.js access (no direct file system manipulation from renderer)
- Uses IPC bridge for preload scripts
- Backend API accessible only on localhost:127.0.0.1:5000

---

### 2. React Frontend (`frontend/src/`)

**Purpose:** User interface for book selection, RSVP playback, and annotation.

**Key Files:**

| File | Responsibility |
|------|-----------------|
| `App.js` | Main component: book library, playback loop, state management |
| `rsvp/timing.js` | WPM calculations, word timing, punctuation delay logic |

**Key Responsibilities:**
- **Book Library Browser:** Display books from library, handle selection/import
- **RSVP Playback Loop:** Word-by-word highlighting at calculated intervals
- **Playback Controls:** Play/pause, speed adjustment, seek/timeline
- **TTS Integration:** Fetch generated audio for paragraphs, handle audio playback
- **Annotations:** Modal to create/edit paragraph-level notes
- **State Management:** useCallbacks and useRefs for timing-critical operations

**Timing Calculation:**
```javascript
// From rsvp/timing.js
baseMsForWpm(wpm) = (60,000 / wpm)  // Base milliseconds per word
tokenDelayMs(token, baseMs) = baseMs + (punctuation_penalty)
```

**Frontend Architecture Patterns:**
- Functional React components (hooks only, no classes)
- useRef for audio and timing state to avoid re-renders
- useCallback for memoized event handlers
- useMemo for computed values (WPM calculations, library grouping)
- Local state for UI (error messages, loading states)
- Fetch API for all backend communication (no axios/fetch wrapper)

---

### 3. FastAPI Backend (`backend/main.py`)

**Purpose:** REST API server for document processing, state management, and TTS orchestration.

**Core Responsibilities:**

1. **Document Parsing**
   - Accept file uploads (PDF, EPUB, DOCX, TXT, MD)
   - Route to appropriate parser based on file extension
   - Return structured content (title, author, sentences/paragraphs)

2. **State Management**
   - Singleton tables: `CurrentBook` (id=1) and `PlaybackState` (id=1)
   - Persist playback position, speed, and session metadata
   - Reset state on book close

3. **RSVP Tokenization**
   - Split content into sentences for word-by-word display
   - Preserve punctuation metadata (attach to tokens)
   - Maintain paragraph indices for annotation linkage

4. **Text-Audio Synchronization (Phase 7)**
   - Calculate per-sentence durations based on word count and speed
   - Map playback position (seconds) to current sentence index
   - Allow seeking by sentence index

5. **TTS Generation**
   - Integrate with Google Cloud Text-to-Speech API
   - Generate MP3/WAV audio from paragraph text
   - Cache audio files in `./cache/audio/`
   - Stream or download audio to frontend

6. **Annotation Management**
   - Create, read, update, delete paragraph-level notes
   - Export annotations as formatted text file
   - Link annotations to book ID and paragraph index

7. **Library Scanning**
   - Scan configured library directory (`library_path`)
   - Return available books with metadata
   - Support library path updates via API

**API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check (DB & cache status) |
| `/api/library` | GET | List books in library |
| `/api/books/{book_id}` | GET | Get book metadata, paragraphs, tokens |
| `/api/library/path` | PUT | Update library path |
| `/api/book/import` | POST | Upload & import book |
| `/api/book/current` | GET | Get currently loaded book |
| `/api/book/close` | POST | Close book & reset state |
| `/api/playback/speed` | GET | Get adaptive speed (Phase 6) |
| `/api/playback/update` | POST | Update position/speed |
| `/api/playback/current-sentence` | GET | Get sentence at position (Phase 7) |
| `/api/playback/sync-sentence` | POST | Seek to sentence by index |
| `/api/tts` | POST | Generate TTS audio |
| `/api/audio/{job_id}/stream` | GET | Stream audio file |
| `/api/audio/{job_id}/download` | GET | Download audio file |
| `/api/annotations` | POST | Create annotation |
| `/api/annotations/{book_id}` | GET | List annotations |
| `/api/annotations/{annotation_id}` | DELETE | Delete annotation |
| `/api/annotations/{book_id}/export` | GET | Export annotations as TXT |
| `/api/settings` | GET | Get app configuration |

---

### 4. SQLite Database

**Purpose:** Persistent storage for book state, playback progress, and annotations.

**Tables:**

#### CurrentBook (Singleton: id=1)
```python
id: int (primary key, always 1)
title: str (nullable)
author: str (nullable)
filepath: str (nullable, uploaded filename)
filetype: str (pdf, epub, docx, txt, md)
content_json: str (JSON array of sentences)
created_at: datetime
updated_at: datetime
```

**Usage:**
- Stores currently loaded book content as JSON array
- Single row (id=1) enforced in code; reset on import or close
- `content_json` is array of sentence strings

#### PlaybackState (Singleton: id=1)
```python
id: int (primary key, always 1)
position_seconds: float (current audio position)
speed: float (playback speed multiplier, 0.5-3.0)
session_start: datetime (session begin time for adaptive speed)
last_updated: datetime (last state change)
current_sentence_index: int (Phase 7: current sentence number)
sentence_durations_json: str (Phase 7: JSON array of per-sentence durations)
```

**Usage:**
- Tracks real-time playback state
- `position_seconds` maps to audio position or RSVP timing
- `session_start` used to calculate adaptive speed (Phase 6)
- `sentence_durations_json` enables text-audio sync (Phase 7)
- Reset to defaults on book close

#### Annotation
```python
id: int (auto-increment primary key)
book_id: str (indexed, foreign reference to book)
paragraph_index: int (0-based index in book content)
section_title: str (nullable, e.g., "Chapter 3")
source_text: str (paragraph text being annotated)
note_text: str (user's note/highlight)
created_at: datetime
updated_at: datetime
```

**Usage:**
- One-to-many: one book has many annotations
- `book_id` is hash/slug derived from filename (not FK to CurrentBook)
- `paragraph_index` links to position in tokenized content
- Allows export as formatted text file

---

## Data Flow for Key Operations

### 1. Book Import Flow

```
User: Clicks "Import Book" button
  │
  ├─► Frontend: Opens file picker (Electron/OS dialog)
  │
  ├─► User: Selects PDF/EPUB/DOCX/TXT file
  │
  ├─► Frontend: POST /api/book/import with FormData
  │   ├─ File upload via multipart/form-data
  │   └─ Backend receives UploadFile
  │
  ├─► Backend: _read_uploaded_file()
  │   ├─ For TXT/MD: decode directly
  │   ├─ For PDF/EPUB/DOCX: save to temp file
  │   ├─ Load parser from PARSER_REGISTRY
  │   └─ parser.parse_file() → returns { title, author, content: [...] }
  │
  ├─► Backend: ContentFilter().filter_text()
  │   └─ Remove frontmatter, page numbers, footnotes
  │
  ├─► Backend: _split_sentences()
  │   └─ Regex split on sentence boundaries (.!?)
  │
  ├─► Backend: _upsert_current_book()
  │   ├─ Save to CurrentBook (id=1)
  │   ├─ Store sentences as JSON in content_json
  │   ├─ Calculate sentence_durations for sync
  │   └─ Reset PlaybackState to defaults
  │
  ├─► Backend: Returns BookImportResult
  │   ├─ id, title, author, filepath, num_sentences
  │   └─ HTTP 200
  │
  ├─► Frontend: Updates state
  │   ├─ setBook() with response
  │   ├─ Fetch /api/book/current to get full content
  │   ├─ Tokenize content (frontend copy for UI)
  │   ├─ Begin RSVP playback loop
  │   └─ Clear error message
  │
  └─► UI: Display book title, start playback
```

### 2. RSVP Playback Flow

```
User: Clicks "Play"
  │
  ├─► Frontend: setPlaying(true)
  │
  ├─► Frontend: Playback Loop (requestAnimationFrame)
  │   ├─ Calculate nextAtRef = nextToken * tokenDelayMs
  │   ├─ When elapsed time >= nextAtRef:
  │   │   ├─ Highlight current token (setIndex)
  │   │   ├─ If sentence_end: request TTS for next paragraph
  │   │   └─ Increment token index
  │   └─ Continue until playing=false or end of book
  │
  ├─► TTS Generation (triggered on sentence_end)
  │   ├─ Frontend: GET current paragraph from tokens
  │   ├─ POST /api/tts { text, voice }
  │   │
  │   ├─► Backend: _call_tts()
  │   │   ├─ _get_tts_service() (lazy singleton)
  │   │   ├─ GoogleTTSService.synthesize_to_file()
  │   │   │   └─ Call Google Cloud TTS API
  │   │   ├─ Save MP3 to ./cache/audio/{job_id}.mp3
  │   │   └─ Return TtsResponse with audio_path
  │   │
  │   ├─ Frontend: Receive audio_path (/api/audio/{job_id}/stream)
  │   ├─ audioRef.current.src = audio_url
  │   └─ audioRef.current.play()
  │
  ├─► Frontend: Speed Adjustment
  │   ├─ User changes WPM slider
  │   ├─ POST /api/playback/update { speed }
  │   └─ Update playback loop timing (baseMs recalculated)
  │
  ├─► Frontend: Pause/Seek
  │   ├─ POST /api/playback/update { position_seconds }
  │   ├─ GET /api/playback/current-sentence
  │   ├─ Backend: _get_sentence_at_position()
  │   │   └─ Binary search through cumulative durations
  │   ├─ Return current_sentence_index
  │   └─ Frontend: Reset token index to match
  │
  └─► User: Clicks "Stop" or book reaches end
      ├─ setPlaying(false)
      ├─ POST /api/playback/update to persist final position
      └─ Stop playback loop
```

### 3. Annotation Save Flow

```
User: Highlights paragraph & clicks "Annotate"
  │
  ├─► Frontend: Show AnnotationModal
  │   ├─ Display source_text (paragraph being annotated)
  │   └─ Show textarea for note_text
  │
  ├─► User: Types note & clicks "Save"
  │
  ├─► Frontend: POST /api/annotations
  │   ├─ AnnotationCreate payload:
  │   │   ├─ book_id: "hash_from_filename"
  │   │   ├─ paragraph_index: currentParagraphIndex
  │   │   ├─ section_title: "Chapter X" (optional, inferred)
  │   │   ├─ source_text: full paragraph text
  │   │   └─ note_text: user's note
  │   │
  │   ├─► Backend: create_annotation()
  │   │   ├─ Create Annotation record
  │   │   ├─ Insert to database
  │   │   └─ Return AnnotationResponse
  │   │
  │   ├─ Frontend: Receive annotation with id, created_at
  │   ├─ Update local annotations state
  │   └─ Show confirmation toast
  │
  └─► User: Can view/export annotations later
      ├─ GET /api/annotations/{book_id} (list all)
      ├─ GET /api/annotations/{book_id}/export (download as TXT)
      └─ DELETE /api/annotations/{annotation_id} (remove)
```

### 4. Text-Audio Synchronization Flow (Phase 7)

```
Backend: When book is imported
  │
  ├─► _calculate_sentence_durations(sentences, speed)
  │   ├─ For each sentence:
  │   │   ├─ Count words
  │   │   ├─ duration = (words / 150 WPM) * 60 / speed
  │   │   └─ Minimum 0.5 seconds per sentence
  │   └─ Store as JSON: [1.2, 0.8, 1.5, ...]
  │
  └─► Save to PlaybackState.sentence_durations_json
      └─ Persisted in DB, reused on resume

Frontend: During playback (on seek)
  │
  ├─► User seeks to position X seconds
  │
  ├─► POST /api/playback/sync-sentence { position_seconds: X }
  │
  ├─► Backend: _get_sentence_at_position(sentences, durations, X)
  │   ├─ Iterate through cumulative durations
  │   ├─ Find sentence where cumulative_time <= X < cumulative_time + duration[i]
  │   └─ Return sentence_index
  │
  ├─► Backend: Update PlaybackState.current_sentence_index
  │   └─ Store for resume/tracking
  │
  ├─► Frontend: Receive sentence_index
  │   ├─ Recalculate token_index from sentence boundary
  │   ├─ Highlight correct word immediately
  │   └─ Continue playback from new position
  │
  └─► Result: Smooth seek with text staying in sync
```

---

## File Structure

```
ReadMeLocal/
├── README.md                          # Project overview
├── CLAUDE.md                          # Developer guidance
├── docs/
│   ├── architecture.md               # This file
│   ├── API.md                        # API endpoint reference
│   └── ...
│
├── backend/                           # Python FastAPI server
│   ├── main.py                       # Entry point, FastAPI app, all endpoints
│   ├── requirements.txt              # Python dependencies
│   ├── pyproject.toml                # Project metadata
│   │
│   ├── parsers/                      # Document parsers (pluggable)
│   │   ├── __init__.py
│   │   ├── pdf_parser.py            # PDF parsing (PyPDF2)
│   │   ├── pdf_blocks.py            # PDF block-aware parsing
│   │   ├── epub_parser.py           # EPUB parsing (ebooklib)
│   │   └── docx_parser.py           # DOCX parsing (python-docx)
│   │
│   ├── tts/                          # TTS service (Google Cloud)
│   │   ├── __init__.py
│   │   └── google_tts.py            # GoogleTTSService class
│   │
│   ├── content_filter.py             # ContentFilter (strip frontmatter, etc.)
│   ├── rsvp_tokens.py               # split_paragraphs(), tokenize_paragraphs()
│   ├── library.py                   # scan_library() function
│   │
│   ├── tests/                        # Unit & integration tests
│   │   ├── conftest.py
│   │   ├── test_rsvp_tokens.py
│   │   ├── test_pdf_parser.py
│   │   ├── test_library_*.py
│   │   └── ...
│   │
│   └── __pycache__/                 # Compiled Python (ignored in git)
│
├── frontend/                          # Electron + React app
│   ├── package.json                 # Node dependencies, npm scripts
│   ├── package-lock.json
│   │
│   ├── public/
│   │   ├── index.html               # Electron window HTML
│   │   ├── icon.png                 # App icon
│   │   └── preload.js               # IPC bridge (if used)
│   │
│   ├── src/                         # React components
│   │   ├── index.js                 # React entry
│   │   ├── App.js                   # Main component
│   │   ├── App.css                  # Styles
│   │   │
│   │   ├── rsvp/
│   │   │   └── timing.js            # WPM calculations, timing logic
│   │   │
│   │   └── __tests__/               # Jest unit tests
│   │       ├── App.test.js
│   │       ├── timing.test.js
│   │       └── ...
│   │
│   ├── electron/
│   │   └── main.js                  # Electron main process
│   │       ├── Launches Python backend
│   │       ├── Creates main window
│   │       └── Handles app lifecycle
│   │
│   └── node_modules/                # npm packages (ignored in git)
│
├── config/                           # Configuration & secrets
│   ├── settings.yaml                # App configuration (git-tracked)
│   ├── secrets.env.template         # Template for API keys
│   └── secrets.env                  # API keys (git-ignored)
│
├── cache/                            # Runtime caches
│   ├── audio/                       # Generated TTS audio files
│   │   ├── tts-20250101120000.mp3
│   │   ├── tts-20250101120001.mp3
│   │   └── ...
│   └── ...
│
├── db/                              # Database files
│   └── readme.db                    # SQLite database
│
└── .git/                            # Git repository
    └── ...
```

---

## Configuration

### `config/settings.yaml`

Central configuration file (git-tracked, safe to commit).

```yaml
# TTS Provider & Voice Settings
tts:
  enabled: true
  provider: "google"
  default_voice: "en-US-Neural2-D"
  audio_encoding: "MP3"
  speaking_rate: 1.0

voices:
  - name: "en-US-Neural2-D"
    language_code: "en-US"
    gender: "MALE"

# Playback Configuration
playback:
  start_speed: 1.5              # Initial speed (1.5x)
  speed_increment: 0.1          # Increase every 15 minutes
  increment_interval_minutes: 15
  max_speed: 2.5

# RSVP Settings
rsvp:
  wpm_default: 150              # Default reading speed
  wpm_max: 1024                 # UI slider maximum

# Session Behavior
session:
  single_book_mode: true        # Only one book at a time
  auto_finish_threshold: 0.95   # Auto-finish at 95% progress

# Library & Database
library_path: "/path/to/books"  # Local book folder
database_path: "./db/readme.db"
cache_dir: "./cache"

# Annotation Settings
annotations:
  rewind_threshold_minutes: 5   # Allow rewind within 5 min

# Content Filtering
content_filtering:
  skip_frontmatter: true
  skip_page_numbers: true
  skip_footnotes: true

# Feature Flags
features:
  local_tts: true
  annotations: true
  bookmarks: true
  summarization: false
```

### `config/secrets.env`

API credentials (git-ignored, copy from template).

```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
# or inline JSON for Google Cloud TTS
```

---

## Key Design Patterns

### 1. Singleton State Pattern
- `CurrentBook` and `PlaybackState` tables always use `id=1`
- Single row per table enforced in application code
- Simplifies queries: no filtering needed, direct `db.get(Model, 1)`
- Reset on book close or import

### 2. Pluggable Parser Registry
```python
PARSER_REGISTRY = {
    ".pdf": ("backend.parsers.pdf_parser", "PDFParser", "pdf"),
    ".epub": ("backend.parsers.epub_parser", "EPUBParser", "epub"),
    ".docx": ("backend.parsers.docx_parser", "DOCXParser", "docx"),
}
```
- Dynamic import: `import_module(module_path)` → `getattr(class_name)`
- Extensible: add new format by registering parser
- Lazy loading: parser only imported when needed

### 3. Lazy Singleton Service (TTS)
```python
_LOCAL_TTS_SERVICE = None
_LOCAL_TTS_LOCK = threading.Lock()

def _get_tts_service():
    global _LOCAL_TTS_SERVICE
    if _LOCAL_TTS_SERVICE is not None:
        return _LOCAL_TTS_SERVICE
    with _LOCAL_TTS_LOCK:
        if _LOCAL_TTS_SERVICE is None:
            _LOCAL_TTS_SERVICE = GoogleTTSService(...)
    return _LOCAL_TTS_SERVICE
```
- Thread-safe initialization
- Expensive service (Google API client) created once
- Reused across requests

### 4. Content Normalization Pipeline
```
Raw Text
  ↓ parse_file() [parser-specific]
Structured { title, author, content }
  ↓ filter_text() [ContentFilter]
Filtered (frontmatter removed)
  ↓ split_sentences() or split_paragraphs()
Sentence/Paragraph array
  ↓ tokenize_paragraphs() [RSVP tokens]
Token array { text, punct, sentence_end, paragraph_index }
```

### 5. Frontend Timing State Management
- **useRef for timing state:** `nextAtRef`, `audioRef`, `prevParagraphRef`
  - Avoids re-renders during playback loop
  - Direct mutation without triggering React reconciliation
- **useState for UI state:** `playing`, `wpm`, `index`, `annotations`
  - Trigger re-renders and component updates
- **Separation:** timing loop in requestAnimationFrame, state updates batched

### 6. Text-Audio Sync (Phase 7)
- **Duration Calculation:** Per-sentence duration stored at import time
- **Position Mapping:** Cumulative duration array enables O(n) seek
- **Resume:** `sentence_durations_json` persisted, reused on app restart
- **Adaptive Speed:** Durations recalculated if speed changes during session

---

## Security & Privacy

### Local-First Architecture
- **Backend**: Binds only to `127.0.0.1:5000`, no external network exposure
- **CORS**: Restricted to `http://localhost:*` and `http://127.0.0.1:*` only
- **Data**: All processing, storage, and caching local to machine
- **No telemetry**: No tracking, analytics, or external API calls except TTS (required)

### Electron Security
- `contextIsolation: true` – Renderer process isolated from Node.js
- `nodeIntegration: false` – No direct Node.js access from renderer
- IPC bridge for controlled preload scripts (if used)
- Prevents malicious injected code from accessing file system

### Configuration Secrets
- `secrets.env` git-ignored: never commit API keys
- Template provided: `secrets.env.template`
- Google Cloud credentials loaded from environment variable or file path

### Database Privacy
- SQLite file local only: `./db/readme.db`
- No network synchronization (single-device app)
- Annotations stored with book ID (hash of filename), not user account

---

## Performance Considerations

### Timing-Critical Frontend Loop
- **RequestAnimationFrame**: Synced to display refresh rate (~60 Hz)
- **useRef state**: Avoids re-render overhead in inner loop
- **Batched updates**: `setIndex`, `setAnnotations` batched via React concurrent rendering
- **Memoization**: `baseMsForWpm`, `libraryByType` memoized to prevent recalculation

### Backend Parsing
- **Lazy parser loading**: Parser module imported only on first use of that file type
- **Temp files for binary formats**: PDF/EPUB/DOCX saved to `/tmp`, deleted after parsing
- **Content filtering**: Applied during import, not on every playback frame

### TTS Caching
- **Per-paragraph caching**: Audio files stored in `./cache/audio/` by job ID
- **No duplicate generation**: Frontend can reuse cached audio if same paragraph plays twice
- **Async I/O**: TTS call run in executor thread pool (non-blocking)

### Database Queries
- **Singleton pattern**: `db.get(Model, 1)` is O(1) primary key lookup
- **Indexed annotations**: `book_id` indexed for fast filtering
- **Full-text search**: Not implemented (could be added with SQLite FTS)

---

## Future Extensibility

### Parser Registry Expansion
- Add new document type: register format, implement parser class, add to `PARSER_REGISTRY`
- Example: `.mobi` (Kindle format) – implement `MobiParser.parse_file()`

### TTS Provider Switching
- Current: Google Cloud only
- Extensible: Abstract `TTSService` interface, implement `LocalTTSService`, `OpenAITTSService`
- Configuration: Select provider in `settings.yaml`

### Playback Features
- **Bookmarks:** Add `Bookmark` table, implement bookmark CRUD endpoints
- **Reading History:** Track books and session times per book
- **Export audio:** Generate full-book MP3 file (aggregate paragraph TTS)
- **Synchronized highlighting:** Option to highlight words as audio plays (not just RSVP)

### Content Enhancements
- **Table of contents (TOC):** Extract chapters/sections from PDF or EPUB
- **Search:** Full-text search within current book
- **Footnote extraction:** Separate footnotes/references from main text
- **Metadata extraction:** ISBN, published date, category from PDF metadata

### UI Improvements
- **Dark mode:** Add theme toggle, CSS variables for light/dark schemes
- **Keyboard shortcuts:** Navigation, playback control (space=play, arrow keys=seek)
- **Touch gestures:** Swipe to change book, pinch to adjust UI scale
- **Accessibility:** ARIA labels, screen reader support, high-contrast mode

---

## Development Workflow

### Starting the Application (Dev Mode)

```bash
# Terminal 1: Start React + Python backend
cd frontend
npm run electron-dev

# This automatically:
# 1. Starts React dev server (localhost:3000, HMR enabled)
# 2. Launches Electron window
# 3. Spawns Python backend (localhost:5000)
# 4. Connects all three together
```

### Testing

```bash
# Backend unit tests
cd backend
pytest
pytest backend/tests/test_rsvp_tokens.py  # Specific test file

# Frontend unit tests
cd frontend
npm test

# Manual API testing
curl http://localhost:5000/api/health
curl http://localhost:5000/api/settings
```

### Common Debugging

**Backend API unreachable from frontend:**
- Check Python process running: `lsof -i :5000`
- Verify CORS: inspect browser network tab for `Access-Control-*` headers
- Check config: ensure `local_api_host`, `local_api_port` in `settings.yaml`

**Playback timing off:**
- Verify WPM calculation: `App.js` line 70 `baseMsForWpm(wpm)`
- Check token generation: `rsvp/timing.js` `tokenDelayMs()` calculation
- Inspect playback loop: `App.js` `useEffect` with `requestAnimationFrame`

**Annotation not saving:**
- Check browser console for fetch errors
- Verify book_id generation: consistent hash across sessions
- Check DB file exists: `./db/readme.db`

**TTS generation slow or fails:**
- Verify Google Cloud credentials: `GOOGLE_APPLICATION_CREDENTIALS` env var set
- Check API quota: Google Cloud Console → Text-to-Speech quota
- Inspect audio cache: files should appear in `./cache/audio/`

---

## Related Documentation

- **API Reference:** `docs/API.md` – All endpoint signatures and response schemas
- **CLAUDE.md:** Project guidelines for developers
- **RSVP Algorithm:** Implemented in `frontend/src/rsvp/timing.js` and `backend/rsvp_tokens.py`
- **Testing Guide:** Test conventions and coverage goals in `backend/tests/`

