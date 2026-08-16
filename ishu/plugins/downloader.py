import os
import asyncio
import re
import aiohttp
from pyrogram import filters, types, enums

from ishu import app, yt, logger
from ishu.helpers.insta import download_instagram_reel


@app.on_message(filters.command(["song", "download"]) & ~app.bl_users)
async def song_downloader(_, m: types.Message):
    """
    Download YouTube Audio by Song Name or YouTube Link.
    Usage: /song <song name or link> or /download <song name or link>
    """
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text("<b>Usage:</b>\n<code>/song <song name or YouTube link></code>\n<code>/download <song name or YouTube link></code>")

    query = ""
    if len(m.command) >= 2:
        query = m.text.split(None, 1)[1].strip()
    elif m.reply_to_message and (m.reply_to_message.text or m.reply_to_message.caption):
        query = (m.reply_to_message.text or m.reply_to_message.caption).strip()

    if not query:
        return await m.reply_text("<b>Please provide a song name or YouTube link!</b>")

    status_msg = await m.reply_text("<b>Searching for song...</b>", quote=True)

    try:
        title, duration_min, duration_sec, thumbnail, vidid = await yt.details(query)
        await status_msg.edit_text(f"<b>Downloading audio:</b>\n<b>{title}</b>...")

        file_path = await yt.download(vidid, video=False)
        if not file_path or not os.path.exists(file_path):
            return await status_msg.edit_text("<b>Failed to download song. Please try again!</b>")

        await status_msg.edit_text("<b>Uploading audio...</b>")

        thumb_path = None
        if thumbnail:
            try:
                os.makedirs("cache", exist_ok=True)
                thumb_path = f"cache/thumb_{vidid}.jpg"
                if not os.path.exists(thumb_path):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(thumbnail, timeout=10) as resp:
                            if resp.status == 200:
                                with open(thumb_path, "wb") as f:
                                    f.write(await resp.read())
            except Exception as e:
                logger.warning(f"Thumbnail download failed for {vidid}: {e}")

        caption = f"<b>Title:</b> {title}\n<b>Duration:</b> {duration_min}\n<b>Downloaded via:</b> {app.name}"
        await m.reply_audio(
            audio=file_path,
            caption=caption,
            title=title,
            performer="YouTube",
            duration=duration_sec,
            thumb=thumb_path if (thumb_path and os.path.exists(thumb_path)) else None,
            quote=True,
        )
        await status_msg.delete()

        # Clean up local temporary files
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    except Exception as err:
        logger.error(f"Song downloader error: {err}")
        await status_msg.edit_text(f"<b>Error:</b> {err}")


@app.on_message(filters.command(["vsong", "video", "ytvideo", "vdownload", "ytdl"]) & ~app.bl_users)
async def video_downloader(_, m: types.Message):
    """
    Download YouTube Video by Name or Link.
    Usage: /video <video name or link> or /vsong <video name or link>
    """
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text("<b>Usage:</b>\n<code>/video <video name or YouTube link></code>\n<code>/vsong <video name or YouTube link></code>")

    query = ""
    if len(m.command) >= 2:
        query = m.text.split(None, 1)[1].strip()
    elif m.reply_to_message and (m.reply_to_message.text or m.reply_to_message.caption):
        query = (m.reply_to_message.text or m.reply_to_message.caption).strip()

    if not query:
        return await m.reply_text("<b>Please provide a video name or YouTube link!</b>")

    status_msg = await m.reply_text("<b>Searching for video...</b>", quote=True)

    try:
        title, duration_min, duration_sec, thumbnail, vidid = await yt.details(query)
        await status_msg.edit_text(f"<b>Downloading video:</b>\n<b>{title}</b>...")

        file_path = await yt.download(vidid, video=True)
        if not file_path or not os.path.exists(file_path):
            return await status_msg.edit_text("<b>Failed to download video. Please try again!</b>")

        await status_msg.edit_text("<b>Uploading video...</b>")

        thumb_path = None
        if thumbnail:
            try:
                os.makedirs("cache", exist_ok=True)
                thumb_path = f"cache/thumb_{vidid}.jpg"
                if not os.path.exists(thumb_path):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(thumbnail, timeout=10) as resp:
                            if resp.status == 200:
                                with open(thumb_path, "wb") as f:
                                    f.write(await resp.read())
            except Exception as e:
                logger.warning(f"Thumbnail download failed for {vidid}: {e}")

        caption = f"<b>Title:</b> {title}\n<b>Duration:</b> {duration_min}\n<b>Downloaded via:</b> {app.name}"
        await m.reply_video(
            video=file_path,
            caption=caption,
            duration=duration_sec,
            thumb=thumb_path if (thumb_path and os.path.exists(thumb_path)) else None,
            quote=True,
        )
        await status_msg.delete()

        # Clean up local temporary files
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    except Exception as err:
        logger.error(f"Video downloader error: {err}")
        await status_msg.edit_text(f"<b>Error:</b> {err}")


@app.on_message(filters.command(["insta", "reel", "ig"]) & ~app.bl_users)
async def insta_downloader(_, m: types.Message):
    """
    Download Instagram Reel/Post Video via link.
    Usage: /insta <instagram reel link> or /reel <instagram link>
    """
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text("<b>Usage:</b>\n<code>/insta <instagram reel link></code>\n<code>/reel <instagram reel link></code>")

    link = ""
    if len(m.command) >= 2:
        link = m.text.split(None, 1)[1].strip()
    elif m.reply_to_message and (m.reply_to_message.text or m.reply_to_message.caption):
        link = (m.reply_to_message.text or m.reply_to_message.caption).strip()

    if not link or "instagram.com" not in link:
        return await m.reply_text("<b>Please provide a valid Instagram link!</b>")

    status_msg = await m.reply_text("<b>Downloading Instagram Reel...</b>", quote=True)

    try:
        file_path, title = await download_instagram_reel(link)
        if not file_path or not os.path.exists(file_path):
            return await status_msg.edit_text("<b>Failed to download Instagram Reel. Please ensure the post is public.</b>")

        await status_msg.edit_text("<b>Uploading Reel...</b>")

        caption = f"<b>Instagram Reel</b>\n\n<b>Downloaded via:</b> {app.name}"
        await m.reply_video(
            video=file_path,
            caption=caption,
            quote=True,
        )
        await status_msg.delete()

        # Clean up temporary file
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

    except Exception as err:
        logger.error(f"Instagram downloader error: {err}")
        await status_msg.edit_text(f"<b>Error:</b> {err}")
