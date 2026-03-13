import json
import threading
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, request, render_template, Response, send_file
from faster_whisper import WhisperModel

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB
BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────
# 后台清理线程
# ──────────────────────────────────────────

def cleanup_old_outputs():
    """后台线程：定期清理 outputs/ 中超过 2 小时的文件（含空文件）。"""
    while True:
        try:
            now = time.time()
            for f in OUTPUTS_DIR.iterdir():
                if f.is_file() and (now - f.stat().st_mtime) > 7200:
                    f.unlink(missing_ok=True)
        except Exception:
            pass
        time.sleep(600)  # 每 10 分钟扫一次


# 启动时清理历史空文件
try:
    for _f in OUTPUTS_DIR.iterdir():
        if _f.is_file() and _f.stat().st_size == 0:
            _f.unlink(missing_ok=True)
except Exception:
    pass

_cleanup_thread = threading.Thread(target=cleanup_old_outputs, daemon=True)
_cleanup_thread.start()


# ──────────────────────────────────────────
# Whisper 模型缓存
# ──────────────────────────────────────────
_whisper_cache: dict = {}
_whisper_lock = threading.Lock()


def get_whisper_model(model_size: str, device: str, compute_type: str,
                      cpu_threads: int, num_workers: int) -> WhisperModel:
    """返回缓存的 Whisper 模型实例；参数变化时才重新加载。"""
    key = (model_size, device, compute_type, cpu_threads, num_workers)
    with _whisper_lock:
        if key not in _whisper_cache:
            _whisper_cache.clear()
            _whisper_cache[key] = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=cpu_threads,
                num_workers=num_workers,
            )
        return _whisper_cache[key]


# ──────────────────────────────────────────
# SenseVoice 模型缓存
# ──────────────────────────────────────────
_sv_cache: dict = {}
_sv_lock = threading.Lock()


def get_sv_model(device: str):
    """返回缓存的 SenseVoice 模型实例；device 变化时才重新加载。"""
    key = device
    with _sv_lock:
        if key not in _sv_cache:
            # 延迟导入，避免未安装时影响 Whisper 功能启动
            from funasr import AutoModel
            _sv_cache.clear()
            _sv_cache[key] = AutoModel(
                model="iic/SenseVoiceSmall",
                trust_remote_code=False,   # 使用 funasr 内置版本，无需下载 model.py
                vad_model="fsmn-vad",
                vad_kwargs={"max_single_segment_time": 30000},
                device=device,
            )
        return _sv_cache[key]


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────

def to_int(data, key, default_value):
    value = data.get(key, default_value)
    if value in (None, ""):
        return default_value
    return int(value)


def to_float(data, key, default_value):
    value = data.get(key, default_value)
    if value in (None, ""):
        return default_value
    return float(value)


def to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def build_output_path(original_filename: str) -> Path:
    """在服务器临时目录中创建转写结果文件路径。"""
    stem = Path(original_filename).stem or "result"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return OUTPUTS_DIR / f"{stem}_{timestamp}_{unique_id}.txt"


def save_upload(uploaded) -> Path:
    """保存上传文件到 uploads/ 临时目录并返回路径。"""
    uploads_dir = BASE_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(uploaded.filename).name
    temp_path = uploads_dir / f"upload_{int(time.time() * 1000)}_{safe_name}"
    uploaded.save(temp_path)
    return temp_path


# ──────────────────────────────────────────
# 路由
# ──────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/download/<filename>", methods=["GET"])
def download_result(filename):
    """提供转写结果文件下载（文件保留 2 小时后由后台定时清理）。"""
    safe_filename = Path(filename).name
    file_path = OUTPUTS_DIR / safe_filename
    if not file_path.exists() or not file_path.is_relative_to(OUTPUTS_DIR):
        return Response("文件不存在或已过期", status=404)
    if file_path.stat().st_size == 0:
        file_path.unlink(missing_ok=True)
        return Response("转写结果为空，请重新转写", status=404)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_filename,
        mimetype="text/plain; charset=utf-8",
    )


# ── Whisper 转写路由 ──────────────────────

