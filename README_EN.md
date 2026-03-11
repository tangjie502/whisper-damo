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

## Conda Quick Start
- Create env: `conda create -n whisper-damo -c conda-forge python=3.10 -y`
- Activate: `conda activate whisper-damo`
- Install deps: `pip install -r requirements.txt`
- Run server: `python3 app.py` (serves at `http://127.0.0.1:5050`)

Tip: Using the `conda-forge` channel helps ensure recent Python and build tools. All app dependencies are installed via `pip` inside the Conda env.

## Notes
- Generated data folders `uploads/` and `outputs/` are ignored (see `.gitignore`).
- The UI is a single page at `templates/index.html` and uses CDN assets; no separate build step.
- Validate locally using the steps above and a sample audio file.

## Repository Guidelines
- Keep changes small, focused, and consistent with existing style in `app.py`.
- Prefer descriptive IDs/labels in HTML matching backend fields (e.g., `audio_file`, `model_size`).

## GPU Acceleration
Both Whisper (via faster-whisper/CTranslate2) and SenseVoice can use GPU for higher throughput and lower latency.

- Whisper (faster-whisper)
  - Device: set `device=cuda` (or `auto`) in the UI.
  - Recommended `compute_type`:
    - GPU: `float16` (balanced) or `int8_float16` (saves VRAM)
    - CPU: `int8` or `int8_float32`
  - CTranslate2 GPU wheels: if `device=cuda` still runs on CPU, you likely installed a CPU-only wheel.
    - Example (adjust to your CUDA version):
      - `pip install -U ctranslate2 -f https://opennmt.net/CTranslate2/whl/cu118/`
    - Check CTranslate2 docs for available CUDA variants (e.g., cu121/cu124).

- SenseVoice (FunASR)
  - Device: set `sv_device=cuda:0` (or choose GPU in the UI).
  - If `torch.cuda.is_available() == False`, install a PyTorch build matching your CUDA (see pytorch.org).

Tip: When VRAM is tight, choose a smaller model (e.g., `small`), use `int8_float16`, and/or reduce `chunk_length`.

## Model Cache & Offline
- Whisper models are cached via Hugging Face Hub, default: `~/.cache/huggingface/hub`.
  - Customize cache via env vars:
    - `HF_HOME=/path/to/cache_root` (recommended)
    - or `HUGGINGFACE_HUB_CACHE` / `XDG_CACHE_HOME`
- First run downloads models automatically. For offline deployment:
  1) Run once online to complete downloads, or prefetch via `huggingface-cli download`.
  2) Copy the cache directory to the target machine.
  3) Set `HF_HOME` on the target to point to that cache, then start the app.
- Common sizes: `tiny` / `base` / `small` / `medium` / `large-v2` / `large-v3` / `distil-large-v3`.

## Performance Tuning
- Whisper parameters:
  - `beam_size`: 1–3 speeds up; larger improves accuracy but slows down.
  - `best_of`: increases hypothesis search; better but slower; interacts with `beam_size`.
  - `chunk_length`: 20–30s balances streaming and stability; reduce if memory-bound.
  - `word_timestamps`: off is slightly faster; on provides word-level timestamps.
  - `cpu_threads`: for CPU use physical cores; `num_workers`: usually 1–2.
- VAD: keep `vad_filter=True`; try `min_silence_duration_ms=500–800` and `hallucination_silence_threshold=2.0` to reduce hallucinations.
- SenseVoice: `batch_size_s=60` is a robust default; adjust with GPU resources.

## Troubleshooting
- “The device 'cuda' is not available”
  - Install CTranslate2 GPU wheel (Whisper) or CUDA-enabled PyTorch (SenseVoice).
  - Ensure CUDA toolkit/driver versions match the wheel you install.
- Out of memory (VRAM/RAM)
  - Use a smaller model (e.g., `small`), pick `int8_float16`, reduce `beam_size`/`best_of`, lower `chunk_length`.
- Slow or offline model downloads
  - See “Model Cache & Offline”; pre-download and copy cache, or use a faster/internal mirror.

---
Chinese version: see `README.md`.

---
If you want CI, tests, or a deployment guide added, open an issue or let me know.
