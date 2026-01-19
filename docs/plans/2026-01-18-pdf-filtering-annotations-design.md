# PDF Filtering & Annotations Design

**Date:** 2026-01-18
**Status:** Approved

## Overview

Two features to improve the reading experience:
1. **Position-aware PDF filtering** — Use text coordinates to reliably strip headers, footers, page numbers, and footnotes
2. **Paragraph-level annotations** — Pause RSVP to take notes, with smart rewind and TXT export

## Feature 1: Enhanced PDF Content Filtering

### Problem

PDFs have no semantic structure — text is positioned visually. Current regex-based filtering misses headers, footers, and page numbers that don't match expected patterns.

### Approach: Position-Aware Heuristics

1. **Extract text with coordinates** — Use PyMuPDF's block/span data which includes `(x0, y0, x1, y1)` bounding boxes and font metadata

2. **Classify by position**:
   - Top 10% of page → likely header
   - Bottom 10% of page → likely footer/page number
   - Small font + bottom position → footnote

3. **Validate with patterns**:
   - Repeated text across pages at same Y-position → header/footer
   - Isolated numbers at page bottom → page numbers
   - Superscript + small text block → footnote

4. **Configurable thresholds** in `settings.yaml`:
   ```yaml
   pdf_filtering:
     header_zone_percent: 0.10
     footer_zone_percent: 0.10
     min_body_font_size: 9
   ```

### Files to Modify

- `backend/parsers/pdf_parser.py` — Add position-aware extraction
- `backend/content_filter.py` — Add PDF-specific filtering methods
- `config/settings.yaml` — New config section

## Feature 2: Annotation System

### Data Model

Annotations tied to paragraphs, not individual RSVP words:

```sql
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY,
    book_id TEXT NOT NULL,           -- links to book being read
    paragraph_index INTEGER NOT NULL, -- which paragraph
    section_title TEXT,              -- "Chapter 3" if detectable
    source_text TEXT NOT NULL,       -- the paragraph text for export context
    note_text TEXT NOT NULL,         -- user's annotation
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Why Paragraph-Level

- RSVP shows one word at a time, but thoughts relate to the *idea*, not the word
- Paragraphs are natural thought units
- Exporting "Note: [thought]" under "Source: [paragraph]" provides context when reviewing

### UX: Pause, Note, Resume

1. **While RSVP is playing**, press `N` (or click note icon)
2. **RSVP pauses**, note modal appears showing:
   - Current paragraph text (context)
   - Text input for note
   - Save / Cancel buttons
3. **Save** stores annotation, resumes RSVP
4. **Cancel** closes modal, resumes RSVP

### 5-Minute Rewind Logic

- On pause, record: `pause_time`, `paragraph_index`, `word_index`
- On resume:
  - If `now - pause_time < 5 minutes` → continue from exact word
  - If `now - pause_time >= 5 minutes` → rewind to start of that paragraph

Configuration:
```yaml
annotations:
  rewind_threshold_minutes: 5
```

### Keyboard Shortcuts

- `N` — Open annotation modal
- `Esc` — Cancel/close modal
- `Cmd/Ctrl + Enter` — Save note

### API Endpoints

- `POST /api/annotations` — Create annotation
- `GET /api/annotations/{book_id}` — List annotations for book
- `DELETE /api/annotations/{id}` — Delete annotation
- `GET /api/annotations/{book_id}/export` — Export as TXT

## Feature 3: TXT Export

### Format

Notes paired with source text, organized by position in book:

```
========================================
ANNOTATIONS: "All About Love" by bell hooks
Exported: 2026-01-18
Total notes: 7
========================================

--- Chapter 1, Paragraph 3 ---
SOURCE:
"The word 'love' is most often defined as a noun, yet all the more
astute theorists of love acknowledge that we would all love better
if we used it as a verb."

NOTE:
Love as action, not feeling. Connect to her later point about will.

----------------------------------------
```

### Trigger

- Button in UI: "Export Annotations"
- Downloads `{book-title}-annotations.txt`

## Implementation Order

1. **PDF filtering** — Improves reading experience immediately
2. **Annotation data model** — Backend foundation (SQLite table + endpoints)
3. **Annotation UI** — Frontend modal + keyboard shortcuts
4. **Export** — Builds on stored annotations

## Files to Modify

| File | Changes |
|------|---------|
| `backend/parsers/pdf_parser.py` | Position-aware text extraction |
| `backend/content_filter.py` | PDF-specific filtering methods |
| `backend/main.py` | Annotation model + CRUD endpoints + export |
| `frontend/src/App.js` | Annotation modal, keyboard handlers, export button |
| `frontend/src/App.css` | Modal styling |
| `config/settings.yaml` | New config sections |

## Not Included (Future Work)

- DOCX/RTF export
- Duplicate book detection
- OCR for scanned PDFs
