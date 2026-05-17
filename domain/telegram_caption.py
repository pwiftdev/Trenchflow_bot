import re
from html import escape


TELEGRAM_CAPTION_LIMIT = 1024


def fit_telegram_caption(caption: str, limit: int = TELEGRAM_CAPTION_LIMIT) -> str:
    """Trim caption without breaking HTML mid-line (Telegram rejects broken tags)."""
    if len(caption) <= limit:
        return caption

    suffix = "\n…"
    budget = limit - len(suffix)
    lines = caption.split("\n")
    kept: list[str] = []
    used = 0
    for line in lines:
        extra = len(line) + (1 if kept else 0)
        if used + extra > budget:
            break
        kept.append(line)
        used += extra

    if kept:
        return "\n".join(kept) + suffix
    return caption[:budget] + "…"


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def href_attr(url: str) -> str:
    return escape(url, quote=True)
