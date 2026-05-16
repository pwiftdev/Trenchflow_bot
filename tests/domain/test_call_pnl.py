from datetime import datetime, timedelta, timezone

from domain.call_pnl import format_since_call_line


def test_first_scan_line() -> None:
    line = format_since_call_line(
        first_market_cap_usd=None,
        current_market_cap_usd=147_400,
        first_scanned_at=datetime.now(timezone.utc),
        first_caller_label="Alice",
        is_first_scan=True,
        current_caller_label="Alice",
    )
    assert "First call" in line
    assert "$147.40K" in line


def test_repeat_scan_shows_pnl_since_call() -> None:
    first_at = datetime.now(timezone.utc) - timedelta(minutes=12)
    line = format_since_call_line(
        first_market_cap_usd=100_000,
        current_market_cap_usd=130_000,
        first_scanned_at=first_at,
        first_caller_label="Alice",
        is_first_scan=False,
        current_caller_label="Bob",
    )
    assert "Since call" in line
    assert "+30.0%" in line
    assert "12m ago" in line
