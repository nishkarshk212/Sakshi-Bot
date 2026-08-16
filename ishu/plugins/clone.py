from pyrogram import filters, types, enums
from ishu import app, db, logger
from ishu.core.clone import boot_single_clone, stop_single_clone, cloned_clients, cloned_assistants


@app.on_message(filters.command(["clone"]) & ~app.bl_users)
async def clone_bot_handler(_, m: types.Message):
    """
    Clone this music bot using your own Bot Token, Log Group & Assistant Session!
    Usage: /clone <bot_token> [log_group_id] [assistant_session]
    """
    if len(m.command) < 2:
        return await m.reply_text(
            "<b>Clone Music Bot Feature</b>\n\n"
            "You can create your own clone of this music bot for free!\n\n"
            "<b>How to clone:</b>\n"
            "1. Go to @BotFather and create a new bot using <code>/newbot</code>.\n"
            "2. Copy your bot API Token (e.g. <code>123456789:ABCdef...</code>).\n"
            "3. Send: <code>/clone <bot_token> [log_group_id] [assistant_session]</code> here!\n\n"
            "<b>Clone Management Commands:</b>\n"
            "• <code>/cloned</code> — List your cloned bots, owners & log groups\n"
            "• <code>/setowner <bot_username> <owner_id></code> — Set owner ID for a clone bot\n"
            "• <code>/setloggroup <bot_username> <log_group_id></code> — Set log group ID for a clone bot\n"
            "• <code>/setassistant <bot_username> <session_string></code> — Set Assistant for a clone\n"
            "• <code>/rmclone <username/token></code> — Remove a cloned bot",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.clone_panel_markup(),
            quote=True,
        )

    args = m.text.split()
    bot_token = args[1].strip()
    user_id = m.from_user.id
    log_group = None
    session_string = None

    if len(args) > 2:
        val = args[2].strip()
        if val.startswith("-") or val.isdigit():
            try:
                log_group = int(val)
            except ValueError:
                pass
            if len(args) > 3:
                session_string = args[3].strip()
        else:
            session_string = val

    status_msg = await m.reply_text("<b>Verifying bot token & starting clone...</b>", quote=True)

    try:
        ok, username, name_or_err, ass_info = await boot_single_clone(
            bot_token=bot_token,
            user_id=user_id,
            session_string=session_string,
            owner_id=user_id,
            log_group=log_group,
        )
        if ok:
            log_info = str(log_group) if log_group else "Not set"
            await status_msg.edit_text(
                f"<b>Bot Cloned Successfully!</b>\n\n"
                f"<b>Bot Name:</b> {name_or_err}\n"
                f"<b>Bot Username:</b> @{username}\n"
                f"<b>Owner ID:</b> <code>{user_id}</code>\n"
                f"<b>Log Group:</b> <code>{log_info}</code>\n"
                f"<b>Assistant:</b> {ass_info}\n\n"
                f"Your clone bot @{username} is online and ready!",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=buttons.clone_panel_markup(),
            )
        else:
            await status_msg.edit_text(
                f"<b>Failed to Clone Bot:</b>\n<code>{name_or_err}</code>\n\n"
                f"Please make sure your bot token is correct and valid from @BotFather.",
                parse_mode=enums.ParseMode.HTML,
            )
    except Exception as err:
        logger.error(f"Clone error for user {user_id}: {err}")
        await status_msg.edit_text(f"<b>Error cloning bot:</b> {err}")


