# Google Cloud TTS + Documentation Overhaul Design

**Date:** 2026-01-19
**Status:** Approved

## Overview

Replace all existing TTS providers (Coqui local, OpenAI cloud via Heroku) with Google Cloud Text-to-Speech as the single provider. Simultaneously overhaul project documentation for accuracy and expanded coverage.

## Goals

1. **Simplify TTS architecture** — One provider, direct API calls, no Heroku relay
2. **Reduce dependencies** — Remove ~500MB Coqui/PyTorch overhead
3. **Improve documentation** — Accurate README, expanded docs coverage

## Non-Goals

- Summarization features (explicitly excluded)
- Multi-provider TTS (only Google)
- Offline TTS capability (requires internet)

---

## Part A: Google Cloud TTS Integration

### Architecture

```
Frontend (React) → Local FastAPI → Google Cloud TTS API
                        ↓
                   Audio Cache (./cache/audio/)
```

### Component Changes

| Component | Current | New |
|-----------|---------|-----|
| `backend/tts/` | `coqui.py`, `__init__.py` | `google_tts.py` only |
| `config/settings.yaml` | Coqui + OpenAI voices | Google voices only |
| `config/secrets.env` | `OPENAI_API_KEY` | `GOOGLE_CLOUD_API_KEY` |
| Dependencies | `TTS` (~1GB), `openai` | `google-cloud-texttospeech` |

### Voice Configuration

```yaml
tts:
  provider: "google"
  default_voice: "en-US-Neural2-D"
  audio_encoding: "MP3"  # or LINEAR16 for WAV

voices:
  - name: "en-US-Neural2-D"
    language_code: "en-US"
    gender: "MALE"
    description: "Neural2 male voice"
  - name: "en-US-Neural2-F"
    language_code: "en-US"
    gender: "FEMALE"
    description: "Neural2 female voice"
  - name: "en-US-Studio-O"
    language_code: "en-US"
    gender: "FEMALE"
    description: "Studio quality female"
  - name: "en-GB-Neural2-B"
    language_code: "en-GB"
    gender: "MALE"
    description: "British male voice"
```

### Implementation: `backend/tts/google_tts.py`

```python
from google.cloud import texttospeech
from pathlib import Path
import hashlib

def synthesize_speech(
    text: str,
    voice_name: str = "en-US-Neural2-D",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
    audio_encoding: str = "MP3",
) -> bytes:
    """
    Synthesize speech using Google Cloud TTS.

    Args:
        text: Text to synthesize (plain or SSML)
        voice_name: Google voice name
        speaking_rate: Speed multiplier (0.25 to 4.0)
        pitch: Pitch adjustment (-20.0 to 20.0 semitones)
        audio_encoding: "MP3" or "LINEAR16"

    Returns:
        Audio bytes
    """
    client = texttospeech.TextToSpeechClient()

    # Detect SSML vs plain text
    if text.strip().startswith("<speak>"):
        synthesis_input = texttospeech.SynthesisInput(ssml=text)
    else:
        synthesis_input = texttospeech.SynthesisInput(text=text)

    # Parse voice name for language code
    language_code = "-".join(voice_name.split("-")[:2])

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=getattr(texttospeech.AudioEncoding, audio_encoding),
        speaking_rate=speaking_rate,
        pitch=pitch,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    return response.audio_content


def get_cache_key(text: str, voice: str, rate: float) -> str:
    """Generate cache key for audio."""
    content = f"{text}:{voice}:{rate}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

### Features to Preserve

| Feature | Implementation |
|---------|----------------|
| **Audio caching** | Hash text+voice+rate → check cache before API call |
| **Streaming** | Return audio URL for frontend playback |
| **Download** | `/api/audio/{job_id}/download` endpoint unchanged |
| **Adaptive speed** | Map app's 1.5×-2.5× to Google's `speaking_rate` (0.25-4.0) |

### SSML for Punctuation Pauses

```xml
<speak>
  The quick brown fox<break time="300ms"/> jumps over the lazy dog<break time="500ms"/>
  This is a new sentence.
