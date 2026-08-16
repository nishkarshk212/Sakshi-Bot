# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import re

from pyrogram import enums, errors, filters, types

from ishu import anon, app, config, db, lang, queue, tg, userbot, yt
from ishu.helpers import admin_check, buttons, can_manage_vc
from ishu.plugins import all_modules


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
@lang.language()
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


@app.on_callback_query(filters.regex("controls") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _controls(_, query: types.CallbackQuery):
    args = query.data.split()
    action, chat_id = args[1], int(args[2])
    qaction = len(args) == 4
    user = query.from_user.mention

    if not await db.get_call(chat_id):
        try:
            return await query.answer(query.lang["not_playing"], show_alert=True)
        except errors.QueryIdInvalid:
            try:
                await query.message.delete()
            except Exception:
                pass
            return

    if action == "status":
        return await query.answer()
    await query.answer(query.lang["processing"], show_alert=True)

    if action == "pause":
        if not await db.playing(chat_id):
            return await query.answer(
                query.lang["play_already_paused"], show_alert=True
            )
        await anon.pause(chat_id)
        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, query.lang["paused"], False)
            )
        status = query.lang["paused"]
        reply = query.lang["play_paused"].format(user)

    elif action == "resume":
        if await db.playing(chat_id):
            return await query.answer(query.lang["play_not_paused"], show_alert=True)
        await anon.resume(chat_id)
        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, query.lang["playing"], True)
            )
        reply = query.lang["play_resumed"].format(user)

    elif action == "skip":
        await anon.play_next(chat_id)
        status = query.lang["skipped"]
        reply = query.lang["play_skipped"].format(user)

    elif action == "force":
        pos, media = queue.check_item(chat_id, args[3])
        if not media or pos == -1:
            return await query.edit_message_text(query.lang["play_expired"])

        m_id = queue.get_current(chat_id).message_id
        queue.force_add(chat_id, media, remove=pos)
        try:
            await app.delete_messages(
                chat_id=chat_id, message_ids=[m_id, media.message_id], revoke=True
            )
            media.message_id = None
        except Exception:
            pass

        msg = await app.send_message(chat_id=chat_id, text=query.lang["play_next"])
        # Download the file if not already cached locally
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
        media.message_id = msg.id
        return await anon.play_media(chat_id, msg, media)

    elif action == "replay":
        media = queue.get_current(chat_id)
        media.user = user
        await anon.replay(chat_id)
        status = query.lang["replayed"]
        reply = query.lang["play_replayed"].format(user)

    elif action == "stop":
        await anon.stop(chat_id)
        status = query.lang["stopped"]
        reply = query.lang["play_stopped"].format(user)

    try:
        if action in ["skip", "replay", "stop"]:
            await query.message.reply_text(reply, quote=False)
            await query.message.delete()
        else:
            mtext = re.sub(
                r"\n\n<blockquote>.*?</blockquote>",
                "",
                query.message.caption.html or query.message.text.html,
                flags=re.DOTALL,
            )
            keyboard = buttons.controls(
                chat_id, status=status if action != "resume" else None,
                autoplay=await db.get_autoplay(chat_id),
            )
        await query.edit_message_text(
            f"{mtext}\n\n<blockquote>{reply}</blockquote>", reply_markup=keyboard
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^autoplay$|^autoplay\s") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    enable = not await db.get_autoplay(chat_id)
    await db.set_autoplay(chat_id, enable)
    mode = await db.get_autoplay_mode(chat_id)
    await query.answer(
        f"Autoplay {'enabled' if enable else 'disabled'}", show_alert=True
    )
    try:
        await query.edit_message_reply_markup(
            reply_markup=buttons.controls(chat_id, autoplay=enable, mode=mode)
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^autoplay_mode") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _autoplay_mode_cb(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    curr_mode = await db.get_autoplay_mode(chat_id)
    next_mode = {"vibe": "artist", "artist": "trending", "trending": "vibe"}.get(curr_mode, "vibe")
    await db.set_autoplay_mode(chat_id, next_mode)
    labels = {"vibe": "🎧 Vibe Radio", "artist": "🎤 Artist Radio", "trending": "🔥 Trending Hits"}
    await query.answer(f"Autoplay Mode: {labels[next_mode]}", show_alert=True)
    try:
        await query.edit_message_reply_markup(
            reply_markup=buttons.controls(chat_id, autoplay=await db.get_autoplay(chat_id), mode=next_mode)
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^youtube_menu") & ~app.bl_users)
@lang.language()
async def _youtube_menu_cb(_, query: types.CallbackQuery):
    args = query.data.split()
    chat_id = int(args[1]) if len(args) > 1 else query.message.chat.id
    from ishu.helpers._inline import _panel_state
    
    msg = query.message
    current_caption = msg.caption.html if msg.caption else (msg.text.html if msg.text else None)
    _panel_state[chat_id] = _panel_state.get(chat_id, {})
    _panel_state[chat_id]["menu_open"] = True
    if current_caption and "YouTube Music Category" not in current_caption:
        _panel_state[chat_id]["playing_caption"] = current_caption

    active_cat = _panel_state[chat_id].get("active_cat", "songs")
    link = _panel_state[chat_id].get("link")
    
    menu_text = (
        "<b><emoji id=5321505140199418151>🔴</emoji> YouTube Music Category & Filter Options:</b>\n\n"
        "Select a section to browse & stream Indian music:\n"
        "• <emoji id=5321505140199418151>🎵</emoji> <b>Songs</b> — High Quality Audio Hits\n"
        "• <emoji id=5233578612665375810>🎤</emoji> <b>Artists</b> — Popular Indian Artists\n"
        "• <emoji id=5462956611033117422>💿</emoji> <b>Albums</b> — Official Music Albums\n"
        "• <emoji id=6007817446398890097>📑</emoji> <b>Playlists</b> — Top Indian Charts & Mixes\n"
        "• <emoji id=5366477429223209600>🎬</emoji> <b>Music Videos</b> — Official HD Music Videos"
    )
    await query.answer("YouTube Music Category Options")
    try:
        if query.message.caption:
            await query.edit_message_caption(
                caption=menu_text,
                reply_markup=buttons.youtube_menu_markup(chat_id, active_cat=active_cat, link=link),
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            await query.edit_message_text(
                menu_text,
                reply_markup=buttons.youtube_menu_markup(chat_id, active_cat=active_cat, link=link),
                parse_mode=enums.ParseMode.HTML,
            )
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^yt_cat\s") & ~app.bl_users)
@lang.language()
async def _yt_cat_cb(_, query: types.CallbackQuery):
    args = query.data.split()
    cat_type = args[1]
    chat_id = int(args[2]) if len(args) > 2 else query.message.chat.id
    from ishu.helpers._inline import _panel_state
    
    _panel_state[chat_id] = _panel_state.get(chat_id, {})
    _panel_state[chat_id]["active_cat"] = cat_type
    link = _panel_state.get(chat_id, {}).get("link")
    
    # 1. Update autoplay settings to use this category
    await db.set_autoplay(chat_id, True)
    await db.set_autoplay_mode(chat_id, cat_type)
    
    # 2. Instantly update button colors on the menu panel
    try:
        await query.edit_message_reply_markup(
            reply_markup=buttons.youtube_menu_markup(chat_id, active_cat=cat_type, link=link)
        )
    except Exception:
        pass
    
    cat_labels = {
        "songs": "Songs",
        "artists": "Artists",
        "albums": "Albums",
        "playlists": "Playlists",
        "videos": "Music Videos",
    }
    
    await query.answer(f"Autoplay set to {cat_labels.get(cat_type, cat_type)} Mode ♾", show_alert=True)


@app.on_callback_query(filters.regex(r"^yt_menu_back") & ~app.bl_users)
@lang.language()
async def _yt_menu_back_cb(_, query: types.CallbackQuery):
    args = query.data.split()
    chat_id = int(args[1]) if len(args) > 1 else query.message.chat.id
    from ishu.helpers._inline import _panel_state
    
    _panel_state[chat_id] = _panel_state.get(chat_id, {})
    _panel_state[chat_id]["menu_open"] = False
    
    await query.answer()
    
    kb = buttons.controls(
        chat_id,
        autoplay=await db.get_autoplay(chat_id),
        mode=await db.get_autoplay_mode(chat_id),
    )
    
    saved_caption = _panel_state.get(chat_id, {}).get("playing_caption")
    if not saved_caption or "YouTube Music Category" in saved_caption:
        curr = queue.get_current(chat_id)
        if curr:
            _lang = await lang.get_lang(chat_id)
            short_title = curr.title.split("|")[0].split("(")[0].strip()
            if len(short_title) > 50:
                short_title = short_title[:47].rstrip() + "…"
            saved_caption = _lang["play_media"].format(
                getattr(curr, "url", config.SUPPORT_CHAT),
                short_title,
                getattr(curr, "duration", "3:30"),
                getattr(curr, "user", "User"),
            )
        else:
            saved_caption = "<b><emoji id=5039827436737397847>✨</emoji> Player Control Panel</b>"
            
    try:
        if query.message.caption:
            await query.edit_message_caption(
                caption=saved_caption,
                reply_markup=kb,
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            await query.edit_message_text(
                saved_caption,
                reply_markup=kb,
                parse_mode=enums.ParseMode.HTML,
            )
    except Exception:
        pass


@app.on_callback_query(filters.regex("help") & ~app.bl_users)
@lang.language()
async def _help(_, query: types.CallbackQuery):
    data = query.data.split()
    if len(data) == 1:
        bot_un = getattr(getattr(query, "_client", None), "me", None)
        username = getattr(bot_un, "username", None) or app.username or "bot"
        return await query.answer(url=f"https://t.me/{username}?start=help")

    if data[1] == "back":
        return await query.edit_message_text(
            text=query.lang["help_menu"], reply_markup=buttons.help_markup(query.lang)
        )
    elif data[1] == "close":
        try:
            await query.message.delete()
            return await query.message.reply_to_message.delete()
        except Exception:
            return

    await query.edit_message_text(
        text=query.lang[f"help_{data[1]}"],
        reply_markup=buttons.help_markup(query.lang, True),
    )


@app.on_callback_query(filters.regex("settings") & ~app.bl_users)
@lang.language()
@admin_check
async def _settings_cb(_, query: types.CallbackQuery):
    cmd = query.data.split()
    if len(cmd) == 1:
        return await query.answer()
    await query.answer(query.lang["processing"], show_alert=True)

    chat_id = query.message.chat.id
    _admin = await db.get_play_mode(chat_id)
    _delete = await db.get_cmd_delete(chat_id)
    _language = await db.get_lang(chat_id)

    if cmd[1] == "delete":
        _delete = not _delete
        await db.set_cmd_delete(chat_id, _delete)
    elif cmd[1] == "play":
        await db.set_play_mode(chat_id, _admin)
        _admin = not _admin
    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            _admin,
            _delete,
            _language,
            chat_id,
        )
    )


@app.on_callback_query(filters.regex("^stats_") & ~app.bl_users)
@lang.language()
async def _stats_cb(_, query: types.CallbackQuery):
    data = query.data.split("_")[1]
    if data == "close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    elif data == "back":
        admin_count = 0
        for chat_id in await db.get_chats():
            try:
                member = await app.get_chat_member(chat_id, app.me.id)
                if member.status == enums.ChatMemberStatus.ADMINISTRATOR:
                    admin_count += 1
            except Exception:
                pass
        text = (
            "<blockquote><b>SYSTEM STATUS\n"
            "──────────────────\n"
            "STATUS: ONLINE AND READY\n"
            "PING: FAST\n"
            f"CHATS: {admin_count}\n"
            "──────────────────\n"
            f"POWERED BY: {app.name}</b></blockquote>"
        )
        try:
            await query.edit_message_caption(
                caption=text,
                reply_markup=buttons.stats_key(),
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass
        return
    elif data == "net":
        assistants_count = len(userbot.clients)
        blocked_count = len(db.blacklisted) + len(app.bl_users)
        chats_count = len(await db.get_chats())
        users_count = len(await db.get_users())
        modules_count = len(all_modules)
        sudoers_count = len(app.sudoers)
        auto_leave = config.AUTO_LEAVE
        play_limit = config.DURATION_LIMIT // 60
        
        text = (
            f"<blockquote><b>{app.name} MAINFRAME\n"
            "──────────────────\n"
            f"ASSISTANTS: {assistants_count}\n"
            f"BLOCKED: {blocked_count}\n"
            f"CHATS: {chats_count}\n"
            f"USERS: {users_count}\n"
            f"MODULES: {modules_count}\n"
            f"SUDOERS: {sudoers_count}\n"
            "──────────────────\n"
            f"AUTO LEAVE: {auto_leave}\n"
            f"PLAY LIMIT: {play_limit} mins</b></blockquote>"
        )
        try:
            await query.edit_message_caption(
                caption=text,
                reply_markup=buttons.stats_net_key(),
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass


@app.on_callback_query(filters.regex("^clone_") & ~app.bl_users)
async def clone_callbacks(_, query: types.CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    async def safe_edit(txt: str, markup=None):
        if query.message and (query.message.photo or query.message.video or query.message.animation):
            try:
                return await query.edit_message_caption(caption=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except Exception:
                return await query.message.edit_caption(caption=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        else:
            try:
                return await query.edit_message_text(text=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            except Exception:
                return await query.message.edit_text(text=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

    if data in ["clone_main_menu", "clone_start"]:
        text = (
            "<b>Clone Bot Settings & Management Panel</b>\n\n"
            "Create and manage your own custom music & downloader bot for free!\n"
            "Select an option from the buttons below to configure your clone bot settings."
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_guide":
        text = (
            "<b>How to Clone Your Own Music Bot:</b>\n\n"
            "1. Open @BotFather on Telegram and send <code>/newbot</code>.\n"
            "2. Enter a name and username for your new bot.\n"
            "3. Copy your API Bot Token (e.g., <code>123456789:ABCdef...</code>).\n"
            "4. Send command in chat: <code>/clone &lt;bot_token&gt;</code>\n\n"
            "Your clone bot will start instantly!"
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_my_bots":
        clones = await db.get_user_clones(user_id)
        if not clones:
            text = (
                "<b>You haven't cloned any bots yet!</b>\n\n"
                "Use <code>/clone &lt;bot_token&gt;</code> to create your first clone bot."
            )
        else:
            text = "<b>Your Cloned Bots & Settings:</b>\n\n"
            for idx, c in enumerate(clones, 1):
                un = c.get("username", "bot")
                nm = c.get("name", "Music Bot")
                tok = c.get("bot_token", "")
                own_id = c.get("owner_id", user_id)
                lg = c.get("log_group") or "Not set"
                ass_un = c.get("assistant_username") or "Default"
                short_tok = tok[:10] + "..." if tok else "N/A"
                text += (
                    f"<b>{idx}.</b> {nm} (@{un})\n"
                    f"   • Token: <code>{short_tok}</code>\n"
                    f"   • Owner ID: <code>{own_id}</code>\n"
                    f"   • Log Group: <code>{lg}</code>\n"
                    f"   • Assistant: @{ass_un}\n\n"
                )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_set_owner":
        text = (
            "<b>Set Clone Bot Owner ID</b>\n\n"
            "To set or change the Owner User ID for your clone bot, use command:\n"
            "<code>/setowner &lt;bot_username&gt; &lt;owner_id&gt;</code>\n\n"
            "<b>Example:</b>\n<code>/setowner MyMusicBot 7408854697</code>"
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_set_log":
        text = (
            "<b>Set Clone Bot Log Group</b>\n\n"
            "To set a custom Log Supergroup/Channel for your clone bot, use command:\n"
            "<code>/setloggroup &lt;bot_username&gt; &lt;log_group_id&gt;</code>\n\n"
            "<b>Example:</b>\n<code>/setloggroup MyMusicBot -1001234567890</code>"
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_gen_session":
        text = (
            "<b>Generate Pyrogram v2 Session String</b>\n\n"
            "You can generate a session string right here in this bot!\n\n"
            "Click command: <code>/gensession</code>\n\n"
            "Follow the 3 quick steps:\n"
            "1. Send your Telegram phone number.\n"
            "2. Enter the OTP code received on Telegram.\n"
            "3. Enter 2FA Password (if enabled).\n\n"
            "Your Pyrogram v2 Session String will be generated instantly!"
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_set_assistant":
        text = (
            "<b>Set Clone Bot Voice Chat Assistant</b>\n\n"
            "To attach a dedicated Pyrogram Assistant session string to your clone bot, use command:\n"
            "<code>/setassistant &lt;bot_username&gt; [session_string]</code>\n\n"
            "<i>Note: If no session string is provided, the default assistant will be auto-generated and set!</i>"
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_remove_bot":
        text = (
            "<b>Remove & Stop Clone Bot</b>\n\n"
            "To delete and stop a cloned bot, use command:\n"
            "<code>/rmclone &lt;bot_username_or_token&gt;</code>"
        )
        await safe_edit(text, buttons.clone_panel_markup())
    elif data == "clone_back_start":
        user_mention = f'<a href="tg://user?id={query.from_user.id}">{query.from_user.first_name}</a>'
        b_un = getattr(bot_un, "username", None) or getattr(getattr(bot_un, "me", None), "username", None) or app.username
        b_nm = getattr(bot_un, "name", None) or getattr(getattr(bot_un, "me", None), "first_name", None) or app.name
        bot_mention = f'<a href="https://t.me/{b_un}">{b_nm}</a>'
        _lang = await lang.get_lang(query.message.chat.id)
        start_text = _lang["start_pm"].format(user_mention, bot_mention)
        await safe_edit(start_text, buttons.start_key(_lang, private=True, bot_username=b_un))
