# Argus Bot

Solana-native Telegram bot for crypto trading groups. **Phase 1 (shipped):** CA scan cards, call tracking, founders alpha feed. **Phase 2+ (not shipped):** wallet tracker, ratings, webhooks, referral buy buttons.

Monetization target: referral fees from trading bots (BonkBot, Trojan, Photon, Maestro) — **buy buttons are not in the codebase yet.**

This file is loaded into every Cursor / Claude session. Keep it tight and current. Update **Status** when a phase ships.

---

## Status

- **Current phase:** Phase 1 — **v1 scan path shipped** (prod-verified on VPS).
- **Last working feature:** `/scan` + paste CA → Birdeye photo card; refresh/delete callbacks; alpha feed to founders chat.
- **Known issue:** **Holder count** — Helius `getTokenAccounts` merged into card but unreliable in prod; Birdeye overview count used when present.
- **Runtime:** `ENV=dev` → polling only. `ENV=prod` → `main.py` raises `NotImplementedError` (webhook not wired).
- **Deploy:** Hetzner, systemd `argus`, `/opt/argus`. Repo: https://github.com/pwiftdev/Trenchflow_bot
- **Infra (2026-05-18):** Shared DB pool (`db/runtime.py` + `bot/runtime.py`); reused `httpx` clients per provider; Helius holder RPC off by default (`HELIUS_FETCH_HOLDER_COUNT`).
- **Next (ordered):** Fix holder count display (Birdeye path) → Redis CA cache → Jupiter/DexScreener market fallback when Birdeye fails → custom sniper/fresh/cluster metrics → `ENV=prod` webhook → cross-group **threshold** alert → Phase 2 `/track` + worker.

See `CHANGELOG.md` for the ship log.

---

## What exists in the repo (accurate inventory)

### Telegram (`bot/`)

| Piece | Role |
|-------|------|
| `app.py` | Registers handlers; `post_init` → BotFather command menu |
| `handlers/scan.py` | `/scan`, `run_scan()` |
| `handlers/ca_detect.py` | Auto-scan on mint in message text |
| `handlers/scan_callbacks.py` | 🔄 refresh, 🗑️ delete |
| `handlers/help.py`, `group_setup.py` | Help + welcome on bot added |
| `handlers/ping.py`, `vpstest.py`, `dbtest.py`, `founderstest.py` | Ops / connectivity |
| `scan_pipeline.py` | `build_scan_result()` — parallel API fetch |
| `scan_reply.py` | Photo card with text fallback |
| `scan_keyboard.py` | Explorer URLs (no buy buttons) |
| `scan_context.py` | `record_scan_event`, first/since-call lines |
| `alpha_notify.py` | Mirror group scans to `FOUNDERS_CHAT_ID` |
| `commands.py` | Public: `/scan`, `/help`. Founders: `/founderstest` |
| `filters.py` | `HAS_SOLANA_MINT` message filter |

**Commands not implemented:** `/track`, `/wallets`.

### Services (`services/` — network I/O only)

| File | Used for |
|------|----------|
| `birdeye.py` | Overview, security, holder profile, v3 holders, OHLCV ATH |
| `dexscreener.py` | Token orders (DEX Paid), LP owner addresses for T10 exclude |
| `helius.py` | Mint/freeze, holder count attempt, DAS token image |

**Not in repo:** `jupiter.py`, `twitter.py`, `claude.py`. **No Redis client** despite `REDIS_URL` in settings.

### Domain (`domain/` — pure logic, no HTTP)

| File | Role |
|------|------|
| `ca.py` | Base58 mint validation + extract from text |
| `scan_card.py` | HTML caption tree (stats, security, Trench, socials) |
| `token_snapshot.py`, `security_snapshot.py` | Card DTOs |
| `birdeye_parse.py` | Birdeye JSON → snapshots; merge Helius security |
| `trench_alert.py` | Holder-profile tag tree (“⚠️ Trench”) |
| `lp_holders.py` | Top-10 supply % excluding LP wallets |
| `call_pnl.py` | First call + since-call **MC %** (not wallet FIFO PnL) |
| `alpha_feed.py` | Founders alert text + cross-group line |
| `dex_orders.py` | DexScreener paid/boost parsing |
| `scan_media.py`, `metadata_image.py`, `telegram_caption.py`, `explorer_links.py` | Photo/caption/helpers |

**Planned, not in repo:** `rating.py`, `pnl.py` (FIFO wallet PnL), `clusters.py`.

