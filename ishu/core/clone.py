import asyncio
from pyrogram import Client
from ishu import app, config, db, logger

cloned_clients: dict[str, Client] = {}
cloned_assistants: dict[str, Client] = {}


def _attach_handlers_to_clone(clone_app: Client):
    """Copy all registered handlers from main app to the clone bot client."""
    dispatcher = getattr(app, "dispatcher", None)
    if not dispatcher:
        return

    groups = getattr(dispatcher, "groups", None)
    if groups is None:
        groups = getattr(dispatcher, "handlers", {})

    if isinstance(groups, dict):
        for group, handlers in groups.items():
            if isinstance(handlers, (list, tuple)):
                for handler in handlers:
                    try:
                        clone_app.add_handler(handler, group=group)
                    except Exception as e:
                        logger.warning(f"Could not add handler {handler} to clone: {e}")


async def boot_single_clone(
    bot_token: str,
    user_id: int,
    username: str = None,
    name: str = None,
    session_string: str = None,
    owner_id: int = None,
    log_group: int = None,
) -> tuple[bool, str, str, str]:
    """
    Boot a single clone bot token and optional Assistant userbot session.
    Returns (success, bot_username, bot_name, assistant_info)
    """
    if bot_token in cloned_clients:
        client = cloned_clients[bot_token]
        ass_info = "Default Assistant"
        if bot_token in cloned_assistants:
            ass_client = cloned_assistants[bot_token]
            ass_info = f"@{getattr(ass_client.me, 'username', 'userbot')}"
        return True, getattr(client.me, "username", username or "bot"), getattr(client.me, "first_name", name or "Clone Bot"), ass_info

    try:
        session_name = f"clone_{bot_token.split(':')[0]}"
        clone_app = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=bot_token,
            in_memory=True,
        )
        await clone_app.start()
        _attach_handlers_to_clone(clone_app)
        
        bot_username = clone_app.me.username or username or "bot"
        bot_name = clone_app.me.first_name or name or "Clone Bot"
        
        cloned_clients[bot_token] = clone_app

        assistant_id = None
        assistant_username = None
        assistant_info = "Default Assistant"

        effective_session = session_string or config.SESSION1
        if effective_session:
            try:
                ass_name = f"ass_clone_{bot_token.split(':')[0]}"
                ass_client = Client(
                    name=ass_name,
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=effective_session,
                    in_memory=True,
                )
                await ass_client.start()
                assistant_id = ass_client.me.id
                assistant_username = ass_client.me.username or f"user_{assistant_id}"
                cloned_assistants[bot_token] = ass_client
                assistant_info = f"@{assistant_username}"
                logger.info(f"Clone assistant @{assistant_username} booted for bot @{bot_username}.")
            except Exception as ass_err:
                logger.warning(f"Failed to start clone assistant session for bot @{bot_username}: {ass_err}")

        await db.add_clone(
            bot_token=bot_token,
            user_id=user_id,
            username=bot_username,
            name=bot_name,
            session_string=session_string,
            assistant_id=assistant_id,
            assistant_username=assistant_username,
            owner_id=owner_id or user_id,
            log_group=log_group,
        )
        logger.info(f"Clone bot @{bot_username} started successfully (Owner: {owner_id or user_id}, LogGroup: {log_group}, Assistant: {assistant_info}).")
        return True, bot_username, bot_name, assistant_info
    except Exception as e:
        logger.warning(f"Failed to start clone bot token {bot_token[:10]}...: {e}")
        return False, "", str(e), ""


async def boot_all_clones():
    """Boot all cloned bots and assistants stored in database."""
    clones = await db.get_clones()
    if not clones:
        return
    logger.info(f"Found {len(clones)} clone bot(s) in database. Booting...")
    count = 0
    for item in clones:
        bot_token = item.get("bot_token")
        user_id = item.get("user_id", 0)
        username = item.get("username")
        name = item.get("name")
        session_string = item.get("session_string")
        owner_id = item.get("owner_id")
        log_group = item.get("log_group")
        if bot_token:
            ok, un, _, _ = await boot_single_clone(
                bot_token, user_id, username, name, session_string, owner_id, log_group
            )
            if ok:
                count += 1
    logger.info(f"Successfully booted {count} clone bot(s).")


async def stop_single_clone(bot_token_or_query: str) -> bool:
    """Stop a running clone client, assistant, and remove from DB."""
    target_token = None
    for token, client in list(cloned_clients.items()):
        if token == bot_token_or_query or (getattr(client.me, "username", "").lower() == bot_token_or_query.lstrip("@").lower()):
            target_token = token
            try:
                await client.stop()
            except Exception:
                pass
            cloned_clients.pop(token, None)
            
            if token in cloned_assistants:
                try:
                    await cloned_assistants[token].stop()
                except Exception:
                    pass
                cloned_assistants.pop(token, None)
            break

    removed = await db.remove_clone(bot_token_or_query)
    return removed or (target_token is not None)