@app.on_message(filters.command(["setowner"]) & ~app.bl_users)
async def set_owner_handler(_, m: types.Message):
    """
    Set or update Owner ID for a cloned bot.
    Usage: /setowner <bot_username_or_token> <owner_id>
    """
    if len(m.command) < 3:
        return await m.reply_text(
            "<b>Usage:</b>\n<code>/setowner <bot_username or bot_token> <new_owner_id></code>",
            quote=True,
        )

    query = m.command[1].strip()
    try:
        new_owner_id = int(m.command[2].strip())
    except ValueError:
        return await m.reply_text("<b>Invalid Owner ID! Must be a numeric User ID.</b>", quote=True)

    user_id = m.from_user.id
    clones = await db.get_user_clones(user_id)
    target_clone = None
    for c in clones:
        if c.get("bot_token") == query or c.get("username", "").lower() == query.lstrip("@").lower():
            target_clone = c
            break

    if not target_clone:
        return await m.reply_text("<b>Could not find a cloned bot created by you matching that query!</b>", quote=True)

    try:
        bot_token = target_clone["bot_token"]
        await db.add_clone(
            bot_token=bot_token,
            user_id=target_clone.get("user_id", user_id),
            username=target_clone.get("username", ""),
            name=target_clone.get("name", "Clone Bot"),
            session_string=target_clone.get("session_string"),
            owner_id=new_owner_id,
            log_group=target_clone.get("log_group"),
        )
        await m.reply_text(
            f"<b>Owner ID updated for @{target_clone.get('username')}!</b>\n"
            f"<b>New Owner ID:</b> <code>{new_owner_id}</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.clone_panel_markup(),
            quote=True,
        )
    except Exception as err:
        logger.error(f"Set owner error: {err}")
        await m.reply_text(f"<b>Error setting owner:</b> {err}", quote=True)


@app.on_message(filters.command(["setloggroup", "setlogger", "setlog"]) & ~app.bl_users)
async def set_loggroup_handler(_, m: types.Message):
    """
    Set or update Log Group / Channel ID for a cloned bot.
    Usage: /setloggroup <bot_username_or_token> <log_group_id>
    """
    if len(m.command) < 3:
        return await m.reply_text(
            "<b>Usage:</b>\n<code>/setloggroup <bot_username or bot_token> <log_group_id></code>",
            quote=True,
        )

    query = m.command[1].strip()
    try:
        new_log_group = int(m.command[2].strip())
    except ValueError:
        return await m.reply_text("<b>Invalid Log Group ID! Must be a chat ID like -1001234567890.</b>", quote=True)

    user_id = m.from_user.id
    clones = await db.get_user_clones(user_id)
    target_clone = None
    for c in clones:
        if c.get("bot_token") == query or c.get("username", "").lower() == query.lstrip("@").lower():
            target_clone = c
            break

    if not target_clone:
        return await m.reply_text("<b>Could not find a cloned bot created by you matching that query!</b>", quote=True)

    try:
        bot_token = target_clone["bot_token"]
        await db.add_clone(
            bot_token=bot_token,
            user_id=target_clone.get("user_id", user_id),
            username=target_clone.get("username", ""),
            name=target_clone.get("name", "Clone Bot"),
            session_string=target_clone.get("session_string"),
            owner_id=target_clone.get("owner_id", user_id),
            log_group=new_log_group,
        )
        await m.reply_text(
            f"<b>Log Group ID updated for @{target_clone.get('username')}!</b>\n"
            f"<b>New Log Group:</b> <code>{new_log_group}</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.clone_panel_markup(),
            quote=True,
        )
    except Exception as err:
        logger.error(f"Set log group error: {err}")
        await m.reply_text(f"<b>Error setting log group:</b> {err}", quote=True)


