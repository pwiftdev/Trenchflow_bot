from telegram import InlineKeyboardButton, InlineKeyboardMarkup

REFRESH_PREFIX = "scan_refresh:"
DELETE_CALLBACK = "scan_delete"


def build_scan_keyboard(mint: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("REFRESH", callback_data=f"{REFRESH_PREFIX}{mint}"),
                InlineKeyboardButton("DELETE", callback_data=DELETE_CALLBACK),
            ],
        ]
    )
