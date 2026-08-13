import os
import uuid
from urllib.parse import urlparse

import yt_dlp

# 下载目录，可用环境变量覆盖
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")

# 支持的平台域名白名单（防 SSRF：仅允许访问这些域名，禁止内网/任意地址）
ALLOWED_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "facebook.com",
    "fb.watch",
    "instagram.com",
    "twitter.com",
    "x.com",
    "pinterest.com",
}

# 基于代码位置定位 cookie 文件，避免依赖进程工作目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIE_FILE = os.path.join(BASE_DIR, "cookies.txt")


class UnsupportedUrlError(Exception):
    """URL 不在支持范围内（协议不对 / 域名不在白名单 / 非法）。"""


def validate_url(url: str) -> None:
    """校验 URL：仅允许 http/https 且域名在白名单内。"""
    if not url or len(url) > 2048:
        raise UnsupportedUrlError("Invalid URL")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsupportedUrlError("Only http/https URLs are supported")

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise UnsupportedUrlError("Invalid URL")

    if not any(
        hostname == domain or hostname.endswith("." + domain)
        for domain in ALLOWED_DOMAINS
    ):
        raise UnsupportedUrlError("This website is not supported")


def _hostname(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _is_youtube(hostname: str) -> bool:
    return hostname == "youtube.com" or hostname.endswith(".youtube.com") or hostname == "youtu.be"


def get_video_info(url: str) -> dict:
    """解析并下载视频，返回标题/缩略图/本地下载路径。"""
    validate_url(url)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    options = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filepath,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "socket_timeout": 60,
        "no_color": True,
    }

    # 仅 YouTube 且 cookie 文件存在时启用登录态
    if _is_youtube(_hostname(url)) and os.path.exists(COOKIE_FILE):
        options["cookiefile"] = COOKIE_FILE

    # 代理可选，通过 PROXY_URL 环境变量配置（如 http://127.0.0.1:10808）
    proxy = os.environ.get("PROXY_URL")
    if proxy:
        options["proxy"] = proxy

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

    return {
        "title": info.get("title") or "Video",
        "thumbnail": info.get("thumbnail"),
        "download_url": "/downloads/" + filename,
    }
