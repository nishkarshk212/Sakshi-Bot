import asyncio
import os
import re
import sys
import aiohttp
from ishu import logger

async def download_instagram_reel(url: str) -> tuple[str | None, str | None]:
    """
    Downloads an Instagram reel or video post.
    Returns (file_path, title/caption)
    """
    match = re.search(r"(?:reel|p|reels)/([A-Za-z0-9_-]+)", url)
    if not match:
        return None, None
    code = match.group(1)
    
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/insta_{code}.mp4"

    if os.path.exists(file_path) and os.path.getsize(file_path) > 10000:
        return file_path, f"Instagram Reel ({code})"

    headers_tg = {"User-Agent": "TelegramBot (like TelegramAuth)"}
    headers_browser = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }

    async with aiohttp.ClientSession() as session:
        # Method 1: DDInstagram / VXInstagram API proxy
        dd_urls = [
            f"https://ddinstagram.com/reel/{code}/",
            f"https://ddinstagram.com/p/{code}/",
            f"https://vxinstagram.com/reel/{code}/",
        ]
        for dd_url in dd_urls:
            try:
                async with session.get(dd_url, headers=headers_tg, timeout=8) as r:
                    if r.status == 200:
                        html = await r.text()
                        found = re.findall(r"property=\"og:video\"\s+content=\"([^\"]+)\"", html)
                        if not found:
                            found = re.findall(r"content=\"([^\"]+)\"\s+property=\"og:video\"", html)
                        if not found:
                            found = re.findall(r"https://[^\s\"\'<>]+\.mp4[^\s\"\'<>]*", html)
                        
                        for v_url in found:
                            v_clean = v_url.replace("&amp;", "&")
                            async with session.get(v_clean, headers=headers_browser, timeout=60) as vr:
                                if vr.status == 200:
                                    data = await vr.read()
                                    if len(data) > 10000:
                                        with open(file_path, "wb") as f:
                                            f.write(data)
                                        logger.info(f"DDInstagram download success for {code}: {len(data)} bytes")
                                        return file_path, f"Instagram Reel ({code})"
            except Exception as e:
                logger.debug(f"DDInstagram err for {dd_url}: {e}")

        # Method 2: InDown Scraper API
        try:
            async with session.get("https://indown.io/reels", headers=headers_browser, timeout=5) as r:
                if r.status == 200:
                    html = await r.text()
                    tokens = re.findall(r"name=\"_token\"\s+value=\"([^\"]+)\"", html)
                    if tokens:
                        data = {"referer": "https://indown.io/reels", "locale": "en", "_token": tokens[0], "link": url}
                        async with session.post("https://indown.io/download", data=data, headers=headers_browser, timeout=10) as r2:
                            if r2.status == 200:
                                res_html = await r2.text()
                                hrefs = re.findall(r"href=\"(https://[^\"]+)\"", res_html)
                                media_links = [h for h in hrefs if "cdninstagram" in h or ".mp4" in h or "fbcdn" in h or "indown" in h]
                                for m_link in media_links:
                                    m_clean = m_link.replace("&amp;", "&")
                                    async with session.get(m_clean, headers=headers_browser, timeout=60) as vr:
                                        if vr.status == 200:
                                            content = await vr.read()
                                            if len(content) > 10000:
                                                with open(file_path, "wb") as f:
                                                    f.write(content)
                                                logger.info(f"InDown success for {code}: {len(content)} bytes")
                                                return file_path, f"Instagram Reel ({code})"
        except Exception as e:
            logger.debug(f"InDown err: {e}")

        # Method 3: Direct yt-dlp fallback
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-warnings", "-q",
            "-o", file_path,
            url
        ]
        try:
            proc = await asyncio.create_subprocess_exec(*cmd)
            await proc.communicate()
            if os.path.exists(file_path) and os.path.getsize(file_path) > 10000:
                logger.info(f"yt-dlp success for {code}: {os.path.getsize(file_path)} bytes")
                return file_path, f"Instagram Reel ({code})"
        except Exception as e:
            logger.debug(f"yt-dlp insta err: {e}")

    return None, None
