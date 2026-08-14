
# Pinterest Video Downloader FastAPI

## Install

pip install -r requirements.txt

## Run

uvicorn main:app --reload

Open:

http://127.0.0.1:8000

## Docker

docker build -t pinterest-downloader .

# 基本运行
docker run -p 8000:8000 pinterest-downloader

# 持久化数据（建议）：下载文件、统计/设置数据库、cookies
docker run -p 8000:8000 \
  -v pinterest_downloads:/app/downloads \
  -v pinterest_stats:/app/stats.db \
  pinterest-downloader

镜像说明：
- 以非 root 用户 appuser 运行；下载目录、stats.db、cookies.txt、ads.txt 均需可写
- 单 worker 运行（api_guard 限流为内存态，多 worker 需 Redis）
- 端口可通过 PORT 环境变量覆盖
- 管理密码等配置通过环境变量传入，如 -e ADMIN_PASSWORD=your-password