@app.on_message(filters.command(["setassistant", "setass"]) & ~app.bl_users)
async def set_assistant_handler(_, m: types.Message):
    """
    Set or update Assistant Pyrogram Session for a cloned bot.
    Usage: /setassistant <bot_username_or_token> [assistant_session_string]
    If session_string is omitted, automatically sets the default Assistant session!
    """
    if len(m.command) < 2:
        return await m.reply_text(
            "<b>Usage:</b>\n<code>/setassistant <bot_username or bot_token> [assistant_session_string]</code>\n\n"
            "<i>If no session string is provided, the default assistant session will be auto-configured and set!</i>",
            quote=True,
        )

    args = m.text.split(None, 2)
    query = args[1].strip()
    session_string = args[2].strip() if len(args) > 2 else config.SESSION1
    user_id = m.from_user.id

    clones = await db.get_user_clones(user_id)
    target_clone = None
    for c in clones:
        if c.get("bot_token") == query or c.get("username", "").lower() == query.lstrip("@").lower():
            target_clone = c
            break

    if not target_clone:
        return await m.reply_text("<b>Could not find a cloned bot created by you matching that query!</b>", quote=True)

    status_msg = await m.reply_text("<b>Auto-configuring Assistant Pyrogram Session...</b>", quote=True)

    try:
        bot_token = target_clone["bot_token"]
        await stop_single_clone(bot_token)
        ok, username, name_or_err, ass_info = await boot_single_clone(
            bot_token=bot_token,
            user_id=user_id,
            username=target_clone.get("username"),
            name=target_clone.get("name"),
            session_string=session_string,
            owner_id=target_clone.get("owner_id", user_id),
            log_group=target_clone.get("log_group"),
        )
        if ok:
            await status_msg.edit_text(
                f"<b>Assistant Auto-Configured & Set Successfully!</b>\n\n"
                f"<b>Bot Username:</b> @{username}\n"
                f"<b>Assistant:</b> {ass_info}\n\n"
                f"Your clone bot will now use assistant {ass_info} for voice chats!",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=buttons.clone_panel_markup(),
            )
        else:
            await status_msg.edit_text(f"<b>Failed to connect Assistant:</b> {name_or_err}")
    except Exception as err:
        logger.error(f"Set assistant error: {err}")
        await status_msg.edit_text(f"<b>Error:</b> {err}")


@app.on_message(filters.command(["cloned", "myclones"]) & ~app.bl_users)
async def list_user_clones(_, m: types.Message):
    """
    List all cloned bots created by the user along with Owner, Log Group & Assistant info.
    Usage: /cloned
    """
    user_id = m.from_user.id
    clones = await db.get_user_clones(user_id)
    if not clones:
        return await m.reply_text(
            "<b>You haven't cloned any bots yet!</b>\n"
            "Use <code>/clone <bot_token> [log_group_id] [assistant_session]</code> to create your own bot.",
            reply_markup=buttons.clone_panel_markup(),
            quote=True,
        )

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

    text += (
        "<i>Management Commands:</i>\n"
        "• <code>/setowner <bot_username> <owner_id></code>\n"
        "• <code>/setloggroup <bot_username> <log_group_id></code>\n"
        "• <code>/setassistant <bot_username> <session_string></code>"
    )
    await m.reply_text(
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.clone_panel_markup(),
        quote=True,
    )


@app.on_message(filters.command(["rmclone", "delclone"]) & ~app.bl_users)
async def remove_clone_handler(_, m: types.Message):
    """
    Remove a cloned bot.
    Usage: /rmclone <username or token>
    """
    if len(m.command) < 2:
        return await m.reply_text("<b>Usage:</b>\n<code>/rmclone <bot_username or bot_token></code>", quote=True)

    query = m.command[1].strip()
    status_msg = await m.reply_text("<b>Removing cloned bot & assistant...</b>", quote=True)

    success = await stop_single_clone(query)
    if success:
        await status_msg.edit_text(
            f"<b>Cloned bot <code>{query}</code> removed & stopped successfully!</b>",
            reply_markup=buttons.clone_panel_markup(),
        )
    else:
        await status_msg.edit_text(f"<b>Could not find or remove clone <code>{query}</code>.</b>")


@app.on_message(filters.command(["gensession", "genstring", "string", "stringfather"]) & ~app.bl_users)
async def gen_session_handler(_, m: types.Message):
    """
    Generate Pyrogram Session String using StringFather Bot.
    """
    markup = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton(text="Generate Session String", url="https://t.me/StringFatherBot"),
        ]
    ])
    await m.reply_text(
        "<b>Generate Pyrogram Session String</b>\n\n"
        "You can generate a Pyrogram v2 Session String for your clone bot assistant using @StringFatherBot on Telegram!\n\n"
        "1. Click the button below to open @StringFatherBot.\n"
        "2. Choose <b>Pyrogram v2</b> session format.\n"
        "3. Enter your phone number and OTP code.\n"
        "4. Copy the generated session string and set it for your clone bot using:\n"
        "<code>/setassistant &lt;bot_username&gt; &lt;session_string&gt;</code>\n\n"
        "<i>Note: If you leave session_string blank, the default master assistant is auto-assigned!</i>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=markup,
        quote=True,
    )
