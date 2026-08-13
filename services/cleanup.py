"""下载文件清理：定期删除超过保留期的临时文件，防止磁盘被占满。"""
import asyncio
import logging
import os
import time

from services.downloader import DOWNLOAD_DIR

logger = logging.getLogger(__name__)

# 文件保留时长（秒），默认 24 小时，可用环境变量覆盖
FILE_MAX_AGE_SECONDS = int(os.environ.get("FILE_MAX_AGE_SECONDS", str(24 * 60 * 60)))
# 清理检查间隔（秒），默认 1 小时
CLEANUP_INTERVAL_SECONDS = int(os.environ.get("CLEANUP_INTERVAL_SECONDS", str(60 * 60)))


def clean_old_files() -> int:
    """删除超过保留期的文件，返回删除数量。"""
    if not os.path.isdir(DOWNLOAD_DIR):
        return 0

    now = time.time()
    removed = 0
    for name in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > FILE_MAX_AGE_SECONDS:
                os.remove(path)
                removed += 1
        except OSError as e:
            logger.warning("Failed to remove %s: %s", path, e)

    if removed:
        logger.info("Cleaned %d expired file(s) from %s", removed, DOWNLOAD_DIR)
    return removed


async def cleanup_loop() -> None:
    """后台循环：周期执行清理，异常时记录日志后继续。"""
    while True:
        try:
            clean_old_files()
        except Exception:
            logger.exception("Cleanup task failed")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
