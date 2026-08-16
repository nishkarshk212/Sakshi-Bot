import functools
import re
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

SMOOTH_MAP = {
    "a": "ᴧ", "A": "ᴧ",
    "b": "ʙ", "B": "ʙ",
    "c": "ᴄ", "C": "ᴄ",
    "d": "ᴅ", "D": "ᴅ",
    "e": "є", "E": "є",
    "f": "ғ", "F": "ғ",
    "g": "ɢ", "G": "ɢ",
    "h": "ʜ", "H": "ʜ",
    "i": "ɪ", "I": "ɪ",
    "j": "ᴊ", "J": "ᴊ",
    "k": "ᴋ", "K": "ᴋ",
    "l": "ʟ", "L": "ʟ",
    "m": "ϻ", "M": "ϻ",
    "n": "η", "N": "η",
    "o": "σ", "O": "σ",
    "p": "ᴘ", "P": "ᴘ",
    "q": "q", "Q": "Q",
    "r": "ʀ", "R": "ʀ",
    "s": "s", "S": "s",
    "t": "ᴛ", "T": "ᴛ",
    "u": "υ", "U": "υ",
    "v": "ᴠ", "V": "ᴠ",
    "w": "ᴡ", "W": "ᴡ",
    "x": "x", "X": "x",
    "y": "ʏ", "Y": "ʏ",
    "z": "ᴢ", "Z": "ᴢ",
}


def apply_smooth_to_text(plain_text: str) -> str:
    return "".join(SMOOTH_MAP.get(c, c) for c in plain_text)


def to_smooth_font(html_text: str) -> str:
    if not html_text or not isinstance(html_text, str):
        return html_text
    pattern = re.compile(r"(<code>.*?</code>|<pre>.*?</pre>|<[^>]+>|https?://[^\s<\"]+)", re.DOTALL | re.IGNORECASE)
    parts = []
    last_end = 0
    for match in pattern.finditer(html_text):
        start, end = match.span()
        if start > last_end:
            parts.append(apply_smooth_to_text(html_text[last_end:start]))
        token = match.group(0)
        if token.startswith("<") or token.startswith("http"):
            parts.append(token)
        else:
            parts.append(apply_smooth_to_text(token))
        last_end = end
    if last_end < len(html_text):
        parts.append(apply_smooth_to_text(html_text[last_end:]))
    return "".join(parts)


def patch_inline_keyboard(reply_markup):
    """Optionally apply smooth font to button labels if reply_markup is an InlineKeyboardMarkup."""
    if not reply_markup or not isinstance(reply_markup, InlineKeyboardMarkup):
        return reply_markup
    try:
        new_rows = []
        for row in reply_markup.inline_keyboard:
            new_row = []
            for btn in row:
                if getattr(btn, "text", None):
                    btn.text = to_smooth_font(btn.text)
                new_row.append(btn)
            new_rows.append(new_row)
        reply_markup.inline_keyboard = new_rows
    except Exception:
        pass
    return reply_markup


def patch_pyrogram_for_smooth_font():
    """Patch Pyrogram methods to automatically transform all message texts and captions to smooth font."""

    # 1. Client.send_message
    orig_send_message = Client.send_message
    @functools.wraps(orig_send_message)
    async def smooth_send_message(self, chat_id, text, *args, **kwargs):
        if text and isinstance(text, str):
            text = to_smooth_font(text)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_send_message(self, chat_id, text, *args, **kwargs)
    Client.send_message = smooth_send_message

    # 2. Client.edit_message_text
    orig_edit_message_text = Client.edit_message_text
    @functools.wraps(orig_edit_message_text)
    async def smooth_edit_message_text(self, chat_id, message_id, text=None, *args, **kwargs):
        if text and isinstance(text, str):
            text = to_smooth_font(text)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_edit_message_text(self, chat_id, message_id, text=text, *args, **kwargs)
    Client.edit_message_text = smooth_edit_message_text

    # 3. Client.edit_message_caption
    orig_edit_message_caption = Client.edit_message_caption
    @functools.wraps(orig_edit_message_caption)
    async def smooth_edit_message_caption(self, chat_id, message_id, caption=None, *args, **kwargs):
        if caption and isinstance(caption, str):
            caption = to_smooth_font(caption)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_edit_message_caption(self, chat_id, message_id, caption=caption, *args, **kwargs)
    Client.edit_message_caption = smooth_edit_message_caption

    # 4. Message.reply_text / reply
    orig_reply_text = Message.reply_text
    @functools.wraps(orig_reply_text)
    async def smooth_reply_text(self, text, *args, **kwargs):
        if text and isinstance(text, str):
            text = to_smooth_font(text)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_reply_text(self, text, *args, **kwargs)
    Message.reply_text = smooth_reply_text
    Message.reply = smooth_reply_text

    # 5. Message.edit_text / edit
    orig_msg_edit_text = Message.edit_text
    @functools.wraps(orig_msg_edit_text)
    async def smooth_msg_edit_text(self, text, *args, **kwargs):
        if text and isinstance(text, str):
            text = to_smooth_font(text)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_msg_edit_text(self, text, *args, **kwargs)
    Message.edit_text = smooth_msg_edit_text
    Message.edit = smooth_msg_edit_text

    # 6. Message.edit_caption
    orig_msg_edit_caption = Message.edit_caption
    @functools.wraps(orig_msg_edit_caption)
    async def smooth_msg_edit_caption(self, caption=None, *args, **kwargs):
        if caption and isinstance(caption, str):
            caption = to_smooth_font(caption)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_msg_edit_caption(self, caption=caption, *args, **kwargs)
    Message.edit_caption = smooth_msg_edit_caption

    # 7. Media sending: Client.send_photo, send_audio, send_video
    orig_send_photo = Client.send_photo
    @functools.wraps(orig_send_photo)
    async def smooth_send_photo(self, chat_id, photo, caption=None, *args, **kwargs):
        if caption and isinstance(caption, str):
            caption = to_smooth_font(caption)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_send_photo(self, chat_id, photo, caption=caption, *args, **kwargs)
    Client.send_photo = smooth_send_photo

    orig_send_audio = Client.send_audio
    @functools.wraps(orig_send_audio)
    async def smooth_send_audio(self, chat_id, audio, caption=None, *args, **kwargs):
        if caption and isinstance(caption, str):
            caption = to_smooth_font(caption)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_send_audio(self, chat_id, audio, caption=caption, *args, **kwargs)
    Client.send_audio = smooth_send_audio

    orig_send_video = Client.send_video
    @functools.wraps(orig_send_video)
    async def smooth_send_video(self, chat_id, video, caption=None, *args, **kwargs):
        if caption and isinstance(caption, str):
            caption = to_smooth_font(caption)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = patch_inline_keyboard(kwargs["reply_markup"])
        return await orig_send_video(self, chat_id, video, caption=caption, *args, **kwargs)
    Client.send_video = smooth_send_video


# Apply patch immediately when module is imported
patch_pyrogram_for_smooth_font()
