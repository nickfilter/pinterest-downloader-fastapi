from fastapi import APIRouter, Form
from fastapi.responses import FileResponse

from services.downloader import download_video



router = APIRouter()



@router.post("/download")
async def download(

    url:str = Form(...)

):


    try:


        filepath = download_video(
            url
        )


        return FileResponse(

            filepath,

            filename="video.mp4",

            media_type="video/mp4"

        )


    except Exception as e:


        return {

            "error":
            str(e)

        }