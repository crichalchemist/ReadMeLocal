### Cleaned and reformatted revised plan (forward)

Last updated: 2025-11-06 04:21

This supersedes prior plans. Focus: a minimal, single‑book MVP with sentence‑level sync, smart filtering, and adaptive speed.

---

### Option C — Sentence‑Level Sync (Recommended for MVP)
#### Phases 2–3 Combined: Minimalistic MVP Implementation

#### Overview
- Build a focused, single‑book reading experience with smart content filtering and adaptive speed.

---

### Phase 2: Core Backend (45 mins)
- Database (Simplified)
  - Single‑book schema: store only current book state
  - Tables: `current_book`, `playback_state` (no library management)
  - Alembic setup: initialize with minimal schema
- Models & Schemas
  - `CurrentBook` model (one row, overwritten on new import)
  - `PlaybackState` model (tracks speed, position, session start)
  - Content filtering utilities
- API Endpoints
  - POST `/api/book/import` — parse and set as current book
  - GET `/api/book/current` — get current book with cleaned content
  - POST `/api/book/close` — clear current book slot
  - GET `/api/playback/speed` — get current adaptive speed
  - POST `/api/playback/update` — update playback position

---

### Phase 3: Smart Content Parsing (45 mins)
- Content Filter Implementation
  - Frontmatter Skipper
    - Detect “Chapter 1” markers (regex patterns)
    - Fallback: skip first 5% if no markers found
  - Page Number Remover
    - Remove standalone numbers on lines
    - Remove "Page X" patterns
  - Footnote Remover
    - Strip `[1]`, `[2]` style references
    - Remove footnote sections at chapter ends
  - Header/Footer Remover
    - Detect repeated lines (book title, author)
    - Remove lines appearing > 3 times
- Parser Enhancement
  - Integrate `ContentFilter` into each parser (PDF, EPUB, TXT, DOCX)
  - Split text into sentences for highlighting
  - Store as array: `["Sentence 1.", "Sentence 2.", ...]`
- Testing
  - Create test fixtures with sample books
  - Test filter accuracy on various formats
  - Tune regex patterns

---

### Phases 4–5: Minimalistic UI (60 mins)
- Empty State
  - Large drop zone with clear instructions
  - “Select File” button as fallback
  - Clean, centered design
- Reading View
  - Full‑screen text display
  - Current sentence highlighted (subtle background color)
  - Auto‑scroll to keep highlighted sentence centered
  - Chapter/section name at top
- Playback Controls (Bottom Bar)
  - Play/Pause (space bar shortcut)
  - Speed indicator (1.5× → auto‑incrementing)
  - Skip backward/forward 15 s
  - Minimal menu (⋮): Close Book, Settings
- Drag & Drop Handler
  - If a book is already open → confirm close
  - Auto‑parse dropped file
  - Auto‑generate TTS audio (show progress)
  - Auto‑start playback when ready

---

### Phase 6: Adaptive Speed System (30 mins)
- Backend Service
  - `AdaptiveSpeedManager` class
  - Tracks session start time
  - Calculates current speed: `1.5 + (minutes_elapsed / 15) * 0.1`
  - Caps at 2.5×
- Frontend Integration
  - Poll speed every minute
  - Update audio playback rate
  - Display current speed in UI
  - Optional: toast notification on speed increase
- Persistence
  - Save session start time to DB
  - Resume speed calculation on app restart
  - Reset on new book

---

### Phase 7: Text–Audio Sync (45 mins)
- Sentence‑Level Highlighting
  - Estimate sentence durations
  - Count words in sentence
  - Calculate: `duration = (words / (150 * speed)) * 60`
- Track Audio Position
  - Get `currentTime` from audio player
  - Calculate which sentence should be highlighted
  - Update highlight in real time
- Auto‑scroll
  - Keep highlighted sentence centered
  - Smooth scrolling animation
- Audio Player Integration
  - HTML5 Audio API with playback‑rate control
  - Seek handlers (±15 s buttons)
  - Position persistence (save every 5 s)

---

### Phase 8: Single‑Book Lock (20 mins)
- Session Manager
  - `BookSessionManager` enforces one‑book‑at‑a‑time
  - API returns error if book already open
  - Frontend shows confirmation dialog
- Close Book Flow
  - Manual close: ⋮ → Close Book
  - Confirmation: “Progress will be lost. Continue?”
  - Clear current book state
  - Return to drop zone
- Auto‑finish Detection
  - Mark as finished when playback reaches 95%
  - Show completion message
  - Automatically unlock for new book

---

### Key Features Summary
- ✅ Minimalistic UI: Single‑pane, no clutter
- ✅ Drag & Drop: Instant file → reading
- ✅ Smart Filtering: Skip frontmatter, page numbers, footnotes
- ✅ Adaptive Speed: 1.5× → increments every 15 minutes
- ✅ Text Highlighting: Sentence‑level sync with audio
- ✅ Single‑Book Focus: One book at a time; finish before next

---

### Testing Checkpoints
- After Phase 3: Test content filtering with 3–5 sample books
- After Phase 5: Test drag‑and‑drop UX flow
- After Phase 6: Verify speed adaptation over a 30‑min session
- After Phase 7: Test text–audio sync accuracy
- After Phase 8: Test book‑locking behavior

---

### Configuration Changes
Update `config/settings.yaml`:

```yaml
playback:
  start_speed: 1.5
  speed_increment: 0.1
  increment_interval_minutes: 15
  max_speed: 2.5

content_filtering:
  skip_frontmatter: true
  skip_page_numbers: true
  skip_footnotes: true
  skip_headers_footers: true
  frontmatter_skip_percent: 0.05  # Fallback: skip first 5%

ui:
  theme: "minimal"
  highlight_style: "sentence"  # vs "word"
  auto_scroll: true

session:
  single_book_mode: true
  auto_finish_threshold: 0.95  # 95% completion
```

---

### Success Criteria
- Drop a book → immediate parsing → auto‑play
- No page numbers, footnotes, or frontmatter visible
- Playback starts at 1.5× and increases to 1.6× after 15 minutes
- Current sentence is highlighted as audio plays
- Cannot open a second book until the first is closed
- Clean, distraction‑free reading experience

---

### Estimated Total Time
- 4–5 hours of focused development
- Phases affected: 2, 3, 4, 5, 6, 7, 8 (condensed and refocused)