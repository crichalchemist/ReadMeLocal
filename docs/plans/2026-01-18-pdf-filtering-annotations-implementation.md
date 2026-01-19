# PDF Filtering & Annotations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve PDF content extraction with position-aware filtering, add paragraph-level annotations with TXT export.

**Architecture:** Position-aware PDF parsing uses PyMuPDF's block coordinates to classify text regions (header/body/footer). Annotations stored in SQLite, linked to paragraphs. Frontend modal with keyboard shortcuts for pause-and-note workflow.

**Tech Stack:** PyMuPDF (fitz), SQLAlchemy, FastAPI, React hooks

---

## Phase 1: Position-Aware PDF Filtering

### Task 1.1: Add PDF Filtering Config

**Files:**
- Modify: `config/settings.yaml`

**Step 1: Add config section**

Add to `config/settings.yaml` after the `content_filtering` section:

```yaml
# PDF-specific filtering (position-aware)
pdf_filtering:
  header_zone_percent: 0.10    # Top 10% of page
  footer_zone_percent: 0.10    # Bottom 10% of page
  min_body_font_size: 9        # Fonts smaller than this in footer = footnotes
  detect_repeated_headers: true
```

**Step 2: Commit**

```bash
git add config/settings.yaml
git commit -m "config: add pdf_filtering settings"
```

---

### Task 1.2: Create PDF Block Extractor

**Files:**
- Create: `backend/parsers/pdf_blocks.py`
- Test: `backend/tests/test_pdf_blocks.py`

**Step 1: Write the failing test**

Create `backend/tests/test_pdf_blocks.py`:

```python
"""Tests for position-aware PDF block extraction."""
import pytest
from backend.parsers.pdf_blocks import PDFBlockExtractor, TextBlock


def test_block_extractor_returns_blocks_with_coordinates():
    """Blocks should have position and font metadata."""
    # This will fail until we create the module
    extractor = PDFBlockExtractor()
    assert hasattr(extractor, 'extract_blocks')


def test_classify_header_zone():
    """Text in top 10% should be classified as header."""
    extractor = PDFBlockExtractor(header_zone_percent=0.10)
    block = TextBlock(
        text="Chapter Title",
        x0=100, y0=50, x1=400, y1=70,  # Near top
        page_height=800,
        font_size=14
    )
    assert extractor.classify_zone(block) == "header"


def test_classify_footer_zone():
    """Text in bottom 10% should be classified as footer."""
    extractor = PDFBlockExtractor(footer_zone_percent=0.10)
    block = TextBlock(
        text="Page 42",
        x0=350, y0=750, x1=400, y1=770,  # Near bottom
        page_height=800,
        font_size=10
    )
    assert extractor.classify_zone(block) == "footer"


def test_classify_body_zone():
    """Text in middle should be classified as body."""
    extractor = PDFBlockExtractor()
    block = TextBlock(
        text="Regular paragraph text here.",
        x0=100, y0=400, x1=500, y1=420,  # Middle
        page_height=800,
        font_size=12
    )
    assert extractor.classify_zone(block) == "body"
```

**Step 2: Run test to verify it fails**

```bash
cd /Volumes/Containers/ReadMeLocal
pytest backend/tests/test_pdf_blocks.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'backend.parsers.pdf_blocks'`

**Step 3: Write minimal implementation**

Create `backend/parsers/pdf_blocks.py`:

