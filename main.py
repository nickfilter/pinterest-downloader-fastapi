
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from api.download import router
from fastapi.responses import FileResponse

app = FastAPI(title="Online Video Downloader")
app.include_router(router)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    "/downloads",
    StaticFiles(
        directory="static/downloads"
    ),
    name="downloads"
)


@app.get("/")
async def home(request: Request):
   return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={}
    )
from fastapi import Request


@app.get("/tiktok-downloader")
async def tiktok(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={

            "title":
            "TikTok Video Downloader",

            "description":
            "Download TikTok videos online without watermark."

        }
    )



@app.get("/youtube-downloader")
async def youtube(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={

            "title":
            "YouTube Video Downloader",

            "description":
            "Download YouTube videos in MP4 format."

        }
    )


@app.get("/facebook-downloader")
async def facebook(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={

            "title":
            "facebook Video Downloader",

            "description":
            "Download facebook videos online without watermark."

        }
    )



@app.get("/pinterest-downloader")
async def pinterest(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={

            "title":
            "pinterest Video Downloader",

            "description":
            "Download pinterest videos in MP4 format."

        }
    )
@app.get("/instagram-downloader")
async def Instagram(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={

            "title":
            "Instagram Video Downloader",

            "description":
            "Download Instagram videos in MP4 format."

        }
    )
@app.get("/twitter-downloader")
async def twitter(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={

            "title":
            "twitter Video Downloader",

            "description":
            "Download twitter videos in MP4 format."

        }
    )
@app.get("/about")
async def about(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="downloader.html",
        context={

            "title":
            "How to use Downloader",

            "description":
            "Download  videos in MP4 format."

        }
    )
@app.get("/ads.txt")
async def ads_txt():
    return FileResponse("ads.txt", media_type="text/plain")