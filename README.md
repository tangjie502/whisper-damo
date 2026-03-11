# Whisper Damo — Flask Transcription App

A small Flask app that wraps faster-whisper for local audio transcription with streaming output and simple downloads.

## Features
- Upload audio (large files supported up to ~500MB)
- Choose model size and options via the UI
- Stream partial results in the browser while transcribing
- Download the final transcript from `/download/<filename>`

## Quick Start
- Create venv: `python3 -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run server: `python3 app.py` (serves at `http://127.0.0.1:5050`)

Open the app in your browser, upload an audio file, and watch the streaming transcript. When it finishes, use the provided link to download the transcript.

## Notes
- Generated data folders `uploads/` and `outputs/` are ignored (see `.gitignore`).
- The UI is a single page at `templates/index.html` and uses CDN assets; no separate build step.
- Validate locally using the steps above and a sample audio file.

## Repository Guidelines
- Keep changes small, focused, and consistent with existing style in `app.py`.
- Prefer descriptive IDs/labels in HTML matching backend fields (e.g., `audio_file`, `model_size`).

---
If you want CI, tests, or a deployment guide added, open an issue or let me know.
