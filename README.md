# Whisper Damo — Flask 语音转写应用

一个基于 Flask 的本地语音转写 Web 应用，底层使用 faster-whisper，在浏览器中流式显示识别结果，并支持下载最终文本。

## 功能特点
- 上传音频（单文件最大约 500 MB）
- 在页面中选择模型大小与相关选项
- 转写过程中实时流式显示片段结果
- 任务完成后可从 `/download/<filename>` 下载最终转写文本
- 前端使用模板与 CDN 资源，无需单独构建步骤

## 快速开始（虚拟环境 venv）
- 创建与激活环境：`python3 -m venv .venv && source .venv/bin/activate`
- 安装依赖：`pip install -r requirements.txt`
- 运行服务：`python3 app.py`（默认访问 `http://127.0.0.1:5050`）

打开浏览器访问页面，上传音频文件，即可在界面中实时看到流式输出。完成后页面会提供下载链接以获取最终转写文本。

## Conda 快速开始
- 创建环境：`conda create -n whisper-damo -c conda-forge python=3.10 -y`
- 激活环境：`conda activate whisper-damo`
- 安装依赖：`pip install -r requirements.txt`
- 运行服务：`python3 app.py`（默认访问 `http://127.0.0.1:5050`）

提示：使用 `conda-forge` 渠道可获得较新的 Python 与构建工具。本应用的依赖在 Conda 环境内通过 `pip` 安装。

## 目录说明
- `app.py`：主服务与路由，上传处理与流式转写
- `templates/index.html`：单页 UI，配置转写任务与查看结果
- `requirements.txt`：运行时依赖
- `uploads/`：运行时上传的临时音频（已忽略）
- `outputs/`：运行时生成的转写文件（已忽略）
- `.github/workflows/ci.yml`：最小化 CI（仅语法检查）
- `CONTRIBUTING.md`：贡献指南
- `AGENTS.md`：仓库协作/代理说明

## 注意与安全
- 请勿提交运行时数据：`uploads/` 与 `outputs/` 已在 `.gitignore` 中忽略。
- 路由已通过 `Path(...).name` 防止路径遍历。
- 支持较大的音频文件（约 500 MB）。如需调整限制，请在代码或文档中说明。

## 手动验证
- 启动服务：`python3 app.py`
- 通过 UI 上传一段示例音频
- 确认页面出现流式输出
- 检查下载链接是否可返回正确的转写文本

## GPU 加速
Whisper（faster-whisper 基于 CTranslate2）与 SenseVoice 均可使用 GPU，以获得更高吞吐与更低延迟。

- Whisper（faster-whisper）
  - 设备：在页面中将 `device` 设为 `cuda`（或 `auto`）。
  - `compute_type` 建议：
    - GPU：`float16`（速度/精度均衡）或 `int8_float16`（更省显存）
    - CPU：`int8` 或 `int8_float32`
  - CTranslate2 GPU 轮子：若你将 `device=cuda` 但仍落回 CPU，大概率是安装了 CPU 版 CTranslate2。
    - 示例（按你的 CUDA 版本调整）：
      - `pip install -U ctranslate2 -f https://opennmt.net/CTranslate2/whl/cu118/`
    - 具体 CUDA 版本（如 cu121/cu124）与可用轮子以 CTranslate2 官方文档为准。

- SenseVoice（FunASR）
  - 设备：将 `sv_device` 设为 `cuda:0`（或在 UI 选择 GPU）。
  - 若报 `torch.cuda.is_available() == False`，请安装与你 CUDA 匹配的 PyTorch GPU 版本（参考 PyTorch 官网命令生成器）。

提示：显存不足时优先选择更小模型（如 `small`）或使用量化 `int8_float16`，并适当减小 `chunk_length`。

## 模型缓存与离线使用
- Whisper 模型由 Hugging Face Hub 缓存，默认路径：`~/.cache/huggingface/hub`。
  - 可通过设置环境变量自定义缓存位置：
    - `HF_HOME=/path/to/cache_root`（推荐）
    - 或 `HUGGINGFACE_HUB_CACHE` / `XDG_CACHE_HOME`
- 首次运行会自动下载模型。如需离线部署：
  1) 在有网环境运行一次以完成下载，或使用 `huggingface-cli download` 预下载；
  2) 将缓存目录拷贝到目标机器；
  3) 在目标机设置 `HF_HOME` 指向该缓存目录后再启动应用。
- 常见模型大小：`tiny` / `base` / `small` / `medium` / `large-v2` / `large-v3` / `distil-large-v3` 等。体积越大，精度更高但显存/内存与时间也更高。

## 性能调优建议
- Whisper 参数：
  - `beam_size`：1–3 可显著提速；更大提高精度但更慢。
  - `best_of`：解码候选数量，增大更准更慢；与 `beam_size` 共同影响速度。
  - `chunk_length`：20–30 秒通常能在流式与稳定之间取得平衡；显存吃紧时可减小。
  - `word_timestamps`：关闭可稍快；开启可获得词级时间戳。
  - `cpu_threads`：CPU 模式建议设为物理核数；`num_workers` 建议 1–2。
- VAD：`vad_filter=True` 并将 `min_silence_duration_ms` 设为 500–800ms，`hallucination_silence_threshold=2.0` 可抑制幻听片段。
- SenseVoice：`batch_size_s=60` 已在代码中设置为较稳健值；GPU 下可视资源适当增减。

## 常见问题排查
- “The device 'cuda' is not available”
  - 未安装 CTranslate2 的 GPU 版（Whisper）或未安装带 CUDA 的 PyTorch（SenseVoice）。
  - CUDA 驱动/版本不匹配。请使用与你系统 CUDA 版本匹配的轮子。
- 显存不足或 OOM
  - 换用更小模型（如 `small`），或使用 `compute_type=int8_float16`，降低 `beam_size`/`best_of`，减小 `chunk_length`。
- 下载模型过慢或无网
  - 参考“模型缓存与离线使用”，预下载并拷贝缓存；或设置更快镜像（如企业内部镜像）。

---
English version: see `README_EN.md`.
