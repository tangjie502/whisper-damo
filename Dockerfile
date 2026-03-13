# ── Stage: builder ──────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# 换用阿里云 apt 镜像（国内服务器必须）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn


# ── Stage: runtime ───────────────────────────────────────────
FROM python:3.10-slim

LABEL maintainer="whisper-damo"
LABEL description="Speech transcription server: Whisper / SenseVoice / Azure"

WORKDIR /app

# 运行时系统依赖：ffmpeg (音频解码) + libsndfile (librosa)
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 拷贝已安装的 Python 包
COPY --from=builder /install /usr/local

# 拷贝应用代码
COPY app.py .
COPY templates/ templates/

# 运行时目录（用 volume 挂载）
RUN mkdir -p uploads outputs

# 非 root 用户运行（安全最佳实践）
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5050

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5050/')" || exit 1

# 生产模式：Gunicorn 单进程多线程（保持模型缓存共享）
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:5050", \
     "--workers", "1", \
     "--threads", "8", \
     "--timeout", "600", \
     "--worker-class", "gthread", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