@app.route("/transcribe_stream", methods=["POST"])
def transcribe_stream():
    uploaded = request.files.get("audio_file")
    if not uploaded or not uploaded.filename:
        return Response(
            json.dumps({"type": "error", "error": "未选择音频文件"}, ensure_ascii=False) + "\n",
            mimetype="application/x-ndjson",
        )

    temp_input_path = save_upload(uploaded)

    request_data = {
        "uploaded_filename": uploaded.filename,
        "temp_input_path": str(temp_input_path),
        "model_size": (request.form.get("model_size") or "medium").strip(),
        "device": (request.form.get("device") or "cpu").strip(),
        "compute_type": (request.form.get("compute_type") or "int8").strip(),
        "language": (request.form.get("language") or "zh").strip(),
        "cpu_threads": to_int(request.form, "cpu_threads", 8),
        "num_workers": to_int(request.form, "num_workers", 1),
        "beam_size": to_int(request.form, "beam_size", 5),
        "best_of": to_int(request.form, "best_of", 5),
        "temperature": to_float(request.form, "temperature", 0.0),
        "chunk_length": int(request.form.get("chunk_length")) if request.form.get("chunk_length") not in (None, "") else None,
        "hallucination_silence_threshold": to_float(request.form, "hallucination_silence_threshold", 2.0),
        "min_silence_duration_ms": to_int(request.form, "min_silence_duration_ms", 500),
        "vad_filter": to_bool(request.form.get("vad_filter"), True),
        "word_timestamps": to_bool(request.form.get("word_timestamps"), True),
        "condition_on_previous_text": to_bool(request.form.get("condition_on_previous_text"), False),
        "initial_prompt": (request.form.get("initial_prompt") or "").strip() or None,
        "hotwords": (request.form.get("hotwords") or "").strip() or None,
    }

    return Response(generate_whisper(request_data), mimetype="application/x-ndjson")


