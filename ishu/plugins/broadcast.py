import os
import asyncio

from pyrogram import errors, filters, types

from ishu import app, db, lang, logger

broadcasting = asyncio.Lock()


@app.on_message(filters.command(["broadcast", "gcast"]) & app.sudoers)
@lang.language()
async def _broadcast(client, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text(message.lang["gcast_usage"])

    if broadcasting.locked():
        return await message.reply_text(message.lang["gcast_active"])

    msg = message.reply_to_message
    copy = "-copy" in message.command
    nochat = "-nochat" in message.command
    onlyuser = "-user" in message.command
    onlygroup = "-group" in message.command

    sent = await message.reply_text(message.lang["gcast_start"])
    count, ucount = 0, 0
    failed = None

    groups, users = set(), set()

    if not nochat and not onlyuser:
        groups = set(await db.get_chats())

    if not onlygroup:
        users = set(await db.get_users())

    async with broadcasting:
        # Broadcast to group chats
        for chat in list(groups):
            try:
                if copy:
                    await msg.copy(chat, reply_markup=msg.reply_markup)
                else:
                    try:
                        await msg.forward(chat)
                    except Exception:
                        await msg.copy(chat, reply_markup=msg.reply_markup)
                count += 1
                await asyncio.sleep(0.15)
            except errors.FloodWait as fw:
                await asyncio.sleep(fw.value + 3)
            except (errors.PeerIdInvalid, errors.ChannelInvalid, errors.ChatWriteForbidden, errors.UserNotParticipant, errors.ChatAdminRequired, errors.ChatRestricted):
                continue
            except Exception as ex:
                if not failed:
                    failed = open("errors.txt", "w")
                failed.write(f"Chat {chat} - {ex}\n")

        # Broadcast to PM users
        for user in list(users):
            try:
                if copy:
                    await msg.copy(user, reply_markup=msg.reply_markup)
                else:
                    try:
                        await msg.forward(user)
                    except Exception:
                        await msg.copy(user, reply_markup=msg.reply_markup)
                ucount += 1
                await asyncio.sleep(0.15)
            except errors.FloodWait as fw:
                await asyncio.sleep(fw.value + 3)
            except (errors.PeerIdInvalid, errors.UserIsBlocked, errors.InputUserDeactivated, errors.UserDeactivated, errors.UserDeactivatedBan):
                continue
            except Exception as ex:
                if not failed:
                    failed = open("errors.txt", "w")
                failed.write(f"User {user} - {ex}\n")

    text = message.lang["gcast_end"].format(count, ucount)
    if failed:
        failed.close()
        try:
            await message.reply_document(
                document="errors.txt",
                caption=text,
            )
            os.remove("errors.txt")
        except Exception:
            pass

    await sent.edit_text(text)
