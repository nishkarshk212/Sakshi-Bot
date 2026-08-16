import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

__version__ = "3.0.3"

from config import Config

config = Config()
config.check()

tasks = []
boot = time.time()

from ishu.core.bot import Bot
app = Bot()

from ishu.core.dir import ensure_dirs
ensure_dirs()

from ishu.core.userbot import Userbot
userbot = Userbot()

from ishu.core.mongo import MongoDB
db = MongoDB()

from ishu.core.lang import Language
lang = Language()

from ishu.core.telegram import Telegram
from ishu.core.youtube import YouTube

tg = Telegram()
yt = YouTube()

# Helpers
from ishu.helpers import Queue, Thumbnail

queue = Queue()
thumb = Thumbnail()

from ishu.core.calls import TgCall
anon = TgCall()

from ishu.helpers import font


async def stop() -> None:
    logger.info("Stopping...")

    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.exceptions.CancelledError:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()

    logger.info("Stopped.\n")
