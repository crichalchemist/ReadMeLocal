# ReadMe Local Configuration Guide

This guide explains all configuration options for ReadMe Local, including TTS settings, library paths, playback preferences, and advanced features.

## Overview

ReadMe Local uses two primary configuration files:

- **`config/settings.yaml`** – Application settings (TTS, playback, library paths, feature flags)
- **`config/secrets.env`** – Sensitive credentials (API keys, service account paths)

Both files reside in the `config/` directory at the project root.

### Initial Setup

1. **Copy the secrets template:**
   ```bash
   cp config/secrets.env.template config/secrets.env
   ```

2. **Edit `config/settings.yaml`** with your preferred settings (see sections below)

3. **Fill `config/secrets.env`** with your credentials (see [Environment Variables](#environment-variables))

4. **Add `config/secrets.env` to `.gitignore`** (already configured) – never commit credentials

---

## TTS Settings (Google Cloud)

Configures Text-to-Speech behavior using Google Cloud's neural voices.

### Top-Level TTS Section

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tts.enabled` | Boolean | `true` | Enable/disable TTS synthesis. If `false`, audio generation is skipped. |
| `tts.provider` | String | `"google"` | TTS provider (`"google"` for Google Cloud, extensible for future providers). |
| `tts.default_voice` | String | `"en-US-Neural2-D"` | Default voice ID to use when generating audio (see [Available Voices](#available-voices)). |
| `tts.audio_encoding` | String | `"MP3"` | Output audio format: `"MP3"`, `"LINEAR16"` (WAV), or `"OGG_OPUS"`. MP3 is default for compatibility. |
| `tts.speaking_rate` | Float | `1.0` | Speed multiplier for speech synthesis. Range: `0.25` (slowest) to `4.0` (fastest). |

### Local TTS Section

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `local_tts.enabled` | Boolean | `true` | Enable local TTS fallback (used by backend when generating audio). |
| `local_tts.provider` | String | `"google"` | Provider for local synthesis. Maps to the top-level TTS settings. |
| `local_tts.default_voice` | String | `"en-US-Neural2-D"` | Voice ID for local synthesis. |
| `local_tts.audio_encoding` | String | `"MP3"` | Local audio output format. |
| `local_tts.speaking_rate` | Float | `1.0` | Local synthesis speed multiplier. |

### Available Voices

The `voices` section lists all available Google Cloud Neural2 voices. Select one for `tts.default_voice`:

#### US English

| Voice ID | Gender | Description |
|----------|--------|-------------|
| `en-US-Neural2-A` | Male | Neural2 US voice option A |
| `en-US-Neural2-C` | Female | Neural2 US voice option C |
| `en-US-Neural2-D` | Male | Neural2 US voice option D (default) |
| `en-US-Neural2-F` | Female | Neural2 US voice option F |
| `en-US-Studio-O` | Female | Studio-quality US female voice |
| `en-US-Studio-Q` | Male | Studio-quality US male voice |

#### British English

| Voice ID | Gender | Description |
|----------|--------|-------------|
| `en-GB-Neural2-A` | Female | Neural2 British voice option A |
| `en-GB-Neural2-B` | Male | Neural2 British voice option B |

**Note:** For additional voices or languages, see [Google Cloud Text-to-Speech documentation](https://cloud.google.com/text-to-speech/docs/voices).

---

## Library Settings

Configures where ReadMe Local reads books from.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `library_path` | String | `"/Volumes/Rich 3TB/books"` | Absolute path to your local book library folder. ReadMe scans this directory for supported file formats (PDF, EPUB, DOCX, TXT). Change this to your actual books folder. |

### Supported Formats

- `.pdf` – PDF documents
- `.epub` – EPUB 2.0 and 3.0 ebooks
- `.docx` – Microsoft Word documents
- `.txt` – Plain text files

ReadMe automatically detects file types and applies the appropriate parser.

---

## Playback Settings

Configures audio playback behavior, including adaptive speed adjustment.

### Default Volume

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_volume` | Float | `0.8` | Default playback volume. Range: `0.0` (mute) to `1.0` (maximum). |

### Adaptive Playback Speed

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `playback.start_speed` | Float | `1.5` | Initial playback speed (words per minute multiplier). Start lower for comprehension; increase as comfort grows. |
| `playback.speed_increment` | Float | `0.1` | Speed increase per interval. Applied every `increment_interval_minutes`. |
| `playback.increment_interval_minutes` | Integer | `15` | Minutes of listening before automatic speed increase. Set to `0` to disable adaptive speed. |
| `playback.max_speed` | Float | `2.5` | Maximum playback speed. Adaptive speed will not exceed this value. |

**Example:** With defaults, speed increases by 0.1× every 15 minutes until reaching 2.5×.

### Session Behavior

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `session.single_book_mode` | Boolean | `true` | If `true`, only one book can be read per session. Switching books resets playback state. |
| `session.auto_finish_threshold` | Float | `0.95` | Automatically mark book as finished when reaching this progress ratio (e.g., `0.95` = 95% complete). |

---

## Cache Settings

Configures local caching for parsed content and generated audio.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `cache_dir` | String | `"./cache"` | Relative or absolute path to cache directory. Stores parsed documents and generated audio. |
| `cache_max_size_mb` | Integer | `1000` | Maximum cache size in megabytes before eviction. Oldest files are removed first. |
| `auto_clear_cache` | Boolean | `false` | If `true`, cache is cleared on app startup. Useful for development; disable in production. |

---

## Database Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `database_path` | String | `"./db/readme.db"` | Relative or absolute path to SQLite database file. Stores book metadata, playback state, annotations, bookmarks. |

---

## UI Settings

### Top-Level UI Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `theme` | String | `"light"` | Legacy theme setting (superseded by `ui.theme`). |
| `sidebar_width` | Integer | `300` | Width of left sidebar in pixels. |

### UI Section

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ui.theme` | String | `"minimal"` | UI theme (`"minimal"`, `"dark"`, `"light"`). Controls color scheme and layout density. |
| `ui.highlight_style` | String | `"sentence"` | RSVP highlight behavior: `"word"` (highlight single word) or `"sentence"` (highlight entire sentence). |
| `ui.auto_scroll` | Boolean | `true` | Automatically scroll text to keep highlighted word visible. Set to `false` for manual scrolling. |

---

## API Settings

Configures the backend FastAPI server.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `local_api_host` | String | `"0.0.0.0"` | Host binding for the FastAPI backend. `"0.0.0.0"` listens on all interfaces; `"127.0.0.1"` restricts to localhost only (recommended for security). |
| `local_api_port` | Integer | `5000` | Port for FastAPI backend. Default is `5000`; change if port is already in use. |

**Security note:** When running in a trusted local environment, `0.0.0.0` is acceptable. For networked environments, restrict to `127.0.0.1`.

---

## Content Filtering

Automatically removes boilerplate, page numbers, and repetitive content to improve RSVP experience.

### General Filtering

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `content_filtering.skip_frontmatter` | Boolean | `true` | Skip frontmatter (title page, copyright, table of contents) detected at document start. |
| `content_filtering.frontmatter_skip_percent` | Float | `0.05` | Frontmatter is assumed to be the first N% of document (default: 5%). |
| `content_filtering.skip_page_numbers` | Boolean | `true` | Detect and skip page numbers (e.g., "42", "p. 42") that appear in text. |
| `content_filtering.skip_footnotes` | Boolean | `true` | Detect and remove footnotes and endnote references. |
| `content_filtering.skip_headers_footers` | Boolean | `true` | Remove recurring headers and footers (e.g., chapter titles, author names). |
| `content_filtering.repeat_threshold` | Integer | `3` | Minimum repetitions before text is classified as a header/footer. |

### PDF-Specific Filtering

PDFs often have physical page layouts with headers/footers. Position-aware filtering handles this:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `pdf_filtering.header_zone_percent` | Float | `0.10` | Top N% of each PDF page considered "header zone" and filtered. Default: 10% (top edge). |
| `pdf_filtering.footer_zone_percent` | Float | `0.10` | Bottom N% of each PDF page considered "footer zone" and filtered. Default: 10% (bottom edge). |
| `pdf_filtering.min_body_font_size` | Integer | `9` | Minimum font size (points) for body text. Text smaller than this is assumed to be annotations/footnotes. |
| `pdf_filtering.detect_repeated_headers` | Boolean | `true` | Enable detection of repeated text across pages (e.g., chapter names, running titles). |

---

## Annotation Settings

Configures annotation storage and behavior.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `annotations.rewind_threshold_minutes` | Integer | `5` | When creating an annotation, how many minutes of playback to "rewind" for context. Enables re-reading surrounding text. Set to `0` to disable rewind. |

---

## Feature Flags

Enable or disable specific ReadMe Local features.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `features.summarization` | Boolean | `false` | Enable AI-powered chapter/book summarization (currently disabled). |
| `features.local_tts` | Boolean | `true` | Enable local TTS synthesis (Google Cloud). Disable to skip audio generation. |
| `features.annotations` | Boolean | `true` | Enable annotation CRUD operations (create, read, update, delete notes while reading). |
| `features.bookmarks` | Boolean | `true` | Enable bookmark creation and management. |
| `features.export_audio` | Boolean | `false` | Enable audio file export (save generated speech as standalone MP3/WAV files). |

---

## Environment Variables

Sensitive data is stored in `config/secrets.env`, which you create from the template:

```bash
cp config/secrets.env.template config/secrets.env
```

Edit `config/secrets.env` with your credentials.

### Google Cloud TTS Authentication

ReadMe Local requires Google Cloud credentials to use neural voice synthesis. Two options:

#### Option 1: Service Account Key (Recommended)

Most secure and recommended for local development.

1. **Create a service account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name: `readme-local-tts` (or similar)
   - Grant role: **Cloud Text-to-Speech API User**

2. **Create and download a key:**
   - Click the service account you created
   - Go to the **Keys** tab
   - Click **Add Key** → **Create new key**
   - Select **JSON** format
   - Save the downloaded JSON file to a secure location (e.g., `~/.config/readme/credentials.json`)

3. **Set environment variable:**
   ```bash
   # In config/secrets.env:
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json
   ```

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | String | Yes (Option 1) | Absolute path to the service account JSON key file. ReadMe loads this file on startup to authenticate with Google Cloud. |

#### Option 2: API Key

Simpler but less flexible than service accounts.

1. **Get an API key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **API Key**
   - Restrict to "Cloud Text-to-Speech API"

2. **Set environment variable:**
   ```bash
   # In config/secrets.env:
   GOOGLE_CLOUD_API_KEY=your-api-key-here
   ```

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `GOOGLE_CLOUD_API_KEY` | String | Yes (Option 2) | Google Cloud API key for Text-to-Speech. Use if not using service account. Less secure (avoid committing). |

### Optional Environment Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | String | No | Google Cloud project ID. Auto-detected from service account key if not set. Specify explicitly if using API key. |
| `DB_ENCRYPTION_KEY` | String | No | Encryption key for SQLCipher database encryption (reserved for future use). Currently unused. |

---

## Configuration Examples

### Minimal Setup (Fastest Reading)

For users who want to quickly get through books:

```yaml
playback:
  start_speed: 2.0
  speed_increment: 0.2
  increment_interval_minutes: 10
  max_speed: 3.5

tts:
  speaking_rate: 1.2

ui:
  highlight_style: "word"
  auto_scroll: true
```

### Careful Study (Comprehension Focus)

For educational or detailed reading:

```yaml
playback:
  start_speed: 1.0
  speed_increment: 0.05
  increment_interval_minutes: 30
  max_speed: 1.5

tts:
  speaking_rate: 0.9

content_filtering:
  skip_frontmatter: true
  skip_page_numbers: true
```

### Development/Testing

For testing and development:

```yaml
cache_dir: "./cache-dev"
auto_clear_cache: true
database_path: "./db/test.db"
local_api_host: "127.0.0.1"
local_api_port: 5001

features:
  local_tts: false  # Disable TTS to speed up testing
```

---

## Troubleshooting

### "No credentials found" error

**Cause:** `GOOGLE_APPLICATION_CREDENTIALS` not set or path is incorrect.

**Fix:**
1. Verify `config/secrets.env` exists (not `secrets.env.template`)
2. Verify the path in `GOOGLE_APPLICATION_CREDENTIALS` is absolute and points to a valid JSON file
3. Restart the application

### TTS audio sounds robotic or too fast/slow

**Cause:** `tts.speaking_rate` is too extreme.

**Fix:**
- For faster: increase to `1.2–1.5` (not above `2.0`)
- For slower: decrease to `0.8–0.9` (not below `0.5`)
- Test incrementally

### Cache fills up disk space

**Cause:** `auto_clear_cache: false` and `cache_max_size_mb` is too high.

**Fix:**
- Reduce `cache_max_size_mb` to a reasonable size (e.g., `500`)
- Enable `auto_clear_cache: true` if disk space is critical
- Manually delete old cache files from `cache_dir`

### Book not appearing in library

**Cause:** `library_path` points to wrong folder or contains unsupported file types.

**Fix:**
1. Verify `library_path` is an absolute path to your books folder
2. Verify files are in supported formats: `.pdf`, `.epub`, `.docx`, `.txt`
3. Restart the application to rescan the library

---

## File Location Reference

| File | Purpose | Location |
|------|---------|----------|
| Settings | Main configuration | `config/settings.yaml` |
| Secrets template | Environment variable template | `config/secrets.env.template` |
| Secrets (yours) | Your credentials | `config/secrets.env` (not in git) |
| Database | Book metadata, playback state | `db/readme.db` (default) |
| Cache | Parsed content, audio | `cache/` (default) |

---

## Next Steps

- **Edit `config/settings.yaml`** to customize playback speed, library path, and TTS voice
- **Create `config/secrets.env`** with your Google Cloud credentials
- **Start the app:** `npm run electron-dev` (frontend) or `uvicorn main:app --reload` (backend only)
- **Verify:** Check backend logs at `http://localhost:5000/docs` (Swagger API docs)
