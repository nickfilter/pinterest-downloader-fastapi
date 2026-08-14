import glob
import logging
import os
import re
import socket
import urllib.request
import uuid
from urllib.parse import urlparse

import yt_dlp

from services import stats

logger = logging.getLogger(__name__)

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


class VideoExtractionError(Exception):
    """无法从该链接提取到可下载内容（非视频、被平台拦截等）。"""


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


def check_connectivity(url: str) -> None:
    """下载前快速探测目标平台连通性；不通则立即抛错，避免等待 yt-dlp 长超时。

    仅做 DNS 解析 + TCP 连接（5 秒超时），不做 TLS 握手，开销极小。
    """
    hostname = _hostname(url)
    if not hostname:
        return
    # 配置了代理时跳过直连预检：直连不通不代表代理不通，交给 yt-dlp 走代理
    if _effective_proxy():
        return
    try:
        addr = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)[0][4][0]
        with socket.create_connection((addr, 443), timeout=5):
            pass
    except socket.timeout:
        raise VideoExtractionError(
            "Server cannot reach this platform (network timeout). "
            "Please check the server's outbound network or configure a proxy."
        ) from None
    except socket.gaierror:
        raise VideoExtractionError(
            "Server cannot reach this platform (DNS resolution failed). "
            "Please check the server's network configuration."
        ) from None
    except OSError:
        raise VideoExtractionError(
            "Server cannot reach this platform (connection failed). "
            "Please check the server's outbound network or configure a proxy."
        ) from None


def _effective_proxy() -> str | None:
    """代理配置：后台设置优先，其次环境变量 PROXY_URL；均无则返回 None。"""
    proxy = stats.get_setting("proxy_url", "").strip()
    if not proxy:
        proxy = os.environ.get("PROXY_URL", "")
    return proxy or None


def sync_cookie_file() -> bool:
    """确保 cookies.txt 与后台配置一致：配置非空则写入文件，为空则删除。"""
    cookies_text = stats.get_setting("cookies_text", "").strip()
    if not cookies_text:
        if os.path.exists(COOKIE_FILE):
            try:
                os.remove(COOKIE_FILE)
            except OSError:
                logger.warning("Failed to remove cookie file %s", COOKIE_FILE)
        return False
    try:
        current = ""
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                current = f.read()
        if current != cookies_text:
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                f.write(cookies_text)
    except OSError:
        logger.warning("Failed to write cookie file %s", COOKIE_FILE)
        return False
    return True


def _base_options() -> dict:
    """公共选项：Cookie（后台配置，对所有平台生效）与可选代理。"""
    options = {
        "noplaylist": True,
        "socket_timeout": 15,
        "no_color": True,
    }

    if sync_cookie_file():
        options["cookiefile"] = COOKIE_FILE

    proxy = _effective_proxy()
    if proxy:
        options["proxy"] = proxy

    return options


def _first_thumbnail(info: dict):
    thumb = info.get("thumbnail")
    if isinstance(thumb, list):
        return thumb[0] if thumb else None
    return thumb


