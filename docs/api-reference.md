# ReadMe Local API Reference

## Overview

The ReadMe Local API is a FastAPI-based REST service that manages document parsing, text-to-speech synthesis, playback control, and annotation management for the ReadMe Local desktop application. All endpoints are accessible over localhost only for security.

**Base URL:** `http://localhost:5000`
**API Version:** 0.3.0

---

## Health & Settings

### GET /

Root endpoint that returns service status and version information.

**Request:**
```bash
curl http://localhost:5000/
```

**Response:**
```json
{
  "status": "ok",
  "service": "ReadMe Local API",
  "version": "0.3.0"
}
```

---

### GET /api/health

Health check endpoint that validates database and cache directory availability.

**Request:**
```bash
curl http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "database_path": "/path/to/db/readme.db",
  "database_exists": true,
  "cache_dir": "/path/to/cache",
  "cache_exists": true
}
```

**Status Values:**
- `"healthy"` - Database and cache directories exist
- `"degraded"` - One or more required directories are missing

---

### GET /api/settings

Retrieve all application settings including voices, library paths, RSVP configuration, playback speeds, and TTS settings.

**Request:**
```bash
curl http://localhost:5000/api/settings
```

**Response:**
```json
{
  "voices": [
    {
      "name": "en-US-Neural2-D",
      "language_code": "en-US",
      "speaking_rate": 1.0
    }
  ],
  "library_path": "/Users/books",
  "rsvp": {
    "wpm_default": 150,
    "wpm_max": 1024
  },
  "playback": {
    "start_speed": 1.5,
    "speed_increment": 0.1,
    "increment_interval_minutes": 15,
    "max_speed": 2.5
  },
  "tts": {
    "enabled": true,
    "provider": "google",
    "default_voice": "en-US-Neural2-D",
    "audio_encoding": "MP3"
  }
}
```

---

## Library

### GET /api/library

List all books available in the configured library path.

**Query Parameters:** None

**Request:**
```bash
curl http://localhost:5000/api/library
```