```python
"""Position-aware PDF text block extraction using PyMuPDF."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"


def _load_pdf_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f) or {}
        return settings.get("pdf_filtering", {})
    except FileNotFoundError:
        return {}


@dataclass
class TextBlock:
    """A text block with position and font metadata."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_height: float
    font_size: float
    page_num: int = 0


ZoneType = Literal["header", "body", "footer"]


class PDFBlockExtractor:
    """Extract and classify text blocks from PDFs by position."""

    def __init__(
        self,
        header_zone_percent: float = 0.10,
        footer_zone_percent: float = 0.10,
        min_body_font_size: float = 9.0,
    ):
        cfg = _load_pdf_config()
        self.header_zone_percent = cfg.get("header_zone_percent", header_zone_percent)
        self.footer_zone_percent = cfg.get("footer_zone_percent", footer_zone_percent)
        self.min_body_font_size = cfg.get("min_body_font_size", min_body_font_size)

    def classify_zone(self, block: TextBlock) -> ZoneType:
        """Classify a block as header, body, or footer based on Y position."""
        relative_y = block.y0 / block.page_height

        if relative_y < self.header_zone_percent:
            return "header"
        elif relative_y > (1 - self.footer_zone_percent):
            return "footer"
        return "body"

    def extract_blocks(self, file_path: str) -> List[TextBlock]:
        """Extract text blocks with coordinates from a PDF file."""
        import fitz  # PyMuPDF

        blocks: List[TextBlock] = []
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_height = page.rect.height

            # Get text blocks with position info
            block_list = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

            for b in block_list:
                if b.get("type") != 0:  # Skip non-text blocks (images)
                    continue

                # Extract text and font info from spans
                text_parts = []
                font_sizes = []

                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        text_parts.append(span.get("text", ""))
                        font_sizes.append(span.get("size", 12))

                text = " ".join(text_parts).strip()
                if not text:
                    continue

                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12

                blocks.append(TextBlock(
                    text=text,
                    x0=b["bbox"][0],
                    y0=b["bbox"][1],
                    x1=b["bbox"][2],
                    y1=b["bbox"][3],
                    page_height=page_height,
                    font_size=avg_font_size,
                    page_num=page_num,
                ))

        doc.close()
        return blocks
```

**Step 4: Run test to verify it passes**

```bash
pytest backend/tests/test_pdf_blocks.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/parsers/pdf_blocks.py backend/tests/test_pdf_blocks.py
git commit -m "feat: add position-aware PDF block extraction"
```

---

### Task 1.3: Add Repeated Header Detection

**Files:**
- Modify: `backend/parsers/pdf_blocks.py`
- Test: `backend/tests/test_pdf_blocks.py`

**Step 1: Add failing test**

Add to `backend/tests/test_pdf_blocks.py`:

```python
def test_detect_repeated_headers():
    """Text appearing at same Y position across multiple pages = header."""
    extractor = PDFBlockExtractor()
    blocks = [
        TextBlock(text="Book Title", x0=100, y0=50, x1=300, y1=70, page_height=800, font_size=12, page_num=0),
        TextBlock(text="Book Title", x0=100, y0=50, x1=300, y1=70, page_height=800, font_size=12, page_num=1),
        TextBlock(text="Book Title", x0=100, y0=50, x1=300, y1=70, page_height=800, font_size=12, page_num=2),
        TextBlock(text="Unique content", x0=100, y0=200, x1=500, y1=220, page_height=800, font_size=12, page_num=0),
    ]
    repeated = extractor.find_repeated_headers(blocks, threshold=3)
    assert "book title" in repeated  # Normalized lowercase
    assert "unique content" not in repeated
```

**Step 2: Run test to verify it fails**

```bash
pytest backend/tests/test_pdf_blocks.py::test_detect_repeated_headers -v
```

Expected: FAIL with `AttributeError: 'PDFBlockExtractor' object has no attribute 'find_repeated_headers'`

**Step 3: Add implementation**

Add to `PDFBlockExtractor` class in `backend/parsers/pdf_blocks.py`:

```python
    def find_repeated_headers(self, blocks: List[TextBlock], threshold: int = 3) -> set:
        """Find text that appears repeatedly at similar Y positions (likely headers/footers)."""
        from collections import defaultdict
        import re

        # Group by normalized text
        text_positions: defaultdict = defaultdict(list)
        for block in blocks:
            normalized = re.sub(r"\s+", " ", block.text.strip().lower())
            if len(normalized) > 80:  # Skip long content
                continue
            text_positions[normalized].append((block.y0, block.page_num))

        # Find text appearing on multiple pages at similar positions
        repeated = set()
        for text, positions in text_positions.items():
            unique_pages = len(set(p[1] for p in positions))
            if unique_pages >= threshold:
                repeated.add(text)

        return repeated
```

**Step 4: Run test to verify it passes**

