
from fastapi import APIRouter
from pydantic import BaseModel
from services.pinterest import extract_video

router = APIRouter()

class VideoRequest(BaseModel):
    url: str

@router.post("/download")
async def download(data: VideoRequest):
    result = await extract_video(data.url)
    return result
