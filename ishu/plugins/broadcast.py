import os
import asyncio

from pyrogram import errors, filters, types

from ishu import app, config, db, lang, logger

broadcasting = asyncio.Lock()


async def send_to_target(b_cli, chat_id: int, msg: types.Message, copy: bool = True):
    """Send message to target chat_id using specific bot client b_cli."""
    if not copy:
        return await b_cli.forward_messages(chat_id=chat_id, from_chat_id=msg.chat.id, message_ids=msg.id)

    try:
        return await b_cli.copy_message(chat_id=chat_id, from_chat_id=msg.chat.id, message_id=msg.id, reply_markup=msg.reply_markup)
    except Exception:
        # Fallback to direct media / text send if b_cli cannot read from_chat_id
        if msg.text:
            return await b_cli.send_message(chat_id, msg.text, reply_markup=msg.reply_markup)
        elif msg.photo:
            return await b_cli.send_photo(chat_id, msg.photo.file_id, caption=msg.caption, reply_markup=msg.reply_markup)
        elif msg.audio:
            return await b_cli.send_audio(chat_id, msg.audio.file_id, caption=msg.caption, reply_markup=msg.reply_markup)
        elif msg.video:
            return await b_cli.send_video(chat_id, msg.video.file_id, caption=msg.caption, reply_markup=msg.reply_markup)
        elif msg.document:
            return await b_cli.send_document(chat_id, msg.document.file_id, caption=msg.caption, reply_markup=msg.reply_markup)
        elif msg.voice:
            return await b_cli.send_voice(chat_id, msg.voice.file_id, caption=msg.caption, reply_markup=msg.reply_markup)
        elif msg.animation:
            return await b_cli.send_animation(chat_id, msg.animation.file_id, caption=msg.caption, reply_markup=msg.reply_markup)
        elif msg.sticker:
            return await b_cli.send_sticker(chat_id, msg.sticker.file_id)
        else:
            return await b_cli.send_message(chat_id, msg.text or msg.caption or "", reply_markup=msg.reply_markup)


@app.on_message(filters.command(["broadcast", "gcast"]) & app.sudoers)
@lang.language()
async def _broadcast(client, message: types.Message):
    """
    Broadcast handler:
    - Clone owner broadcast: sends broadcast ONLY through their cloned bot to its chats/users.
    - Master owner broadcast: sends broadcast through main bot AND ALL cloned bots across all chats/users!
    """
    if not message.reply_to_message:
        return await message.reply_text(message.lang["gcast_usage"])

    if broadcasting.locked():
        return await message.reply_text(message.lang["gcast_active"])

    msg = message.reply_to_message
    copy = "-copy" in message.command
    nochat = "-nochat" in message.command
    onlyuser = "-user" in message.command
    onlygroup = "-group" in message.command

    sender_id = message.from_user.id
    is_master = (sender_id == config.OWNER_ID or sender_id in getattr(app, "sudoer_ids", set()))

    sent = await message.reply_text(message.lang["gcast_start"])
    count, ucount = 0, 0
    failed = None

    async with broadcasting:
        from ishu.core.clone import cloned_clients

        if is_master:
            # Master owner broadcasts via main app AND all booted cloned bots
            bot_clients = [app] + list(cloned_clients.values())
        else:
            # Clone owner broadcasts ONLY via current clone bot
            bot_clients = [client]

        # De-duplicate bot clients
        unique_clients = []
        for b_cli in bot_clients:
            if b_cli not in unique_clients:
                unique_clients.append(b_cli)

        for b_cli in unique_clients:
            b_id = getattr(b_cli, "id", None) or getattr(getattr(b_cli, "me", None), "id", None)
            
            # Fetch target groups & users for this specific bot
            b_groups = set()
            b_users = set()

            if not nochat and not onlyuser:
                # Groups
                if b_id:
                    bot_specific_groups = await db.get_bot_chats(b_id)
                    b_groups.update(bot_specific_groups)
                if not b_groups:
                    b_groups.update(await db.get_chats())

            if not onlygroup:
                # Users
                if b_id:
                    bot_specific_users = await db.get_bot_users(b_id)
                    b_users.update(bot_specific_users)
                if not b_users:
                    b_users.update(await db.get_users())

            # Broadcast to group chats using b_cli
            for chat in list(b_groups):
                try:
                    await send_to_target(b_cli, chat, msg, copy=copy)
                    count += 1
                    await asyncio.sleep(0.15)
                except errors.FloodWait as fw:
                    await asyncio.sleep(fw.value + 3)
                except (errors.PeerIdInvalid, errors.ChannelInvalid, errors.ChatWriteForbidden, errors.UserNotParticipant):
                    # Bot is not a member of this chat, skip silently
                    continue
                except Exception as ex:
                    if not failed:
                        failed = open("errors.txt", "w")
                    failed.write(f"Chat {chat} - {ex}\n")

            # Broadcast to PM users using b_cli
            for user in list(b_users):
                try:
                    await send_to_target(b_cli, user, msg, copy=copy)
                    ucount += 1
                    await asyncio.sleep(0.15)
                except errors.FloodWait as fw:
                    await asyncio.sleep(fw.value + 3)
                except (errors.PeerIdInvalid, errors.UserIsBlocked, errors.InputUserDeactivated):
                    # User blocked bot or deactivated, skip silently
                    continue
                except Exception as ex:
                    if not failed:
                        failed = open("errors.txt", "w")
                    failed.write(f"User {user} - {ex}\n")

    text = message.lang["gcast_end"].format(count, ucount)
    if failed:
        failed.close()
        await message.reply_document(
            document="errors.txt",
            caption=text,
        )
        try:
            os.remove("errors.txt")
        except Exception:
            pass

    await sent.edit_text(text)
