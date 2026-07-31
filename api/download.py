from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool

from services.downloader import get_video_info


router = APIRouter()



class DownloadRequest(BaseModel):

    url: str





@router.post("/download")
async def download(
    request: DownloadRequest
):

    try:

        result = await run_in_threadpool(
            get_video_info,
            request.url
        )


        return {

            "success": True,

            "title": result.get("title"),

            "thumbnail": result.get("thumbnail"),

            "download_url": result.get("download_url")

        }


    except Exception as e:


        return {


            "success": False,

            "error": str(e)

        }