# Repository Guidelines

## Project Structure & Module Organization
This repository is a small Flask-based transcription app built around `faster-whisper`.

- `app.py`: main server, routes, model caching, upload handling, and streaming transcription.
- `templates/index.html`: single-page UI for configuring jobs and viewing results.
- `requirements.txt`: Python runtime dependencies.
- `uploads/`: temporary uploaded audio files created at runtime.
- `outputs/`: generated transcript files created at runtime.

Treat `uploads/` and `outputs/` as generated data; do not rely on them for source changes.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create and activate a local virtual environment.
- `pip install -r requirements.txt`: install Flask and transcription dependencies.
- `python3 app.py`: start the local server on `127.0.0.1:5050` with debug enabled.

There is no separate frontend build step; the UI is served from `templates/index.html` and uses CDN-hosted assets.

## Coding Style & Naming Conventions
- Use 4-space indentation in Python and keep functions focused and small.
- Follow Python naming conventions: `snake_case` for functions/variables, `UPPER_CASE` for module constants.
- Keep route handlers and helpers consistent with the existing style in `app.py`.
- In HTML, prefer clear IDs and descriptive labels that match backend form fields such as `audio_file` or `model_size`.

No formatter or linter configuration is committed yet, so match the current code style and keep diffs minimal.

## Testing Guidelines
There is no automated test suite in the repository yet. For changes, validate locally with targeted manual checks:

- start the server with `python3 app.py`
- upload a sample audio file through the UI
- confirm streaming output appears and `/download/<filename>` returns the transcript

If you add tests, prefer `pytest`, place them under `tests/`, and name files `test_<feature>.py`.

## Commit & Pull Request Guidelines
This repository currently has no commit history, so use short, imperative commit messages such as `Add upload validation` or `Refine transcript download flow`.

Pull requests should include a brief summary, manual test notes, and screenshots for UI changes. Link related issues when available and call out any dependency or runtime changes.

## Security & Configuration Tips
- Keep uploaded media and generated transcripts out of commits.
- Validate file-handling changes carefully; routes already protect against path traversal via `Path(...).name`.
- Large audio files are allowed up to 500 MB; preserve or document any limit changes.
