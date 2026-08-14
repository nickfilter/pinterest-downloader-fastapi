# ---------- 构建阶段：安装 Python 依赖 ----------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# 先拷贝依赖清单并安装，充分利用 Docker 层缓存（依赖变更频率远低于业务代码）
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---------- 运行阶段 ----------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# ffmpeg：yt-dlp 合并视频/音频必需；ca-certificates：HTTPS 请求必需
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 拷贝构建阶段安装好的依赖
COPY --from=builder /install /usr/local

# 拷贝业务代码
COPY . .

# 预创建下载目录（main.py 启动时 StaticFiles 挂载要求目录存在）
# 创建非 root 运行用户，并赋予 /app 写权限（stats.db / cookies.txt / ads.txt / downloads 均需写入）
RUN mkdir -p /app/downloads \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# 下载文件持久化卷（stats.db / cookies.txt 建议通过 -v 挂载持久化，见 README）
VOLUME ["/app/downloads"]

EXPOSE 8000

# 健康检查：探测首页
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)"

# 单 worker：api_guard 限流为内存态，多 worker 需额外 Redis 支持
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
