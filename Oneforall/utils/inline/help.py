from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Oneforall import app


# =========================
# MAIN HELP PANEL (4 MAIN BUTTONS)
# =========================

def help_pannel(_, START: Union[bool, int] = None):
    first = [
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")]
    ]

    second = [
        [
            InlineKeyboardButton(text=_["BACK_PAGE"], callback_data="mbot_cb"),
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="settingsback_helper"),
            InlineKeyboardButton(text=_["NEXT_PAGE"], callback_data="mbot_cb"),
        ]
    ]

    mark = second if START else first

    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• ᴠɪᴅєσᴄʜᴧᴛ •", callback_data="help_category videochat"),
                InlineKeyboardButton(" • ꜰᴜη •", callback_data="help_category fun"),
            ],
            [
                InlineKeyboardButton("• ϻᴧηᴧɢєϻєηᴛ •", callback_data="help_category moderation"),
                InlineKeyboardButton("• ꜱᴜᴅσєʀꜱ σηʟʏ •", callback_data="help_category sudoers"),
            ],
            *mark,
        ]
    )
    return upl


# =========================
# VIDEOCHAT CATEGORY
# =========================

def videochat_panel(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text=_["H_B_6"], callback_data="help_callback hb6"),
                InlineKeyboardButton(text=_["H_B_11"], callback_data="help_callback hb11"),
                InlineKeyboardButton(text=_["H_B_12"], callback_data="help_callback hb12"),
            ],
            [
                InlineKeyboardButton(text=_["H_B_13"], callback_data="help_callback hb13"),
                InlineKeyboardButton(text=_["H_B_14"], callback_data="help_callback hb14"),
                InlineKeyboardButton(text=_["H_B_15"], callback_data="help_callback hb15"),
            ],
            [
                InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="back_to_main"),
            ],
        ]
    )


# =========================
# FUN CATEGORY
# =========================

def fun_panel(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text=_["H_B_16"], callback_data="help_callback hb16"),
                InlineKeyboardButton(text=_["H_B_17"], callback_data="help_callback hb17"),
                InlineKeyboardButton(text=_["H_B_22"], callback_data="help_callback hb22"),
                InlineKeyboardButton(text="🎮 ғᴜɴ ɢᴀᴍᴇ",callback_data="help_callback hb26"),
            ],
            [
                InlineKeyboardButton(text=_["H_B_25"], callback_data="help_callback hb25"),
                InlineKeyboardButton(text=_["H_B_27"], callback_data="help_callback hb27"),
                InlineKeyboardButton(text="✨ ғsᴜʙ",callback_data="help_callback hb20"),
                ),
            ],
            [
                InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="back_to_main"),
            ],
        ]
    )


# =========================
# MODERATION CATEGORY
# =========================

def moderation_panel(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text=_["H_B_1"], callback_data="help_callback hb1"),
                InlineKeyboardButton(text=_["H_B_8"], callback_data="help_callback hb8"),
                InlineKeyboardButton(text=_["H_B_9"], callback_data="help_callback hb9"),
            ],
            [
                InlineKeyboardButton(text=_["H_B_18"], callback_data="help_callback hb18"),
                InlineKeyboardButton(text=_["H_B_20"], callback_data="help_callback hb20"),
                InlineKeyboardButton(text=_["H_B_24"], callback_data="help_callback hb24"),
            ],
            [
                InlineKeyboardButton(text=_["H_B_28"], callback_data="help_callback hb28"),
            ],
            [
                InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="back_to_main"),
            ],
        ]
    )


# =========================
# SUDOERS CATEGORY
# =========================

def sudoers_panel(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text=_["H_B_7"], callback_data="help_callback hb7"),
                InlineKeyboardButton(text=_["H_B_4"], callback_data="help_callback hb4"),
                InlineKeyboardButton(text=_["H_B_5"], callback_data="help_callback hb5"),
            ],
            [
                InlineKeyboardButton(text=_["H_B_3"], callback_data="help_callback hb3"),
                InlineKeyboardButton(text=_["H_B_2"], callback_data="help_callback hb2"),
            ],
            [
                InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="back_to_main"),
            ],
        ]
    )


# =========================
# BACK MARKUP
# =========================

def help_back_markup(_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="back_to_main",
                ),
            ]
        ]
    )


# =========================
# PRIVATE HELP PANEL
# =========================

def private_help_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                url=f"https://t.me/{app.username}?start=help",
            ),
        ],
    ]
    return buttons