### Database (`db/`)

- **Alembic migrations:** `tokens`, `groups`, `wallets`, `tracked_wallets`, `scan_events`, `swaps`.
- **App writes today:** `groups` (upsert), `scan_events` (every scan). **`queries.py`:** `record_scan_event`, `fetch_first_scan_in_chat`, `count_distinct_groups_for_ca`, `ping_database`.
- **Not written by app yet:** `tokens`, `wallets`, `tracked_wallets`, `swaps`.

### Entrypoints & runtime

- `main.py` — bot only, polling when `ENV=dev`.
- `bot/runtime.py` — `startup()` / `shutdown()` wire shared DB pool + HTTP clients (`post_init` / `post_shutdown` in `bot/app.py`).
- **No `worker.py`**, **no `workers/`** package in tree.

### Tests (`tests/`)

Implemented: `test_ca`, `test_scan_card`, `test_trench_alert`, `test_call_pnl`, `test_alpha_feed`, `test_birdeye_parse`, `test_lp_holders`, `test_dex_orders`, service parse tests, bot handler tests.  
**Not implemented:** `test_rating`, `test_pnl` (FIFO), sniper/fresh-wallet unit tests.  
**No** `tests/integration/` directory yet.

---

## Scan pipeline (hot path)

`build_scan_result()` (`bot/scan_pipeline.py`) runs in parallel:

1. Birdeye: overview, security, holder profile (`BIRDEYE_HOLDER_PROFILE_INTERVAL`, default `1h`), v3 holders (limit 100).
2. Helius (if key): security merge + metadata image.
3. DexScreener: orders + LP owners.
4. Birdeye: ATH from OHLCV (`BIRDEYE_ATH_LOOKBACK_DAYS`, default 90).

Then: top-10 ex-LP, Trench alert, dev-sold enrichment, caption via `format_scan_card` + `fit_telegram_caption`.

**`/scan` requires `BIRDEYE_API_KEY`.** Scan fails with user-visible error if Birdeye missing or token not indexed. There is **no** DexScreener/Jupiter fallback for market data yet.

---

## Product pitch (target state)

Groups today run Rick + wallet tracker + holder bot — noisy chats. Argus aims for one cleaner CA card, smart-wallet tracking, cross-group alpha, and referral buy buttons. **Only the scan card + alpha feed + per-group call tracking are live.**

---

## Tech stack

| Layer | Choice | In repo today |
|-------|--------|----------------|
| Language | Python 3.11+ | Yes |
| Bot | python-telegram-bot v21 | Yes — **polling only** |
| Market data | **Birdeye primary**; DexScreener for paid + LP | Yes |
| On-chain | Helius RPC (partial) | Yes — not webhooks yet |
| DB | PostgreSQL (Supabase) + SQLAlchemy async + Alembic | Yes |
| Cache | Redis (Upstash) | **Settings only** — not wired |
| Fallback price | Jupiter | **Planned** — not in repo |
| Scheduler | APScheduler | **Planned** — not in repo |
| LLM lore | Claude Haiku | **Planned** — not in repo |
| Hosting | Hetzner VPS | Yes |

**Do not switch stack without updating this file.**

---

## Folder structure (actual)

```
/bot/                 # Handlers, scan pipeline, alpha notify
/services/            # birdeye.py, dexscreener.py, helius.py
/domain/              # scan_card.py, ca.py, call_pnl.py, trench_alert.py, …
/db/                  # models.py, queries.py, migrations/
/config/              # settings.py, logging.py
/tests/               # pytest
/deploy/              # argus.service
main.py
```

**Rule:** HTTP in `/services/`. Pure logic in `/domain/`.

---

## Naming conventions

- snake_case files/functions; PascalCase classes.
- Telegram commands: lowercase, no underscores — `/scan`, `/help` (future: `/track`).
- DB tables: plural snake_case.
- Env vars: `SCREAMING_SNAKE_CASE` with service prefix.

---

## Database (mental model)

| Table | Purpose | App usage today |
|-------|---------|-----------------|
| `scan_events` | Every scan | **Written** |
| `groups` | Telegram groups | **Upserted** on scan |
| `tokens` | CA metadata cache | Schema only |
| `wallets` | Global wallet + rating fields | Schema only |
| `tracked_wallets` | Group ↔ wallet | Schema only |
| `swaps` | Swap history for FIFO PnL | Schema only |

