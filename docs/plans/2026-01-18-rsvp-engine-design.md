# RSVP Engine Design (Local Web App)

Date: 2026-01-18  
Status: Draft (approved)

## Goals
- Build a local-only web app for speed-reading PDF/EPUB files.
- Use RSVP with a fixed focal point and a scrolling context pane.
- Start at 150 WPM with a configurable max of 1024 WPM.
- Support punctuation-based pause rules in v1.
- Keep the stack: FastAPI backend + React frontend.

## Architecture
The backend scans a configured library folder for `.pdf` and `.epub` files, parses them, and emits a normalized token stream with sentence and paragraph markers. The frontend fetches the stream, runs the RSVP scheduler, and renders the reader UI. The RSVP engine lives entirely in the browser and uses a monotonic clock to avoid timer drift. State (book progress, last position) is persisted locally in SQLite for resume.

## Components
- **Backend (FastAPI)**
  - Library scan endpoint (`GET /api/library`)
  - Book details + tokens (`GET /api/books/{id}`)
  - Re-import/refresh endpoint for stale files
  - Parsing fallback: PyMuPDF → pdfplumber (PDF); ebooklib for EPUB
- **Frontend (React)**
  - Library list + metadata panel
  - Reader view: RSVP focal display + scrolling context pane
  - Controls: play/pause, WPM slider (150–1024), jump ±10 words
  - RSVP scheduler: `performance.now()`-driven progression

## Data Flow
1) UI loads library list.  
2) User selects a book; backend returns tokens + markers.  
3) Frontend precomputes per-token durations: base ms from WPM plus punctuation pauses.  
4) Scheduler advances tokens when elapsed time crosses the next threshold.  
5) Context pane highlights the current token and auto-scrolls.

## Timing Rules (v1)
- Base duration: `60_000 / WPM`
- Punctuation pauses: commas/semicolons +150ms, periods/question/exclamation +300ms, paragraph break +500ms.
- Single-word display only (no chunking in v1).

## Error Handling
- Missing library path: return 400 with actionable message.
- Parse failure: try alternate parser, then surface error with re-import option.
- Stale file detected: mark as stale and prompt re-import.

## Testing
- Backend: parsing + token normalization tests in `backend/tests`.
- Frontend: timing math + scheduler progression tests in `frontend/src/__tests__`.
- Integration: golden PDF/EPUB fixtures with expected token counts.

## Open Questions (deferred)
- Chunking (multi-word per slide)
- Worker-based scheduler for heavy UI loads
- Advanced language-specific pause rules