```bash
pytest backend/tests/test_pdf_blocks.py::test_detect_repeated_headers -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/parsers/pdf_blocks.py backend/tests/test_pdf_blocks.py
git commit -m "feat: add repeated header detection for PDFs"
```

---

### Task 1.4: Integrate Block Extractor into PDF Parser

**Files:**
- Modify: `backend/parsers/pdf_parser.py`
- Test: `backend/tests/test_pdf_parser.py`

**Step 1: Add failing test**

Create or update `backend/tests/test_pdf_parser.py`:

```python
"""Tests for PDF parser with position-aware filtering."""
import pytest
from unittest.mock import MagicMock, patch
from backend.parsers.pdf_parser import PDFParser


def test_parser_uses_position_filtering():
    """Parser should filter out header/footer zones."""
    parser = PDFParser()
    # Verify the parser has position-aware capability
    assert hasattr(parser, 'use_position_filtering')
    assert parser.use_position_filtering is True
```

**Step 2: Run test to verify it fails**

```bash
pytest backend/tests/test_pdf_parser.py::test_parser_uses_position_filtering -v
```

Expected: FAIL with `AttributeError: 'PDFParser' object has no attribute 'use_position_filtering'`

**Step 3: Update PDF parser**

Replace `backend/parsers/pdf_parser.py`:

```python
"""
PDF Document Parser for ReadMe
Position-aware text extraction with header/footer filtering
"""
from typing import List, Optional

import fitz  # PyMuPDF

from backend.content_filter import ContentFilter
from backend.parsers.pdf_blocks import PDFBlockExtractor, TextBlock


class PDFParser:
    """PDF document parser with position-aware filtering."""

    def __init__(self, use_position_filtering: bool = True):
        self.content_filter = ContentFilter()
        self.block_extractor = PDFBlockExtractor()
        self.use_position_filtering = use_position_filtering

    def parse_file(self, file_path: str) -> dict:
        """Parse a PDF file and return structured content."""
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()

            if self.use_position_filtering:
                text_content = self._extract_with_position_filtering(file_path)
            else:
                text_content = self._extract_simple(file_path)

            # Apply additional content filtering
            filtered_text = self.content_filter.filter_text(text_content)
            sentences = self._split_sentences(filtered_text)

            return {
                "title": self._extract_title(file_path, text_content),
                "author": self._extract_author(text_content),
                "content": sentences,
                "num_sentences": len(sentences),
                "total_pages": total_pages,
            }

        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")

    def _extract_with_position_filtering(self, file_path: str) -> str:
        """Extract text using position-aware block filtering."""
        blocks = self.block_extractor.extract_blocks(file_path)

        # Find repeated headers/footers
        repeated = self.block_extractor.find_repeated_headers(blocks)

        # Filter blocks
        body_texts = []
        for block in blocks:
            zone = self.block_extractor.classify_zone(block)

            # Skip header/footer zones
            if zone in ("header", "footer"):
                continue

            # Skip repeated text (running headers)
            normalized = block.text.strip().lower()
            import re
            normalized = re.sub(r"\s+", " ", normalized)
            if normalized in repeated:
                continue

            body_texts.append(block.text)

        return "\n".join(body_texts)

    def _extract_simple(self, file_path: str) -> str:
        """Simple text extraction without position filtering."""
        doc = fitz.open(file_path)
        text_content = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content += page.get_text() + "\n"
        doc.close()
        return text_content

    def _extract_title(self, file_path: str, text_content: str) -> str:
        """Extract title from PDF metadata or first meaningful line."""
        import os
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        lines = text_content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if 10 < len(line) < 100:
                if not any(skip in line.lower() for skip in ['chapter', 'page', 'table of contents']):
                    return line

        return base_name

    def _extract_author(self, text_content: str) -> Optional[str]:
        """Try to extract author from content."""
        return None

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]
```

**Step 4: Run test to verify it passes**

```bash
pytest backend/tests/test_pdf_parser.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/parsers/pdf_parser.py backend/tests/test_pdf_parser.py
git commit -m "feat: integrate position-aware filtering into PDF parser"
```

---

## Phase 2: Annotation Data Model

### Task 2.1: Create Annotation SQLAlchemy Model

