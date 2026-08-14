"""设备信息解析与 IP 地理位置查询（带内存缓存，避免频繁请求在线服务）。

地理位置使用 ip-api.com 免费接口（http，无需 Key），按代理配置请求；
本地/内网 IP 直接标记为本地，不发起网络请求。
"""
import ipaddress
import json
import logging
import threading
import time
import urllib.parse
import urllib.request

from services import downloader, stats

logger = logging.getLogger(__name__)

# 地理位置缓存：ip -> {"country","region","city","ts"}，TTL 24 小时
_GEO_CACHE: dict[str, dict] = {}
_GEO_TTL = 24 * 3600
_GEO_LOCK = threading.Lock()

# 在线接口最多等待秒数
_GEO_TIMEOUT = 5


def parse_user_agent(ua: str) -> dict:
    """从 User-Agent 解析设备 / 系统 / 浏览器。"""
    ua = (ua or "").lower()
    if not ua:
        return {"device": "未知", "os": "未知", "browser": "未知"}

    # 设备
    if "ipad" in ua or "tablet" in ua:
        device = "平板"
    elif any(k in ua for k in ("mobile", "iphone", "ipod", "android", "windows phone")):
        device = "手机"
    else:
        device = "电脑"

    # 系统
    if "windows" in ua:
        os_name = "Windows"
    elif "iphone" in ua or "ipod" in ua or "ipad" in ua:
        os_name = "iOS"
    elif "android" in ua:
        os_name = "Android"
    elif "mac os" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    else:
        os_name = "其他"

    # 浏览器
    if "edg/" in ua:
        browser = "Edge"
    elif "opr/" in ua or "opera" in ua:
        browser = "Opera"
    elif "chrome/" in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua:
        browser = "Safari"
    elif "msie" in ua or "trident" in ua:
        browser = "IE"
    else:
        browser = "其他"

    return {"device": device, "os": os_name, "browser": browser}


def is_local_ip(ip: str) -> bool:
    """本地 / 内网 / 未知 IP 不查询地理信息。"""
    ip = (ip or "").strip().lower()
    if not ip or ip in ("unknown", "localhost"):
        return True
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except ValueError:
        return True  # 无法解析的 IP 视为本地，不发起查询


def _query_geo_api(ip: str) -> dict:
    """调用 ip-api.com 查询地理位置；失败返回空字段。"""
    params = urllib.parse.urlencode(
        {"fields": "status,country,regionName,city", "lang": "zh-CN"}
    )
    url = f"http://ip-api.com/json/{ip}?{params}"
    handlers = []
    proxy = downloader._effective_proxy()
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        with opener.open(req, timeout=_GEO_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
        if data.get("status") == "success":
            return {
                "country": str(data.get("country") or ""),
                "region": str(data.get("regionName") or ""),
                "city": str(data.get("city") or ""),
            }
    except Exception as e:
        logger.warning("Geo lookup failed for ip=%s: %s", ip, e)
    return {"country": "", "region": "", "city": ""}


def get_geo_info(ip: str) -> dict:
    """获取 IP 地理位置（带缓存）。本地 IP 返回「本地」。"""
    ip = (ip or "").strip()
    if is_local_ip(ip):
        return {"country": "本地", "region": "", "city": ""}

    now = time.time()
    with _GEO_LOCK:
        cached = _GEO_CACHE.get(ip)
        if cached and now - cached["ts"] < _GEO_TTL:
            return {k: cached[k] for k in ("country", "region", "city")}

    info = _query_geo_api(ip)
    with _GEO_LOCK:
        _GEO_CACHE[ip] = {
            "country": info["country"],
            "region": info["region"],
            "city": info["city"],
            "ts": now,
        }
    return info


def record_visit_with_geo(path: str, ip: str, ua: str) -> None:
    """组装：查询地理位置 + 解析设备，并写入访问明细（供后台线程调用）。"""
    info = get_geo_info(ip)
    dev = parse_user_agent(ua)
    stats.record_visit(
        path, ip,
        country=info["country"], region=info["region"], city=info["city"],
        device=dev["device"], browser=dev["browser"], os=dev["os"], ua=ua,
    )


def record_download_with_geo(url: str, success: bool, error: str, ip: str, ua: str) -> None:
    """组装：查询地理位置 + 解析设备，并写入下载明细（供后台线程调用）。"""
    info = get_geo_info(ip)
    dev = parse_user_agent(ua)
    stats.record_download(
        url, success, error,
        ip=ip,
        country=info["country"], region=info["region"], city=info["city"],
        device=dev["device"], browser=dev["browser"], os=dev["os"],
    )


def record_admin_login_with_geo(ip: str, success: bool, message: str, ua: str) -> None:
    """组装：查询地理位置 + 解析设备，并写入管理员登录日志（供后台线程调用）。"""
    info = get_geo_info(ip)
    dev = parse_user_agent(ua)
    stats.record_admin_login(
        ip, success, message,
        country=info["country"], region=info["region"], city=info["city"],
        device=dev["device"], browser=dev["browser"], os=dev["os"], ua=ua,
    )
