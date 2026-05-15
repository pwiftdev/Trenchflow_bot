# Trenchflow Bot

A Solana-native Telegram bot that replaces Rick + a wallet tracker + a holder bot with one cleaner product. Built for crypto trading groups. Monetized via referral fees from existing trading bots (BonkBot, Trojan, Photon, Maestro), not by charging groups.

This file is loaded into every Cursor / Claude session. Keep it tight and current. Update the **Status** line below whenever a phase ships.

---

## Status

- **Current phase:** Phase 0 — Foundations (in progress)
- **Last working feature:** `/ping` → `pong` verified in Telegram (dev polling, `ENV=dev`, `python main.py`)
- **Next task:** Supabase + first migration (`tokens`, `groups`, `scan_events`), then prod webhook on VPS. Local bot + token are done.

See `CHANGELOG.md` for what shipped previously.

---

## Product Pitch (one paragraph)

Most Telegram trading groups run 4–5 bots (Rick for CA info, a wallet tracker, a holder bot, sometimes an alpha bot) — the chat ends up unreadable. Trenchflow consolidates those into one bot with a cleaner CA card, integrated smart-wallet tracking, and a proprietary cross-group alpha layer (we see scan activity across every group running the bot, nobody else does). Quick-buy buttons on each card route through referral programs of the major trading bots — that's the revenue model. The trading layer is a Phase-2 product, not part of v1.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | Async-first. Chose over Node for Cursor readability and Solana SDK ecosystem. |
| Bot framework | `python-telegram-bot` v21 | Webhook mode in prod, polling in dev. |
| Solana data | Helius (RPC + Enhanced Transactions + Webhooks) | Primary source for holders, txs, wallet activity. |
| Price/market data | Birdeye → DexScreener → Jupiter (fallback chain) | Always fall through; don't fail a card on one upstream being down. |
| DB | PostgreSQL via Supabase | Migrations live in `db/migrations/`. |
| Cache / queue | Redis (Upstash) | TTL caches for CA cards, rate-limit counters, scan-threshold counters. |
| Scheduler | APScheduler in-process | Nightly wallet rating refresh, daily cleanup. Move to Celery if it grows. |
| LLM (lore) | Claude API, model `claude-haiku-4-5` | Short 2-line project summaries. Keep prompts short — Haiku is cheap but token costs add up. |
| Hosting | Single VPS (Hetzner CX22) to start | Split bot + worker into two services once we exceed ~50 tracked wallets. |

**Do not switch any of these without updating this file.** If you genuinely need a new dependency, justify it in the PR description.

---

## Folder Structure

```
/bot/              # Telegram handlers (commands, callbacks, CA detection)
/workers/          # Helius webhook receiver, swap parser, notification dispatcher
/services/         # External API clients — one file per provider
    helius.py
    birdeye.py
    dexscreener.py
    jupiter.py
    twitter.py
    claude.py
/domain/           # Core business logic — pure functions, no I/O
    ca_card.py     # CA card composition
    rating.py      # Wallet rating algorithm
    pnl.py         # FIFO cost basis, PnL math
    clusters.py    # Holder cluster detection
/db/
    models.py      # SQLAlchemy or asyncpg row mappers
    queries.py     # All SQL lives here, not scattered
    migrations/    # Alembic
/config/
    settings.py    # Pydantic Settings, reads .env
/tests/            # Pytest. Mirror the src tree.
main.py            # Entry point for bot
worker.py          # Entry point for webhook worker
```

**Rule:** anything that calls a network goes in `/services/`. Anything in `/domain/` must be a pure function so it can be unit-tested. Cursor: do not put HTTP calls in `/domain/`.

---

## Naming Conventions

- snake_case for files, functions, vars. PascalCase for classes.
- File names describe what's inside, not what they do. `services/helius.py` not `services/helius_client.py`.
- Telegram commands are lowercase, no underscores: `/scan`, `/track`, `/wallets`.
- DB tables are plural snake_case: `tokens`, `wallets`, `tracked_wallets`, `scan_events`, `groups`.
- Env vars are SCREAMING_SNAKE_CASE prefixed by service: `HELIUS_API_KEY`, `BIRDEYE_API_KEY`, `TELEGRAM_BOT_TOKEN`.
- Never abbreviate Solana terms. It's `mint_authority`, not `mint_auth`.

