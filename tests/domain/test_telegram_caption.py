from domain.telegram_caption import fit_telegram_caption


def test_fit_telegram_caption_does_not_break_html_mid_tag() -> None:
    line = '<a href="https://x.com/search?q=a&amp;b">X</a>'
    caption = "\n".join(["header", line, "footer", "extra"])
    fitted = fit_telegram_caption(caption, limit=60)
    assert "<a href" not in fitted or line in fitted or fitted.endswith("…")
    assert len(fitted) <= 60
    assert "…" in fitted


def test_fit_telegram_caption_unchanged_when_short() -> None:
    caption = "short caption"
    assert fit_telegram_caption(caption) == caption
