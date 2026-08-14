import asyncio
import hashlib
import logging
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.download import router
from services.cleanup import cleanup_loop
from services import api_guard, cookie_service, downloader, geo, stats

logger = logging.getLogger(__name__)

# 后台访问/下载明细记录任务引用集合，防止 asyncio 任务被 GC 提前回收
_background_tasks: set = set()

# 所有路径基于代码位置，避免依赖进程工作目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 管理密码：环境变量 ADMIN_PASSWORD 覆盖，默认 admin123；
# 后台修改密码后优先使用 SQLite 中保存的 admin_password_hash
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

_PBKDF2_ITERATIONS = 200_000
# 当前有效的管理员 token 缓存（修改密码后刷新，旧会话立即失效）
_admin_token_cache: str | None = None


def _hash_password(pw: str) -> str:
    """PBKDF2-SHA256 加盐哈希，返回 salt$iterations$digest。"""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", pw.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    ).hex()
    return f"{salt}${_PBKDF2_ITERATIONS}${digest}"


def _verify_password(pw: str, stored: str) -> bool:
    try:
        salt, iterations, digest = stored.split("$", 2)
        calc = hashlib.pbkdf2_hmac(
            "sha256", pw.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return secrets.compare_digest(calc, digest)
    except (ValueError, TypeError):
        return False


def _admin_token() -> str:
    """当前有效的管理 token：后台修改过密码则基于哈希值，否则基于环境变量/默认密码。"""
    global _admin_token_cache
    if _admin_token_cache is None:
        _admin_token_cache = _compute_admin_token()
    return _admin_token_cache


def _compute_admin_token() -> str:
    stored = stats.get_setting("admin_password_hash", "")
    if stored:
        return hashlib.sha256(f"admin:{stored}".encode()).hexdigest()
    return hashlib.sha256(f"admin:{ADMIN_PASSWORD}".encode()).hexdigest()


def verify_admin_password(pw: str) -> bool:
    """校验管理密码：已自定义（settings 中存哈希）优先，否则用环境变量/默认密码。"""
    stored = stats.get_setting("admin_password_hash", "")
    if stored:
        return _verify_password(pw, stored)
    return secrets.compare_digest(pw, ADMIN_PASSWORD)

# ---- 登录保护：同一 IP 10 分钟内失败 5 次，封禁该 IP 10 分钟（SQLite 持久化） ----
LOGIN_FAIL_LIMIT = 5
LOGIN_FAIL_WINDOW = 600  # 失败计数窗口（秒）
LOGIN_BLOCK_SECONDS = 600  # 封禁时长（秒）


def _client_ip(request: Request) -> str:
    """取客户端 IP：优先 X-Forwarded-For（反向代理场景），否则取连接地址。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _spawn_visit_record(path: str, ip: str, ua: str) -> None:
    """异步记录访问明细（地理查询走后台线程，不阻塞响应）。"""
    task = asyncio.create_task(asyncio.to_thread(geo.record_visit_with_geo, path, ip, ua))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _spawn_page_view_record(path: str) -> None:
    """异步累计页面访问计数（线程池，避免阻塞事件循环）。"""
    task = asyncio.create_task(asyncio.to_thread(stats.record_page_view, path))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _spawn_admin_login_record(ip: str, success: bool, message: str, ua: str) -> None:
    """异步记录管理员登录日志（地理查询走后台线程，不阻塞响应）。"""
    task = asyncio.create_task(
        asyncio.to_thread(geo.record_admin_login_with_geo, ip, success, message, ua)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _is_blocked(ip: str) -> float | None:
    """返回剩余封禁秒数；未封禁返回 None。"""
    return stats.login_block_remaining(ip)


def _record_failure(ip: str) -> float | None:
    """记录一次登录失败；若触发封禁返回封禁时长，否则 None。"""
    return stats.login_failure_record(
        ip, LOGIN_FAIL_WINDOW, LOGIN_FAIL_LIMIT, LOGIN_BLOCK_SECONDS
    )


def _clear_failures(ip: str) -> None:
    stats.login_failure_clear(ip)

DEFAULT_TITLE = "Social Video Downloader"
DEFAULT_FOOTER = "© 2026 Social Video Downloader"


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(cleanup_loop()),
        asyncio.create_task(cookie_service.cookie_auto_update_loop()),
    ]
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="Online Video Downloader", lifespan=lifespan)
app.include_router(router)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)
app.mount(
    "/downloads",
    StaticFiles(directory=os.path.join(BASE_DIR, "downloads")),
    name="downloads",
)


@app.middleware("http")
async def track_page_views(request: Request, call_next):
    """统计页面访问：记录所有 HTML 页面请求，跳过静态/下载/管理资源。"""
    path = request.url.path
    if request.method == "GET":
        skip = (
            path.startswith(("/static/", "/downloads/", "/admin"))
            or path in ("/ads.txt", "/favicon.ico")
        )
        if not skip:
            ua = request.headers.get("user-agent", "")
            ip = _client_ip(request)
            _spawn_page_view_record(path)
            _spawn_visit_record(path, ip, ua)
    return await call_next(request)


async def site_context(extra: dict | None = None) -> dict:
    """组装公共站点配置（标题、footer、统计代码、API 令牌），供所有页面渲染（DB 查询走线程池）。"""
    (
        site_title,
        footer_text,
        ga4_id,
        baidu_id,
        adsense_client_id,
        adsense_ad_slot,
        api_ts,
        api_nonce,
        api_sig,
    ) = await run_in_threadpool(
        lambda: (
            stats.get_setting("site_title", DEFAULT_TITLE),
            stats.get_setting("footer_text", DEFAULT_FOOTER),
            stats.get_setting("ga4_id", ""),
            stats.get_setting("baidu_id", ""),
            stats.get_setting("adsense_client_id", ""),
            stats.get_setting("adsense_ad_slot", ""),
            *api_guard.issue_token(),
        )
    )
    ctx = {
        "site_title": site_title,
        "footer_text": footer_text,
        "ga4_id": ga4_id,
        "baidu_id": baidu_id,
        "adsense_client_id": adsense_client_id,
        "adsense_ad_slot": adsense_ad_slot,
        "api_ts": api_ts,
        "api_nonce": api_nonce,
        "api_sig": api_sig,
    }
    if extra:
        ctx.update(extra)
    return ctx


def _is_admin(request: Request) -> bool:
    return request.cookies.get("admin_token") == _admin_token()


# 各平台落地页：(路径, 页面标题, 页面描述)
PLATFORMS = [
    ("/youtube-downloader", "YouTube Video Downloader", "Download YouTube videos in MP4 format."),
    ("/tiktok-downloader", "TikTok Video Downloader", "Download TikTok videos online without watermark."),
    ("/facebook-downloader", "Facebook Video Downloader", "Download Facebook videos online without watermark."),
    ("/instagram-downloader", "Instagram Video Downloader", "Download Instagram videos in MP4 format."),
    ("/twitter-downloader", "Twitter Video Downloader", "Download Twitter videos in MP4 format."),
    ("/pinterest-downloader", "Pinterest Video Downloader", "Download Pinterest videos in MP4 format."),
]


def _make_platform_page(path: str, title: str, description: str):
    async def handler(request: Request):
        ctx = await site_context({"title": title, "description": description})
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context=ctx,
        )

    handler.__name__ = "page_" + path.strip("/").replace("-", "_")
    return handler


for path, title, description in PLATFORMS:
    app.add_api_route(
        path,
        _make_platform_page(path, title, description),
        methods=["GET"],
        tags=["pages"],
    )


@app.get("/")
async def home(request: Request):
    ctx = await site_context()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=ctx,
    )


@app.get("/about")
async def about(request: Request):
    ctx = await site_context(
        {
            "title": "How to use Downloader",
            "description": "Download videos in MP4 format.",
        }
    )
    return templates.TemplateResponse(
        request=request,
        name="downloader.html",
        context=ctx,
    )


@app.get("/ads.txt")
async def ads_txt():
    return FileResponse(
        os.path.join(BASE_DIR, "ads.txt"),
        media_type="text/plain",
    )


# ---------------- 后台管理 ----------------

@app.get("/admin")
async def admin_page(request: Request):
    """管理后台：登录后展示访问统计、下载记录与站点设置。"""
    # 已自定义密码时不向前端返回明文
    custom_pw = await run_in_threadpool(lambda: stats.get_setting("admin_password_hash", ""))
    ctx = await site_context(
        {
            "is_admin": _is_admin(request),
            "admin_username": "admin",
            "admin_password": "" if custom_pw else ADMIN_PASSWORD,
            "is_custom_password": bool(custom_pw),
        }
    )
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context=ctx,
    )


@app.post("/admin/login")
async def admin_login(request: Request):
    ip = _client_ip(request)
    # 封禁检查：封禁期内直接拒绝，不再校验密码（SQLite 查询走线程池）
    blocked = await run_in_threadpool(_is_blocked, ip)
    if blocked is not None:
        _spawn_admin_login_record(ip, False, "IP 被封禁，拒绝登录", request.headers.get("user-agent", ""))
        return JSONResponse(
            {
                "success": False,
                "message": f"登录失败次数过多，该 IP 已被封禁，请约 {int(blocked // 60) + 1} 分钟后再试",
            },
            status_code=429,
        )

    data = await request.json()
    if await run_in_threadpool(verify_admin_password, str(data.get("password", ""))):
        await run_in_threadpool(_clear_failures, ip)
        _spawn_admin_login_record(ip, True, "登录成功", request.headers.get("user-agent", ""))
        resp = RedirectResponse(url="/admin", status_code=303)
        resp.set_cookie("admin_token", _admin_token(), httponly=True, max_age=7 * 24 * 3600)
        return resp

    _spawn_admin_login_record(ip, False, "密码错误", request.headers.get("user-agent", ""))
    remain = await run_in_threadpool(_record_failure, ip)
    if remain is not None:
        return JSONResponse(
            {
                "success": False,
                "message": f"密码错误，同一 IP 10 分钟内失败已达 {LOGIN_FAIL_LIMIT} 次，"
                f"该 IP 已封禁 {LOGIN_BLOCK_SECONDS // 60} 分钟",
            },
            status_code=429,
        )
    return JSONResponse({"success": False, "message": "密码错误"}, status_code=401)


@app.get("/admin/logout")
async def admin_logout():
    resp = RedirectResponse(url="/admin", status_code=303)
    resp.delete_cookie("admin_token")
    return resp


def _require_admin(request: Request) -> None:
    if not _is_admin(request):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _read_ads_txt() -> str:
    """读取 ads.txt 文件内容（不存在或读取失败返回空字符串）。"""
    try:
        with open(os.path.join(BASE_DIR, "ads.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _write_ads_txt(content: str) -> None:
    """写入 ads.txt 文件（同步磁盘，立即生效）。"""
    with open(os.path.join(BASE_DIR, "ads.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _collect_stats_snapshot() -> dict:
    """后台线程聚合管理后台统计快照（全部 SQLite 查询一次完成，不阻塞事件循环）。"""
    return {
        "page_views": stats.get_page_views(100),
        "page_views_total": stats.get_page_views_total(),
        "download_stats": stats.get_download_stats(),
        "downloads": stats.get_downloads(100),
        "daily_stats": stats.get_daily_stats(30),
        "recent_visits": stats.get_recent_visits(50),
        "visits_summary": stats.get_visits_summary(),
        "login_logs": stats.get_admin_login_logs(100),
        "login_logs_summary": stats.get_login_logs_summary(),
        "settings": {
            "site_title": stats.get_setting("site_title", DEFAULT_TITLE),
            "footer_text": stats.get_setting("footer_text", DEFAULT_FOOTER),
            "ga4_id": stats.get_setting("ga4_id", ""),
            "baidu_id": stats.get_setting("baidu_id", ""),
            "adsense_client_id": stats.get_setting("adsense_client_id", ""),
            "adsense_ad_slot": stats.get_setting("adsense_ad_slot", ""),
            "ads_txt": _read_ads_txt(),
            "proxy_url": stats.get_setting("proxy_url", ""),
            "cookies_text": stats.get_setting("cookies_text", ""),
            "cookie_api_url": stats.get_setting("cookie_api_url", ""),
            "cookie_auto_update_hours": stats.get_setting("cookie_auto_update_hours", "0"),
            "cookie_check_result": stats.get_setting("cookie_check_result", ""),
            "cookie_checked_at": stats.get_setting("cookie_checked_at", ""),
            "cookie_updated_at": stats.get_setting("cookie_updated_at", ""),
        },
    }


@app.get("/admin/api/stats")
async def admin_stats(request: Request):
    _require_admin(request)
    return await run_in_threadpool(_collect_stats_snapshot)


def _save_settings_sync(data: dict) -> None:
    """后台线程批量保存站点设置（含 cookies.txt 同步），不阻塞事件循环。"""
    if "site_title" in data:
        stats.set_setting("site_title", str(data["site_title"])[:100])
    if "footer_text" in data:
        stats.set_setting("footer_text", str(data["footer_text"])[:500])
    if "ga4_id" in data:
        # 仅保留 G-/UA- 等合法 Measurement ID 形态
        ga4 = str(data["ga4_id"]).strip()
        if ga4 and not ga4.startswith(("G-", "UA-", "GT-")):
            ga4 = ""
        stats.set_setting("ga4_id", ga4[:50])
    if "baidu_id" in data:
        # 百度统计站点 ID 仅允许数字
        baidu = "".join(ch for ch in str(data["baidu_id"]) if ch.isdigit())
        stats.set_setting("baidu_id", baidu[:20])
    if "adsense_client_id" in data:
        # AdSense 发布商 ID：仅保留 ca-pub- 合法形态
        client = str(data["adsense_client_id"]).strip()
        if client and not client.startswith("ca-pub-"):
            client = ""
        stats.set_setting("adsense_client_id", client[:30])
    if "adsense_ad_slot" in data:
        # AdSense 广告单元 Slot ID 仅允许数字
        slot = "".join(ch for ch in str(data["adsense_ad_slot"]) if ch.isdigit())
        stats.set_setting("adsense_ad_slot", slot[:15])
    if "ads_txt" in data:
        # ads.txt 广告授权文件：直接写盘，最长 10000 字符
        ads = str(data["ads_txt"])[:10000]
        # 移除控制字符（保留换行），防止写入异常字符
        ads = "".join(ch for ch in ads if ch not in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f")
        _write_ads_txt(ads)
    if "proxy_url" in data:
        stats.set_setting("proxy_url", str(data["proxy_url"]).strip()[:300])
    if "cookies_text" in data:
        stats.set_setting("cookies_text", str(data["cookies_text"])[:50000])
        # 保存后立即同步 cookies.txt，保证清空/更新即时生效
        downloader.sync_cookie_file()
    if "cookie_api_url" in data:
        stats.set_setting("cookie_api_url", str(data["cookie_api_url"]).strip()[:2048])
    if "cookie_auto_update_hours" in data:
        try:
            hours = max(0, min(168, float(data["cookie_auto_update_hours"])))
        except (TypeError, ValueError):
            hours = 0
        stats.set_setting("cookie_auto_update_hours", str(hours))


@app.post("/admin/api/settings")
async def admin_save_settings(request: Request):
    _require_admin(request)
    data = await request.json()
    await run_in_threadpool(_save_settings_sync, data)
    return {"success": True}


def _apply_new_password(new_pw: str) -> None:
    """保存新密码哈希并刷新 token 缓存，使旧会话立即失效（后台线程执行）。"""
    global _admin_token_cache
    new_hash = _hash_password(new_pw)
    stats.set_setting("admin_password_hash", new_hash)
    _admin_token_cache = hashlib.sha256(f"admin:{new_hash}".encode()).hexdigest()


@app.post("/admin/api/password")
async def admin_change_password(request: Request):
    """修改管理密码：校验旧密码 -> 保存新密码哈希 -> 刷新 token（旧会话失效）。"""
    _require_admin(request)
    ip = _client_ip(request)
    data = await request.json()
    old_pw = str(data.get("old_password", ""))
    new_pw = str(data.get("new_password", ""))

    if not await run_in_threadpool(verify_admin_password, old_pw):
        _spawn_admin_login_record(ip, False, "修改密码失败：旧密码错误", request.headers.get("user-agent", ""))
        return JSONResponse({"success": False, "message": "旧密码错误"}, status_code=400)
    if not (6 <= len(new_pw) <= 64):
        return JSONResponse({"success": False, "message": "新密码长度需为 6-64 位"}, status_code=400)
    if old_pw == new_pw:
        return JSONResponse({"success": False, "message": "新密码不能与旧密码相同"}, status_code=400)

    await run_in_threadpool(_apply_new_password, new_pw)
    _spawn_admin_login_record(ip, True, "修改管理密码成功", request.headers.get("user-agent", ""))
    return {"success": True, "message": "密码已修改，请使用新密码重新登录"}


@app.get("/admin/api/cookie/test")
async def admin_cookie_test(request: Request, platform: str = "youtube"):
    """检测当前 Cookie 对指定平台是否有效。"""
    _require_admin(request)
    return await run_in_threadpool(cookie_service.detect_cookie_status, platform)


@app.post("/admin/api/cookie/update")
async def admin_cookie_update(request: Request):
    """从后台配置的 Cookie API 拉取并保存最新 Cookie。"""
    _require_admin(request)
    return await run_in_threadpool(cookie_service.update_cookie_from_api)