</speak>
```

### Speed Mapping

| App Speed | Google `speaking_rate` |
|-----------|------------------------|
| 1.0× | 1.0 |
| 1.5× | 1.5 |
| 2.0× | 2.0 |
| 2.5× | 2.5 |

Direct 1:1 mapping works within Google's 0.25-4.0 range.

### Error Handling

- **API quota exceeded** → Return 429 with clear message
- **Invalid voice** → Fallback to default voice, log warning
- **Network failure** → Return 503 with retry guidance
- **Invalid credentials** → Return 401 with setup instructions

### Files to Delete

- `backend/tts/coqui.py`
- `backend/tts/__init__.py` (if only re-exporting)
- OpenAI TTS references in `main.py`
- `TTS` package from `requirements.txt`
- `openai` package from `requirements.txt`

### New Dependencies

```
google-cloud-texttospeech>=2.14.0
```

---

## Part B: Documentation Overhaul

### New Structure

```
ReadMeLocal/
├── README.md                    # Project overview (rewritten)
├── CLAUDE.md                    # AI assistant guidance (updated)
├── docs/
│   ├── getting-started.md       # Quick start guide
│   ├── configuration.md         # Full settings.yaml reference
│   ├── api-reference.md         # All FastAPI endpoints
│   ├── architecture.md          # System design, data flow
│   └── plans/                   # Design documents
│       └── ...
```

### README.md Rewrite

**Current issues:**
- Features list outdated (says PDF "planned" but implemented)
- References Heroku/OpenAI (being removed)
- Project structure shows untracked files
- Roadmap phases outdated
- Large Coqui TTS section (being removed)

**New structure:**
1. Brief tagline and description
2. Key features (accurate)
3. Quick start (condensed, link to full guide)
4. Architecture diagram (simplified)
5. Configuration overview (link to full docs)
6. Development commands
7. Contributing
8. License

### New Documentation Files

#### `docs/getting-started.md`
- Prerequisites (Python, Node, Google Cloud account)
- Clone and setup
- Configure Google Cloud credentials
- Run the application
- First book import walkthrough

#### `docs/configuration.md`
- Complete `settings.yaml` reference
- Every setting explained with defaults
- Environment variables (`secrets.env`)
- Voice configuration examples

#### `docs/api-reference.md`
- All endpoints with:
  - Method and path
  - Request body schema
  - Response schema
  - Example curl commands
- Organized by domain (books, playback, TTS, annotations)

#### `docs/architecture.md`
- System overview diagram
- Component responsibilities
- Data flow for key operations
- Database schema
- File structure explanation

### CLAUDE.md Updates

- Remove Coqui/OpenAI references
- Update TTS section for Google Cloud
- Reflect current project state
- Update development commands if needed

---

## Implementation Phases

### Phase A: Google Cloud TTS Integration

1. Add `google-cloud-texttospeech` to `requirements.txt`
2. Create `backend/tts/google_tts.py`
3. Update `main.py` TTS endpoint
4. Update `config/settings.yaml` with Google voices
5. Update `config/secrets.env.template`
6. Remove Coqui/OpenAI code and dependencies
7. Update frontend voice selector
8. Test end-to-end

### Phase B: Documentation Overhaul

1. Rewrite `README.md`
2. Create `docs/getting-started.md`
3. Create `docs/configuration.md`
4. Create `docs/api-reference.md`
5. Create `docs/architecture.md`
6. Update `CLAUDE.md`

---

## Testing Strategy

### TTS Integration Tests
- Synthesis with default voice
- Synthesis with custom voice/speed
- Cache hit/miss verification
- Error handling (invalid voice, quota, network)
- SSML parsing

### Documentation Verification
- All code examples work
- All endpoints documented match implementation
- Configuration examples are valid YAML
- Links are not broken

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Google Cloud requires billing setup | Document clearly in getting-started |
| API costs for heavy usage | Aggressive caching, document pricing |
| Breaking existing workflows | Keep endpoint signatures stable |
| Missing edge cases in docs | Review against actual codebase |
