import asyncio
import signal
import importlib
from contextlib import suppress

from ishu import (
    anon,
    app,
    config,
    db,
    logger,
    stop,
    userbot,
    yt,
    thumb,
)

from ishu.plugins import all_modules


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    await stop_event.wait()


async def main():
    await db.connect()

    await app.boot()
    await userbot.boot()
    # Backfill chats from the userbot's real dialogs (bots can't call
    # GetDialogs, so this must run AFTER userbot.boot() populates clients).
    await db.crawl_dialogs()
    await anon.boot()

    # Thumbnail initialization
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"ishu.plugins.{module}")

    logger.info(f"Loaded {len(all_modules)} modules.")

    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)

    app.bl_users.update(await db.get_blacklisted())

    await idle()
    await stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
