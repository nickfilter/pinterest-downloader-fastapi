import os
import yt_dlp
import traceback

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)


COOKIE_FILE = os.path.join(
    BASE_DIR,
    "cookies.txt"
)



def get_video_info(url):


    is_youtube = (
        "youtube.com" in url
        or
        "youtu.be" in url
    )



    options = {


        # 只解析，不下载
        "format":
        "bestvideo+bestaudio/best",



        # 禁止播放列表
        "noplaylist":
        True,



        # 超时
        "socket_timeout":
        60,



        # 代理
        "proxy":
        "http://127.0.0.1:10808",



        # 不显示颜色日志
        "no_color":
        True,



        # YouTube优化
        "extractor_args":{


            "youtube":{


                "player_client":[

                    "android",
                    "web"

                ]

            }


        }


    }



    # 只有YouTube使用cookies

    if is_youtube and os.path.exists(COOKIE_FILE):


        options["cookiefile"] = COOKIE_FILE




    try:


        with yt_dlp.YoutubeDL(options) as ydl:


            info = ydl.extract_info(

                url,

                download=False

            )



            formats = info.get(
                "formats",
                []
            )



            video_url = None



            audio_url = None




            # 找mp4视频

            for f in reversed(formats):


                if (

                    f.get("vcodec") != "none"

                    and

                    f.get("acodec") != "none"

                    and

                    f.get("ext") == "mp4"

                ):


                    video_url = f.get(
                        "url"
                    )

                    break




            # 找音频


            for f in reversed(formats):


                if (

                    f.get("acodec") != "none"

                    and

                    f.get("vcodec") == "none"

                ):


                    audio_url = f.get(
                        "url"
                    )

                    break




            # 没找到使用默认


            if not video_url:

                video_url = info.get(
                    "url"
                )



            if not audio_url:

                audio_url = video_url




            return {

    "title": info.get("title") or "Video",

    "thumbnail": info.get("thumbnail"),

    "download_url": video_url or info.get("url")

}



    except Exception as e:

        # 打印完整错误到服务器控制台
        traceback.print_exc()

        return {


            "success":
            False,


            "error": "Download failed. Please try again."

        }