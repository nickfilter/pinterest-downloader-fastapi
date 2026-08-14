"""Cookie 有效性检测与 Cookie API 对接更新。

- 检测：用当前配置的 Cookie 对指定平台做 HTTP 探测 + yt-dlp 提取验证，
  判断 Cookie 是否有效（是否过期 / 被平台拦截）。
- 更新：从外部 Cookie API 拉取最新 Cookie（JSON 或纯文本），保存到后台配置
  并同步 cookies.txt。
- 自动更新：后台可配置自动更新周期（小时），启动后按周期拉取。
"""
import asyncio
import json
import logging
import time
import urllib.error
import urllib.request

import yt_dlp

from services import downloader, stats

logger = logging.getLogger(__name__)

# 各平台 HTTP 探测地址（用于快速判断平台是否放行）
HTTP_PROBE_URLS = {
    "youtube": "https://www.youtube.com/",
    "instagram": "https://www.instagram.com/",
    "pinterest": "https://www.pinterest.com/",
    "tiktok": "https://www.tiktok.com/",
    "facebook": "https://www.facebook.com/",
    "twitter": "https://x.com/",
}

# 需要 yt-dlp 深度验证（走真实提取流程）的平台及其公开测试视频 URL
YDL_PROBE_URLS = {
    "youtube": "https://www.youtube.com/watch?v=BaW_jenozKc",
    "instagram": "https://www.instagram.com/reel/CGaKJebAWfS/",
}

COOKIE_MAX_LENGTH = 50000  # 与后台保存上限一致


