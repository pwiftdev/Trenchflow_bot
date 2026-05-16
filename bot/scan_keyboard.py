from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from domain import explorer_links
from domain.token_snapshot import TokenSnapshot


def build_scan_keyboard(snapshot: TokenSnapshot) -> InlineKeyboardMarkup:
    mint = snapshot.mint
    dex_url = snapshot.pair_url or explorer_links.dexscreener_token_url(mint)

    row1 = [
        InlineKeyboardButton("DEF", url=explorer_links.defined_fi_url(mint)),
        InlineKeyboardButton("DS", url=dex_url),
        InlineKeyboardButton("GT", url=explorer_links.gecko_terminal_url(mint)),
        InlineKeyboardButton("EXP", url=explorer_links.solscan_token_url(mint)),
        InlineKeyboardButton("X", url=explorer_links.x_search_url(snapshot.symbol, mint)),
    ]

    return InlineKeyboardMarkup([row1])