def generate_whisper(data):
    """Whisper 流式生成转写结果（NDJSON 格式）。"""
    temp_path = Path(data["temp_input_path"])
    output_path = build_output_path(data["uploaded_filename"])

    try:
        yield json.dumps(
            {
                "type": "start",
                "message": "开始加载模型并转写",
                "output_file": str(output_path),
            },
            ensure_ascii=False,
        ) + "\n"

        model = get_whisper_model(
            data["model_size"],
            data["device"],
            data["compute_type"],
            data["cpu_threads"],
            data["num_workers"],
        )

        transcribe_kwargs = {
            "language": data["language"],
            "beam_size": data["beam_size"],
            "best_of": data["best_of"],
            "temperature": data["temperature"],
            "vad_filter": data["vad_filter"],
            "vad_parameters": {"min_silence_duration_ms": data["min_silence_duration_ms"]},
            "condition_on_previous_text": data["condition_on_previous_text"],
            "word_timestamps": data["word_timestamps"],
            "hallucination_silence_threshold": data["hallucination_silence_threshold"],
        }

        if data["chunk_length"] is not None:
            transcribe_kwargs["chunk_length"] = data["chunk_length"]
        if data["initial_prompt"]:
            transcribe_kwargs["initial_prompt"] = data["initial_prompt"]
        if data["hotwords"]:
            transcribe_kwargs["hotwords"] = data["hotwords"]

        segments, info = model.transcribe(str(temp_path), **transcribe_kwargs)

        with output_path.open("w", encoding="utf-8") as f:
            for segment in segments:
                text = (segment.text or "").strip()
                if not text:
                    continue

                if data["word_timestamps"]:
                    line = f"[{segment.start:.2f}-{segment.end:.2f}] {text}"
                else:
                    line = text

                f.write(line + "\n")
                f.flush()

                yield json.dumps(
                    {
                        "type": "segment",
                        "text": line,
                        "output_file": str(output_path),
                    },
                    ensure_ascii=False,
                ) + "\n"

        if output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            yield json.dumps(
                {"type": "error", "error": "转写结果为空，请检查音频文件是否有效。"},
                ensure_ascii=False,
            ) + "\n"
            return

        download_url = f"/download/{output_path.name}"
        yield json.dumps(
            {
                "type": "done",
                "download_url": download_url,
                "filename": output_path.name,
                "info": {
                    "language": getattr(info, "language", ""),
                    "language_probability": getattr(info, "language_probability", ""),
                },
            },
            ensure_ascii=False,
        ) + "\n"

    except Exception as e:
        yield json.dumps(
            {
                "type": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
            ensure_ascii=False,
        ) + "\n"
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ── SenseVoice 转写路由 ───────────────────

@app.route("/transcribe_stream_sv", methods=["POST"])
def transcribe_stream_sv():
    uploaded = request.files.get("audio_file")
    if not uploaded or not uploaded.filename:
        return Response(
            json.dumps({"type": "error", "error": "未选择音频文件"}, ensure_ascii=False) + "\n",
            mimetype="application/x-ndjson",
        )

    temp_input_path = save_upload(uploaded)

    request_data = {
        "uploaded_filename": uploaded.filename,
        "temp_input_path": str(temp_input_path),
        "language": (request.form.get("sv_language") or "auto").strip(),
        "device": (request.form.get("sv_device") or "cpu").strip(),
        "use_itn": to_bool(request.form.get("sv_use_itn"), True),
    }

    return Response(generate_sensevoice(request_data), mimetype="application/x-ndjson")


def generate_sensevoice(data):
    """SenseVoice 流式生成转写结果（NDJSON 格式，与 Whisper 格式兼容）。"""
    temp_path = Path(data["temp_input_path"])
    output_path = build_output_path(data["uploaded_filename"])

    try:
        yield json.dumps(
            {
                "type": "start",
                "message": "正在加载 SenseVoice 模型...",
                "output_file": str(output_path),
            },
            ensure_ascii=False,
        ) + "  " * 1024 + "\n"
        import librosa
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
        from funasr import AutoModel
        import re

        model = get_sv_model(data["device"])
        
        # Load VAD model separately or just let FunASR handle it by passing the audio twice?
        # A simpler approach: use the same SenseVoice model's built-in VAD but disable merge to get chunks.
        # However, FunASR SenseVoice `merge_vad=False` returns a single text. 
        # So we explicitly load FSMN-VAD to get timestamps:
        vad_model = AutoModel(model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', device=data["device"])
        vad_res = vad_model.generate(input=str(temp_path))
        
        if not vad_res or 'value' not in vad_res[0]:
            output_path.unlink(missing_ok=True)
            yield json.dumps(
                {"type": "error", "error": "无法分析音频结构，请检查音频文件。"},
                ensure_ascii=False,
            ) + "  " * 1024 + "\n"
            return
            
        segments_timing = vad_res[0]['value']
        audio, sr = librosa.load(str(temp_path), sr=16000)

        all_emotion_labels = set()
        all_event_labels = set()
        detected_lang = data["language"]

        # If it's empty
        if not segments_timing:
            output_path.unlink(missing_ok=True)
            yield json.dumps(
                {"type": "error", "error": "转写结果为空，请检查音频文件是否有效。"},
                ensure_ascii=False,
            ) + "  " * 1024 + "\n"
            return

        with output_path.open("w", encoding="utf-8") as f:
            for start_ms, end_ms in segments_timing:
                start_samp = int((start_ms / 1000.0) * sr)
                end_samp = int((end_ms / 1000.0) * sr)
                chunk = audio[start_samp:end_samp]
                
                # If chunk is too short, skip
                if len(chunk) < 400:
                    continue

                res = model.generate(
                    input=chunk, 
                    cache={}, 
                    language=data["language"], 
                    use_itn=data["use_itn"], 
                    ban_emo_unk=False
                )
                
                if not res:
                    continue
                    
                raw_text = res[0].get("text", "")
                clean_text = rich_transcription_postprocess(raw_text).strip()
                
                if not clean_text:
                    continue

                # 提取情感/事件/语言标签
                lang_match = re.search(r"<\|(zh|en|ja|ko|yue|nospeech)\|>", raw_text)
                if lang_match:
                    detected_lang = lang_match.group(1)

                emotion_labels = re.findall(r"<\|(HAPPY|SAD|ANGRY|FEARFUL|DISGUSTED|SURPRISED|NEUTRAL)\|>", raw_text)
                event_labels = re.findall(r"<\|(BGM|Laughter|Applause|Cry|Sneeze|Breath|Cough)\|>", raw_text)
                all_emotion_labels.update(emotion_labels)
                all_event_labels.update(event_labels)
                
                start_s = start_ms / 1000.0
                end_s = end_ms / 1000.0
                
                # Formatted text matching Whisper style
                formatted_line = f"[{start_s:.2f}-{end_s:.2f}] {clean_text}"
                
                f.write(formatted_line + "\n")
                yield json.dumps(
                    {
                        "type": "segment",
                        "text": formatted_line,
                        "output_file": str(output_path),
                    },
                    ensure_ascii=False,
                ) + "  " * 1024 + "\n"

        if output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            yield json.dumps(
                {"type": "error", "error": "转写结果为空，请检查音频文件是否有效。"},
                ensure_ascii=False,
            ) + "  " * 1024 + "\n"
            return

        emotion_display = ", ".join(all_emotion_labels)
        event_display = ", ".join(all_event_labels)

        download_url = f"/download/{output_path.name}"
        yield json.dumps(
            {
                "type": "done",
                "download_url": download_url,
                "filename": output_path.name,
                "info": {
                    "language": detected_lang,
                    "language_probability": "",
                    "emotion": emotion_display,
                    "event": event_display,
                },
            },
            ensure_ascii=False,
        ) + "  " * 1024 + "\n"


    except Exception as e:
        yield json.dumps(
            {
                "type": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
            ensure_ascii=False,
        ) + "\n"
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True, threaded=True)
