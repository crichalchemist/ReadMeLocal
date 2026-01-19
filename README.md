# ReadMe Local

Convert books to natural-sounding speech with synchronized word-by-word highlighting. ReadMe Local is a self-hosted desktop app that transforms PDF, EPUB, TXT, and DOCX files into an immersive reading experience. Built with Electron, React, and FastAPI—privacy-first, runs entirely on your machine.

## Key Features

- **Multi-Format Support** — Parse PDF, EPUB, DOCX, and plaintext files
- **Smart PDF Filtering** — Position-aware extraction that skips frontmatter, headers, footers, and page numbers
- **RSVP Reading** — Real-time sentence highlighting synchronized with audio playback
- **Adaptive Playback** — Reading speed automatically increases over time (1.5× → 2.5×)
- **Paragraph Annotations** — Add, search, and export notes at specific positions in books
- **Natural Voices** — Google Cloud Text-to-Speech with multiple speakers and accents
- **Local-First Privacy** — No tracking, no data collection—everything runs on your computer

## Quick Start

**Requirements:** Python 3.11+, Node.js 18+, and a [Google Cloud TTS API key](https://cloud.google.com/text-to-speech)

1. Clone and install dependencies:
   ```bash
   git clone https://github.com/crichalchemist/ReadMeLocal && cd ReadMeLocal
   cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   cd ../frontend && npm install
   ```

2. Configure your API key:
   ```bash
   cp config/secrets.env.template config/secrets.env
   # Edit config/secrets.env and add your Google Cloud credentials
   ```

3. Launch the app:
   ```bash
   cd frontend && npm run electron-dev
   ```

For detailed setup and troubleshooting, see [docs/getting-started.md](docs/getting-started.md).

## Architecture

```
┌────────────────────────────────┐
│   Electron + React UI          │
│   (localhost:3000)             │
└──────────────┬─────────────────┘
               │
               ▼
┌────────────────────────────────┐
│   FastAPI Backend              │
│   (localhost:5000)             │
├─ Document Parsers             │
├─ RSVP Tokenizer               │
├─ Google Cloud TTS             │
└─ SQLite Database              │
```

**Components:**
- **Frontend**: Electron + React with real-time RSVP highlighting
- **Backend**: FastAPI handling document parsing, TTS requests, and playback state
- **Database**: SQLite storing books, progress, and annotations
- **Parsers**: PDF, EPUB, DOCX, and plaintext extraction with content filtering

## Configuration

Customize app behavior in `config/settings.yaml`:
- TTS voice selection and speaking rate
- Playback speed limits and acceleration intervals
- Content filtering rules (frontmatter, page numbers, etc.)
- Annotation rewind threshold

See [docs/configuration.md](docs/configuration.md) for detailed options.

## Development

**Backend:**
```bash
cd backend && source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 5000
pytest                    # Run tests
black .                   # Format code
```

**Frontend:**
```bash
cd frontend
npm start              # React dev server (localhost:3000)
npm run electron-dev   # Full app with backend and Electron
npm test               # Run tests
```

**API Docs:** Once backend is running, visit http://localhost:5000/docs

## Contributing

Found a bug or have an idea? Open an issue to discuss before submitting pull requests. All contributions welcome!

## License

MIT

---

**Status:** Phase 8 — Under Active Development

See [CLAUDE.md](CLAUDE.md) for development guidelines.