---

## Database (high-level)

The exact schema lives in `db/migrations/`. The big-picture mental model:

- **tokens** — every CA we've ever scanned. Cached metadata. Updated when stale (>1h).
- **groups** — every Telegram group the bot is in. `group_id`, `name`, settings (min USD threshold, etc.).
- **wallets** — global wallet table. `address` is the PK. Rating fields live here (`pnl_30d`, `win_rate`, `hit_rate`, `rating_score`). One row per wallet, ever.
- **tracked_wallets** — many-to-many between groups and wallets. A wallet can be tracked in multiple groups with different labels.
- **scan_events** — log row every time a CA is scanned. Used for the cross-group threshold alert. Indexed on (ca, ts).
- **swaps** — parsed swap history per wallet. Source of truth for PnL calculations.

When in doubt, add a row, don't mutate. We need history for ratings to be honest.

---

## Key Business Logic (gotchas)

### CA detection regex
Solana addresses are base58, 32–44 chars. Match `[1-9A-HJ-NP-Za-km-z]{32,44}` and validate by attempting base58 decode → 32 bytes. Reject 0/O/I/l silently (those aren't in base58). Do not trigger on token names or symbols.

### Snipers / fresh wallets
- **Sniper** = a wallet that bought within the first 20 blocks (~8 seconds) of the token's first liquidity event.
- **Fresh wallet** = wallet whose first-ever transaction is ≤7 days old at the time of the buy.
- These two metrics are where Rick is weak and where we win on accuracy. **Write tests for the calculations.** Cursor will produce subtly wrong code if you don't.

### Rating algorithm (`domain/rating.py`)
Weighted blend, normalize each component to 0–1:
- 30-day PnL (USD) — weight 0.35
- Win rate (% of buys that closed green) — weight 0.20
- Hit rate (% of buys that did ≥2x) — weight 0.30
- Recency penalty (exp decay from last activity) — weight 0.15

Output is `rating_score` in [0, 1]. The exact weights will change — keep them in `config/settings.py` not hardcoded, so we can tune without redeploying.

### Smart-wallet threshold on CA cards
Show "X smart wallets bought" only for wallets with `rating_score > 0.6` AND that bought this token in the last 24h. Below the threshold is noise.

### Cross-group scan threshold
When a CA is scanned in N distinct groups within T minutes, post a founders-console alert. Defaults: N=3, T=30. Configurable. Dedupe per (ca, group_id) so spam-scanning in one group doesn't trip the threshold.

### Cluster detection (`domain/clusters.py`)
For the top 10 holders, group wallets that share a SOL funding source (look back at the first SOL deposit). 2+ holders sharing a funder = a cluster. Surface "X clusters in top 10" on the CA card. Big clusters are a red flag.

---

## Data Source Rules

- **Helius first** for anything on-chain: holders, mint state, wallet txs, token metadata via DAS. Has webhooks — use them, don't poll.
- **Birdeye** for market data: price, MC, liquidity, 24h volume.
- **DexScreener** as fallback when Birdeye is rate-limited or the token is too new for Birdeye to have indexed.
- **Jupiter price API** as final fallback for a price-only sanity check.
- **Twitter** only for lore. Don't use it for anything that has to be accurate / fast.
- **Cache everything.** CA cards in Redis for 30s, lore for 24h, holder snapshots for 5 min. Network calls in the hot path are the #1 thing that makes the bot feel slow.

If you add a new data source, add a new file in `/services/` and put the API key in `.env.example`.

---

## Secrets & Config

All secrets go in `.env` (gitignored). `.env.example` is committed with empty values so future devs / Cursor know what env vars exist.

Required env vars:
```
TELEGRAM_BOT_TOKEN=
HELIUS_API_KEY=
HELIUS_WEBHOOK_SECRET=
BIRDEYE_API_KEY=
DATABASE_URL=
REDIS_URL=
ANTHROPIC_API_KEY=
FOUNDERS_CHAT_ID=
SENTRY_DSN=          # optional
TWITTER_BEARER=      # optional, lore only
```

Never commit a real key. Never log a key. If a key needs to be printed for debug, redact to last 4 chars.

---

## Testing

- `pytest` from repo root. Tests mirror the source tree.
- **Required tests:**
  - CA detection regex (positive + negative cases including the 0/O/I/l confusables).
  - Rating algorithm (`domain/rating.py`) — fixture wallets with known PnL, assert score ranking.
  - PnL FIFO math (`domain/pnl.py`) — multi-buy, partial-sell, multi-token cases.
  - Sniper / fresh-wallet calc — fixtures with mocked block timestamps.
- Integration tests against Helius / Birdeye go in `/tests/integration/` and run on opt-in (`pytest -m integration`). Don't burn API credits in CI by default.

---

## Conventions When Editing Code

- **One feature per prompt.** Don't ask Cursor to "build the wallet tracker" — ask it to add `/track` command, then add webhook registration, then add the swap parser. Big asks produce big mistakes.
- **Plan before applying.** For non-trivial changes, ask Cursor to describe its plan first; review; then let it edit.
- **Don't let Cursor rewrite the rating algorithm casually.** That math is load-bearing. Changes to `/domain/rating.py` get a real review.
- **Prefer adding to extending.** New API client? New file in `/services/`. Don't pile into an existing one.
- **Async everywhere.** This bot is I/O bound. Sync code in the hot path is a bug.
- **Log structured.** Use `structlog`. Log levels: DEBUG for hot paths, INFO for command handling, WARNING for upstream failures we recovered from, ERROR for things a human needs to see.

---

## What NOT to do

- **Do not** introduce a new ORM, framework, or DB. Stack is set above.
- **Do not** put network calls in `/domain/`. That folder is pure logic.
- **Do not** hardcode magic numbers (rating weights, thresholds, TTLs). Put them in `config/settings.py`.
- **Do not** ship a feature that touches user funds. Custody is a Phase-2 decision and not on the table yet.
- **Do not** trust user-submitted wallets as smart wallets by default. They go into `tracked_wallets` but only contribute to `rating_score` after a founder approves.
- **Do not** poll Helius when a webhook would work. Quota is real.
- **Do not** commit `.env`, the Helius webhook secret, or the Anthropic key. Pre-commit hook should catch this — if it didn't, fix the hook.
- **Do not** silently fall back to placeholder data on a CA card. If Birdeye is down and DexScreener also fails, say so on the card. Honesty over polish.

---

## Glossary (Solana / trading bot terms used in code)

- **CA** — Contract Address. The token mint address. The thing users paste.
- **LP** — Liquidity Pool. "LP burned" = the LP tokens were sent to a dead address, signalling devs can't pull liquidity.
- **Mint authority** — the address allowed to mint more of the token. "Renounced" = set to null = good.
- **Freeze authority** — the address allowed to freeze user balances. Should be null on a legit token.
- **Snipers** — wallets that bought in the first few blocks. High sniper count = orchestrated launch, often a sell wall later.
- **Fresh wallet** — wallet created very recently. High % of fresh wallets in top holders = likely a coordinated rug setup.
- **Cluster** — group of wallets funded from the same source. Indicates one person controlling multiple "different" holders.
- **Smart wallet** — a wallet with proven historical performance in our DB (rating_score > 0.6).
- **Rick** — the dominant existing CA-info bot in Solana trading groups. The thing we're displacing.
- **PnL** — Profit and Loss. We compute FIFO from on-chain swaps; don't use third-party PnL APIs (they disagree with each other).
- **Hit rate** — % of a wallet's buys that did ≥2x at any point. Different from win rate (which is just green/red on close).

---

## Open product decisions (resolve before relevant phase)

- Phase 5: Twitter API tier — Basic ($100/mo) vs. scraping. Defer until referral revenue > $0.
- Phase 6: trading bot — yes/no/defer. Default is defer.
- Founders console membership — currently just the two founders. Don't widen without explicit decision.

---

If you (Cursor, Claude, future contributor) are unsure about a decision, default to: **ship the smallest correct version, write a test for it, and update this file with what you learned.**
