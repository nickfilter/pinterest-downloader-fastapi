import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.download import router
from services.cleanup import cleanup_loop

# 所有路径基于代码位置，避免依赖进程工作目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()


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
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"title": title, "description": description},
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
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="downloader.html",
        context={
            "title": "How to use Downloader",
            "description": "Download videos in MP4 format.",
        },
    )


@app.get("/ads.txt")
async def ads_txt():
    return FileResponse(
        os.path.join(BASE_DIR, "ads.txt"),
        media_type="text/plain",
    )
