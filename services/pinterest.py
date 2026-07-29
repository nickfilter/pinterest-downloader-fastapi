
import re
import requests

async def extract_video(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        html = requests.get(url, headers=headers, timeout=15).text

        videos = re.findall(
            r'https?://[^"\\]+?\.mp4[^"\\]*',
            html
        )

        if videos:
            return {
                "success": True,
                "video": videos[0]
            }

        return {
            "success": False,
            "message": "No video found"
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