**Response:**
```json
{
  "books": [
    {
      "id": "book_001",
      "title": "Example Book",
      "ext": ".pdf",
      "path": "/Users/books/example_book.pdf",
      "modified": "2025-01-19T10:30:00Z"
    },
    {
      "id": "book_002",
      "title": "Another Document",
      "ext": ".epub",
      "path": "/Users/books/another_document.epub",
      "modified": "2025-01-18T15:45:00Z"
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Library path not configured

---

### PUT /api/library/path

Update the library path configuration. Accepts an empty path to clear the setting.

**Request Body:**
```json
{
  "path": "/Users/books"
}
```

**Request:**
```bash
curl -X PUT http://localhost:5000/api/library/path \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/books"}'
```

**Response:**
```json
{
  "library_path": "/Users/books",
  "items": [
    {
      "id": "book_001",
      "title": "Example Book",
      "ext": ".pdf",
      "path": "/Users/books/example_book.pdf"
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Library path does not exist

---

### GET /api/books/{book_id}

Retrieve detailed information about a specific book, including parsed content, paragraphs, and tokenized text.

**Path Parameters:**
- `book_id` (string) - Book identifier from library

**Request:**
```bash
curl http://localhost:5000/api/books/book_001
```

**Response:**
```json
{
  "id": "book_001",
  "title": "Example Book",
  "author": "John Doe",
  "paragraphs": [
    "This is the first paragraph.",
    "This is the second paragraph with more content."
  ],
  "tokens": [
    {
      "word": "This",
      "paragraph_index": 0,
      "word_index": 0,
      "is_punctuation": false
    },
    {
      "word": "is",
      "paragraph_index": 0,
      "word_index": 1,
      "is_punctuation": false
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Library path not configured
- `404 Not Found` - Book not found in library

---

## Book Management

### POST /api/book/import

Import and parse an uploaded document file. Sets it as the current book.

**Supported File Types:** `.txt`, `.md`, `.pdf`, `.epub`, `.docx`

**Request:**
```bash
curl -X POST http://localhost:5000/api/book/import \
  -F "file=@/path/to/document.pdf"
```

**Response:**
```json
{
  "id": 1,
  "title": "Document Title",
  "author": "Author Name",
  "filepath": "document.pdf",
  "filetype": "pdf",
  "num_sentences": 42
}
```

**Response Schema:**
- `id` (int) - Database ID for the imported book (always 1 in single-book mode)
- `title` (string) - Inferred or extracted title
- `author` (string, nullable) - Extracted author if available
- `filepath` (string) - Original filename
- `filetype` (string) - File type: `pdf`, `epub`, `docx`, `txt`, `md`
- `num_sentences` (int) - Total number of parsed sentences

**Error Responses:**
- `409 Conflict` - A book is already open (in single-book mode)
- `415 Unsupported Media Type` - File type not supported
- `500 Internal Server Error` - Parsing failed

---

### GET /api/book/current

Retrieve the currently loaded book and its content.

**Request:**
```bash
curl http://localhost:5000/api/book/current
```

**Response:**
```json
{
  "id": 1,
  "title": "Current Book",
  "author": "Author Name",
  "filepath": "current_book.pdf",
  "filetype": "pdf",
  "content": [
    "First sentence of the book.",
    "Second sentence here.",
    "Third sentence continues the story."
  ]
}
```

**Error Responses:**
- `404 Not Found` - No book is currently loaded

---

### POST /api/book/close

Close the currently loaded book and reset playback state.

**Request:**
```bash
curl -X POST http://localhost:5000/api/book/close
```

**Response:**
```json
{
  "status": "closed"
}
```

**Side Effects:**
- Clears current book from database
- Resets playback position to 0.0 seconds
- Resets playback speed to configured start speed

---

## Playback

### GET /api/playback/speed

Get the current playback speed. Includes adaptive speed calculation based on session elapsed time.

**Request:**
```bash
curl http://localhost:5000/api/playback/speed
```

**Response:**
```json
{
  "speed": 1.5
}
```

**Details:**
- Returns adaptive speed based on elapsed session time if configured
- Speed ranges from 0.5x to 3.0x
- Persists speed to database for visibility

---

### POST /api/playback/update

Update playback position and/or speed. Both fields are optional.

**Request Body:**
```json
{
  "position_seconds": 125.5,
  "speed": 1.8
}
```

**Request:**
```bash
curl -X POST http://localhost:5000/api/playback/update \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 125.5, "speed": 1.8}'
```

**Response:**
```json
{
  "position_seconds": 125.5,
  "speed": 1.8,
  "last_updated": "2025-01-19T14:30:00Z"
}
```

**Constraints:**
- `position_seconds`: Minimum 0.0, clamped if negative
- `speed`: Clamped between 0.5 and 3.0

**Error Responses:**
- `400 Bad Request` - Invalid speed value
- `500 Internal Server Error` - Playback state not initialized

---

### GET /api/playback/current-sentence

Get the currently highlighted sentence based on the current playback position.

**Request:**
```bash
curl http://localhost:5000/api/playback/current-sentence
```

**Response:**
```json
{
  "sentence_index": 5,
  "sentence_text": "This is the current sentence being highlighted.",
  "position_seconds": 45.5
}
```

**Details:**
- Uses estimated sentence durations based on word count and playback speed
- Minimum duration per sentence: 0.5 seconds
- Updates current sentence index in playback state

**Error Responses:**
- `404 Not Found` - No book loaded or book content unavailable
- `500 Internal Server Error` - Failed to parse content or state not initialized

---

### POST /api/playback/sync-sentence

Update playback position based on a specific audio position (used for seeking).

**Request Body:**
```json
{
  "position_seconds": 60.0
}
```

**Request:**
```bash
curl -X POST http://localhost:5000/api/playback/sync-sentence \
  -H "Content-Type: application/json" \
  -d '{"position_seconds": 60.0}'
```

**Response:**
```json
{
  "position_seconds": 60.0,
  "sentence_index": 7,
  "status": "updated"
}
```

**Details:**
- Finds the sentence that corresponds to the given audio position
- Clamps position to minimum 0.0
- Updates both position and sentence index in playback state

**Error Responses:**
- `404 Not Found` - No book loaded or content unavailable
- `500 Internal Server Error` - Failed to parse content or state not initialized

---

## Text-to-Speech (TTS)

### POST /api/tts

Generate speech audio from text using Google Cloud TTS.

**Request Body:**
```json
{
  "text": "This is the text to convert to speech.",
  "voice": "en-US-Neural2-D",
  "mode": "cloud",
  "model": "neural"
}
```

**Request:**
```bash
curl -X POST http://localhost:5000/api/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test.",
    "voice": "en-US-Neural2-D"
  }'
```

**Response:**
```json
{
  "job_id": "tts-20250119143000123456",
  "duration": 2.5,
  "sample_rate": 22050,
  "audio_path": "/api/audio/tts-20250119143000123456/stream",
  "download_path": "/api/audio/tts-20250119143000123456/download"
}
```

**Request Parameters:**
- `text` (string, required) - Text to synthesize (max 8000 characters)
- `voice` (string, optional) - Voice name from configured voices
- `mode` (string, optional) - "cloud" or "local" (currently only cloud supported)
- `model` (string, optional) - Model identifier

**Response Schema:**
- `job_id` (string) - Unique identifier for this synthesis job
- `duration` (float, nullable) - Estimated duration in seconds (if available)
- `sample_rate` (int, nullable) - Audio sample rate in Hz
- `audio_path` (string) - Relative path for streaming the audio
- `download_path` (string) - Relative path for downloading the audio

**Error Responses:**
- `400 Bad Request` - Text is required or empty
- `503 Service Unavailable` - TTS disabled or Google Cloud dependency missing

---

### GET /api/audio/{job_id}/stream

Stream audio file for playback.

**Path Parameters:**
- `job_id` (string) - Job ID from TTS response

**Request:**
```bash
curl http://localhost:5000/api/audio/tts-20250119143000123456/stream
```

**Response:**
- Audio file with appropriate media type (audio/mpeg, audio/wav, etc.)
- Supports resume/seek operations

**Error Responses:**
- `404 Not Found` - Audio file not found for this job ID

---

### GET /api/audio/{job_id}/download

Download audio file.

**Path Parameters:**
- `job_id` (string) - Job ID from TTS response

**Request:**
```bash
curl http://localhost:5000/api/audio/tts-20250119143000123456/download
```

**Response:**
- Audio file as downloadable attachment with original filename

**Error Responses:**
- `404 Not Found` - Audio file not found for this job ID

---

## Annotations

### POST /api/annotations

Create a new annotation for a paragraph in a book.

**Request Body:**
```json
{
  "book_id": "book_001",
  "paragraph_index": 5,
  "section_title": "Chapter 2: Introduction",
  "source_text": "Original text from the paragraph.",
  "note_text": "My personal note about this paragraph."
}
```

**Request:**
```bash
curl -X POST http://localhost:5000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": "book_001",
    "paragraph_index": 5,
    "section_title": "Chapter 2",
    "source_text": "Original paragraph text",
    "note_text": "Important note"
  }'
```

**Response:**
```json
{
  "id": 42,
  "book_id": "book_001",
  "paragraph_index": 5,
  "section_title": "Chapter 2: Introduction",
  "source_text": "Original text from the paragraph.",
  "note_text": "My personal note about this paragraph.",
  "created_at": "2025-01-19T14:30:00Z",
  "updated_at": "2025-01-19T14:30:00Z"
}
```

**Request Schema:**
- `book_id` (string, required) - Unique identifier for the book
- `paragraph_index` (int, required) - Zero-based paragraph index
- `section_title` (string, optional) - Chapter or section name
- `source_text` (string, required) - The text being annotated
- `note_text` (string, required) - The user's note

---

### GET /api/annotations/{book_id}

List all annotations for a specific book.

**Path Parameters:**
- `book_id` (string) - Book identifier

**Request:**
```bash
curl http://localhost:5000/api/annotations/book_001
```

**Response:**
```json
{
  "annotations": [
    {
      "id": 42,
      "book_id": "book_001",
      "paragraph_index": 5,
      "section_title": "Chapter 2: Introduction",
      "source_text": "Original text from the paragraph.",
      "note_text": "My personal note about this paragraph.",
      "created_at": "2025-01-19T14:30:00Z",
      "updated_at": "2025-01-19T14:30:00Z"
    },
    {
      "id": 43,
      "book_id": "book_001",
      "paragraph_index": 12,
      "section_title": "Chapter 3",
      "source_text": "Another annotated paragraph.",
      "note_text": "Second note",
      "created_at": "2025-01-19T15:00:00Z",
      "updated_at": "2025-01-19T15:00:00Z"
    }
  ],
  "total": 2
}
```

**Ordering:** Annotations are ordered by paragraph index (ascending)

---

### DELETE /api/annotations/{annotation_id}

Delete a specific annotation by ID.

**Path Parameters:**
- `annotation_id` (int) - Annotation ID

**Request:**
```bash
curl -X DELETE http://localhost:5000/api/annotations/42
```

**Response:**
```json
{
  "status": "deleted",
  "id": 42
}
```

**Error Responses:**
- `404 Not Found` - Annotation not found

---

### GET /api/annotations/{book_id}/export

Export all annotations for a book as a plain text file.

**Path Parameters:**
- `book_id` (string) - Book identifier

**Request:**
```bash
curl http://localhost:5000/api/annotations/book_001/export > annotations.txt
```

**Response:**
```
========================================
ANNOTATIONS: book_001
Exported: 2025-01-19
Total notes: 2
========================================

--- Chapter 2: Introduction, Paragraph 5 ---
SOURCE:
"Original text from the paragraph."

NOTE:
My personal note about this paragraph.

----------------------------------------

--- Chapter 3, Paragraph 12 ---
SOURCE:
"Another annotated paragraph."

NOTE:
Second note

----------------------------------------
```

**Content Type:** `text/plain; charset=utf-8`

**Error Responses:**
- `404 Not Found` - No annotations found for this book

---

## Error Handling

All endpoints return HTTP status codes according to REST conventions:

| Status | Meaning |
|--------|---------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Invalid request parameters or body |
| `404 Not Found` | Resource not found |
| `409 Conflict` | Request conflicts with current state (e.g., book already open) |
| `415 Unsupported Media Type` | Unsupported file type |
| `500 Internal Server Error` | Server-side error during processing |
| `503 Service Unavailable` | Service disabled or dependency missing |

Error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

---

## Configuration

The API behavior is controlled by `/config/settings.yaml`. Key settings:

```yaml
# Library settings
library_path: "/Users/books"

# Playback configuration
playback:
  start_speed: 1.5                    # Initial playback speed (1.0 = normal)
  speed_increment: 0.1                # Speed increase per interval
  increment_interval_minutes: 15      # Minutes between speed increases
  max_speed: 2.5                      # Maximum playback speed

# RSVP (Rapid Serial Visual Presentation) settings
rsvp:
  wpm_default: 150                    # Words per minute for timing
  wpm_max: 1024                       # Maximum WPM value

# Session configuration
session:
  single_book_mode: true              # Only one book can be open at a time
  auto_finish_threshold: 0.95         # Auto-mark complete at 95% progress

# TTS configuration
local_tts:
  enabled: true                       # Enable Google Cloud TTS
  default_voice: "en-US-Neural2-D"   # Default voice
  speaking_rate: 1.0                  # Speaking rate (0.25 to 4.0)
  audio_encoding: "MP3"               # Audio format: MP3, WAV, OGG, FLAC

# Voice definitions
voices:
  - name: "en-US-Neural2-D"
    language_code: "en-US"
    speaking_rate: 1.0
```

---

## Notes

1. **Single-Book Mode:** By default, only one book can be open at a time. Attempting to import another book while one is active returns a 409 Conflict error.

2. **Playback State:** Playback position and speed are persisted in the database using a singleton row with `id=1`.

3. **Sentence Timing:** The API estimates sentence durations based on word count and playback speed (assuming ~150 words per minute). The minimum duration is 0.5 seconds per sentence.

4. **Local-Only Access:** The API only accepts connections from localhost (127.0.0.1) for security reasons.

5. **Audio Caching:** Generated TTS audio is cached in the `./cache/audio` directory and can be streamed or downloaded multiple times without regeneration.

6. **Content Filtering:** When importing text-based files (.txt, .md), the ContentFilter automatically removes frontmatter, page numbers, and footnotes before tokenization.
