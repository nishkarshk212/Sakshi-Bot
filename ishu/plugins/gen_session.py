import asyncio
import re
from pyrogram import filters, types, enums, errors, Client
from ishu import app, db, config, logger
from ishu.helpers import buttons

# Temporary state storage for active session generation sessions
GEN_SESSIONS = {}
USER_TEMP_SESSIONS = {}


def clean_gen(user_id: int):
    """Clean up and disconnect client for a user."""
    sess = GEN_SESSIONS.pop(user_id, None)
    if sess and sess.get("client"):
        try:
            asyncio.create_task(sess["client"].disconnect())
        except Exception:
            pass


async def send_session_success(user_id: int, status_msg: types.Message, string_session: str):
    """Display generated session string along with interactive cloned bot selection buttons."""
    USER_TEMP_SESSIONS[user_id] = string_session
    clones = await db.get_user_clones(user_id)

    text = (
        "<b>Pyrogram v2 Session String Generated Successfully!</b>\n\n"
        f"<code>{string_session}</code>\n\n"
        "<b>Warning:</b> Keep your session string private and never share it with untrusted persons!\n\n"
    )

    rows = []
    if clones:
        text += "<b>Select which cloned bot you want to attach this Assistant to:</b>"
        for idx, c in enumerate(clones):
            un = c.get("username", "bot")
            nm = c.get("name", "Clone Bot")
            rows.append([
                types.InlineKeyboardButton(
                    text=f"Set for {nm} (@{un})",
                    callback_data=f"setass_clone_{idx}"
                )
            ])
    else:
        text += (
            "<i>You haven't created any cloned bots yet!</i>\n"
            "Use command: <code>/clone &lt;bot_token&gt;</code> to create your first music bot."
        )

    rows.append([
        types.InlineKeyboardButton(text="Clone Bot Settings", callback_data="clone_main_menu"),
    ])

    markup = types.InlineKeyboardMarkup(rows)
    await status_msg.edit_text(
        text=text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=markup,
    )


@app.on_message(filters.command(["gensession", "genstring", "string", "session"]) & filters.private & ~app.bl_users)
async def start_session_gen(_, m: types.Message):
    """
    Start interactive Pyrogram v2 Session String Generation inside this bot.
    """
    user_id = m.from_user.id
    clean_gen(user_id)

    GEN_SESSIONS[user_id] = {
        "step": "phone",
        "api_id": config.API_ID,
        "api_hash": config.API_HASH,
        "client": None,
    }

    await m.reply_text(
        "<b>Pyrogram v2 Session String Generator</b>\n\n"
        "This bot will generate your Pyrogram v2 String Session safely and directly inside Telegram!\n\n"
        "<b>Step 1/3: Phone Number</b>\n"
        "Please send your Telegram account <b>Phone Number</b> with your country code.\n"
        "<b>Example:</b> <code>+919876543210</code> or <code>+12025550123</code>\n\n"
        "<i>Send /cancel anytime to abort process.</i>",
        parse_mode=enums.ParseMode.HTML,
        quote=True,
    )


@app.on_message(filters.command(["cancel"]) & filters.private & ~app.bl_users)
async def cancel_session_gen(_, m: types.Message):
    """Cancel active session generation."""
    user_id = m.from_user.id
    if user_id in GEN_SESSIONS:
        clean_gen(user_id)
        return await m.reply_text("<b>Session String generation cancelled successfully!</b>", quote=True)
    await m.reply_text("<b>No active session generation process found.</b>", quote=True)


