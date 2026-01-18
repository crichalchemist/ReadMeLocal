# RSVP Web App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local-only RSVP speed-reading web app that scans a library folder of PDF/EPUB files and renders RSVP playback with a context pane.

**Architecture:** FastAPI scans and parses files, normalizes text into token streams, and serves library/book APIs. React UI fetches tokens, schedules RSVP playback using a monotonic clock, and renders a focal word plus scrolling context.

**Tech Stack:** FastAPI, Python 3.11+, React (react-scripts), SQLite (local state), PyMuPDF/pdfplumber, ebooklib, pytest, Jest.

---

### Task 1: Add library configuration and scanner utility

**Files:**
- Modify: `config/settings.yaml`
- Create: `backend/library.py`
- Test: `backend/tests/test_library_scan.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from backend.library import scan_library


def test_scan_library_filters_and_sorts(tmp_path: Path):
    (tmp_path / "A.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "b.epub").write_text("x", encoding="utf-8")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")

    results = scan_library(tmp_path)
    names = [item["title"] for item in results]

    assert names == ["A", "b"]
    assert all(item["ext"] in (".pdf", ".epub") for item in results)
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_library_scan.py::test_scan_library_filters_and_sorts -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.library'`

**Step 3: Write minimal implementation**

```python
# backend/library.py
from __future__ import annotations

import hashlib
from pathlib import Path

SUPPORTED_EXTS = (".pdf", ".epub")


def _book_id(path: Path) -> str:
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()


def scan_library(library_path: Path) -> list[dict]:
    items: list[dict] = []
    for file_path in library_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTS:
            continue
        items.append(
            {
                "id": _book_id(file_path),
                "title": file_path.stem,
                "path": str(file_path),
                "ext": file_path.suffix.lower(),
            }
        )
    return sorted(items, key=lambda item: item["title"].lower())
```

Update `config/settings.yaml`:

```yaml
library_path: "/volumes/Rich 3TB/books"
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_library_scan.py::test_scan_library_filters_and_sorts -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add config/settings.yaml backend/library.py backend/tests/test_library_scan.py
git commit -m "feat: add library path and scanner"
```

---

### Task 2: Add RSVP tokenization utilities

**Files:**
- Create: `backend/rsvp_tokens.py`
- Test: `backend/tests/test_rsvp_tokens.py`

**Step 1: Write the failing test**

```python
from backend.rsvp_tokens import split_paragraphs, tokenize_paragraphs


def test_tokenize_paragraphs_marks_punctuation():
    text = "Hello world. Next, line.\n\nNew para!"
    paragraphs = split_paragraphs(text)
    tokens = tokenize_paragraphs(paragraphs)

    assert paragraphs == ["Hello world. Next, line.", "New para!"]
    assert tokens[1]["text"] == "world"
    assert tokens[1]["punct"] == "."
    assert tokens[-1]["text"] == "para"
    assert tokens[-1]["punct"] == "!"
    assert tokens[-1]["paragraph_index"] == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_rsvp_tokens.py::test_tokenize_paragraphs_marks_punctuation -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.rsvp_tokens'`

**Step 3: Write minimal implementation**

```python
# backend/rsvp_tokens.py
from __future__ import annotations

import re

PUNCTUATION = {",", ";", ":", ".", "!", "?"}


def split_paragraphs(text: str) -> list[str]:
    chunks = re.split(r"\n\s*\n+", text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def tokenize_paragraphs(paragraphs: list[str]) -> list[dict]:
    tokens: list[dict] = []
    word_re = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?|[.,;:!?]")
    for p_index, paragraph in enumerate(paragraphs):
        for match in word_re.findall(paragraph):
            if match in PUNCTUATION and tokens:
                tokens[-1]["punct"] = match
                if match in {".", "!", "?"}:
                    tokens[-1]["sentence_end"] = True
                continue
            tokens.append(
                {
                    "text": match,
                    "punct": "",
                    "sentence_end": False,
                    "paragraph_index": p_index,
                }
            )
    return tokens
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_rsvp_tokens.py::test_tokenize_paragraphs_marks_punctuation -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/rsvp_tokens.py backend/tests/test_rsvp_tokens.py
git commit -m "feat: add RSVP tokenization utilities"
```

