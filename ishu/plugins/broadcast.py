import os
import asyncio

from pyrogram import errors, filters, types, enums

from ishu import app, config, db, lang, logger

broadcasting = asyncio.Lock()


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

    sender_id = message.from_user.id
    is_master = (sender_id == config.OWNER_ID or sender_id in getattr(app, "sudoer_ids", set()))

    sent = await message.reply_text(message.lang["gcast_start"])
    count, ucount = 0, 0
    failed = None

    async with broadcasting:
        from ishu.core.clone import cloned_clients
        bot_clients = []

        if is_master:
            # Master owner broadcasts via main app AND all cloned bots
            bot_clients.append(app)
            for c_app in cloned_clients.values():
                if c_app not in bot_clients:
                    bot_clients.append(c_app)
        else:
            # Clone owner broadcasts ONLY via current clone bot
            bot_clients.append(client)

        for b_client in bot_clients:
            b_groups, b_users = set(), set()
            if not nochat:
                b_groups = set(await db.get_chats())
                try:
                    async for d in b_client.get_dialogs():
                        if d.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                            b_groups.add(d.chat.id)
                except Exception:
                    pass

            if onlyuser:
                b_users = set(await db.get_users())
                try:
                    async for d in b_client.get_dialogs():
                        if d.chat.type == enums.ChatType.PRIVATE:
                            b_users.add(d.chat.id)
                except Exception:
                    pass

            target_chats = list(b_groups | b_users)
            for chat in target_chats:
                try:
                    if copy:
                        await msg.copy(chat, reply_markup=msg.reply_markup)
                    else:
                        await msg.forward(chat)

                    if chat in b_groups:
                        count += 1
                    else:
                        ucount += 1
                    await asyncio.sleep(0.15)
                except errors.FloodWait as fw:
                    await asyncio.sleep(fw.value + 5)
                except Exception as ex:
                    if not failed:
                        failed = open("errors.txt", "w")
                    failed.write(f"{chat} - {ex}\n")
                    continue

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
