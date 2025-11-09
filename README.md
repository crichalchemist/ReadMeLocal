# ReadMe - Local AI Reading Assistant

A self-hosted desktop application that converts digital books and documents into natural-sounding speech with AI-powered summaries. Built with Electron, React, and FastAPI.

## 🎯 Features

- **File Format Support**: `.txt`, `.md`, `.pdf`, `.epub`, `.docx` files
- **Smart Content Filtering**: skips frontmatter, page numbers, footnotes, and repeated headers/footers
- **Sentence-level Parsing**: content stored as sentences for precise highlighting
- **Text-Audio Synchronization**: real-time sentence highlighting during playback (Phase 7)
- **Adaptive Speed**: automatically increases reading speed over time (1.5× → 2.5×)
- **Basic Playback State API**: track position and speed locally
- **Privacy-first**: local-first architecture; optional cloud compute (Heroku) for AI features
- **Offline Mode**: fully functional for local parsing and reading; cloud AI features are optional

## 🏗️ Architecture

```
┌───────────────┐     ┌──────────────┐     ┌─────────────┐
│ Electron UI   │────►│ Local FastAPI│────►│ Heroku Cloud│
│ (React)       │     │ (Python)     │     │ (Optional)  │
└───────────────┘     └──────────────┘     └─────────────┘
        ▲                     │                     │
        │                     ▼                     ▼
        │            SQLite / Parsers      OpenAI TTS / GPT
        └─────────── Playback & UI ─────────────────┘
```

### Components

- Frontend: Electron + React (minimal UI; Phase 4 completed)
- Backend: FastAPI (Python) on localhost:5000 (v0.3.0)
- Database: SQLite (single-book state)
- Parsing: `.txt`/`.md` supported now; PDF/EPUB/DOCX planned
- Cloud (Optional): Separate Heroku service (see readme-cloud repo)

## 📋 Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **OpenAI API Key** (optional; required for cloud TTS/summarization)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ReadMeLocal
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Frontend

```bash
cd ../frontend

# Install dependencies
npm install
```

### 4. Configure Environment

```bash
# Copy the template
cp config/secrets.env.template config/secrets.env

# Edit config/secrets.env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the Application

Start the app (Electron will auto-start the Python backend):
```bash
cd frontend
npm run electron-dev
```

The app will automatically:
1. Start the Python backend server on `localhost:5000`
2. Launch the React development server
3. Open the Electron desktop application

## 📦 Project Structure

```
ReadMeLocal/
├── backend/                  # Python FastAPI server (local)
│   ├── main.py              # Entry point (v0.3.0)
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                 # Electron + React app
│   ├── electron/
│   │   ├── main.js          # Window management & IPC
│   │   └── preload.js       # Security bridge
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── config/                   # Configuration files
│   ├── settings.yaml        # App settings (incl. content_filtering)
│   └── secrets.env.template # API keys template (copy to secrets.env)
├── db/                      # SQLite database (runtime)
├── README.md
├── revisedplan.md
├── CHECKPOINT_1.md
└── .junie/
    └── guidelines.md
```

Note: Cloud backend (Heroku) lives in a separate repository (readme-cloud).

## 🔧 Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload --host 127.0.0.1 --port 5000

# Run tests
pytest

# Format code
black .
```

### Frontend Development

```bash
cd frontend

# Run React dev server only
npm start

# Run Electron with React
npm run electron-dev

# Build for production
npm run build
npm run electron-build
```

### API Documentation

Once the backend is running, visit:
- **Interactive API Docs**: http://localhost:5000/docs
- **Alternative Docs**: http://localhost:5000/redoc

## 🗺️ Roadmap

### Phase 1 — Project Setup ✓
- Project scaffolding, Electron + React shell, FastAPI skeleton

### Phase 2 — Core Backend (Single‑Book) ✓
- Current book import endpoints (.txt/.md)
- Playback state (position, speed)

### Phase 3 — Smart Content Parsing ✓
- ContentFilter: skip frontmatter, page numbers, footnotes, repeated headers/footers
- Store content as sentences
- Backend version bumped to v0.3.0

### Phase 4 — Minimalistic UI ✓
- Empty state with drop zone and Select File button
- Reading view with sentence highlighting and auto‑scroll
- Basic playback controls (play/pause, speed indicator)

### Phase 5 — Cloud TTS Integration ✓
- Heroku service hookup (OpenAI TTS)
- Local audio caching and streaming endpoint

### Phase 6 — Adaptive Speed ✓
- Incremental speed adjustments over session (1.5× start; +0.1× every 15 min; capped at 2.5×)

### Phase 7 — Text–Audio Sync ✓
- Estimate sentence durations and real‑time highlighting

### Phase 8 — Single‑Book Lock
- Prevent opening a second book until current is closed

## 🔐 Security

- Backend only binds to `localhost` (not exposed to network)
- All cloud communication uses HTTPS
- API keys stored in git-ignored `secrets.env`
- No telemetry or external tracking
- Electron security best practices (contextIsolation, no nodeIntegration)

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome! Please open an issue to discuss any changes.

## 📄 License

[Your chosen license]

## 🙏 Acknowledgments

- OpenAI for GPT and TTS APIs
- FastAPI and Electron communities
- Open source document parsing libraries

---

**Status**: 🚧 In Development (Phase 8 — Single–Book Lock next) · Backend v0.3.0

For detailed technical specifications, see [.junie/guidelines.md](.junie/guidelines.md)