---

### Task 3: Add library and book APIs

**Files:**
- Modify: `backend/main.py`
- Test: `backend/tests/test_library_api.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from pathlib import Path
from backend.main import app


def test_library_endpoint_returns_books(tmp_path: Path, monkeypatch):
    (tmp_path / "Sample.pdf").write_text("Hello world.", encoding="utf-8")
    monkeypatch.setenv("README_LIBRARY_PATH", str(tmp_path))

    client = TestClient(app)
    res = client.get("/api/library")

    assert res.status_code == 200
    data = res.json()
    assert data[0]["title"] == "Sample"
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_library_api.py::test_library_endpoint_returns_books -v`  
Expected: FAIL with 404 or import errors

**Step 3: Write minimal implementation**

```python
# backend/main.py (add near config)
LIBRARY_PATH = Path(
    os.getenv("README_LIBRARY_PATH", SETTINGS.get("library_path", ""))
).expanduser()

# add to /api/settings response
"library_path": str(LIBRARY_PATH),
"rsvp": {
    "wpm_default": 150,
    "wpm_max": 1024,
},

# add endpoint
from backend.library import scan_library

@app.get("/api/library")
def list_library():
    if not LIBRARY_PATH or not LIBRARY_PATH.exists():
        raise HTTPException(status_code=400, detail="Library path not configured")
    return scan_library(LIBRARY_PATH)
```

Add `/api/books/{book_id}` (simplified sketch):

```python
from backend.rsvp_tokens import split_paragraphs, tokenize_paragraphs

@app.get("/api/books/{book_id}")
def get_book(book_id: str):
    items = scan_library(LIBRARY_PATH)
    match = next((item for item in items if item["id"] == book_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Book not found")

    parser = _load_parser(match["ext"])
    parsed = parser.parse_file(match["path"])
    raw_text = parsed.get("raw_text") or "\n\n".join(parsed.get("content", []))
    paragraphs = split_paragraphs(raw_text)
    tokens = tokenize_paragraphs(paragraphs)
    return {
        "id": match["id"],
        "title": parsed.get("title") or match["title"],
        "author": parsed.get("author"),
        "paragraphs": paragraphs,
        "tokens": tokens,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_library_api.py::test_library_endpoint_returns_books -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_library_api.py
git commit -m "feat: add library and book APIs"
```

---

### Task 4: Add RSVP timing helpers in the frontend

**Files:**
- Create: `frontend/src/rsvp/timing.js`
- Test: `frontend/src/__tests__/timing.test.js`

**Step 1: Write the failing test**

```javascript
import { baseMsForWpm, tokenDelayMs } from "../rsvp/timing";

test("tokenDelayMs adds punctuation pauses", () => {
  const base = baseMsForWpm(150);
  const token = { text: "world", punct: "." };
  expect(tokenDelayMs(token, base)).toBe(base + 300);
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --watchAll=false`  
Expected: FAIL with module not found

**Step 3: Write minimal implementation**

```javascript
// frontend/src/rsvp/timing.js
export const baseMsForWpm = (wpm) => Math.round(60000 / wpm);

export const tokenDelayMs = (token, baseMs) => {
  const punct = token.punct || "";
  if (punct === "," || punct === ";" || punct === ":") return baseMs + 150;
  if (punct === "." || punct === "!" || punct === "?") return baseMs + 300;
  return baseMs;
};
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --watchAll=false`  
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/rsvp/timing.js frontend/src/__tests__/timing.test.js
git commit -m "feat: add RSVP timing helpers"
```

---

### Task 5: Replace the UI with library + RSVP reader

**Files:**
- Modify: `frontend/src/App.js`
- Modify: `frontend/src/App.css`

**Step 1: Write the failing test (minimal UI smoke test)**

```javascript
import { render, screen } from "@testing-library/react";
import App from "../App";

