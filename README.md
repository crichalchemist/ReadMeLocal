# ReadMe - Local AI Reading Assistant

A self-hosted desktop application that converts digital books and documents into natural-sounding speech with AI-powered summaries. Built with Electron, React, and FastAPI.

## 🎯 Features

- **Multi-Format Support**: Open `.pdf`, `.epub`, `.txt`, and `.docx` files
- **AI Text-to-Speech**: Natural-sounding voices powered by OpenAI TTS
- **Smart Playback**: Play, pause, seek, adjust speed, and navigate by paragraph
- **Library Management**: Track reading progress across all your books
- **Bookmarks & Notes**: Save annotations and highlights locally
- **AI Summarization**: Get intelligent summaries of chapters or selections
- **Privacy-First**: Local-first architecture with optional cloud compute
- **Offline Mode**: Full functionality offline (except AI features)

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

- **Frontend**: Electron + React + TailwindCSS
- **Backend**: FastAPI (Python) running on localhost:5000
- **Database**: SQLite for local data storage
- **Parsers**: PyMuPDF, pdfplumber, ebooklib, docx2txt
- **Cloud** (Optional): Heroku for AI workloads

## 📋 Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **OpenAI API Key** (for TTS and summarization)

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

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
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
├── frontend/                  # Electron + React app
│   ├── electron/             # Electron main process
│   │   ├── main.js          # Window management & IPC
│   │   └── preload.js       # Security bridge
│   ├── src/                 # React source
│   │   ├── components/      # UI components
│   │   ├── pages/           # Page components
│   │   └── store/           # State management
│   └── package.json
├── backend/                  # Python FastAPI server
│   ├── main.py              # Entry point
│   ├── tts/                 # Text-to-speech engines
│   ├── parsers/             # Document parsers
│   └── requirements.txt
├── cloud/                    # Heroku cloud service
│   ├── app.py               # Cloud API entry
│   ├── routers/             # API routes
│   └── services/            # AI services
├── db/                       # SQLite database
├── config/                   # Configuration files
│   ├── settings.yaml        # App settings
│   └── secrets.env          # API keys (git-ignored)
└── cache/                    # Audio & text cache

```

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

### Phase 1 (MVP) - Current
- [x] Project setup & directory structure
- [x] Basic Electron + React app
- [x] FastAPI backend skeleton
- [ ] PDF/EPUB parsing
- [ ] Basic playback controls
- [ ] Cloud TTS integration

### Phase 2
- [ ] Voice selector UI
- [ ] Audio caching system
- [ ] Library management

### Phase 3
- [ ] AI summarization
- [ ] Local note system
- [ ] Bookmarks UI

### Phase 4
- [ ] Local Coqui-TTS (offline mode)
- [ ] Performance optimizations

### Phase 5
- [ ] UI polish & themes
- [ ] Export audiobooks
- [ ] Keyboard shortcuts

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

**Status**: 🚧 In Development (Phase 1 MVP)

For detailed technical specifications, see [.junie/guidelines.md](.junie/guidelines.md)
