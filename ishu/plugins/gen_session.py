import asyncio
import re
from pyrogram import Client, filters, types, enums
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
    PasswordHashInvalid,
)

from ishu import app, config, lang, logger

# Store session generation user states
gen_state = {}

@app.on_message(filters.command(["gensession", "gen_session", "session"]) & filters.private & ~app.bl_users)
async def gen_session_command(client, message: types.Message):
    user_id = message.from_user.id
    gen_state[user_id] = {"step": "phone"}
    
    text = (
        "<b> Pyrogram v2 Session String Generator</b>\n\n"
        "Generate your Pyrogram v2 session string securely in private chat!\n\n"
        "<b>Step 1/3:</b> Please send your Telegram phone number with country code.\n"
        "<b>Example:</b> <code>+919876543210</code>\n\n"
        "<i>To cancel at any time, send <code>/cancel</code>.</i>"
    )
    await message.reply_text(text, parse_mode=enums.ParseMode.HTML, quote=True)


@app.on_message(filters.command(["cancel"]) & filters.private)
async def cancel_gen_session(client, message: types.Message):
    user_id = message.from_user.id
    if user_id in gen_state:
        state = gen_state.pop(user_id, {})
        temp_client = state.get("client")
        if temp_client:
            try:
                await temp_client.disconnect()
            except Exception:
                pass
        await message.reply_text(" Session generation process cancelled.", quote=True)
    else:
        await message.reply_text("No active session generation process found.", quote=True)


@app.on_message(filters.private & ~filters.command(["gensession", "gen_session", "session", "cancel", "start"]) & ~app.bl_users)
async def handle_gen_session_input(client, message: types.Message):
    user_id = message.from_user.id
    if user_id not in gen_state:
        return

    state = gen_state[user_id]
    step = state.get("step")

    if step == "phone":
        phone_number = message.text.strip().replace(" ", "")
        temp_client = Client(
            f"session_gen_{user_id}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            in_memory=True,
        )
        try:
            await temp_client.connect()
        except Exception as e:
            gen_state.pop(user_id, None)
            return await message.reply_text(f" Failed to initialize Telegram client: {e}", quote=True)

        try:
            code_info = await temp_client.send_code(phone_number)
        except PhoneNumberInvalid:
            await temp_client.disconnect()
            return await message.reply_text(" Invalid phone number! Please enter with country code (e.g. +919876543210).", quote=True)
        except ApiIdInvalid:
            await temp_client.disconnect()
            gen_state.pop(user_id, None)
            return await message.reply_text(" API_ID or API_HASH invalid.", quote=True)
        except Exception as e:
            await temp_client.disconnect()
            gen_state.pop(user_id, None)
            return await message.reply_text(f" Failed to send OTP code: {e}", quote=True)

        state["step"] = "code"
        state["phone_number"] = phone_number
        state["phone_code_hash"] = code_info.phone_code_hash
        state["client"] = temp_client

        text = (
            "<b> OTP Code Sent!</b>\n\n"
            f"<b>Step 2/3:</b> Enter the OTP confirmation code sent to <code>{phone_number}</code> via Telegram app.\n\n"
            "<b>Format:</b> Send code as numbers spaced or plain (e.g., <code>1 2 3 4 5</code> or <code>12345</code>)."
        )
        await message.reply_text(text, parse_mode=enums.ParseMode.HTML, quote=True)

    elif step == "code":
        raw_code = message.text.strip().replace(" ", "").replace("-", "")
        temp_client = state.get("client")
        phone_number = state.get("phone_number")
        phone_code_hash = state.get("phone_code_hash")

        try:
            await temp_client.sign_in(phone_number, phone_code_hash, raw_code)
            session_str = await temp_client.export_session_string()
            await temp_client.disconnect()
            gen_state.pop(user_id, None)

            text = (
                "<b> Pyrogram v2 Session String Generated Successfully!</b>\n\n"
                f"<code>{session_str}</code>\n\n"
                " <b>Keep this session string private! Anyone with this string can access your Telegram account.</b>"
            )
            await message.reply_text(text, parse_mode=enums.ParseMode.HTML, quote=True)

        except SessionPasswordNeeded:
            state["step"] = "password"
            text = (
                "<b> 2-Step Verification Enabled!</b>\n\n"
                "<b>Step 3/3:</b> Please enter your Telegram 2FA Password to complete authentication."
            )
            await message.reply_text(text, parse_mode=enums.ParseMode.HTML, quote=True)

        except (PhoneCodeInvalid, PhoneCodeExpired):
            await message.reply_text(" Invalid or expired OTP code. Please try again or re-send `/gensession`.", quote=True)

        except Exception as e:
            await temp_client.disconnect()
            gen_state.pop(user_id, None)
            await message.reply_text(f" Authentication failed: {e}", quote=True)

    elif step == "password":
        password = message.text.strip()
        temp_client = state.get("client")

        try:
            await temp_client.check_password(password)
            session_str = await temp_client.export_session_string()
            await temp_client.disconnect()
            gen_state.pop(user_id, None)

            text = (
                "<b> Pyrogram v2 Session String Generated Successfully!</b>\n\n"
                f"<code>{session_str}</code>\n\n"
                " <b>Keep this session string private! Anyone with this string can access your Telegram account.</b>"
            )
            await message.reply_text(text, parse_mode=enums.ParseMode.HTML, quote=True)

        except PasswordHashInvalid:
            await message.reply_text(" Invalid 2FA password! Please enter the correct password.", quote=True)

        except Exception as e:
            await temp_client.disconnect()
            gen_state.pop(user_id, None)
            await message.reply_text(f" Authentication failed: {e}", quote=True)