def _no_cookie_result(platform: str) -> dict:
    return {
        "ok": True,
        "status": "no_cookie",
        "message": "尚未配置 Cookie，无法检测有效性（留空为不启用）",
        "platform": platform,
        "http_status": None,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _build_opener():
    handlers = []
    proxy = downloader._effective_proxy()
    if proxy:
        handlers.append(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        )
    return urllib.request.build_opener(*handlers)


def _http_probe(url: str, cookie_text: str) -> int | None:
    """带 Cookie 请求目标地址，返回 HTTP 状态码；网络异常返回 None。"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if cookie_text:
        headers["Cookie"] = cookie_text
    req = urllib.request.Request(url, headers=headers)
    try:
        with _build_opener().open(req, timeout=15) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        logger.warning("Cookie probe failed for url=%s", url, exc_info=True)
        return None


def _ydl_probe(url: str) -> str | None:
    """用 yt-dlp 提取公开视频信息。成功返回 None；失败返回错误描述。"""
    options = {
        "noplaylist": True,
        "socket_timeout": 20,
        "no_color": True,
        "skip_download": True,
    }
    if downloader.sync_cookie_file():
        options["cookiefile"] = downloader.COOKIE_FILE
    proxy = downloader._effective_proxy()
    if proxy:
        options["proxy"] = proxy
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(url, download=False)
        return None
    except yt_dlp.utils.DownloadError as e:
        return str(e)
    except Exception as e:  # 其他异常也视为验证失败
        logger.warning("yt-dlp probe failed for url=%s: %s", url, e)
        return str(e)


def detect_cookie_status(platform: str = "youtube") -> dict:
    """检测当前配置 Cookie 对指定平台是否有效。"""
    platform = (platform or "youtube").lower()
    if platform not in HTTP_PROBE_URLS:
        platform = "youtube"
    cookie_text = stats.get_setting("cookies_text", "").strip()
    if not cookie_text:
        return _no_cookie_result(platform)

    lines = [ln for ln in cookie_text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    http_status = _http_probe(HTTP_PROBE_URLS[platform], cookie_text)

    # yt-dlp 深度验证（仅对需要登录验证的平台）
    ydl_error = None
    probe_url = YDL_PROBE_URLS.get(platform)
    if probe_url:
        ydl_error = _ydl_probe(probe_url)

    message_parts = []
    if ydl_error:
        low = ydl_error.lower()
        if "sign in to confirm" in low or "http error 403" in low:
            status = "invalid"
            message_parts.append("平台返回 403/风控（Sign in to confirm），Cookie 已被拦截")
        elif "expired" in low:
            status = "invalid"
            message_parts.append("Cookie 已过期")
        elif "no video" in low or "unsupported" in low:
            status = "unclear"
            message_parts.append("验证视频不可用（链接本身失效），以 HTTP 探测为准")
        else:
            status = "invalid"
            message_parts.append(f"提取验证失败：{ydl_error[:120]}")
    elif http_status is not None and http_status < 400:
        status = "valid"
        message_parts.append("可以正常访问平台，Cookie 有效")
    elif http_status is not None:
        status = "invalid"
        message_parts.append(f"平台返回 HTTP {http_status}，Cookie 可能已过期或被拦截")
    else:
        status = "unclear"
        message_parts.append("网络探测失败（超时/代理异常），无法确认 Cookie 有效性")

    message_parts.append(f"HTTP 状态码：{http_status if http_status is not None else 'N/A'}")
    message_parts.append(f"Cookie 条目数：{len(lines)}")

    stats.set_setting("cookie_check_result", status)
    stats.set_setting("cookie_checked_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    return {
        "ok": True,
        "status": status,
        "message": "；".join(message_parts),
        "platform": platform,
        "http_status": http_status,
        "checked_at": stats.get_setting("cookie_checked_at"),
    }


def fetch_cookie_from_api(api_url: str) -> str:
    """从 Cookie API 拉取最新 Cookie 文本。JSON 支持 cookies/cookie/cookie_text/data 键。

    失败抛出 RuntimeError，消息为可读原因。
    """
    if not api_url or len(api_url) > 2048:
        raise RuntimeError("Cookie API 地址为空或过长")
    if not api_url.lower().startswith(("http://", "https://")):
        raise RuntimeError("Cookie API 地址必须以 http:// 或 https:// 开头")

    req = urllib.request.Request(
        api_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        with _build_opener().open(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except Exception as e:
        raise RuntimeError(f"请求 Cookie API 失败：{e}") from e

    if not raw.strip():
        raise RuntimeError("Cookie API 返回为空")

    # 尝试按 JSON 解析：支持 {cookies} / {cookie} / {data:{cookies}} 等结构
    text = None
    try:
        data = json.loads(raw)
    except ValueError:
        text = raw  # 非 JSON，视为纯文本
    else:
        def _find(d):
            if isinstance(d, dict):
                for key in ("cookies", "cookie", "cookie_text", "cookies_text", "data"):
                    val = d.get(key)
                    if isinstance(val, str):
                        return val
                    nested = _find(val)
                    if nested is not None:
                        return nested
            return None

        found = _find(data)
        if isinstance(found, str) and found.strip():
            text = found
        else:
            raise RuntimeError("Cookie API 返回的 JSON 中未找到 cookie 字段")

    text = text.strip()
    if not text:
        raise RuntimeError("Cookie API 返回内容为空")
    if len(text) > COOKIE_MAX_LENGTH:
        raise RuntimeError(f"Cookie 内容过长（{len(text)} 字符，上限 {COOKIE_MAX_LENGTH}）")
    return text


def update_cookie_from_api() -> dict:
    """从后台配置的 Cookie API 拉取并保存最新 Cookie。"""
    api_url = stats.get_setting("cookie_api_url", "").strip()
    if not api_url:
        return {"ok": False, "status": "error", "message": "尚未配置 Cookie API 地址"}

    try:
        text = fetch_cookie_from_api(api_url)
    except RuntimeError as e:
        logger.warning("Cookie update failed: %s", e)
        return {"ok": False, "status": "error", "message": str(e)}

    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    stats.set_setting("cookies_text", text)
    downloader.sync_cookie_file()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    stats.set_setting("cookie_updated_at", now)
    logger.info("Cookie updated from API: %d line(s), time=%s", len(lines), now)
    return {
        "ok": True,
        "status": "updated",
        "message": f"Cookie 已更新：{len(lines)} 个条目，时间 {now}",
        "lines": len(lines),
        "updated_at": now,
    }


async def cookie_auto_update_loop() -> None:
    """后台循环：按配置周期（小时）自动从 API 更新 Cookie；周期为 0 时退出。"""
    while True:
        try:
            interval = float(stats.get_setting("cookie_auto_update_hours", "0") or 0)
            if interval <= 0:
                return
            last = stats.get_setting("cookie_updated_at", "")
            # 首次运行或已过周期则立即更新
            if not last:
                result = update_cookie_from_api()
                logger.info("Cookie auto update (first run): %s", result.get("message"))
                await asyncio.sleep(interval * 3600)
                continue

            try:
                last_ts = time.mktime(time.strptime(last, "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                last_ts = 0
            elapsed = time.time() - last_ts
            if elapsed >= interval * 3600:
                result = update_cookie_from_api()
                logger.info("Cookie auto update: %s", result.get("message"))
            await asyncio.sleep(3600)  # 每小时检查一次是否到期
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Cookie auto update task failed")
            await asyncio.sleep(3600)