**Files:**
- Modify: `backend/main.py` (add model after PlaybackState class ~line 157)

**Step 1: Add the model**

Add after `PlaybackState` class in `backend/main.py`:

```python
class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    paragraph_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

**Step 2: Verify table creation**

The `Base.metadata.create_all(engine)` call will create the table automatically.

**Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: add Annotation SQLAlchemy model"
```

---

### Task 2.2: Add Annotation Pydantic Schemas

**Files:**
- Modify: `backend/main.py` (add after existing schemas ~line 250)

**Step 1: Add schemas**

Add after `SentenceSyncRequest` class:

```python
# Annotation schemas
class AnnotationCreate(BaseModel):
    book_id: str
    paragraph_index: int
    section_title: Optional[str] = None
    source_text: str
    note_text: str


class AnnotationResponse(BaseModel):
    id: int
    book_id: str
    paragraph_index: int
    section_title: Optional[str]
    source_text: str
    note_text: str
    created_at: datetime
    updated_at: datetime


class AnnotationListResponse(BaseModel):
    annotations: List[AnnotationResponse]
    total: int
```

**Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: add Annotation Pydantic schemas"
```

---

### Task 2.3: Add Annotation CRUD Endpoints

**Files:**
- Modify: `backend/main.py`
- Test: `backend/tests/test_annotations.py`

**Step 1: Write failing tests**

Create `backend/tests/test_annotations.py`:

```python
"""Tests for annotation API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_create_annotation():
    """POST /api/annotations should create an annotation."""
    response = client.post("/api/annotations", json={
        "book_id": "test-book-123",
        "paragraph_index": 5,
        "section_title": "Chapter 1",
        "source_text": "This is the source paragraph.",
        "note_text": "My note about this."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["book_id"] == "test-book-123"
    assert data["note_text"] == "My note about this."
    assert "id" in data


def test_list_annotations():
    """GET /api/annotations/{book_id} should list annotations for a book."""
    # First create one
    client.post("/api/annotations", json={
        "book_id": "list-test-book",
        "paragraph_index": 1,
        "source_text": "Source text.",
        "note_text": "Note text."
    })

    response = client.get("/api/annotations/list-test-book")
    assert response.status_code == 200
    data = response.json()
    assert "annotations" in data
    assert data["total"] >= 1


def test_delete_annotation():
    """DELETE /api/annotations/{id} should delete an annotation."""
    # Create one first
    create_resp = client.post("/api/annotations", json={
        "book_id": "delete-test-book",
        "paragraph_index": 1,
        "source_text": "Source.",
        "note_text": "Note."
    })
    annotation_id = create_resp.json()["id"]

    # Delete it
    delete_resp = client.delete(f"/api/annotations/{annotation_id}")
    assert delete_resp.status_code == 200

    # Verify it's gone
    list_resp = client.get("/api/annotations/delete-test-book")
    ids = [a["id"] for a in list_resp.json()["annotations"]]
    assert annotation_id not in ids
```

**Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_annotations.py -v
```

Expected: FAIL with 404 (endpoints don't exist)

**Step 3: Add endpoints**

Add to `backend/main.py` before the `if __name__ == "__main__":` block:

```python
# ------------------------------------------------------------
# Annotation endpoints
# ------------------------------------------------------------

@app.post("/api/annotations", response_model=AnnotationResponse)
async def create_annotation(req: AnnotationCreate, db: Session = Depends(get_db)):
    """Create a new annotation for a paragraph."""
    now = datetime.now(timezone.utc)
    annotation = Annotation(
        book_id=req.book_id,
        paragraph_index=req.paragraph_index,
        section_title=req.section_title,
        source_text=req.source_text,
        note_text=req.note_text,
        created_at=now,
        updated_at=now,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation


@app.get("/api/annotations/{book_id}", response_model=AnnotationListResponse)
async def list_annotations(book_id: str, db: Session = Depends(get_db)):
    """List all annotations for a book."""
    from sqlalchemy import select
    stmt = select(Annotation).where(Annotation.book_id == book_id).order_by(Annotation.paragraph_index)
    annotations = db.execute(stmt).scalars().all()
    return {"annotations": annotations, "total": len(annotations)}


@app.delete("/api/annotations/{annotation_id}")
async def delete_annotation(annotation_id: int, db: Session = Depends(get_db)):
    """Delete an annotation by ID."""
    annotation = db.get(Annotation, annotation_id)
    if annotation is None:
        raise HTTPException(status_code=404, detail="Annotation not found")
    db.delete(annotation)
    db.commit()
    return {"status": "deleted", "id": annotation_id}
```

**Step 4: Run tests to verify they pass**

```bash
pytest backend/tests/test_annotations.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_annotations.py
git commit -m "feat: add annotation CRUD endpoints"
```

---

### Task 2.4: Add Annotation Export Endpoint

**Files:**
- Modify: `backend/main.py`
- Test: `backend/tests/test_annotations.py`

**Step 1: Add failing test**

Add to `backend/tests/test_annotations.py`:

```python
def test_export_annotations():
    """GET /api/annotations/{book_id}/export should return TXT file."""
    # Create annotations
    client.post("/api/annotations", json={
        "book_id": "export-test-book",
        "paragraph_index": 1,
        "section_title": "Chapter 1",
        "source_text": "First paragraph source.",
        "note_text": "First note."
    })
    client.post("/api/annotations", json={
        "book_id": "export-test-book",
        "paragraph_index": 3,
        "section_title": "Chapter 1",
        "source_text": "Third paragraph source.",
        "note_text": "Second note."
    })

    response = client.get("/api/annotations/export-test-book/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    content = response.text
    assert "First note." in content
    assert "Second note." in content
    assert "SOURCE:" in content
    assert "NOTE:" in content
```

**Step 2: Run test to verify it fails**

```bash
pytest backend/tests/test_annotations.py::test_export_annotations -v
```

Expected: FAIL with 404

**Step 3: Add export endpoint**

Add to `backend/main.py`:

```python
from starlette.responses import PlainTextResponse


@app.get("/api/annotations/{book_id}/export")
async def export_annotations(book_id: str, db: Session = Depends(get_db)):
    """Export annotations as TXT file."""
    from sqlalchemy import select
    stmt = select(Annotation).where(Annotation.book_id == book_id).order_by(Annotation.paragraph_index)
    annotations = db.execute(stmt).scalars().all()

    if not annotations:
        raise HTTPException(status_code=404, detail="No annotations found for this book")

    # Build TXT content
    lines = [
        "=" * 40,
        f"ANNOTATIONS: {book_id}",
        f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"Total notes: {len(annotations)}",
        "=" * 40,
        "",
    ]

    for ann in annotations:
        section = ann.section_title or f"Paragraph {ann.paragraph_index}"
        lines.extend([
            f"--- {section}, Paragraph {ann.paragraph_index} ---",
            "SOURCE:",
            f'"{ann.source_text}"',
            "",
            "NOTE:",
            ann.note_text,
            "",
            "-" * 40,
            "",
        ])

    content = "\n".join(lines)
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")
```

**Step 4: Run test to verify it passes**

```bash
pytest backend/tests/test_annotations.py::test_export_annotations -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/main.py backend/tests/test_annotations.py
git commit -m "feat: add annotation TXT export endpoint"
```

---

## Phase 3: Frontend Annotation UI

### Task 3.1: Add Annotation State and Modal

**Files:**
- Modify: `frontend/src/App.js`
- Modify: `frontend/src/App.css`

**Step 1: Add state variables**

Add after `const [currentParagraphAudio, setCurrentParagraphAudio] = useState(null);` (~line 23):

```javascript
  // Annotation state
  const [showAnnotationModal, setShowAnnotationModal] = useState(false);
  const [annotationText, setAnnotationText] = useState("");
  const [annotations, setAnnotations] = useState([]);
  const [pauseTime, setPauseTime] = useState(null);
  const [pausedParagraphIndex, setPausedParagraphIndex] = useState(null);
```

**Step 2: Add rewind threshold constant**

Add near the top of the component:

```javascript
const REWIND_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes
```

**Step 3: Commit**

```bash
git add frontend/src/App.js
git commit -m "feat: add annotation state variables"
```

---

### Task 3.2: Add Keyboard Handler for Annotations

**Files:**
- Modify: `frontend/src/App.js`

**Step 1: Add keyboard effect**

Add after the existing useEffect hooks:

```javascript
  // Keyboard handler for annotations
  useEffect(() => {
    const handleKeyDown = (e) => {
      // 'N' to open annotation modal (when playing or paused with a book loaded)
      if (e.key === "n" || e.key === "N") {
        if (book && !showAnnotationModal) {
          e.preventDefault();
          setPauseTime(Date.now());
          setPausedParagraphIndex(currentParagraphIndex);
          setPlaying(false);
          setShowAnnotationModal(true);
        }
      }

      // Escape to close modal
      if (e.key === "Escape" && showAnnotationModal) {
        e.preventDefault();
        handleCloseAnnotationModal();
      }

      // Cmd/Ctrl + Enter to save annotation
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && showAnnotationModal) {
        e.preventDefault();
        handleSaveAnnotation();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [book, showAnnotationModal, currentParagraphIndex, playing]);
```

**Step 2: Commit**

```bash
git add frontend/src/App.js
git commit -m "feat: add keyboard handlers for annotations"
```

---

### Task 3.3: Add Annotation Save/Close Handlers

**Files:**
- Modify: `frontend/src/App.js`

**Step 1: Add handler functions**

Add after the keyboard effect:

```javascript
  // Load annotations when book changes
  useEffect(() => {
    if (book?.id) {
      fetch(`${API_BASE}/api/annotations/${book.id}`)
        .then((res) => res.json())
        .then((data) => setAnnotations(data.annotations || []))
        .catch(() => setAnnotations([]));
    }
  }, [book?.id]);

  const handleCloseAnnotationModal = () => {
    setShowAnnotationModal(false);
    setAnnotationText("");

    // Check if we need to rewind (paused > 5 minutes)
    if (pauseTime && Date.now() - pauseTime >= REWIND_THRESHOLD_MS) {
      // Rewind to start of the paused paragraph
      const paragraphStartIndex = tokens.findIndex(
        (t) => t.paragraphIndex === pausedParagraphIndex
      );
      if (paragraphStartIndex >= 0) {
        setIndex(paragraphStartIndex);
      }
    }

    setPauseTime(null);
    setPausedParagraphIndex(null);
  };

  const handleSaveAnnotation = async () => {
    if (!annotationText.trim() || !book) return;

    const currentParagraph = paragraphs[currentParagraphIndex] || "";

    try {
      const response = await fetch(`${API_BASE}/api/annotations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          book_id: book.id,
          paragraph_index: currentParagraphIndex,
          section_title: null, // Could detect chapter if available
          source_text: currentParagraph,
          note_text: annotationText.trim(),
        }),
      });

      if (response.ok) {
        const newAnnotation = await response.json();
        setAnnotations((prev) => [...prev, newAnnotation]);
      }
    } catch (err) {
      console.error("Failed to save annotation:", err);
    }

    handleCloseAnnotationModal();
  };

  const handleExportAnnotations = () => {
    if (!book?.id) return;
    window.open(`${API_BASE}/api/annotations/${book.id}/export`, "_blank");
  };
```

**Step 2: Commit**

```bash
git add frontend/src/App.js
git commit -m "feat: add annotation save/close handlers with rewind logic"
```

---

### Task 3.4: Add Annotation Modal JSX

**Files:**
- Modify: `frontend/src/App.js`

**Step 1: Add modal JSX**

Add before the closing `</div>` of the main return, after the existing content:

```jsx
      {/* Annotation Modal */}
      {showAnnotationModal && (
        <div className="annotation-modal-overlay">
          <div className="annotation-modal">
            <h3>Add Note</h3>
            <div className="annotation-context">
              <strong>Current paragraph:</strong>
              <p className="annotation-source">
                {paragraphs[currentParagraphIndex]?.substring(0, 200)}
                {paragraphs[currentParagraphIndex]?.length > 200 ? "..." : ""}
              </p>
            </div>
            <textarea
              className="annotation-input"
              placeholder="Type your note here..."
              value={annotationText}
              onChange={(e) => setAnnotationText(e.target.value)}
              autoFocus
            />
            <div className="annotation-buttons">
              <button onClick={handleCloseAnnotationModal}>Cancel (Esc)</button>
              <button onClick={handleSaveAnnotation} className="primary">
                Save (⌘+Enter)
              </button>
            </div>
          </div>
        </div>
      )}
```

**Step 2: Add Export button to controls**

Add after the Play/Pause button in the controls section:

```jsx
              {annotations.length > 0 && (
                <button onClick={handleExportAnnotations} className="export-btn">
                  Export Notes ({annotations.length})
                </button>
              )}
```

**Step 3: Commit**

```bash
git add frontend/src/App.js
git commit -m "feat: add annotation modal and export button JSX"
```

---

### Task 3.5: Add Annotation Modal CSS

**Files:**
- Modify: `frontend/src/App.css`

**Step 1: Add modal styles**

Add to end of `frontend/src/App.css`:

```css
/* Annotation Modal */
.annotation-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.annotation-modal {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.annotation-modal h3 {
  margin: 0 0 16px 0;
  color: #eee;
}

.annotation-context {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.annotation-context strong {
  color: #888;
  font-size: 12px;
  text-transform: uppercase;
}

.annotation-source {
  color: #ccc;
  font-size: 14px;
  line-height: 1.5;
  margin: 8px 0 0 0;
  font-style: italic;
}

.annotation-input {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #333;
  border-radius: 8px;
  background: #0f0f1a;
  color: #eee;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.annotation-input:focus {
  outline: none;
  border-color: #4a90d9;
}

.annotation-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.annotation-buttons button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.annotation-buttons button:not(.primary) {
  background: #333;
  color: #ccc;
}

.annotation-buttons button.primary {
  background: #4a90d9;
  color: white;
}

.export-btn {
  background: #2a5a3a;
  color: #9f9;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.export-btn:hover {
  background: #3a7a4a;
}
```

**Step 2: Commit**

```bash
git add frontend/src/App.css
git commit -m "feat: add annotation modal styles"
```

---

### Task 3.6: Add Annotation Config to Settings

**Files:**
- Modify: `config/settings.yaml`

**Step 1: Add config**

Add to `config/settings.yaml`:

```yaml
# Annotation settings
annotations:
  rewind_threshold_minutes: 5
```

**Step 2: Commit**

```bash
git add config/settings.yaml
git commit -m "config: add annotation rewind threshold setting"
```

---

## Phase 4: Final Integration

### Task 4.1: Update Container and Test

**Step 1: Rebuild container**

```bash
colima start
DOCKER_HOST=unix://$HOME/.colima/docker.sock docker build -t readmelocal:latest .
```

**Step 2: Restart container**

```bash
DOCKER_HOST=unix://$HOME/.colima/docker.sock docker rm -f readmelocal
DOCKER_HOST=unix://$HOME/.colima/docker.sock docker run -d --name readmelocal -p 5000:5000 \
  -v /Volumes/Containers/ReadMeLocal/db:/app/db \
  -v /Volumes/Containers/ReadMeLocal/cache:/app/cache \
  -v /Volumes/Containers/ReadMeLocal/config:/app/config:ro \
  -v "$HOME/ReadMeBooks:/library:ro" \
  readmelocal:latest
```

**Step 3: Manual test**

1. Open http://localhost:5000
2. Select a PDF book
3. Start RSVP playback
4. Press 'N' to open annotation modal
5. Add a note and save
6. Click "Export Notes" to download TXT

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete PDF filtering and annotation system

- Position-aware PDF text extraction
- Header/footer/page number filtering by coordinates
- Paragraph-level annotations with SQLite storage
- Pause-and-note workflow with keyboard shortcuts
- 5-minute rewind threshold for context recovery
- TXT export with source text + notes"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1.1-1.4 | Position-aware PDF filtering |
| 2 | 2.1-2.4 | Annotation backend (model + endpoints + export) |
| 3 | 3.1-3.6 | Annotation frontend (modal + keyboard + CSS) |
| 4 | 4.1 | Integration and testing |

**Total tasks:** 14
**Estimated time:** 2-3 hours
