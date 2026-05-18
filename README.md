# Argus

Solana Telegram bot for crypto trading groups — **Phase 1 ships the CA scan path only.** One bot to replace Rick-style CA cards (wallet tracking, ratings, and buy buttons are later phases).

**Prod:** Hetzner VPS, `/opt/argus`, systemd unit `argus`, **polling** (`ENV=dev`).  
**Repo:** https://github.com/pwiftdev/Trenchflow_bot  
**AI / contributor context:** `CLAUDE.md` (keep in sync when you ship).

---

## Shipped today (Phase 1)

| Feature | Notes |
|--------|--------|
| **`/scan <mint>`** | Full token card (photo + HTML caption) |
| **Paste CA** | Auto-scan on valid Solana mint in message text (`bot/handlers/ca_detect.py`) |
| **Market data** | **Birdeye** — overview, security, holder profile, v3 holders, OHLCV ATH |
| **DEX Paid** | **DexScreener** orders API → 🟢/🔴 on card |
| **Top 10 ex-LP** | Birdeye holders + DexScreener LP `pairAddress` exclude (`domain/lp_holders.py`) |
| **Trench block** | Birdeye holder-profile tags (bundler, sniper, insider, smart_trader) as supply % |
| **Security** | T10, fresh 1D/7D (Birdeye), dev sold (DS), DEX paid (DP); Helius merges mint/freeze |
| **Call tracking** | First call + since-call MC % per group (`scan_events` + `domain/call_pnl.py`) |
| **Alpha feed** | Group scans mirrored to `FOUNDERS_CHAT_ID` with 30m cross-group count |
| **Keyboard** | DEF / DS / GT / EXP / X links + refresh / delete |
| **DB** | PostgreSQL: `groups` + `scan_events` written on each scan |

**Ops / dev commands (still registered):** `/ping`, `/vpstest`, `/dbtest`, `/founderstest` (founders menu).

**Known issue:** holder count (👁️ subline + security “Holders”) — uses Birdeye overview; Helius holder RPC disabled by default (was unreliable).

---

## Not built yet (roadmap)

- `/track`, wallet webhooks, `worker.py`, swap ingestion, wallet **ratings** (`domain/rating.py` — not in repo)
- Custom on-chain **sniper / fresh-wallet / cluster** metrics (beyond Birdeye’s bundled fields)
- **Quick-buy** referral buttons (BonkBot, Trojan, etc.)
- **Redis** cache, **Jupiter** price fallback, **Claude** lore, **Twitter**
- **`ENV=prod` webhook** (`main.py` raises today — polling only)
- Separate **cross-group threshold alert** (N groups in T minutes); feed already shows count when >1 group in 30m
- DB tables `tokens`, `wallets`, `tracked_wallets`, `swaps` — migrated schema only, no app writes yet

---

## Requirements

| Variable | Phase 1 |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | **Required** |
| `BIRDEYE_API_KEY` | **Required** for `/scan` |
| `DATABASE_URL` | **Required** for call tracking + alpha feed DB bits |
| `FOUNDERS_CHAT_ID` | Optional — disables alpha feed if unset |
| `HELIUS_API_KEY` | Optional — mint/freeze, token image; holder RPC off unless `HELIUS_FETCH_HOLDER_COUNT=true` |
| `ALPHA_CROSS_GROUP_WINDOW_MINUTES` | Optional — founders feed cross-group window (default 30) |
| `REDIS_URL`, `ANTHROPIC_API_KEY`, `TWITTER_BEARER`, `SENTRY_DSN`, `HELIUS_WEBHOOK_SECRET` | In settings only — **not used in code yet** |

---

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # TELEGRAM_BOT_TOKEN, BIRDEYE_API_KEY, DATABASE_URL at minimum
python main.py         # ENV=dev → polling
pytest
```

**Groups:** [@BotFather](https://t.me/BotFather) → `/setprivacy` → **Disable**, then re-add the bot so it sees pasted CAs.

**Migrations:** `alembic upgrade head` (needs `DATABASE_URL`).

---

## Tech stack (in repo)

Python 3.11+ · **python-telegram-bot** v21 · **httpx** · **SQLAlchemy 2 + asyncpg** · **Alembic** · **structlog** · **Pydantic Settings**

**External APIs used in production path:** Birdeye, DexScreener (orders + pairs), Helius RPC (partial).

---

## Layout

```
main.py                 # Bot entry (polling; prod webhook not wired)
bot/
  app.py                # Handler registration
  scan_pipeline.py      # Parallel fetch + card build
  handlers/             # scan, ca_detect, help, group_setup, callbacks, …
  alpha_notify.py       # Founders feed
domain/
  ca.py, scan_card.py, call_pnl.py, trench_alert.py, lp_holders.py, …
services/
  birdeye.py, dexscreener.py, helius.py   # only API clients implemented
db/
  models.py, queries.py, migrations/
config/settings.py
tests/                  # pytest (mirrors tree; no integration suite yet)
deploy/argus.service
```

There is **no** `worker.py`, **`workers/`** package, or `services/jupiter.py` / `claude.py` / `twitter.py` in the repo yet.

---

## Contributing

Small PRs, one feature at a time. Update `CHANGELOG.md` and `CLAUDE.md` **Status** when you ship.

## License

TBD.
