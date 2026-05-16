# Trenchflow

A Solana-native Telegram bot for crypto trading groups. Replaces Rick + a wallet tracker + a holder bot with one cleaner product.

**Status:** Phase 1 — `/scan` live on VPS; **DEX Paid verified**; **holder count broken (revisit)**. See `CLAUDE.md` **Status**.

## What it does

- Clean CA cards on paste — price, MC, liquidity, top 10 %, snipers, fresh wallets, cluster count, mint/freeze authority.
- Tracks smart wallets and notifies the group on buys/sells.
- Builds a global wallet rating database (PnL, hit rate, win rate, recency).
- Surfaces cross-group alpha to the founders' console — when a CA is scanned in N groups within T minutes, we know first.
- Inline buy buttons routing through BonkBot, Trojan, Photon, Maestro referral programs.

The full build plan (`Trenchflow_Build_Plan.docx`) stays local — it is gitignored and not in the public repo. Project context for AI assistants lives in `CLAUDE.md` — read that before opening Cursor.

## Running locally

Phase 0: `/ping` works in dev (polling). Requires `TELEGRAM_BOT_TOKEN` in `.env`; other keys can stay empty for now.

```bash
# Python 3.11+ recommended (3.9 works with current code)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set TELEGRAM_BOT_TOKEN; ENV=dev
python main.py         # send /ping to your bot → pong
pytest                 # optional sanity check
```

`worker.py` (Helius webhooks) ships in a later phase.

## Tech stack

Python 3.11 · python-telegram-bot v21 · Helius · Birdeye · PostgreSQL (Supabase) · Redis (Upstash) · Claude API for lore.

See `CLAUDE.md` for the rationale on each pick and the rules for changing them.

## Repo layout

```
/bot         Telegram handlers
/workers     Helius webhook receiver, swap parser
/services    External API clients (one file per provider)
/domain      Pure business logic — rating, PnL, clusters
/db          Models, queries, migrations
/config      Settings (Pydantic, reads .env)
/tests       Pytest, mirrors src tree
```

## Contributing

Two-founder project for now. If that changes, a `CONTRIBUTING.md` will appear.

## License

TBD.
