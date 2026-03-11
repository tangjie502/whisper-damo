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

---
English version: see `README_EN.md`.
