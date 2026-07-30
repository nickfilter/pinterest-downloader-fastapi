import yt_dlp
import os
import uuid


DOWNLOAD_DIR = "downloads"


os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)



def download_video(url):


    filename = str(uuid.uuid4())


    output = (
        f"{DOWNLOAD_DIR}/"
        f"{filename}.%(ext)s"
    )


    options = {


        "outtmpl": output,


        "format":
        "bestvideo+bestaudio/best",


        "merge_output_format":
        "mp4",


        "noplaylist":
        True,


        "quiet":
        True

    }


    with yt_dlp.YoutubeDL(options) as ydl:


        info = ydl.extract_info(
            url,
            download=True
        )


        file_path = ydl.prepare_filename(
            info
        )


    if file_path.endswith(".webm"):

        new_path = file_path.replace(
            ".webm",
            ".mp4"
        )

        if os.path.exists(file_path):

            os.rename(
                file_path,
                new_path
            )

        file_path = new_path


    return file_path