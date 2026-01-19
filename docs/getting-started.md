# Getting Started with ReadMe Local

Welcome to ReadMe Local, a privacy-first desktop application for converting books into natural-sounding speech with RSVP (Rapid Serial Visual Presentation) reading. This guide will walk you through setting up the application from scratch.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.11 or later** - Download from [python.org](https://www.python.org)
- **Node.js 18 or later** - Download from [nodejs.org](https://nodejs.org)
- **Git** - Download from [git-scm.com](https://git-scm.com)
- **Google Cloud Account** - Required for text-to-speech functionality

Verify your installations:

```bash
python3 --version    # Should show Python 3.11+
node --version       # Should show Node.js 18+
npm --version        # Should show npm 9+
git --version        # Should show Git 2.0+
```

## Step 1: Clone the Repository

Clone the ReadMe Local repository to your local machine:

```bash
git clone https://github.com/your-org/readme-local.git
cd readme-local
```

## Step 2: Set Up the Backend

The backend is a FastAPI application that handles document parsing, text-to-speech, and RSVP tokenization.

### Create Python Virtual Environment

Navigate to the backend directory and create a virtual environment:

```bash
cd backend
python3 -m venv venv
```

Activate the virtual environment:

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI and Uvicorn (web server)
- Document parsers (PyMuPDF, ebooklib, docx2txt)
- SQLAlchemy (database ORM)
- Google Cloud Text-to-Speech client
- Other utilities

## Step 3: Set Up the Frontend

Navigate back to the project root and set up the frontend:

```bash
cd ../frontend
npm install
```

This installs React, Electron, Tailwind CSS, and development tools.

## Step 4: Configure Google Cloud Text-to-Speech

ReadMe Local uses Google Cloud Text-to-Speech for high-quality audio. Follow these steps to set it up:

### Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a Project" → "New Project"
3. Enter a project name (e.g., "ReadMe Local") and create it

### Enable Text-to-Speech API

1. In the Google Cloud Console, search for "Text-to-Speech"
2. Click on "Cloud Text-to-Speech API"
3. Click the "Enable" button
4. Wait for the API to be enabled (usually takes a few seconds)

### Create a Service Account

1. In the left sidebar, go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Fill in the service account details:
   - **Service account name:** `readme-local` (or any name)
   - **Service account ID:** Auto-generated
   - Click **Create and Continue**
4. Assign roles:
   - Click **Select a role** and search for "Cloud Text-to-Speech"
   - Select **Cloud Text-to-Speech Client**
   - Click **Continue** → **Done**

### Download Service Account Key

1. In the Service Accounts list, click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** and click **Create**
5. Your key file will be downloaded automatically (e.g., `readme-local-xxxxx.json`)
6. **Save this file in a secure location** (you'll reference it in the next step)

### Configure Environment Variables

1. Return to the project root directory:

```bash
cd ..
```

2. Copy the secrets template:

```bash
cp config/secrets.env.template config/secrets.env
```

3. Open `config/secrets.env` in your text editor

4. Update the `GOOGLE_APPLICATION_CREDENTIALS` path to point to your downloaded JSON key file:

```env
# Replace /path/to/your-service-account-key.json with actual path
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/readme-local-xxxxx.json
```

**Important:** Use an absolute path (not a relative path). On macOS, this typically looks like `/Users/username/path/to/key.json`.

Example (macOS):
```env
GOOGLE_APPLICATION_CREDENTIALS=/Users/john/Downloads/readme-local-abc123.json
```

Example (Linux):
```env
GOOGLE_APPLICATION_CREDENTIALS=/home/john/downloads/readme-local-abc123.json
```

Example (Windows):
```env
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\john\Downloads\readme-local-abc123.json
```

### Configure Application Settings

Open `config/settings.yaml` and customize:

```yaml
# Set your local library path (where your books are stored)
library_path: "/path/to/your/books/folder"

# Optional: Adjust default playback speed (1.0 = normal, 1.5 = 1.5x faster)
playback:
  start_speed: 1.5
  max_speed: 2.5

# Optional: Choose your preferred voice
tts:
  default_voice: "en-US-Neural2-D"  # or "en-US-Neural2-F" for female voice
```

Available voices include:
- `en-US-Neural2-D` - Neural2 male voice (US English)
- `en-US-Neural2-F` - Neural2 female voice (US English)
- `en-GB-Neural2-B` - Neural2 male voice (British English)
- `en-GB-Neural2-A` - Neural2 female voice (British English)
- `en-US-Studio-O` - Premium female voice
- `en-US-Studio-Q` - Premium male voice

## Step 5: Run the Application

Start the entire application (React frontend + Python backend + Electron):

```bash
cd frontend
npm run electron-dev
```

This command:
1. Starts the React development server on `http://localhost:3000`
2. Waits for React to be ready
3. Launches Electron, which automatically spawns the Python backend on port 5000
4. Opens the ReadMe Local window

**Wait for the Electron window to appear** – this typically takes 10-15 seconds on first run.

### Troubleshooting Startup Issues

If the application doesn't start:

**Port Already in Use:**
- If port 5000 is occupied, find and kill the process:
  ```bash
  # macOS/Linux
  lsof -i :5000
  kill -9 <PID>

  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  ```

**Module Not Found Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt` (backend) and `npm install` (frontend)
- Try deleting `node_modules` and reinstalling: `rm -rf node_modules && npm install`

**Google Cloud Authentication Error:**
- Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly and points to your JSON key file
- Try running: `echo $GOOGLE_APPLICATION_CREDENTIALS` to verify the environment variable is loaded

**Backend Connection Refused:**
- Check that port 5000 is not blocked by firewall settings
- Verify the Python virtual environment is activated

## Step 6: Import Your First Book

Once the application is running:

1. **Set Library Path** (if not already done):
   - Open application settings
   - Set the library path to a folder containing your books
   - Supported formats: PDF, EPUB, TXT, DOCX

2. **Select a Book**:
   - Browse your library in the left sidebar
   - Click on a book to select it

3. **Start Reading**:
   - Press the **Play** button
   - The text will display one word at a time using RSVP
   - Audio will play simultaneously using Google Cloud Text-to-Speech
   - Use playback controls to adjust speed, pause, or rewind

4. **Annotate** (Optional):
   - Highlight text as it plays
   - Add notes and bookmarks
   - Export annotations later

## Understanding the Architecture

ReadMe Local has three main components:

```
Electron (main.js)
    ↓ spawns Python subprocess
React UI (App.js) ←→ FastAPI Backend (main.py)
                           ↓
                  SQLite Database + Parsers + TTS
```

- **Frontend (React)** - Handles RSVP display, playback controls, UI
- **Backend (FastAPI)** - Processes documents, manages database, calls Google Cloud TTS
- **Database (SQLite)** - Stores books, reading progress, annotations, settings

## Available API Endpoints

While the app is running, you can explore the API documentation:

```
http://localhost:5000/docs
```

This Swagger UI shows all available endpoints for document management, playback state, and annotations.

## Database and Cache

- **Database:** Stored at `db/readme.db` (SQLite)
- **Cache:** Stored at `cache/` (audio files, parsed content)
- **Settings:** `config/settings.yaml`
- **Secrets:** `config/secrets.env` (git-ignored)

## Next Steps

- **Configure Preferences:** Open Settings to adjust voice, playback speed, and filtering options
- **Adjust Content Filtering:** Edit `config/settings.yaml` to skip frontmatter, page numbers, or footnotes
- **Export Annotations:** Use the annotation export feature to save highlights and notes
- **Customize Library:** Set `library_path` to automatically scan your book collection

## Development Commands

If you plan to contribute or modify the code:

**Backend Development:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 5000
```

**Frontend Development:**
```bash
cd frontend
npm start  # React dev server only (localhost:3000)
```

**Run Tests:**
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

**Code Formatting:**
```bash
# Backend
cd backend
black .

# Frontend (uses prettier, configured in package.json)
cd frontend
npm run format  # if configured
```

## Troubleshooting

### "Module not found: google.cloud"
Ensure you've activated the virtual environment and installed requirements:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### "Cannot find Electron"
Clear npm cache and reinstall:
```bash
cd frontend
npm cache clean --force
rm -rf node_modules
npm install
```

### Audio not playing
- Verify Google Cloud credentials are correct
- Check system volume is not muted
- Ensure API quota hasn't been exceeded in Google Cloud Console

### Books not appearing in library
- Verify `library_path` in `config/settings.yaml` is correct and contains supported file formats
- Check file permissions (files must be readable)
- Restart the application after changing library path

### Slow RSVP playback or stuttering
- Reduce `speaking_rate` in `config/settings.yaml` (below 1.0)
- Check system CPU usage
- Close other applications using significant resources

## Getting Help

- Check existing issues in the repository: `https://github.com/your-org/readme-local/issues`
- Review architecture documentation: `CLAUDE.md` in the project root
- Inspect FastAPI logs in the terminal for backend errors

## Security Notes

- **Keep `secrets.env` private** – Never commit this file to version control (it's in `.gitignore`)
- **Service account key security** – Treat your Google Cloud JSON key like a password
- **Local-first design** – All data stays on your machine; nothing is sent to external servers except Google Cloud TTS

## What's Next?

Ready to start reading? Open a book from your library and press Play. Enjoy distraction-free, focused reading with natural-sounding audio!
