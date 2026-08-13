import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from services.downloader import UnsupportedUrlError, get_video_info

logger = logging.getLogger(__name__)

router = APIRouter()


class DownloadRequest(BaseModel):
    url: str


@router.post("/download")
async def download(request: DownloadRequest):
    try:
        result = await run_in_threadpool(get_video_info, request.url)
    except UnsupportedUrlError as e:
        # 非法/不支持地址：客户端问题，返回 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Download failed for url=%s", request.url)
        raise HTTPException(status_code=500, detail="Download failed. Please try again.")

    return {
        "success": True,
        "title": result.get("title"),
        "thumbnail": result.get("thumbnail"),
        "download_url": result.get("download_url"),
    }