test("renders library heading", () => {
  render(<App />);
  expect(screen.getByText(/Library/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --watchAll=false`  
Expected: FAIL with missing heading

**Step 3: Write minimal implementation**

```javascript
// frontend/src/App.js (sketch)
import React, { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import { baseMsForWpm, tokenDelayMs } from "./rsvp/timing";

const API_BASE = "http://localhost:5000";

function App() {
  const [library, setLibrary] = useState([]);
  const [book, setBook] = useState(null);
  const [tokens, setTokens] = useState([]);
  const [paragraphs, setParagraphs] = useState([]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [wpm, setWpm] = useState(150);
  const nextAtRef = useRef(0);

  useEffect(() => {
    fetch(`${API_BASE}/api/library`)
      .then((res) => res.json())
      .then(setLibrary)
      .catch(() => setLibrary([]));
  }, []);

  const baseMs = useMemo(() => baseMsForWpm(wpm), [wpm]);

  useEffect(() => {
    if (!playing || tokens.length === 0) return;
    let rafId;
    const tick = (now) => {
      if (nextAtRef.current === 0) {
        nextAtRef.current = now + tokenDelayMs(tokens[index], baseMs);
      }
      if (now >= nextAtRef.current) {
        setIndex((prev) => Math.min(prev + 1, tokens.length - 1));
        nextAtRef.current = now + tokenDelayMs(tokens[index], baseMs);
      }
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [playing, tokens, index, baseMs]);

  const loadBook = async (bookId) => {
    const res = await fetch(`${API_BASE}/api/books/${bookId}`);
    const data = await res.json();
    setBook(data);
    setTokens(data.tokens || []);
    setParagraphs(data.paragraphs || []);
    setIndex(0);
    setPlaying(false);
    nextAtRef.current = 0;
  };

  return (
    <div className="app">
      <aside className="library">
        <h2>Library</h2>
        <ul>
          {library.map((item) => (
            <li key={item.id}>
              <button onClick={() => loadBook(item.id)}>{item.title}</button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="reader">
        <div className="rsvp">
          <div className="word">{tokens[index]?.text || ""}</div>
          <div className="controls">
            <button onClick={() => setPlaying((p) => !p)}>
              {playing ? "Pause" : "Play"}
            </button>
            <input
              type="range"
              min="150"
              max="1024"
              value={wpm}
              onChange={(e) => setWpm(Number(e.target.value))}
            />
            <span>{wpm} WPM</span>
          </div>
        </div>
        <section className="context">
          {paragraphs.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </section>
      </main>
    </div>
  );
}

export default App;
```

Update `frontend/src/App.css` with basic layout and focal word styling.

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --watchAll=false`  
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.js frontend/src/App.css
git commit -m "feat: replace UI with library + RSVP reader"
```

---

### Task 6: Highlight current token in context pane

**Files:**
- Modify: `frontend/src/App.js`
- Modify: `frontend/src/App.css`
- Test: `frontend/src/__tests__/context.test.js`

**Step 1: Write the failing test**

```javascript
import { render, screen } from "@testing-library/react";
import App from "../App";

test("highlights current word", () => {
  render(<App />);
  expect(screen.queryByText(/current-word/)).not.toBeNull();
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --watchAll=false`  
Expected: FAIL

**Step 3: Write minimal implementation**

Add a computed current paragraph + word span class:

```javascript
// in App.js render
{paragraphs.map((p, i) => (
  <p key={i} className={i === tokens[index]?.paragraph_index ? "active" : ""}>
    {p}
  </p>
))}
```

And CSS:

```css
.context .active {
  background: #fff7cc;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --watchAll=false`  
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/App.js frontend/src/App.css frontend/src/__tests__/context.test.js
git commit -m "feat: highlight current context paragraph"
```

---

## Notes
- Library path comes from `config/settings.yaml` or `README_LIBRARY_PATH` env var.
- Target library: `/volumes/Rich 3TB/books`.

