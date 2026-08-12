# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import pyrogram
from pyrogram import types

from ishu import config, logger


# Commands shown in the Telegram "/" menu. Group-facing commands go in the
# default scope (groups + PM); PM-only commands override in private chats.
MENU_COMMANDS = [
    types.BotCommand(
        "play",
        "Play a song by name/URL (vplay=video, playforce=force as admin)",
    ),
    types.BotCommand("pause", "Pause the current playback"),
    types.BotCommand("resume", "Resume the paused playback"),
    types.BotCommand("skip", "Skip to the next track (next)"),
    types.BotCommand("stop", "Stop playback and clear the queue (end)"),
    types.BotCommand("queue", "Show the current queue / now playing"),
    types.BotCommand("seek", "Seek forward/back in the current track"),
    types.BotCommand("loop", "Loop the current track N times"),
    types.BotCommand("stats", "Show chat stats"),
    types.BotCommand("lang", "Change the bot's language"),
    types.BotCommand("auth", "Authorize a user for admin commands (unauth)"),
    types.BotCommand("admincache", "Reload the admin list for this chat"),
    types.BotCommand("playmode", "Toggle admin-only play mode"),
    types.BotCommand("gadd", "Add a bot to all groups (owner only)"),
]

PRIVATE_COMMANDS = [
    types.BotCommand("start", "Start the bot and view help"),
    types.BotCommand("help", "Show the help message"),
    types.BotCommand("groups", "List groups where the bot is active"),
    types.BotCommand("sudolist", "List sudo users"),
]


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="ishu_v2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True) if hasattr(pyrogram.types, "LinkPreviewOptions") else None,
        )
        self.owner = config.OWNER_ID
        self.logger = config.LOGGER_ID
        self.bl_users = pyrogram.filters.user()
        self.sudoers = pyrogram.filters.user(self.owner)

    async def set_commands(self) -> None:
        """Register the "/" command menu so Telegram suggests commands."""
        try:
            await self.set_bot_commands(
                MENU_COMMANDS, scope=types.BotCommandScopeDefault()
            )
            await self.set_bot_commands(
                PRIVATE_COMMANDS, scope=types.BotCommandScopeAllPrivateChats()
            )
            logger.info("Bot command menu registered.")
        except Exception as ex:
            logger.warning("Failed to set bot commands: %s", ex)

    async def boot(self):
        """
        Starts the bot and performs initial setup.

        Raises:
            SystemExit: If the bot fails to access the log group or is not an administrator in the logger group.
        """
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(self.logger, "Bot Started")
            get = await self.get_chat_member(self.logger, self.id)
        except Exception as ex:
            raise SystemExit(f"Bot has failed to access the log group: {self.logger}\nReason: {ex}")

        if get.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit("Please promote the bot as an admin in logger group.")

        await self.set_commands()
        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        await super().stop()
        logger.info("Bot stopped.")
