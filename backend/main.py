"""
ReadMe Backend - FastAPI Local Server
Main entry point for the local API server
Phase 2: Core Backend — single-book DB + basic endpoints
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import sys
import threading
import wave
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import uvicorn
import yaml
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from starlette.responses import FileResponse

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        SETTINGS = yaml.safe_load(f) or {}
except FileNotFoundError:
    SETTINGS = {}

from backend.content_filter import ContentFilter
from backend.library import scan_library
from backend.rsvp_tokens import split_paragraphs, tokenize_paragraphs

# Feature flags and TTS defaults
FEATURE_FLAGS: Dict[str, bool] = (SETTINGS.get("features") or {}) if isinstance(SETTINGS.get("features"), dict) else {}
LOCAL_TTS_CFG: Dict[str, Optional[str]] = (SETTINGS.get("local_tts") or {}) if isinstance(SETTINGS.get("local_tts"), dict) else {}
LOCAL_TTS_ENABLED = bool(LOCAL_TTS_CFG.get("enabled", FEATURE_FLAGS.get("local_tts", False)))
LOCAL_TTS_DEFAULT_VOICE = LOCAL_TTS_CFG.get("default_voice")
DEFAULT_TTS_MODE = (SETTINGS.get("tts_default", "cloud") or "cloud").lower()

# Resolve DB path relative to project root
_db_rel = SETTINGS.get("database_path", "./db/readme.db")
DB_PATH = (ROOT_DIR / _db_rel).resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Simple cache dir (for future use)
CACHE_DIR = (ROOT_DIR / SETTINGS.get("cache_dir", "./cache")).resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = (CACHE_DIR / "audio").resolve()
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}

# Playback configuration (Phase 6)
_playback_cfg = SETTINGS.get("playback", {}) or {}
START_SPEED = float(_playback_cfg.get("start_speed", 1.5))
SPEED_INCREMENT = float(_playback_cfg.get("speed_increment", 0.1))
INCREMENT_INTERVAL_MIN = int(_playback_cfg.get("increment_interval_minutes", 15))
MAX_SPEED = float(_playback_cfg.get("max_speed", 2.5))
_rsvp_cfg = SETTINGS.get("rsvp", {}) or {}
RSVP_DEFAULT_WPM = int(_rsvp_cfg.get("wpm_default", 150))
RSVP_MAX_WPM = int(_rsvp_cfg.get("wpm_max", 1024))

_session_cfg = SETTINGS.get("session", {}) or {}
SINGLE_BOOK_MODE = bool(_session_cfg.get("single_book_mode", True))
AUTO_FINISH_THRESHOLD = float(_session_cfg.get("auto_finish_threshold", 0.95))

PARSER_REGISTRY = {
    ".pdf": ("backend.parsers.pdf_parser", "PDFParser", "pdf"),
    ".epub": ("backend.parsers.epub_parser", "EPUBParser", "epub"),
    ".docx": ("backend.parsers.docx_parser", "DOCXParser", "docx"),
}
_LOCAL_TTS_SERVICE = None
_LOCAL_TTS_LOCK = threading.Lock()


def _get_library_path() -> Optional[Path]:
    path_value = os.getenv("README_LIBRARY_PATH") or SETTINGS.get("library_path") or ""
    if not path_value:
        return None
    return Path(path_value).expanduser()


def _set_library_path_in_config(new_path: str) -> None:
    config_text = ""
    if CONFIG_PATH.exists():
        config_text = CONFIG_PATH.read_text(encoding="utf-8")

    if "library_path:" in config_text:
        updated_lines = []
        for line in config_text.splitlines():
            if line.strip().startswith("library_path:"):
                updated_lines.append(f'library_path: "{new_path}"')
            else:
                updated_lines.append(line)
        config_text = "\n".join(updated_lines) + "\n"
    elif "# Library Settings" in config_text:
        prefix, suffix = config_text.split("# Library Settings", 1)
        config_text = f"{prefix}# Library Settings\nlibrary_path: \"{new_path}\"\n{suffix.lstrip()}"
    else:
        spacer = "\n" if config_text and not config_text.endswith("\n") else ""
        config_text = f"{config_text}{spacer}library_path: \"{new_path}\"\n"

    CONFIG_PATH.write_text(config_text, encoding="utf-8")

# ------------------------------------------------------------
# Database setup
# ------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class CurrentBook(Base):
    __tablename__ = "current_book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filepath: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    filetype: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    content_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # list[str] JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PlaybackState(Base):
    __tablename__ = "playback_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    position_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    speed: Mapped[float] = mapped_column(Float, default=START_SPEED)
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Phase 7: Text-audio sync
    current_sentence_index: Mapped[int] = mapped_column(Integer, default=0)
    sentence_durations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # list[float] JSON


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Create tables if not exist
Base.metadata.create_all(engine)

# Ensure singleton rows exist
with SessionLocal() as _s:
    if _s.get(PlaybackState, 1) is None:
        _s.add(PlaybackState(id=1, speed=START_SPEED))
        _s.commit()

# ------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------
app = FastAPI(
    title="ReadMe Local API",
    description="Local API server for document parsing, TTS, and playback",
    version="0.3.0",
)

# Configure CORS for localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------
class BookImportResult(BaseModel):
    id: int
    title: Optional[str]
    author: Optional[str]
    filepath: Optional[str]
    filetype: Optional[str]
    num_sentences: int


class CurrentBookResponse(BaseModel):
    id: int
    title: Optional[str]
    author: Optional[str]
    filepath: Optional[str]
    filetype: Optional[str]
    content: List[str]


class PlaybackSpeedResponse(BaseModel):
    speed: float


class PlaybackUpdateRequest(BaseModel):
    position_seconds: Optional[float] = None
    speed: Optional[float] = None


class PlaybackUpdateResponse(BaseModel):
    position_seconds: float
    speed: float
    last_updated: datetime


class LibraryPathUpdate(BaseModel):
    path: str


# Phase 7: Text-audio sync models
class CurrentSentenceResponse(BaseModel):
    sentence_index: int
    sentence_text: str
    position_seconds: float


class SentenceSyncRequest(BaseModel):
    position_seconds: float


# Phase 5: TTS models
class TtsRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    mode: Optional[str] = None  # "cloud" or "local" (local not implemented)
    model: Optional[str] = None


class TtsResponse(BaseModel):
    job_id: str
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    audio_path: Optional[str] = None  # local server streaming path
    download_path: Optional[str] = None  # direct download endpoint


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?。！？])\s+")


def _infer_title_from_path(path: str) -> str:
    try:
        return Path(path).stem
    except Exception:
        return "Untitled"


def _split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_REGEX.split(text)
    # Fallback if regex did not split
    if len(parts) <= 1:
        parts = [p.strip() for p in text.splitlines() if p.strip()]
    return [p.strip() for p in parts if p and p.strip()]


def _load_parser(suffix: str):
    module_path, class_name, _ = PARSER_REGISTRY.get(suffix, (None, None, None))
    if not module_path:
        raise HTTPException(status_code=500, detail=f"No parser registered for {suffix}")
    try:
        parser_module = import_module(module_path)
        parser_cls = getattr(parser_module, class_name)
        return parser_cls()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load parser: {exc}") from exc


def _read_uploaded_file(upload: UploadFile) -> tuple[str, str]:
    """Return (text, filetype) from uploaded file. Supports .txt, .md, .pdf, .epub, .docx."""
    filename = upload.filename or "uploaded"
    suffix = Path(filename).suffix.lower()
    supported_types = {".txt", ".md", ".pdf", ".epub", ".docx"}

    if suffix not in supported_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {suffix}. Supported types: {', '.join(supported_types)}"
        )

    # For text-based files, read content directly
    if suffix in {".txt", ".md"}:
        raw = upload.file.read()
        try:
            text = raw.decode("utf-8")
        except Exception:
            text = raw.decode("utf-8", errors="ignore")
        return text, suffix.lstrip(".")

    # For binary files (PDF, EPUB, DOCX), save to temp file and parse
    else:
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(upload.file.read())
            temp_path = Path(temp_file.name)

        _, _, normalized_type = PARSER_REGISTRY.get(suffix, (None, None, None))
        try:
            parser = _load_parser(suffix)
            result = parser.parse_file(str(temp_path))
            return result, normalized_type
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to parse file: {exc}") from exc
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass


def _calculate_sentence_durations(sentences: List[str], speed: float) -> List[float]:
    """
    Phase 7: Calculate estimated duration for each sentence based on word count and speed.
    Assumes ~150 words per minute reading speed, adjusted for playback speed.
    """
    durations = []
    words_per_minute = 150.0  # Average reading speed
    for sentence in sentences:
        word_count = len(sentence.split())
        # Duration in seconds: (words / words_per_minute) * 60 / speed
        duration = (word_count / words_per_minute) * 60.0 / speed if word_count > 0 else 1.0
        durations.append(max(duration, 0.5))  # Minimum 0.5 seconds per sentence
    return durations


def _get_sentence_at_position(sentences: List[str], durations: List[float], position_seconds: float) -> int:
    """
    Phase 7: Find which sentence should be highlighted at the given audio position.
    """
    cumulative_time = 0.0
    for i, duration in enumerate(durations):
        if position_seconds < cumulative_time + duration:
            return i
        cumulative_time += duration
    return len(sentences) - 1  # Last sentence if position exceeds total duration


def _upsert_current_book(db: Session, *, title: str, filepath: Optional[str], filetype: str, sentences: List[str]) -> CurrentBook:
    now = datetime.now(timezone.utc)
    row = db.get(CurrentBook, 1)
    payload = {
        "title": title,
        "author": None,
        "filepath": filepath,
        "filetype": filetype,
        "content_json": json.dumps(sentences),
        "updated_at": now,
    }
    if row is None:
        row = CurrentBook(id=1, created_at=now, **payload)
        db.add(row)
    else:
        for k, v in payload.items():
            setattr(row, k, v)
    # Reset playback state on new book
    ps = db.get(PlaybackState, 1) or PlaybackState(id=1)
    ps.position_seconds = 0.0
    ps.speed = START_SPEED
    ps.session_start = now
    ps.last_updated = now
    # Phase 7: Calculate and store sentence durations
    durations = _calculate_sentence_durations(sentences, START_SPEED)
    ps.sentence_durations_json = json.dumps(durations)
    ps.current_sentence_index = 0
    db.add(ps)
    db.commit()
    db.refresh(row)
    return row


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "service": "ReadMe Local API", "version": "0.3.0"}


@app.get("/api/health")
async def health_check():
    # Basic checks for DB and directories
    db_ok = DB_PATH.exists()
    cache_ok = CACHE_DIR.exists()
    return {
        "status": "healthy" if (db_ok and cache_ok) else "degraded",
        "database_path": str(DB_PATH),
        "database_exists": db_ok,
        "cache_dir": str(CACHE_DIR),
        "cache_exists": cache_ok,
    }


@app.get("/api/library")
def list_library():
    library_path = _get_library_path()
    if not library_path or not library_path.exists():
        raise HTTPException(status_code=400, detail="Library path not configured")
    return scan_library(library_path)


@app.put("/api/library/path")
def update_library_path(payload: LibraryPathUpdate):
    raw_path = payload.path.strip()
    if not raw_path:
        SETTINGS["library_path"] = ""
        _set_library_path_in_config("")
        return {"library_path": ""}

    new_path = Path(raw_path).expanduser()
    if not new_path.exists():
        raise HTTPException(status_code=400, detail="Library path does not exist")

    SETTINGS["library_path"] = str(new_path)
    _set_library_path_in_config(str(new_path))
    return {"library_path": str(new_path)}


@app.get("/api/books/{book_id}")
def get_book(book_id: str):
    library_path = _get_library_path()
    if not library_path or not library_path.exists():
        raise HTTPException(status_code=400, detail="Library path not configured")

    items = scan_library(library_path)
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


@app.post("/api/book/import", response_model=BookImportResult)
async def import_book(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Parse an uploaded file and set it as the current book.

    Supports .txt, .md, .pdf, .epub, .docx files.
    """
    if SINGLE_BOOK_MODE:
        existing = db.get(CurrentBook, 1)
        if existing is not None:
            raise HTTPException(status_code=409, detail="A book is already open. Close it before importing another.")

    result, filetype = _read_uploaded_file(file)

    # Handle different parser return formats
    if isinstance(result, dict):
        # Parser returned structured data (PDF/EPUB/DOCX)
        title = result.get("title", _infer_title_from_path(file.filename or "Untitled"))
        author = result.get("author")
        sentences = result.get("content", [])
    else:
        # Legacy text-based parsing (TXT/MD)
        text = result
        # Phase 3: Apply smart content filtering before sentence splitting
        filtered = ContentFilter().filter_text(text)
        sentences = _split_sentences(filtered)
        title = _infer_title_from_path(file.filename or "Untitled")
        author = None

    row = _upsert_current_book(db, title=title, filepath=file.filename, filetype=filetype, sentences=sentences)
    # Update author if available
    if author:
        row.author = author
        db.add(row)
        db.commit()

    return {
        "id": row.id,
        "title": row.title,
        "author": row.author,
        "filepath": row.filepath,
        "filetype": row.filetype,
        "num_sentences": len(sentences),
    }