def _build_opener():
    """构建 urllib opener，可选挂载代理（与 yt-dlp 同一套代理配置）。"""
    handlers = []
    proxy = _effective_proxy()
    if proxy:
        handlers.append(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
    return urllib.request.build_opener(*handlers)


def _http_get(url: str, timeout: int = 20):
    """抓取页面文本；失败返回 None。"""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with _build_opener().open(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "ignore")
    except Exception:
        logger.warning("HTTP GET failed for url=%s", url)
        return None


def _download_file(url: str, target: str, timeout: int = 60) -> None:
    """下载文件到本地（走代理）。"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    with _build_opener().open(req, timeout=timeout) as resp, open(
        target, "wb"
    ) as f:
        f.write(resp.read())


def _fetch_pinterest_image_url(pin_url: str) -> str | None:
    """从 Pinterest 页面中提取原图 URL（i.pinimg.com/originals/...）。"""
    html = _http_get(pin_url)
    if not html:
        return None
    m = re.search(r'"url":"(https://i\.pinimg\.com/originals/[^"]+)"', html)
    if not m:
        m = re.search(r"https://i\.pinimg\.com/originals/[^\"\\\s]+", html)
    if not m:
        return None
    return m.group(1).replace("\\/", "/").replace("\\u002F", "/")


def _download_pinterest_image(pin_url: str, stem: str) -> dict | None:
    """Pinterest 图片 Pin 回退：抓取页面并下载原图。失败返回 None。"""
    try:
        image_url = _fetch_pinterest_image_url(pin_url)
        if not image_url:
            logger.warning("No image URL found for pin url=%s", pin_url)
            return None
        ext = os.path.splitext(image_url)[1] or ".jpg"
        target = os.path.join(DOWNLOAD_DIR, stem + ext)
        _download_file(image_url, target)
        local = "/downloads/" + stem + ext
        return {
            "title": "Pinterest Image",
            "thumbnail": local,
            "video_url": None,
            "audio_url": None,
            "image_url": local,
        }
    except Exception:
        logger.warning("Pinterest image fallback failed for url=%s", pin_url)
        return None


def _friendly_error(msg: str) -> str:
    """把 yt-dlp 原始报错转换成用户可读的提示。"""
    if "No video formats found" in msg:
        return "No video found in this link. Make sure the link points to a video."
    if "Sign in to confirm you're not a bot" in msg or "HTTP Error 403" in msg:
        return "Access denied by the platform (bot check). Try another link or refresh cookies."
    if "Unsupported URL" in msg or "not a valid URL" in msg:
        return "This URL is not supported."
    if any(
        k in msg.lower()
        for k in (
            "timed out",
            "unable to connect",
            "connection",
            "getaddrinfo",
            "name or service not known",
            "network is unreachable",
        )
    ):
        return (
            "Server cannot reach this platform (network issue). "
            "Check the server's outbound network or configure a proxy."
        )
    return "Download failed. Please try again."


def get_video_info(url: str) -> dict:
    """解析并下载视频，同时提供缩略图与音频下载地址。"""
    validate_url(url)
    check_connectivity(url)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    stem = str(uuid.uuid4())
    video_path = os.path.join(DOWNLOAD_DIR, stem + ".mp4")
    audio_path = os.path.join(DOWNLOAD_DIR, stem + "_audio.%(ext)s")
    thumb_path = os.path.join(DOWNLOAD_DIR, stem + ".jpg")

    # 1) 下载视频
    video_options = {
        **_base_options(),
        "format": "best[ext=mp4]/best",
        "outtmpl": video_path,
        "merge_output_format": "mp4",
    }
    try:
        with yt_dlp.YoutubeDL(video_options) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        logger.warning("yt-dlp failed for url=%s: %s", url, e)
        err_msg = str(e)
        # Pinterest 图片 Pin：无视频格式时回退为原图下载
        if _hostname(url).endswith("pinterest.com") and (
            "No video formats found" in err_msg
        ):
            image_result = _download_pinterest_image(url, stem)
            if image_result:
                return image_result
        raise VideoExtractionError(_friendly_error(err_msg)) from e

    video_url = "/downloads/" + stem + ".mp4"

    # 2) 下载音频（优先原生 m4a，其次任意最佳音频）；失败不影响主流程
    audio_url = None
    try:
        audio_options = {
            **_base_options(),
            "format": "bestaudio[ext=m4a]/bestaudio",
            "outtmpl": audio_path,
        }
        with yt_dlp.YoutubeDL(audio_options) as ydl:
            ydl.extract_info(url, download=True)
        audio_files = glob.glob(os.path.join(DOWNLOAD_DIR, stem + "_audio.*"))
        if audio_files:
            audio_url = "/downloads/" + os.path.basename(audio_files[0])
    except Exception:
        logger.warning("Audio download failed for url=%s", url)

    # 3) 缩略图本地化；失败则回退为远程 URL
    thumbnail = _first_thumbnail(info)
    thumb_url = thumbnail
    if thumbnail:
        try:
            _download_file(thumbnail, thumb_path)
            thumb_url = "/downloads/" + stem + ".jpg"
        except Exception:
            logger.warning("Thumbnail download failed for url=%s", url)

    return {
        "title": info.get("title") or "Video",
        "thumbnail": thumb_url or "",
        "video_url": video_url,
        "audio_url": audio_url,
        "image_url": None,
    }
