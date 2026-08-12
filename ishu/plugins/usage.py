# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from ishu import app, config, db, lang
from ishu.helpers import buttons


# ── Usage text builder ────────────────────────────────────────────────────────

USAGE_STATS = """<blockquote><b><emoji id=6338968354157499266>💎</emoji> ꜱ ᴏ ɴ ɢ  ᴜ ꜱ ᴀ ɢ ᴇ  ꜱ ᴛ ᴀ ᴛ ꜱ</b></blockquote>

<blockquote><b><emoji id=5274055917766202507>📅</emoji> <u>Today's Playback (Last 24 Hours)</u></b>
<emoji id=5470135030393090150>🎵</emoji> <b>Audio Songs Played:</b> <code>{today_audio}</code>
<emoji id=5321505140199418151>🎬</emoji> <b>Video Songs Played:</b> <code>{today_video}</code>
<emoji id=6242538306773457661>⚡</emoji> <b>Total Played Today:</b> <code>{today_total}</code></blockquote>

<blockquote><b><emoji id=5352629724516458059>🌐</emoji> <u>Overall Playback (All Time)</u></b>
<emoji id=5463107823946717464>🎵</emoji> <b>Overall Audio Songs:</b> <code>{overall_audio}</code>
<emoji id=5937999673510858217>🎬</emoji> <b>Overall Video Songs:</b> <code>{overall_video}</code>
<emoji id=6228704973027284984>🔥</emoji> <b>Overall Total Songs:</b> <code>{overall_total}</code></blockquote>"""


USAGE_AUDIO = """<emoji id=5470135030393090150>🎵</emoji> <u><b>Audio Play Commands</b></u>

<b>Basic:</b>
  <code>/play &lt;song name&gt;</code>
  → Searches YouTube and plays the best match as audio.

  <code>/play &lt;YouTube URL&gt;</code>
  → Plays the given YouTube link directly.

  <code>/play</code>  (reply to an audio/voice message)
  → Plays the replied audio file.

<b>Force Play</b> (skip queue, play immediately):
  <code>/playforce &lt;song name or URL&gt;</code>
  → Bypasses the queue and starts playing right away.

  <code>/play -f &lt;song name or URL&gt;</code>
  → Same as /playforce.

<b>Playlist:</b>
  <code>/play &lt;YouTube Playlist URL&gt;</code>
  → Adds all songs from the playlist to the queue.

<b>Aliases:</b>  <code>/play</code>  •  <code>/playforce</code>"""


USAGE_VIDEO = """<emoji id=5321505140199418151>🎬</emoji> <u><b>Video Play Commands</b></u>

<b>Basic:</b>
  <code>/vplay &lt;song/video name&gt;</code>
  → Searches YouTube and streams the video in the voice chat.

  <code>/vplay &lt;YouTube URL&gt;</code>
  → Streams the given YouTube video directly.

  <code>/vplay</code>  (reply to a video message)
  → Plays the replied video file in the voice chat.

<b>Force Play</b> (skip queue, play immediately):
  <code>/vplayforce &lt;video name or URL&gt;</code>
  → Bypasses the queue and streams video right away.

  <code>/vplay -f &lt;video name or URL&gt;</code>
  → Same as /vplayforce.

<b>Aliases:</b>  <code>/vplay</code>  •  <code>/vplayforce</code>

<b>Note:</b> Video mode requires the voice chat to support screen sharing."""


USAGE_CONTROLS = """<emoji id=6242538306773457661>⚡</emoji> <u><b>Playback Control Commands</b></u>

<b>In-chat Controls:</b>
  <code>/pause</code>      — Pause the current stream
  <code>/resume</code>     — Resume a paused stream
  <code>/skip</code>       — Skip to the next song in queue
  <code>/stop</code>       — Stop streaming and clear the queue
  <code>/replay</code>     — Replay the current song from beginning

<b>Seek (jump to time):</b>
  <code>/seek &lt;seconds&gt;</code>     — Jump forward N seconds
    Example: <code>/seek 60</code>  →  skips ahead 1 minute
  <code>/seekback &lt;seconds&gt;</code> — Jump backward N seconds
    Example: <code>/seekback 30</code>  →  goes back 30 seconds

<b>Queue:</b>
  <code>/queue</code>   — Show all songs in the current queue
  <code>/loop &lt;count&gt;</code>  — Loop the current song N times"""


