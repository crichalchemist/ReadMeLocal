# Sprint Reader Rebuild Plan (Visual-Only)

This plan defines a clean rebuild of ReadMeLocal into a visual-only sprint reader focused on PDF + EPUB ingestion. It removes TTS/audio and emphasizes fast, distraction-free reading on a black screen with single-word display.

## Product Goals
- **File formats**: PDF + EPUB (first), then DOCX/TXT.
- **Reading mode**: single word per tick (RSVP), minimal black screen UI.
- **Local-first**: all parsing happens locally; no cloud dependency.
- **Privacy**: no external telemetry, no remote file upload.

## Architecture (Simplified)
```
Electron UI (React)
   │
   ▼
Local FastAPI (Python)
   │
   ▼
Parsers → Token Store (sentences → words)
```

## Backend Plan (FastAPI)
### Parsing pipeline
1. **Extract text** from PDF/EPUB with trusted libraries.
2. **Normalize**: remove headers/footers, page numbers, repeated whitespace.
3. **Tokenize**: split into sentences → words with punctuation preserved.
4. **Store**: persist tokens + offsets for resume/progress.

### Proposed endpoints
- `POST /api/books/import`
  - Payload: file upload (PDF/EPUB)
  - Response: `{ book_id, title, total_words }`
- `GET /api/books/{id}`
  - Response: metadata + current progress
- `GET /api/books/{id}/tokens?offset=0&limit=500`
  - Response: `{ tokens, next_offset }`
- `POST /api/books/{id}/progress`
  - Payload: `{ offset, wpm }`

### Token schema (conceptual)
```json
{
  "index": 142,
  "text": "Therefore",
  "is_punctuation": false,
  "pause_weight": 1.2
}
```

## Frontend Plan (React + Electron)
### Sprint Reader View
- Full-screen black background
- One word centered, large white type
- Highlight **optimal recognition point** (ORP)
- Controls:
  - Play/pause
  - WPM slider
  - Jump back 10 words
  - Progress bar (word index / total)

### Timing logic (visual-only)
- Base interval derived from WPM
- Increase delay for punctuation and long words
- Clamp minimum/maximum delay for stability

## Security Considerations
- Bind FastAPI to `localhost` only.
- Never enable `nodeIntegration` in Electron.
- Validate file size/type to prevent parser abuse.
- Store tokens locally; never transmit book content externally.

## Milestones
1. **MVP**: PDF + EPUB parsing, single-word UI, WPM control.
2. **Refinement**: punctuation weighting, ORP highlight.
3. **Resilience**: crash-safe progress saves, token caching.
