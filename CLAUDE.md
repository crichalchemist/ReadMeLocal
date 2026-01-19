# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ReadMe Local is a self-hosted desktop application that converts digital books (PDF, EPUB, TXT, DOCX) into natural-sounding speech with RSVP (Rapid Serial Visual Presentation) reading, supported by a comprehensive annotation system. Built with Electron + React (frontend) and FastAPI (backend), it prioritizes privacy through a local-first architecture with Google Cloud Text-to-Speech integration.

## Development Commands

### Backend (Python)
```bash
cd backend
python3 -m venv venv && source venv/bin/activate  # Setup venv
pip install -r requirements.txt                    # Install deps

uvicorn main:app --reload --host 127.0.0.1 --port 5000  # Dev server
pytest                                             # Run all tests
pytest backend/tests/test_rsvp_tokens.py           # Single test file
black .                                            # Format code
```

### Frontend (Electron + React)
```bash
cd frontend
npm install           # Install deps
npm start             # React dev server only (localhost:3000)
npm run electron-dev  # Full app: React + Python backend + Electron
npm test              # Run React tests
npm run build         # Production build
npm run electron-build  # Package Electron app
```

### Full Application
```bash
cd frontend && npm run electron-dev  # Starts everything
```
Electron automatically spawns the Python backend on port 5000.

## Architecture

```
Electron (main.js) → spawns Python subprocess
       ↓
React UI (App.js) ←→ FastAPI backend (main.py)
                            ↓
                    SQLite + Parsers + TTS
```

**Key data flow:**
1. Documents parsed by backend (`backend/parsers/`) with position-aware filtering
2. Content tokenized for RSVP (`backend/rsvp_tokens.py`)
3. React renders word-by-word with timing (`frontend/src/rsvp/timing.js`)
4. TTS via Google Cloud Text-to-Speech with configurable voices and playback speeds
5. User annotations stored and exported via dedicated API endpoints

### Core Modules

| Module | Purpose |
|--------|---------|
| `backend/main.py` | FastAPI app, all API endpoints, DB models |
| `backend/parsers/*.py` | Document extraction (PDF, EPUB, DOCX, TXT) with position-aware filtering |
| `backend/rsvp_tokens.py` | Tokenization with punctuation metadata |
| `backend/content_filter.py` | Skip frontmatter, page numbers, footnotes (position-aware for PDFs) |
| `frontend/src/App.js` | Main React component, RSVP playback loop |
| `frontend/src/rsvp/timing.js` | WPM calculations, punctuation pauses |
| `frontend/src/components/AnnotationModal.js` | Annotation UI with keyboard shortcuts |
| `frontend/electron/main.js` | Electron process, Python subprocess mgmt |

### Pluggable Parser Registry
```python
PARSER_REGISTRY = {
    ".pdf": ("backend.parsers.pdf_parser", "PDFParser", "pdf"),
    ".epub": ("backend.parsers.epub_parser", "EPUBParser", "epub"),
    ".docx": ("backend.parsers.docx_parser", "DOCXParser", "docx"),
    ".txt": ("backend.parsers.text_parser", "TextParser", "txt"),
}
```

## Configuration

- `config/settings.yaml` - App settings (voices, filtering, playback speeds)
- `config/secrets.env` - Google Cloud TTS credentials (copy from `secrets.env.template`, git-ignored)
  - `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud service account JSON file
- `library_path` in settings.yaml - Points to local books folder

## Text-to-Speech

ReadMe Local uses **Google Cloud Text-to-Speech** exclusively for high-quality natural-sounding audio synthesis. Configuration requires:

1. Google Cloud service account JSON credentials file
2. `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to the credentials file
3. Configurable voice selection and playback speeds via settings.yaml

## Annotation System

The annotation system enables reading notes with keyboard shortcuts:

- **N** - Add new annotation at current position
- **Esc** - Close annotation modal
- **Cmd+Enter** (Mac) or **Ctrl+Enter** (Windows/Linux) - Save annotation
- Annotations are stored in SQLite and can be exported via dedicated API endpoints
- Component: `frontend/src/components/AnnotationModal.js`

## Code Style

- **Python**: 4-space indent, `black` formatter, snake_case, type hints (PEP 484)
- **JavaScript/React**: 2-space indent, PascalCase components, hooks prefixed `use`
- **Commits**: `type: short description` (feat, fix, docs, chore)

## Testing

- Backend: `pytest` with files named `test_*.py` in `backend/tests/`
- Frontend: `npm test` runs React tests via `react-scripts`
- Focus coverage on RSVP timing logic and tokenization

## API Documentation

When backend is running: http://localhost:5000/docs (Swagger UI)

## Key Patterns

1. **Local-first**: Backend binds only to localhost:5000
2. **Singleton state**: `CurrentBook` and `PlaybackState` tables use id=1
3. **Functional React**: Hooks only, no class components
4. **Electron security**: `contextIsolation: true`, `nodeIntegration: false`

## Current Status

Phase 7 (Text-Audio Sync) complete. Phase 8 (Single-Book Lock) next.
