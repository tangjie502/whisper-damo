# Contributing

Thanks for your interest in improving this Flask + faster-whisper app!
This guide keeps contributions smooth and consistent.

## Setup
- Python 3.10+ recommended.
- Create a venv and install deps:
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run locally: `python3 app.py` (serves `http://127.0.0.1:5050`).

## Development Guidelines
- Keep functions small and focused; 4-space indentation.
- Use `snake_case` for functions/variables and `UPPER_CASE` for constants.
- Keep route handlers and helpers consistent with the style in `app.py`.
- In HTML, prefer clear IDs/labels that match backend fields (e.g., `audio_file`, `model_size`).

## Generated Data
- Do not commit runtime data. Folders `uploads/` and `outputs/` are ignored.
- Large files (audio up to ~500MB) are allowed at runtime but should never be committed.

## Commit & PRs
- Use short, imperative commit messages (e.g., `Add upload validation`).
- Open PRs against `main` and include:
  - Brief summary of changes and rationale.
  - Manual test notes (steps + result) and screenshots for UI changes.
  - Mention any dependency or runtime changes.

## Manual Testing
- Start the server with `python3 app.py`.
- Upload a sample audio file through the UI.
- Confirm streaming output appears and `/download/<filename>` returns the transcript.

## CI
- A minimal CI runs Python syntax checks; it doesn’t install heavy audio/ML deps.
- If you add tests, prefer `pytest` under `tests/` with files like `test_<feature>.py`.

## Security
- Uploaded media and generated transcripts must not be committed.
- File handling should use `Path(...).name` to avoid path traversal.

## Questions
- Open an issue or start a discussion with context, logs, and steps to reproduce.

