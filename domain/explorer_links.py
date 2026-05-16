from typing import Optional


def solscan_token_url(mint: str) -> str:
    return f"https://solscan.io/token/{mint}"


def gecko_terminal_url(mint: str) -> str:
    return f"https://www.geckoterminal.com/solana/tokens/{mint}"


def birdeye_token_url(mint: str) -> str:
    return f"https://birdeye.so/token/{mint}?chain=solana"


def defined_fi_url(mint: str) -> str:
    return f"https://www.defined.fi/solana/{mint}"


def dexscreener_token_url(mint: str) -> str:
    return f"https://dexscreener.com/solana/{mint}"


def x_search_url(symbol: Optional[str], mint: str) -> str:
    query = symbol or mint
    return f"https://x.com/search?q={query}"
