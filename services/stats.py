"""访问统计、下载记录与站点设置：基于 SQLite 的轻量持久化存储。"""
import logging
import os
import sqlite3
import threading
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "stats.db")

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS page_views (
    path TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    hostname TEXT NOT NULL DEFAULT '',
    success INTEGER NOT NULL DEFAULT 0,
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS login_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    failed_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_login_failures_ip ON login_failures(ip);
CREATE TABLE IF NOT EXISTS login_blocks (
    ip TEXT PRIMARY KEY,
    blocked_until REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS user_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    device TEXT NOT NULL DEFAULT '',
    browser TEXT NOT NULL DEFAULT '',
    os TEXT NOT NULL DEFAULT '',
    ua TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL DEFAULT '',
    visited_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_visits_time ON user_visits(visited_at);
CREATE TABLE IF NOT EXISTS daily_stats (
    date TEXT PRIMARY KEY,
    visits INTEGER NOT NULL DEFAULT 0,
    unique_visitors INTEGER NOT NULL DEFAULT 0,
    downloads INTEGER NOT NULL DEFAULT 0,
    unique_downloaders INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    device TEXT NOT NULL DEFAULT '',
    browser TEXT NOT NULL DEFAULT '',
    os TEXT NOT NULL DEFAULT '',
    ua TEXT NOT NULL DEFAULT '',
    success INTEGER NOT NULL DEFAULT 0,
    message TEXT NOT NULL DEFAULT '',
    logged_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_login_logs_time ON admin_login_logs(logged_at);
"""
# 老库迁移：downloads 表补充 IP / 地理位置 / 设备列
_DOWNLOAD_COLUMNS = (
    "ip", "country", "region", "city", "device", "browser", "os", "platform",
)
_MIGRATION_ALTERS = "".join(
    f"ALTER TABLE downloads ADD COLUMN {col} TEXT NOT NULL DEFAULT '';" for col in _DOWNLOAD_COLUMNS
)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init() -> None:
    with _lock:
        conn = _connect()
        try:
            conn.executescript(_SCHEMA)
            # 迁移：为老库 downloads 表补充新列
            existing = {r["name"] for r in conn.execute("PRAGMA table_info(downloads)").fetchall()}
            for col in _DOWNLOAD_COLUMNS:
                if col not in existing:
                    conn.execute(f"ALTER TABLE downloads ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
            conn.commit()
        finally:
            conn.close()


_init()


def record_page_view(path: str) -> None:
    """记录一次页面访问（按路径累加计数）。"""
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO page_views(path, count, updated_at) VALUES(?, 1, ?) "
                    "ON CONFLICT(path) DO UPDATE SET count = count + 1, updated_at = excluded.updated_at",
                    (path, now),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        logger.exception("Failed to record page view for path=%s", path)


def _platform_of(hostname: str) -> str:
    """从域名推断平台名称，用于下载记录展示。"""
    h = (hostname or "").lower()
    for key, name in (
        ("youtube", "YouTube"),
        ("instagram", "Instagram"),
        ("pinterest", "Pinterest"),
        ("tiktok", "TikTok"),
        ("facebook", "Facebook"),
        ("twitter", "Twitter"),
        ("x.com", "Twitter"),
        ("bilibili", "Bilibili"),
        ("vimeo", "Vimeo"),
    ):
        if key in h:
            return name
    return hostname or "未知"


def record_download(
    url: str,
    success: bool,
    error: str = "",
    *,
    ip: str = "",
    country: str = "",
    region: str = "",
    city: str = "",
    device: str = "",
    browser: str = "",
    os: str = "",
) -> None:
    """记录一次下载请求（成功或失败），附带 IP / 地理位置 / 设备信息。"""
    try:
        hostname = urlparse(url).netloc or ""
        platform = _platform_of(hostname)
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO downloads(url, hostname, success, error, created_at, "
                    "ip, country, region, city, device, browser, os, platform) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        url[:500], hostname, 1 if success else 0, error[:300], now,
                        ip[:45], country[:50], region[:50], city[:50],
                        device[:20], browser[:20], os[:20], platform[:30],
                    ),
                )
                _refresh_daily_stats(conn, now[:10])
                conn.commit()
            finally:
                conn.close()
    except Exception:
        logger.exception("Failed to record download for url=%s", url)


def record_visit(
    path: str,
    ip: str = "",
    country: str = "",
    region: str = "",
    city: str = "",
    device: str = "",
    browser: str = "",
    os: str = "",
    ua: str = "",
) -> None:
    """记录一次页面访问明细（IP / 地理位置 / 设备）。"""
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO user_visits(ip, country, region, city, device, browser, os, ua, path, visited_at) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ip[:45], country[:50], region[:50], city[:50],
                        device[:20], browser[:20], os[:20], ua[:300],
                        (path or "")[:200], now,
                    ),
                )
                _refresh_daily_stats(conn, now[:10])
                conn.commit()
            finally:
                conn.close()
    except Exception:
        logger.exception("Failed to record visit for path=%s", path)


def _refresh_daily_stats(conn: sqlite3.Connection, date_str: str) -> None:
    """刷新指定日期的聚合统计（在调用方事务内执行）。"""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    visits = conn.execute(
        "SELECT COUNT(*) FROM user_visits WHERE substr(visited_at, 1, 10) = ?", (date_str,)
    ).fetchone()[0]
    unique_visitors = conn.execute(
        "SELECT COUNT(DISTINCT ip) FROM user_visits WHERE substr(visited_at, 1, 10) = ?", (date_str,)
    ).fetchone()[0]
    downloads = conn.execute(
        "SELECT COUNT(*) FROM downloads WHERE substr(created_at, 1, 10) = ?", (date_str,)
    ).fetchone()[0]
    unique_downloaders = conn.execute(
        "SELECT COUNT(DISTINCT ip) FROM downloads WHERE substr(created_at, 1, 10) = ?", (date_str,)
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO daily_stats(date, visits, unique_visitors, downloads, unique_downloaders, updated_at) "
        "VALUES(?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(date) DO UPDATE SET visits = excluded.visits, "
        "unique_visitors = excluded.unique_visitors, downloads = excluded.downloads, "
        "unique_downloaders = excluded.unique_downloaders, updated_at = excluded.updated_at",
        (date_str, visits, unique_visitors, downloads, unique_downloaders, now),
    )


def get_page_views(limit: int = 100) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT path, count, updated_at FROM page_views ORDER BY count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_page_views_total() -> int:
    conn = _connect()
    try:
        row = conn.execute("SELECT COALESCE(SUM(count), 0) AS total FROM page_views").fetchone()
        return int(row["total"])
    finally:
        conn.close()


def get_download_stats() -> dict:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END), 0) AS ok, "
            "COALESCE(SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END), 0) AS failed "
            "FROM downloads"
        ).fetchone()
        return {"total": row["total"], "success": row["ok"], "failed": row["failed"]}
    finally:
        conn.close()


def get_downloads(limit: int = 100) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, url, hostname, success, error, created_at, "
            "ip, country, region, city, device, browser, os, platform "
            "FROM downloads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent_visits(limit: int = 50) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, ip, country, region, city, device, browser, os, path, visited_at "
            "FROM user_visits ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_daily_stats(limit: int = 30) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT date, visits, unique_visitors, downloads, unique_downloaders, updated_at "
            "FROM daily_stats ORDER BY date DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_visits_summary() -> dict:
    """今日与累计访问/下载汇总。"""
    conn = _connect()
    try:
        today = time.strftime("%Y-%m-%d")
        row = conn.execute(
            "SELECT "
            "COUNT(*) AS today_visits, "
            "COUNT(DISTINCT ip) AS today_unique_visitors "
            "FROM user_visits WHERE substr(visited_at, 1, 10) = ?",
            (today,),
        ).fetchone()
        drow = conn.execute(
            "SELECT "
            "COUNT(*) AS today_downloads, "
            "COUNT(DISTINCT ip) AS today_download_users "
            "FROM downloads WHERE substr(created_at, 1, 10) = ?",
            (today,),
        ).fetchone()
        trow = conn.execute(
            "SELECT COUNT(*) AS total_visits, COUNT(DISTINCT ip) AS total_unique_visitors FROM user_visits"
        ).fetchone()
        tdrow = conn.execute(
            "SELECT COUNT(*) AS total_downloads, COUNT(DISTINCT ip) AS total_download_users FROM downloads"
        ).fetchone()
        return {
            "today_visits": row["today_visits"],
            "today_unique_visitors": row["today_unique_visitors"],
            "today_downloads": drow["today_downloads"],
            "today_download_users": drow["today_download_users"],
            "total_visits": trow["total_visits"],
            "total_unique_visitors": trow["total_unique_visitors"],
            "total_downloads": tdrow["total_downloads"],
            "total_download_users": tdrow["total_download_users"],
        }
    finally:
        conn.close()


def record_admin_login(
    ip: str,
    success: bool,
    message: str = "",
    *,
    country: str = "",
    region: str = "",
    city: str = "",
    device: str = "",
    browser: str = "",
    os: str = "",
    ua: str = "",
) -> None:
    """记录一次管理员登录尝试（成功/失败），附带 IP / 地理位置 / 设备信息。"""
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO admin_login_logs(ip, country, region, city, device, browser, os, ua, success, message, logged_at) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ip[:45], country[:50], region[:50], city[:50],
                        device[:20], browser[:20], os[:20], ua[:300],
                        1 if success else 0, message[:200], now,
                    ),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        logger.exception("Failed to record admin login ip=%s", ip)


def get_admin_login_logs(limit: int = 100) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, ip, country, region, city, device, browser, os, success, message, logged_at "
            "FROM admin_login_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_login_logs_summary() -> dict:
    """今日与累计的管理员登录成功/失败次数。"""
    conn = _connect()
    try:
        today = time.strftime("%Y-%m-%d")

        def _counts(where: str = "", params: tuple = ()) -> tuple:
            row = conn.execute(
                "SELECT "
                "COALESCE(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END), 0) AS ok, "
                "COALESCE(SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END), 0) AS fail "
                f"FROM admin_login_logs {where}",
                params,
            ).fetchone()
            return int(row["ok"]), int(row["fail"])

        today_ok, today_fail = _counts("WHERE substr(logged_at, 1, 10) = ?", (today,))
        total_ok, total_fail = _counts()
        return {
            "today_success": today_ok,
            "today_failed": today_fail,
            "total_success": total_ok,
            "total_failed": total_fail,
        }
    finally:
        conn.close()


def cleanup_old_records(days: int = 30) -> int:
    """删除超过保留天数的访问/下载明细，返回删除行数。"""
    cutoff = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days * 86400)
    )
    with _lock:
        conn = _connect()
        try:
            v = conn.execute(
                "DELETE FROM user_visits WHERE visited_at < ?", (cutoff,)
            ).rowcount
            d = conn.execute(
                "DELETE FROM downloads WHERE created_at < ?", (cutoff,)
            ).rowcount
            conn.execute("DELETE FROM daily_stats WHERE date < ?", (cutoff[:10],))
            # 管理员登录日志为审计数据，保留更长时间（90 天）
            login_cutoff = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 90 * 86400)
            )
            a = conn.execute(
                "DELETE FROM admin_login_logs WHERE logged_at < ?", (login_cutoff,)
            ).rowcount
            conn.commit()
            return int(v) + int(d) + int(a)
        finally:
            conn.close()


def get_setting(key: str, default: str = "") -> str:
    conn = _connect()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def set_setting(key: str, value: str) -> None:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()


def login_block_remaining(ip: str) -> float | None:
    """返回该 IP 剩余封禁秒数；未封禁返回 None（过期封禁自动清除）。"""
    with _lock:
        conn = _connect()
        try:
            now = time.time()
            row = conn.execute(
                "SELECT blocked_until FROM login_blocks WHERE ip = ?", (ip,)
            ).fetchone()
            if row:
                remaining = row["blocked_until"] - now
                if remaining > 0:
                    return remaining
                conn.execute("DELETE FROM login_blocks WHERE ip = ?", (ip,))
                conn.commit()
            return None
        finally:
            conn.close()


def login_failure_record(
    ip: str, window: float, limit: int, block_seconds: float
) -> float | None:
    """记录一次登录失败（滑动窗口）。返回触发封禁的时长（秒）；未触发返回 None。"""
    with _lock:
        conn = _connect()
        try:
            now = time.time()
            # 清理该 IP 超出窗口的旧失败记录，保证滑动窗口语义
            conn.execute(
                "DELETE FROM login_failures WHERE ip = ? AND failed_at < ?",
                (ip, now - window),
            )
            conn.execute(
                "INSERT INTO login_failures(ip, failed_at) VALUES(?, ?)", (ip, now)
            )
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM login_failures WHERE ip = ?", (ip,)
            ).fetchone()
            if row["c"] >= limit:
                conn.execute(
                    "INSERT OR REPLACE INTO login_blocks(ip, blocked_until) VALUES(?, ?)",
                    (ip, now + block_seconds),
                )
                conn.commit()
                return block_seconds
            conn.commit()
            return None
        finally:
            conn.close()


def login_failure_clear(ip: str) -> None:
    """登录成功后清除该 IP 的失败记录。"""
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM login_failures WHERE ip = ?", (ip,))
            conn.commit()
        finally:
            conn.close()
