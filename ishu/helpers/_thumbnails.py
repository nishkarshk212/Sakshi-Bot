# Copyright (c) 2025 TheHamkerAlone 
# Licensed under the MIT License.
# This file is part of AloneX

import os
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from ishu import config
from ishu.helpers import Track

try:
    from unidecode import unidecode
except ImportError:
    def unidecode(text):
        return text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_TITLE_PATH = os.path.join(BASE_DIR, "font.ttf")
FONT_INFO_PATH = os.path.join(BASE_DIR, "font2.ttf")


def safe_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


class Thumbnail:
    def __init__(self):
        self.size = (1280, 720)

    async def start(self):
        os.makedirs("cache", exist_ok=True)

        if not os.path.exists(FONT_TITLE_PATH):
            print(f"Missing font: {FONT_TITLE_PATH}")

        if not os.path.exists(FONT_INFO_PATH):
            print(f"Missing font: {FONT_INFO_PATH}")

        return True

    async def save_thumb(self, output_path: str, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        for attempt in range(3):
            try:
                if url.startswith("http"):
                    async with aiohttp.ClientSession(headers=headers) as session:
                        async with session.get(url, timeout=15) as resp:
                            if resp.status == 200:
                                content = await resp.read()
                                with open(output_path, "wb") as f:
                                    f.write(content)
                                return output_path
            except Exception as e:
                if attempt == 2:
                    print(f"Error saving thumb: {e}")
                await asyncio.sleep(1)
        return output_path

    async def generate(self, song: Track) -> str:
        try:
            os.makedirs("cache", exist_ok=True)
            temp = f"cache/temp_{song.id}.jpg"
            final_path = f"cache/{song.id}.jpg"
            if os.path.exists(final_path):
                return final_path

            await self.save_thumb(temp, song.thumbnail)
            
            try:
                src = Image.open(temp).convert("RGBA")
            except Exception:
                try:
                    src = Image.new("RGBA", (1280, 720), (30, 30, 30, 255))
                except Exception:
                    return config.DEFAULT_THUMB

            # Dynamic font loading for proper sizes
            font_title = safe_font(FONT_TITLE_PATH, 34)
            font_info = safe_font(FONT_INFO_PATH, 24)
            font_time = safe_font(FONT_INFO_PATH, 20)
            font_brand = safe_font(FONT_TITLE_PATH, 26)

            W, H = self.size

            # --- 1. DARK BLURRED BACKGROUND ---
            # Crop source to 16:9 aspect ratio
            bg_ratio = W / H
            src_ratio = src.width / src.height
            if src_ratio > bg_ratio:
                new_w = int(src.height * bg_ratio)
                offset = (src.width - new_w) // 2
                bg = src.crop((offset, 0, offset + new_w, src.height))
            else:
                new_h = int(src.width / bg_ratio)
                offset = (src.height - new_h) // 2
                bg = src.crop((0, offset, src.width, offset + new_h))

            bg = bg.resize((W, H), Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(40))
            bg = bg.convert("RGBA")
            
            # Dark overlay
            bg_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 140))
            bg = Image.alpha_composite(bg, bg_overlay)

            # --- 2. CARD COMPONENT ---
            card_w, card_h = 900, 560
            card_x = (W - card_w) // 2
            card_y = (H - card_h) // 2 + 20  # Shift down slightly to balance brand header

            # Draw soft drop shadow behind the card
            shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.rounded_rectangle(
                (card_x - 4, card_y + 8, card_x + card_w + 4, card_y + card_h + 12),
                radius=40,
                fill=(0, 0, 0, 110),
            )
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(25))
            bg = Image.alpha_composite(bg, shadow_layer)

            # Create Card Layer
            card_img = Image.new("RGBA", (card_w, card_h), (245, 245, 245, 255))
            card_draw = ImageDraw.Draw(card_img)

            # --- 3. INNER COVER IMAGE ---
            cover_w, cover_h = 820, 320
            cover_x, cover_y = 40, 40
            cover_radius = 20

            cover_resized = ImageOps.fit(src, (cover_w, cover_h), Image.Resampling.LANCZOS)
            
            # Create cover mask for rounded corners
            cover_mask = Image.new("L", (cover_w, cover_h), 0)
            ImageDraw.Draw(cover_mask).rounded_rectangle(
                (0, 0, cover_w, cover_h), radius=cover_radius, fill=255
            )
            card_img.paste(cover_resized, (cover_x, cover_y), cover_mask)

            # --- 4. DETAILS SECTION ---
            # Title
            title_text = unidecode(str(song.title))
            def ellipsize(s, font, max_w):
                bbox = card_draw.textbbox((0, 0), s, font=font)
                if (bbox[2] - bbox[0]) <= max_w:
                    return s
                lo, hi = 1, len(s)
                best = "…"
                while lo <= hi:
                    mid = (lo + hi) // 2
                    cand = s[:mid].rstrip() + "…"
                    bbox = card_draw.textbbox((0, 0), cand, font=font)
                    if (bbox[2] - bbox[0]) <= max_w:
                        best = cand
                        lo = mid + 1
                    else:
                        hi = mid - 1
                return best

            title_str = ellipsize(title_text, font_title, 820)
            title_y = 385
            card_draw.text((40, title_y), title_str, fill=(20, 20, 20, 255), font=font_title)

            # Subtitle (Channel name & views)
            sub_text = song.channel_name or "YouTube"
            if song.view_count:
                sub_text += f"   ·   {song.view_count}"
            subtitle_str = ellipsize(sub_text, font_info, 820)
            subtitle_y = 435
            card_draw.text((40, subtitle_y), subtitle_str, fill=(100, 100, 100, 255), font=font_info)

            # --- 5. PROGRESS BAR ---
            bar_x = 40
            bar_y = 485
            bar_w = 820
            bar_h = 6
            # Track
            card_draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                radius=3,
                fill=(220, 220, 220, 255)
            )
            # Filled (35% default for visual playback representation)
            progress_pct = 0.35
            fill_w = int(bar_w * progress_pct)
            card_draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h),
                radius=3,
                fill=(229, 57, 53, 255)
            )
            # Slider thumb (red dot)
            thumb_radius = 6
            thumb_cx = bar_x + fill_w
            thumb_cy = bar_y + (bar_h // 2)
            card_draw.ellipse(
                (thumb_cx - thumb_radius, thumb_cy - thumb_radius, thumb_cx + thumb_radius, thumb_cy + thumb_radius),
                fill=(229, 57, 53, 255)
            )

            # Timestamps
            time_y = 505
            card_draw.text((40, time_y), "0:00", fill=(100, 100, 100, 255), font=font_time)
            
            duration_str = song.duration or "00:00"
            dur_bbox = card_draw.textbbox((0, 0), duration_str, font=font_time)
            dur_w = dur_bbox[2] - dur_bbox[0]
            card_draw.text((40 + 820 - dur_w, time_y), duration_str, fill=(100, 100, 100, 255), font=font_time)

            # --- 6. RED BOTTOM STRIP ---
            card_draw.rectangle(
                (0, card_h - 8, card_w, card_h),
                fill=(229, 57, 53, 255)
            )

            # Paste Card onto Background with Rounded Corners Mask
            card_mask = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(card_mask).rounded_rectangle(
                (0, 0, card_w, card_h), radius=35, fill=255
            )
            
            bg.paste(card_img, (card_x, card_y), card_mask)

            # Save final image
            out = bg.convert("RGB")
            out.save(final_path, "JPEG", quality=92, optimize=True)

            try:
                if os.path.exists(temp):
                    os.remove(temp)
            except Exception:
                pass

            return final_path

        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            import traceback
            traceback.print_exc()
            return config.DEFAULT_THUMB
