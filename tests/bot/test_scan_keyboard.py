from bot.scan_keyboard import DELETE_CALLBACK, REFRESH_PREFIX, build_scan_keyboard

MINT = "So11111111111111111111111111111111111111112"


def test_scan_keyboard_has_refresh_and_delete() -> None:
    keyboard = build_scan_keyboard(MINT)
    row = keyboard.inline_keyboard[0]
    assert len(row) == 2
    assert row[0].text == "REFRESH"
    assert row[0].callback_data == f"{REFRESH_PREFIX}{MINT}"
    assert row[1].text == "DELETE"
    assert row[1].callback_data == DELETE_CALLBACK