USAGE_EXAMPLES = """<emoji id=6228704973027284984>🔥</emoji> <u><b>Quick Examples</b></u>

<b>Play a song by name:</b>
  <code>/play Blinding Lights</code>

<b>Play a YouTube link:</b>
  <code>/play https://youtu.be/dQw4w9WgXcQ</code>

<b>Play a YouTube playlist:</b>
  <code>/play https://youtube.com/playlist?list=PLxxx</code>

<b>Play a video:</b>
  <code>/vplay Blinding Lights official video</code>

<b>Force play (interrupt queue):</b>
  <code>/playforce Tum Hi Ho</code>
  <code>/play -f Shape of You</code>

<b>Play & seek to 1 min 30 sec:</b>
  <code>/play Perfect</code>  then  <code>/seek 90</code>

<b>Reply to play:</b>
  Reply to any audio/video file with <code>/play</code> or <code>/vplay</code>"""


USAGE_TIPS = """<emoji id=5463107823946717464>🎵</emoji> <u><b>Tips & Notes</b></u>

<b>Download & Streaming:</b>
  • Railway YT API — self-hosted YouTube proxy (Active)

<b>Streaming:</b>
  • Songs start playing instantly via stream URL (no download wait).
  • Queued songs download in the background while the current one plays.
  • Downloaded files are automatically deleted after each song finishes.

<b>Queue limit:</b>  {queue_limit} songs per group
<b>Duration limit:</b>  {duration_limit} minutes max per song

<b>Need help?</b>  <a href={support}>Support Chat</a>"""


# ── Keyboard helpers ──────────────────────────────────────────────────────────

def _usage_keyboard(page: str) -> types.InlineKeyboardMarkup:
    """Inline keyboard for navigating between usage sections."""
    nav = {
        "stats":    ("Play Stats", "usage_stats",    "6338968354157499266"),
        "audio":    ("Audio",      "usage_audio",    "5470135030393090150"),
        "video":    ("Video",      "usage_video",    "5321505140199418151"),
        "controls": ("Controls",   "usage_controls", "6242538306773457661"),
        "examples": ("Examples",   "usage_examples", "6228704973027284984"),
        "tips":     ("Tips",       "usage_tips",     "5463107823946717464"),
    }
    rows = []
    row  = []
    for key, (label, data, emoji_id) in nav.items():
        btn = types.InlineKeyboardButton(
            f"› {label} ‹" if key == page else label,
            callback_data=data,
            style=enums.ButtonStyle.SUCCESS if key == page else enums.ButtonStyle.PRIMARY,
            icon_custom_emoji_id=emoji_id,
        )
        row.append(btn)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        types.InlineKeyboardButton(
            "Close",
            callback_data="usage_close",
            style=enums.ButtonStyle.DANGER,
        )
    ])
    return types.InlineKeyboardMarkup(rows)


async def _page_text(page: str, duration_limit: int, queue_limit: int, support: str) -> str:
    if page == "stats":
        stats = await db.get_play_usage_stats()
        return USAGE_STATS.format(**stats)
    pages = {
        "audio":    USAGE_AUDIO,
        "video":    USAGE_VIDEO,
        "controls": USAGE_CONTROLS,
        "examples": USAGE_EXAMPLES,
        "tips":     USAGE_TIPS.format(
            queue_limit=queue_limit,
            duration_limit=duration_limit,
            support=support,
        ),
    }
    return pages.get(page, USAGE_AUDIO)


# ── /usage command ────────────────────────────────────────────────────────────

@app.on_message(
    filters.command(["usage", "help2", "commands", "cmds"])
    & ~app.bl_users
)
@lang.language()
async def usage_handler(_, m: types.Message) -> None:
    """Send the interactive usage guide with playback stats."""
    text = await _page_text(
        "stats",
        duration_limit=config.DURATION_LIMIT // 60,
        queue_limit=config.QUEUE_LIMIT,
        support=config.SUPPORT_CHAT,
    )
    await m.reply_text(
        text=text,
        reply_markup=_usage_keyboard("stats"),
        quote=True,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ── Callback handler for page navigation ─────────────────────────────────────

@app.on_callback_query(
    filters.regex(r"^usage_(stats|audio|video|controls|examples|tips|close)$")
    & ~app.bl_users
)
async def usage_cb(_, query: types.CallbackQuery) -> None:
    action = query.data.split("_", 1)[1]

    if action == "close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    text = await _page_text(
        action,
        duration_limit=config.DURATION_LIMIT // 60,
        queue_limit=config.QUEUE_LIMIT,
        support=config.SUPPORT_CHAT,
    )
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=_usage_keyboard(action),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await query.answer()
    except Exception:
        await query.answer("Already on this page.", show_alert=False)
