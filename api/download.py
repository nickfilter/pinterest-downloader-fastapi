import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from services.api_guard import rate_limit, verify_token
from services.downloader import (
    UnsupportedUrlError,
    VideoExtractionError,
    get_video_info,
)
from services.geo import record_download_with_geo

logger = logging.getLogger(__name__)

router = APIRouter()

# 后台任务引用，防止被 GC
_background_tasks: set = set()


class DownloadRequest(BaseModel):
    url: str


def _spawn_download_record(url: str, success: bool, error: str, ip: str, ua: str) -> None:
    """异步记录下载明细（地理查询放后台线程，不阻塞响应）。"""
    task = asyncio.create_task(
        asyncio.to_thread(record_download_with_geo, url, success, error, ip, ua)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/download")
async def download(req: Request, body: DownloadRequest):
    ip = _client_ip(req)
    ua = req.headers.get("user-agent", "")

    # ---- 防爬虫：签名令牌 + 频率限制（校验失败不计入下载统计） ----
    ts = req.headers.get("x-api-ts", "")
    nonce = req.headers.get("x-api-nonce", "")
    sig = req.headers.get("x-api-sig", "")
    if not verify_token(ts, nonce, sig):
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired request. Please refresh the page and try again.",
        )
    if not rate_limit(ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
        )

    def _record(success: bool, error: str = "") -> None:
        _spawn_download_record(body.url, success, error, ip, ua)

    try:
        result = await run_in_threadpool(get_video_info, body.url)
    except UnsupportedUrlError as e:
        # 非法/不支持地址：客户端问题，返回 400
        _record(False, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except VideoExtractionError as e:
        # 无法提取内容（非视频、被拦截等）：客户端问题，返回 400
        _record(False, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Download failed for url=%s", body.url)
        _record(False, str(e)[:300])
        raise HTTPException(status_code=500, detail="Download failed. Please try again.")

    _record(True)

    return {
        "success": True,
        "title": result.get("title"),
        "thumbnail": result.get("thumbnail"),
        "video_url": result.get("video_url"),
        "audio_url": result.get("audio_url"),
        "image_url": result.get("image_url"),
    }