@app.get("/api/book/current", response_model=CurrentBookResponse)
async def get_current_book(db: Session = Depends(get_db)):
    row = db.get(CurrentBook, 1)
    if row is None:
        raise HTTPException(status_code=404, detail="No book is currently loaded")
    try:
        content = json.loads(row.content_json or "[]")
    except Exception:
        content = []
    return {
        "id": row.id,
        "title": row.title,
        "author": row.author,
        "filepath": row.filepath,
        "filetype": row.filetype,
        "content": content,
    }


@app.post("/api/book/close")
async def close_current_book(db: Session = Depends(get_db)):
    row = db.get(CurrentBook, 1)
    if row is not None:
        db.delete(row)
    ps = db.get(PlaybackState, 1)
    now = datetime.now(timezone.utc)
    if ps is None:
        ps = PlaybackState(id=1, position_seconds=0.0, speed=START_SPEED, session_start=now, last_updated=now)
    else:
        ps.position_seconds = 0.0
        ps.speed = START_SPEED
        ps.session_start = now
        ps.last_updated = now
    db.add(ps)
    db.commit()
    return {"status": "closed"}


def _compute_adaptive_speed(ps: PlaybackState) -> float:
    try:
        now = datetime.now(timezone.utc)
        elapsed = max(0.0, (now - (ps.session_start or now)).total_seconds() / 60.0)
        increments = int(elapsed // max(1, INCREMENT_INTERVAL_MIN))
        speed = START_SPEED + (increments * SPEED_INCREMENT)
        if speed > MAX_SPEED:
            speed = MAX_SPEED
        if speed < 0.5:
            speed = 0.5
        return float(speed)
    except Exception:
        return float(START_SPEED)


@app.get("/api/playback/speed", response_model=PlaybackSpeedResponse)
async def get_playback_speed(db: Session = Depends(get_db)):
    ps = db.get(PlaybackState, 1)
    if ps is None:
        raise HTTPException(status_code=500, detail="Playback state not initialized")
    # Phase 6: adaptive speed based on elapsed session time
    current = _compute_adaptive_speed(ps)
    # Optionally persist last computed speed for visibility
    ps.speed = current
    ps.last_updated = datetime.now(timezone.utc)
    db.add(ps)
    db.commit()
    return {"speed": current}


@app.post("/api/playback/update", response_model=PlaybackUpdateResponse)
async def update_playback(req: PlaybackUpdateRequest, db: Session = Depends(get_db)):
    ps = db.get(PlaybackState, 1)
    if ps is None:
        raise HTTPException(status_code=500, detail="Playback state not initialized")
    changed = False
    if req.position_seconds is not None:
        ps.position_seconds = max(0.0, float(req.position_seconds))
        changed = True
    if req.speed is not None:
        try:
            ps.speed = max(0.5, min(3.0, float(req.speed)))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid speed")
        changed = True
    if changed:
        ps.last_updated = datetime.now(timezone.utc)
        db.add(ps)
        db.commit()
    return {
        "position_seconds": ps.position_seconds,
        "speed": ps.speed,
        "last_updated": ps.last_updated,
    }


# ------------------------------------------------------------
# Phase 5: Cloud TTS integration and audio streaming
# ------------------------------------------------------------

async def _call_cloud_tts(text: str, voice: Optional[str] = None, model: Optional[str] = None) -> dict:
    base_url = SETTINGS.get("heroku_api_url", "https://readme-ai.herokuapp.com").rstrip("/")
    url = f"{base_url}/api/v1/tts"
    api_key = os.environ.get("HEROKU_API_KEY") or SETTINGS.get("api_key")
    if not api_key:
        raise HTTPException(status_code=503, detail="HEROKU_API_KEY is not configured")
    payload = {
        "text": text,
        "model": model or "gpt-4o-mini-tts",
        "voice": voice or "alloy",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = httpx.Timeout(20.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=f"Cloud TTS error: {resp.text}")
        data = resp.json()
        # Try to fetch audio bytes
        audio_url = data.get("audio_url")
        job_id = data.get("job_id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        if not audio_url:
            raise HTTPException(status_code=502, detail="Cloud TTS returned no audio_url")
        audio_path = AUDIO_DIR / f"{job_id}.mp3"
        aget = await client.get(audio_url)
        if aget.status_code >= 400:
            raise HTTPException(status_code=aget.status_code, detail="Failed to download audio")
        with open(audio_path, "wb") as f:
            f.write(aget.content)
        return {
            "job_id": job_id,
            "duration": data.get("duration"),
            "sample_rate": data.get("sample_rate"),
            "audio_path": str(audio_path),
        }


@app.post("/api/tts", response_model=TtsResponse)
async def generate_tts(req: TtsRequest):
    voice_cfg = _get_voice_entry(req.voice)
    mode = _determine_tts_mode(req.mode, voice_cfg)
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    # Limit text length to a reasonable size for TTS
    if len(text) > 8000:
        text = text[:8000]
    if mode == "cloud":
        data = await _call_cloud_tts(text, voice=req.voice, model=req.model)
    elif mode == "local":
        data = await _call_local_tts(text, voice_cfg=voice_cfg)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported TTS mode: {mode}")

    return TtsResponse(
        job_id=data["job_id"],
        duration=data.get("duration"),
        sample_rate=data.get("sample_rate"),
        audio_path=f"/api/audio/{data['job_id']}/stream",
        download_path=f"/api/audio/{data['job_id']}/download",
    )


@app.get("/api/audio/{job_id}/stream")
async def stream_audio(job_id: str):
    path, mime = _locate_audio_file(job_id)
    return FileResponse(str(path), media_type=mime, filename=path.name)


@app.get("/api/audio/{job_id}/download")
async def download_audio(job_id: str):
    path, mime = _locate_audio_file(job_id)
    return FileResponse(str(path), media_type=mime, filename=path.name)


# ------------------------------------------------------------
# Phase 7: Text-audio synchronization
# ------------------------------------------------------------

@app.get("/api/playback/current-sentence", response_model=CurrentSentenceResponse)
async def get_current_sentence(db: Session = Depends(get_db)):
    """Get the currently highlighted sentence based on playback position."""
    ps = db.get(PlaybackState, 1)
    if ps is None:
        raise HTTPException(status_code=500, detail="Playback state not initialized")

    book = db.get(CurrentBook, 1)
    if book is None:
        raise HTTPException(status_code=404, detail="No book is currently loaded")

    try:
        sentences = json.loads(book.content_json or "[]")
        durations = json.loads(ps.sentence_durations_json or "[]")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse book content")

    if not sentences or not durations:
        raise HTTPException(status_code=404, detail="Book content not available")

    # Find current sentence based on position
    sentence_index = _get_sentence_at_position(sentences, durations, ps.position_seconds)
    sentence_text = sentences[sentence_index] if sentence_index < len(sentences) else ""

    # Update the stored current sentence index
    ps.current_sentence_index = sentence_index
    ps.last_updated = datetime.now(timezone.utc)
    db.add(ps)
    db.commit()

    return {
        "sentence_index": sentence_index,
        "sentence_text": sentence_text,
        "position_seconds": ps.position_seconds,
    }


@app.post("/api/playback/sync-sentence")
async def sync_sentence_position(req: SentenceSyncRequest, db: Session = Depends(get_db)):
    """Update playback position based on sentence index (for seeking)."""
    ps = db.get(PlaybackState, 1)
    if ps is None:
        raise HTTPException(status_code=500, detail="Playback state not initialized")

    book = db.get(CurrentBook, 1)
    if book is None:
        raise HTTPException(status_code=404, detail="No book is currently loaded")

    try:
        sentences = json.loads(book.content_json or "[]")
        durations = json.loads(ps.sentence_durations_json or "[]")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse book content")

    if not sentences or not durations:
        raise HTTPException(status_code=404, detail="Book content not available")

    # Validate the requested position
    position_seconds = max(0.0, float(req.position_seconds))

    # Find which sentence this position corresponds to
    sentence_index = _get_sentence_at_position(sentences, durations, position_seconds)

    # Update playback state
    ps.position_seconds = position_seconds
    ps.current_sentence_index = sentence_index
    ps.last_updated = datetime.now(timezone.utc)
    db.add(ps)
    db.commit()

    return {
        "position_seconds": position_seconds,
        "sentence_index": sentence_index,
        "status": "updated"
    }


def _get_voice_entry(voice_name: Optional[str]) -> Optional[dict]:
    if not voice_name:
        return None
    voices = SETTINGS.get("voices") or []
    for voice in voices:
        if isinstance(voice, dict) and voice.get("name") == voice_name:
            return voice
    return None


def _determine_tts_mode(requested_mode: Optional[str], voice_cfg: Optional[dict]) -> str:
    if requested_mode:
        return (requested_mode or DEFAULT_TTS_MODE).lower()
    if voice_cfg and voice_cfg.get("type") == "local":
        return "local"
    return DEFAULT_TTS_MODE


def _get_local_tts_service():
    if not LOCAL_TTS_ENABLED:
        raise HTTPException(status_code=503, detail="Local TTS is disabled in configuration.")

    global _LOCAL_TTS_SERVICE
    if _LOCAL_TTS_SERVICE is not None:
        return _LOCAL_TTS_SERVICE

    with _LOCAL_TTS_LOCK:
        if _LOCAL_TTS_SERVICE is None:
            try:
                from backend.tts.coqui import CoquiTTSService
            except ImportError as exc:  # pragma: no cover - runtime guard
                raise HTTPException(
                    status_code=503,
                    detail="Coqui TTS dependency missing. Install it with `pip install TTS`."
                ) from exc

            model_name = LOCAL_TTS_CFG.get("model_name") or "tts_models/en/vctk/vits"
            default_speaker = LOCAL_TTS_CFG.get("speaker_id") or LOCAL_TTS_CFG.get("speaker")
            default_language = LOCAL_TTS_CFG.get("language")
            vocoder_path = LOCAL_TTS_CFG.get("vocoder_path")
            use_gpu = bool(LOCAL_TTS_CFG.get("use_gpu", False))

            _LOCAL_TTS_SERVICE = CoquiTTSService(
                model_name=model_name,
                vocoder_path=vocoder_path,
                default_speaker=default_speaker,
                default_language=default_language,
                use_gpu=use_gpu,
                progress_bar=bool(LOCAL_TTS_CFG.get("progress_bar", False)),
            )
    return _LOCAL_TTS_SERVICE


def _probe_wav_metadata(path: Path) -> tuple[Optional[float], Optional[int]]:
    if path.suffix.lower() != ".wav":
        return None, None
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as wav_file:
            frames = wav_file.getnframes()
            framerate = wav_file.getframerate()
            duration = frames / float(framerate) if framerate else None
            return duration, framerate
    except Exception:
        return None, None


async def _call_local_tts(text: str, *, voice_cfg: Optional[dict]) -> dict:
    service = _get_local_tts_service()
    job_id = datetime.now(timezone.utc).strftime("local-%Y%m%d%H%M%S%f")
    output_path = AUDIO_DIR / f"{job_id}.wav"

    speaker = None
    language = None
    style_wav = None
    if voice_cfg:
        speaker = voice_cfg.get("speaker") or voice_cfg.get("speaker_id")
        language = voice_cfg.get("language")
        style_wav = voice_cfg.get("style_wav")
    elif LOCAL_TTS_DEFAULT_VOICE:
        default_cfg = _get_voice_entry(LOCAL_TTS_DEFAULT_VOICE)
        if default_cfg:
            speaker = default_cfg.get("speaker") or default_cfg.get("speaker_id")
            language = default_cfg.get("language")
            style_wav = default_cfg.get("style_wav")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: service.synthesize_to_file(
            text=text,
            output_path=output_path,
            speaker=speaker,
            language=language,
            style_wav=style_wav,
        ),
    )

    duration, sample_rate = _probe_wav_metadata(output_path)
    return {
        "job_id": job_id,
        "duration": duration,
        "sample_rate": sample_rate,
        "audio_path": str(output_path),
    }


def _locate_audio_file(job_id: str) -> tuple[Path, str]:
    for ext, mime in SUPPORTED_AUDIO_EXTENSIONS.items():
        candidate = AUDIO_DIR / f"{job_id}{ext}"
        if candidate.exists():
            return candidate, mime

    matches = list(AUDIO_DIR.glob(f"{job_id}.*"))
    if matches:
        path = matches[0]
        mime = SUPPORTED_AUDIO_EXTENSIONS.get(path.suffix.lower(), "application/octet-stream")
        return path, mime
    raise HTTPException(status_code=404, detail="Audio not found")


@app.get("/api/settings")
async def get_settings():
    library_path = _get_library_path()
    return {
        "tts_default": DEFAULT_TTS_MODE,
        "voices": SETTINGS.get("voices", []),
        "heroku_api_url": SETTINGS.get("heroku_api_url"),
        "library_path": str(library_path) if library_path else "",
        "rsvp": {
            "wpm_default": RSVP_DEFAULT_WPM,
            "wpm_max": RSVP_MAX_WPM,
        },
        "playback": {
            "start_speed": START_SPEED,
            "speed_increment": SPEED_INCREMENT,
            "increment_interval_minutes": INCREMENT_INTERVAL_MIN,
            "max_speed": MAX_SPEED,
        },
        "local_tts": {
            "enabled": LOCAL_TTS_ENABLED,
            "default_voice": LOCAL_TTS_DEFAULT_VOICE,
            "model": LOCAL_TTS_CFG.get("model_name"),
            "provider": LOCAL_TTS_CFG.get("provider", "coqui"),
        },
    }


if __name__ == "__main__":
    # Run the server on localhost only for security
    uvicorn.run(
        "main:app",
        host=SETTINGS.get("local_api_host", "127.0.0.1"),
        port=int(SETTINGS.get("local_api_port", 5000)),
        reload=True,
        log_level="info",
    )
