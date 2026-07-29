
# Pinterest Video Downloader FastAPI

## Install

pip install -r requirements.txt

## Run

uvicorn main:app --reload

Open:

http://127.0.0.1:8000

## Docker

docker build -t pinterest-downloader .

docker run -p 8000:8000 pinterest-downloader