@app.on_message(filters.private & ~filters.command(["gensession", "genstring", "string", "session", "cancel", "start", "help"]) & ~app.bl_users)
async def session_gen_listener(_, m: types.Message):
    """Process user inputs for interactive session string generator."""
    user_id = m.from_user.id
    if user_id not in GEN_SESSIONS:
        return

    sess = GEN_SESSIONS[user_id]
    step = sess["step"]
    text = (m.text or m.caption or "").strip()

    if not text:
        return

    # STEP 1: PHONE NUMBER
    if step == "phone":
        phone = re.sub(r"[^\d+]", "", text)
        if not phone.startswith("+") or len(phone) < 8:
            return await m.reply_text(
                "<b>Invalid Phone Number!</b>\n"
                "Please include your country code (e.g. <code>+919876543210</code>).",
                quote=True,
            )

        status_msg = await m.reply_text("<b>Connecting to Telegram & sending OTP code...</b>", quote=True)

        try:
            client = Client(
                name=f"temp_gen_{user_id}",
                api_id=sess["api_id"],
                api_hash=sess["api_hash"],
                in_memory=True,
            )
            await client.connect()
            code_info = await client.send_code(phone)

            sess["phone"] = phone
            sess["code_hash"] = code_info.phone_code_hash
            sess["client"] = client
            sess["step"] = "otp"

            await status_msg.edit_text(
                f"<b>Step 2/3: Enter OTP Code</b>\n\n"
                f"An authentication OTP code has been sent to your Telegram account on <code>{phone}</code>!\n\n"
                f"<b>Please reply with the OTP code.</b>\n"
                f"<i>Formatting tip: You can format like <code>1 2 3 4 5</code> or <code>12345</code>.</i>\n\n"
                f"<i>Send /cancel anytime to abort.</i>",
                parse_mode=enums.ParseMode.HTML,
            )
        except errors.PhoneNumberInvalid:
            clean_gen(user_id)
            await status_msg.edit_text("<b>Invalid phone number. Please start again with /gensession.</b>")
        except errors.FloodWait as fw:
            clean_gen(user_id)
            await status_msg.edit_text(f"<b>Telegram FloodWait: Please wait {fw.value} seconds before trying again.</b>")
        except Exception as err:
            clean_gen(user_id)
            logger.error(f"Session gen error sending code for {user_id}: {err}")
            await status_msg.edit_text(f"<b>Failed to send OTP code:</b> {err}")

    # STEP 2: OTP CODE
    elif step == "otp":
        otp_code = re.sub(r"\D", "", text)
        if not otp_code or len(otp_code) < 4:
            return await m.reply_text("<b>Invalid OTP code format. Please enter the numeric code sent to your Telegram.</b>", quote=True)

        phone = sess["phone"]
        code_hash = sess["code_hash"]
        client = sess["client"]

        status_msg = await m.reply_text("<b>Verifying OTP code...</b>", quote=True)

        try:
            await client.sign_in(
                phone_number=phone,
                phone_code_hash=code_hash,
                phone_code=otp_code,
            )
            # Logged in successfully!
            string_session = await client.export_session_string()
            await client.disconnect()
            GEN_SESSIONS.pop(user_id, None)

            await send_session_success(user_id, status_msg, string_session)

        except errors.SessionPasswordNeeded:
            sess["step"] = "password"
            await status_msg.edit_text(
                "<b>Step 3/3: Two-Factor Authentication (2FA) Password</b>\n\n"
                "Your account has 2FA Password enabled.\n"
                "<b>Please reply with your Telegram 2FA Password below.</b>\n\n"
                "<i>Send /cancel anytime to abort.</i>",
                parse_mode=enums.ParseMode.HTML,
            )
        except errors.PhoneCodeInvalid:
            await status_msg.edit_text("<b>Invalid OTP code! Please check and enter the correct code.</b>")
        except errors.PhoneCodeExpired:
            clean_gen(user_id)
            await status_msg.edit_text("<b>OTP code expired. Please start again with /gensession.</b>")
        except Exception as err:
            clean_gen(user_id)
            logger.error(f"Session gen error signing in for {user_id}: {err}")
            await status_msg.edit_text(f"<b>Sign in error:</b> {err}")

    # STEP 3: 2FA PASSWORD
    elif step == "password":
        password = text
        client = sess["client"]

        status_msg = await m.reply_text("<b>Verifying 2FA Password...</b>", quote=True)

        try:
            await client.check_password(password=password)
            string_session = await client.export_session_string()
            await client.disconnect()
            GEN_SESSIONS.pop(user_id, None)

            await send_session_success(user_id, status_msg, string_session)

        except errors.PasswordHashInvalid:
            await status_msg.edit_text("<b>Invalid 2FA Password! Please check and try again.</b>")
        except Exception as err:
            clean_gen(user_id)
            logger.error(f"Session gen error checking password for {user_id}: {err}")
            await status_msg.edit_text(f"<b>2FA Verification error:</b> {err}")


@app.on_callback_query(filters.regex(r"^setass_clone_(\d+)"))
async def set_generated_assistant_cb(_, query: types.CallbackQuery):
    """Attach generated session string to selected cloned bot."""
    user_id = query.from_user.id
    idx = int(query.matches[0].group(1))

    string_session = USER_TEMP_SESSIONS.get(user_id)
    if not string_session:
        return await query.answer("Session string expired or not found! Please generate again with /gensession.", show_alert=True)

    clones = await db.get_user_clones(user_id)
    if not clones or idx >= len(clones):
        return await query.answer("Cloned bot not found!", show_alert=True)

    target_clone = clones[idx]
    bot_token = target_clone["bot_token"]
    bot_un = target_clone.get("username", "bot")

    await query.answer(f"Connecting Assistant to @{bot_un}...", show_alert=False)
    status_msg = await query.message.edit_text(f"<b>Connecting Assistant session to @{bot_un}...</b>")

    try:
        from ishu.core.clone import stop_single_clone, boot_single_clone
        await stop_single_clone(bot_token)
        ok, username, name_or_err, ass_info = await boot_single_clone(
            bot_token=bot_token,
            user_id=user_id,
            username=target_clone.get("username"),
            name=target_clone.get("name"),
            session_string=string_session,
            owner_id=target_clone.get("owner_id", user_id),
            log_group=target_clone.get("log_group"),
        )
        if ok:
            await status_msg.edit_text(
                f"<b>Assistant Connected Successfully!</b>\n\n"
                f"<b>Bot Username:</b> @{username}\n"
                f"<b>Assistant:</b> {ass_info}\n\n"
                f"Your clone bot @{username} will now use assistant {ass_info} for voice chats!",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=buttons.clone_panel_markup(),
            )
        else:
            await status_msg.edit_text(f"<b>Failed to connect Assistant:</b> {name_or_err}")
    except Exception as err:
        logger.error(f"Set generated assistant error for user {user_id}: {err}")
        await status_msg.edit_text(f"<b>Error:</b> {err}")
