# ── Stage: builder ──────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# 所有依赖均有预编译 wheel，无需 build-essential
# 使用清华 PyPI 镜像，避免国内网络问题和跨平台哈希冲突
# requirements-docker.txt 仅含直接依赖，让 pip 在 Linux 上解析正确的 wheel
COPY requirements-docker.txt .
RUN --network=host pip install --no-cache-dir --prefix=/install \
    -r requirements-docker.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn


# ── Stage: runtime ───────────────────────────────────────────
FROM python:3.10-slim

LABEL maintainer="whisper-damo"
LABEL description="Speech transcription server: Whisper / SenseVoice / Azure"

WORKDIR /app

# 运行时系统依赖：使用 host 网络确保 apt 可访问（绕过 Docker DNS 问题）
RUN --network=host apt-get update && apt-get install -y --no-install-recommends \
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
