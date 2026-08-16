from pyrogram import enums, types

from ishu import app, config, lang
from ishu.core.lang import lang_codes

_panel_state: dict[int, dict] = {}


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(
            text=text,
            callback_data=f"cancel_dl",
            style=enums.ButtonStyle.DANGER,
        )]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
        autoplay: bool | None = None,
        mode: str = None,
        link: str = None,
        bot_username: str = None,
    ) -> types.InlineKeyboardMarkup:
        if chat_id in _panel_state:
            prev = _panel_state[chat_id]
            if status is None:
                status = prev.get("status")
            if timer is None:
                timer = prev.get("timer")
            if autoplay is None and not remove:
                autoplay = prev.get("autoplay", False)
            if mode is None:
                mode = prev.get("mode", "vibe")
            if link is None:
                link = prev.get("link")
            if bot_username is None:
                bot_username = prev.get("bot_username")
        if mode is None:
            mode = "vibe"

        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(
                    text=status,
                    callback_data=f"controls status {chat_id}",
                    style=enums.ButtonStyle.SUCCESS,
                )]
            )
        elif timer:
            keyboard.append(
                [self.ikb(
                    text=timer,
                    callback_data=f"controls status {chat_id}",
                    style=enums.ButtonStyle.SUCCESS,
                )]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="▷", callback_data=f"controls resume {chat_id}", style=enums.ButtonStyle.SUCCESS),
                    self.ikb(text="II", callback_data=f"controls pause {chat_id}", style=enums.ButtonStyle.SUCCESS),
                    self.ikb(text="⥁", callback_data=f"controls replay {chat_id}", style=enums.ButtonStyle.SUCCESS),
                    self.ikb(text="‣‣I", callback_data=f"controls skip {chat_id}", style=enums.ButtonStyle.SUCCESS),
                    self.ikb(text="▢", callback_data=f"controls stop {chat_id}", style=enums.ButtonStyle.SUCCESS),
                ]
            )

            un = bot_username or getattr(app, "username", None) or "bot"
            clone_button = self.ikb(
                text="Clone Bot",
                url=f"https://t.me/{un}?start=clone",
                style=enums.ButtonStyle.SUCCESS,
            )

            if autoplay:
                mode_info = {
                    "vibe": ("Vibe", enums.ButtonStyle.SUCCESS),
                    "artist": ("Artist", enums.ButtonStyle.SUCCESS),
                    "trending": ("Trending", enums.ButtonStyle.SUCCESS),
                }.get(mode or "vibe", ("Vibe", enums.ButtonStyle.SUCCESS))
                keyboard.append(
                    [
                        self.ikb(
                            text="Autoplay ON",
                            callback_data=f"autoplay {chat_id}",
                            style=enums.ButtonStyle.SUCCESS,
                        ),
                        self.ikb(
                            text=mode_info[0],
                            callback_data=f"autoplay_mode {chat_id}",
                            style=enums.ButtonStyle.SUCCESS,
                        ),
                    ]
                )
                keyboard.append(
                    [
                        clone_button,
                        self.ikb(
                            text="YouTube Menu",
                            callback_data=f"youtube_menu {chat_id}",
                            style=enums.ButtonStyle.SUCCESS,
                        ),
                    ]
                )
            else:
                keyboard.append(
                    [
                        self.ikb(
                            text="Autoplay OFF",
                            callback_data=f"autoplay {chat_id}",
                            style=enums.ButtonStyle.SUCCESS,
                        ),
                        clone_button,
                    ]
                )

        _panel_state[chat_id] = {
            "status": status,
            "timer": timer,
            "autoplay": autoplay,
            "mode": mode,
            "link": link,
            "bot_username": bot_username,
            "remove": remove,
        }
        return self.ikm(keyboard)

    def youtube_menu_markup(self, chat_id: int, active_cat: str = "songs", link: str = None) -> types.InlineKeyboardMarkup:
        def get_style(cat: str):
            return enums.ButtonStyle.SUCCESS if active_cat == cat else enums.ButtonStyle.DANGER

        rows = [
            [
                self.ikb(
                    text="Songs",
                    callback_data=f"yt_cat songs {chat_id}",
                    style=get_style("songs"),
                ),
                self.ikb(
                    text="Artists",
                    callback_data=f"yt_cat artists {chat_id}",
                    style=get_style("artists"),
                ),
            ],
            [
                self.ikb(
                    text="Albums",
                    callback_data=f"yt_cat albums {chat_id}",
                    style=get_style("albums"),
                ),
                self.ikb(
                    text="Playlists",
                    callback_data=f"yt_cat playlists {chat_id}",
                    style=get_style("playlists"),
                ),
            ],
            [
                self.ikb(
                    text="Music Videos",
                    callback_data=f"yt_cat videos {chat_id}",
                    style=get_style("videos"),
                ),
            ],
        ]
        if link:
            rows.append(
                [
                    self.ikb(
                        text="Open Direct Link",
                        url=link,
                        style=enums.ButtonStyle.SUCCESS,
                    )
                ]
            )
        rows.append(
            [
                self.ikb(
                    text="Back to Player",
                    callback_data=f"yt_menu_back {chat_id}",
                    style=enums.ButtonStyle.SUCCESS,
                )
            ]
        )
        return self.ikm(rows)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(
                        text=_lang["back"],
                        callback_data="help back",
                        style=enums.ButtonStyle.DANGER,
                    ),
                    self.ikb(
                        text=_lang["close"],
                        callback_data="help close",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ]
            ]
        else:
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo", "download", "clone"]
            buttons = [
                self.ikb(
                    text=_lang.get(f"help_{i}", cb.capitalize()),
                    callback_data=f"help {cb}",
                    style=enums.ButtonStyle.DANGER,
                )
                for i, cb in enumerate(cbs)
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code})",
                callback_data=f"lang_change {code}",
                style=enums.ButtonStyle.SUCCESS,
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(
            text=text,
            url=config.SUPPORT_CHAT,
            style=enums.ButtonStyle.DANGER,
        )]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text,
                        callback_data=f"controls force {chat_id} {item_id}",
                        style=enums.ButtonStyle.SUCCESS,
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜", callback_data="settings",
                    ),
                    self.ikb(text=admin_only, callback_data="settings play"),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜", callback_data="settings",
                    ),
                    self.ikb(text=cmd_delete, callback_data="settings delete"),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜", callback_data="settings",
                    ),
                    self.ikb(text=lang_codes[language], callback_data="language"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False, bot_username: str = None
    ) -> types.InlineKeyboardMarkup:
        un = bot_username or app.username or "bot"
        rows = [
            [
                self.ikb(
                    text=f"{lang['add_me']}",
                    url=f"https://t.me/{un}?startgroup=true",
                    style=enums.ButtonStyle.DANGER,
                )
            ],
        ]
        if private:
            rows += [
                [
                    self.ikb(text="Create Your Own Music Bot", callback_data="clone_main_menu", style=enums.ButtonStyle.SUCCESS),
                ],
                [
                    self.ikb(text=lang["help"], callback_data="help", style=enums.ButtonStyle.DANGER),
                ],
                [
                    self.ikb(text=lang["support"], url=config.SUPPORT_CHAT, style=enums.ButtonStyle.DANGER),
                    self.ikb(text=lang["channel"], url=config.SUPPORT_CHANNEL, style=enums.ButtonStyle.DANGER),
                ]
            ]
        else:
            rows += [[self.ikb(text=lang["language"], callback_data="language", style=enums.ButtonStyle.DANGER)]]
        return self.ikm(rows)

    def clone_panel_markup(self) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(text="How to Clone Bot", callback_data="clone_guide", style=enums.ButtonStyle.SUCCESS),
                self.ikb(text="My Cloned Bots", callback_data="clone_my_bots", style=enums.ButtonStyle.SUCCESS),
            ],
            [
                self.ikb(text="Generate Session String", callback_data="clone_gen_session", style=enums.ButtonStyle.PRIMARY),
                self.ikb(text="Set Assistant", callback_data="clone_set_assistant", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                self.ikb(text="Set Owner ID", callback_data="clone_set_owner", style=enums.ButtonStyle.PRIMARY),
                self.ikb(text="Set Log Group", callback_data="clone_set_log", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                self.ikb(text="Remove Clone Bot", callback_data="clone_remove_bot", style=enums.ButtonStyle.DANGER),
                self.ikb(text="Back to Main Menu", callback_data="clone_back_start", style=enums.ButtonStyle.DANGER),
            ],
        ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(
                        text="YouTube",
                        url=link,
                        style=enums.ButtonStyle.DANGER,
                    ),
                ],
            ]
        )

    def stats_key(self) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(
                    text="NETWORK STATS",
                    callback_data="stats_net",
                    style=enums.ButtonStyle.SUCCESS,
                )
            ]
        ])

    def stats_net_key(self) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(
                    text="Back",
                    callback_data="stats_back",
                    style=enums.ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="Close",
                    callback_data="stats_close",
                    style=enums.ButtonStyle.PRIMARY,
                ),
            ]
        ])
