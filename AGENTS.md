# Repository Guidelines

## Project Structure & Module Organization
- `frontend/`: Chrome extension UI and RSVP reader. Source lives in `frontend/src`; static assets in `frontend/public` (place `manifest.json`, icons, and HTML shells here).
- `backend/`: Local FastAPI service that prepares text, computes RSVP timing, and brokers events via StreamKit (Python pub-sub).
- `config/`: Runtime settings and secrets templates. Copy `config/secrets.env.template` to `config/secrets.env` and keep it out of git.
- `cache/`, `db/`: Runtime artifacts; do not commit.
- `cloud/`: Optional remote services; not required for the local-first speed reader.

## Build, Test, and Development Commands
- `cd frontend && npm install` - install UI dependencies.
- `npm start` - run the UI dev server.
- `npm run electron-dev` - optional local dev shell while extension packaging evolves.
- `npm test` - run React tests.
- `npm run build` - create production assets for extension packaging.
- `cd backend && python -m venv venv && source venv/bin/activate` - create/activate venv.
- `pip install -r requirements.txt` - install backend deps.
- `uvicorn main:app --reload --host 127.0.0.1 --port 5000` - run the local API.
- `pytest` - run backend tests.

## Coding Style & Naming Conventions
- JavaScript/React: 2-space indentation, semicolons, and file-level formatting consistent with existing code.
- Python: 4-space indentation; format with `black .` in `backend/`.
- React components in PascalCase (e.g., `ReaderPanel`), hooks prefixed with `use`, CSS classes in kebab-case.
- Python modules and functions in snake_case.

## Testing Guidelines
- Frontend: `react-scripts` tests via `npm test`; place tests in `frontend/src` and name files `*.test.js`.
- Backend: `pytest` with tests in `backend/tests` named `test_*.py`.
- Focus coverage on RSVP timing logic, word chunking, and pause rules.

## Commit & Pull Request Guidelines
- Commit messages should follow the existing pattern: `Phase N: <short summary>`.
- PRs should include a clear description, tests run, and screenshots/GIFs for UI changes.
- Call out any config or StreamKit topic changes explicitly.

## Architecture Overview
Text is extracted and tokenized in the backend, then an RSVP engine calculates per-word timing based on WPM and pause rules. The backend emits reading events over StreamKit; the frontend subscribes and renders each word at a fixed focal point while handling play/pause, speed, and chunk-size controls.