---

## Business logic

### Implemented

- **CA detection** (`domain/ca.py`): base58 32–44 chars, decode → 32 bytes; reject 0/O/I/l; first valid mint in text.
- **Trench alert** (`domain/trench_alert.py`): Birdeye holder-profile tags; bundler/sniper/insider/smart_trader on card; dev → DS line.
- **Fresh % on card:** from Birdeye `token_security` (`fresh_1d_pct`, `fresh_7d_pct`) when API returns them — not custom wallet-age scan.
- **Call PnL** (`domain/call_pnl.py`): first scan in group stores MC; repeats show % change vs first call.
- **Alpha feed** (`bot/alpha_notify.py`): every group scan → founders chat; shows distinct group count in last **30 minutes** when >1 (informational, not a threshold alarm).
- **DEX Paid** (`domain/dex_orders.py` + DexScreener orders API).

### Planned (do not assume implemented)

- **Wallet rating** (`domain/rating.py` — weights in `config/settings.py` when added).
- **FIFO wallet PnL** (`domain/pnl.py`) from `swaps` table.
- **Sniper / fresh-wallet (on-chain):** buy within first ~20 blocks; wallet age ≤7 days — needs Helius + tests.
- **Clusters** (`domain/clusters.py`): shared SOL funder in top 10.
- **Smart-wallet line on card:** `rating_score > 0.6` + bought in 24h.
- **Cross-group threshold alert:** N groups in T minutes → dedicated founders alert (defaults N=3, T=30); distinct from the feed’s 30m count line.
- **Redis:** 30s CA-card cache (and other TTLs in settings when added).

---

## Data source rules (Phase 1 reality)

- **Birdeye** — required for scan: price, MC, liquidity, volume, security, holder profile, holders list, ATH.
- **DexScreener** — DEX Paid + LP addresses only (not primary price).
- **Helius** — optional merge for mint/freeze, holder count, image; webhooks deferred to Phase 2.
- **Do not** silently show placeholder market data if Birdeye fails — reply with an error (current behavior).

When adding sources: new file under `/services/`, key in `.env.example`.

---

## Secrets & config

Committed template: `.env.example`.

| Variable | Phase 1 |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Required |
| `BIRDEYE_API_KEY` | Required for scan |
| `DATABASE_URL` | Required for scan logging / call lines |
| `FOUNDERS_CHAT_ID` | Optional (alpha feed) |
| `HELIUS_API_KEY` | Optional |
| `REDIS_URL`, `ANTHROPIC_API_KEY`, `HELIUS_WEBHOOK_SECRET`, `TWITTER_BEARER`, `SENTRY_DSN`, `WEBHOOK_URL` | Not used in code yet |

Never commit `.env`. Never log secrets.

---

## Testing

```bash
pytest   # from repo root
```

**Have tests:** CA regex, scan card, trench alert, call PnL lines, alpha feed, birdeye parse, LP holders, dex orders, caption/media, bot handlers, settings.

**Need before shipping Phase 2 math:** rating, FIFO PnL, on-chain sniper/fresh-wallet.

**Integration tests** (`pytest -m integration`): not set up — add under `tests/integration/` when needed; don’t burn API credits in CI by default.

---

## Conventions when editing

- **One feature per prompt.**
- **Async everywhere** in the hot path.
- **structlog** for logs.
- Magic numbers → `config/settings.py` when you add them.
- Don’t rewrite planned rating math casually once `domain/rating.py` exists.

---

## What NOT to do

- No new ORM/DB/framework.
- No HTTP in `/domain/`.
- No hardcoded thresholds/weights/TTLs (use settings).
- No user funds / custody in Phase 1.
- No polling Helius for wallet activity when webhooks exist (Phase 2).
- No fake fallback prices on failed Birdeye scan.
- Don’t commit `.env` or log API keys.

---

## Glossary

- **CA** — token mint address.
- **Trench** — Birdeye holder-profile tag block on the card (not the bot name).
- **DS / DP** — Dev sold / DEX Paid on security line.
- **First call / Since call** — per-group scan MC tracking (not wallet PnL).
- **Rick** — incumbent CA-info bot we’re replacing.

---

## Open product decisions

- Phase 5: Twitter API vs scraping (lore).
- Phase 6: native trading bot — default defer.
- Founders console membership — founders only until explicit widen.

---

When unsure: **ship the smallest correct version, test it, update this file and `CHANGELOG.md`.**
