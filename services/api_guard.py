# -*- coding: utf-8 -*-
"""API 防爬虫守卫：签名令牌 + IP 频率限制。

- 签名令牌：服务端持久化密钥，页面渲染时签发 (ts, nonce, sig) 三元组，
  前端调用下载接口时回传；服务端校验时间戳窗口 + HMAC + nonce 一次性。
  爬虫绕过页面直接刷 API 会因缺少合法签名被拒绝。
- 频率限制：基于 IP 的滑动窗口限流，防止高频爬取。

说明：nonce 集合与限流队列为单进程内存态；多 worker/多实例部署时
需要换用 Redis 等共享存储（本项目当前为单进程 uvicorn，内存态足够）。
"""
import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from services import stats

TOKEN_TTL = 300  # 令牌有效期（秒），超出需刷新页面重新获取
RATE_LIMIT_PER_MIN = 20  # 单 IP 每分钟允许的下载请求数

_used_nonces: set = set()  # 已使用的 nonce（一次性防重放）
_rate: dict[str, deque] = defaultdict(deque)  # ip -> 请求时间戳队列
_lock = threading.Lock()
_secret_cache: str | None = None


def _secret() -> str:
    """读取或生成 API 签名密钥（持久化到 SQLite，进程内缓存）。"""
    global _secret_cache
    if _secret_cache:
        return _secret_cache
    s = stats.get_setting("api_secret", "")
    if not s:
        s = secrets.token_hex(32)
        stats.set_setting("api_secret", s)
    _secret_cache = s
    return s


def issue_token(now: float | None = None) -> tuple[str, str, str]:
    """签发页面令牌，返回 (ts, nonce, sig)。"""
    ts = str(int(now or time.time()))
    nonce = secrets.token_hex(8)
    msg = f"{ts}:{nonce}".encode()
    sig = hmac.new(_secret().encode(), msg, hashlib.sha256).hexdigest()
    return ts, nonce, sig


def verify_token(ts: str, nonce: str, sig: str, now: float | None = None) -> bool:
    """校验令牌：时间戳窗口 + HMAC 一致 + nonce 未使用过。"""
    try:
        ts_i = int(ts)
    except (TypeError, ValueError):
        return False
    cur = int(now or time.time())
    if abs(cur - ts_i) > TOKEN_TTL:
        return False
    msg = f"{ts}:{nonce}".encode()
    expect = hmac.new(_secret().encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        return False
    with _lock:
        if nonce in _used_nonces:
            return False
        _used_nonces.add(nonce)
        # 控制内存：超过阈值清空（TTL 窗口内的 token 本也已过期）
        if len(_used_nonces) > 10000:
            _used_nonces.clear()
    return True


def rate_limit(ip: str, limit: int = RATE_LIMIT_PER_MIN, window: int = 60) -> bool:
    """IP 滑动窗口限流：窗口内请求数未超限则记录并返回 True，超限返回 False。"""
    now = time.time()
    with _lock:
        q = _rate[ip]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        if len(_rate) > 20000:  # 控制内存：极端情况下重置
            _rate.clear()
    return True
