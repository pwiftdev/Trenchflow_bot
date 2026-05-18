# Changelog

All notable changes to Argus. One line per shipped feature. Newest first.

Format: `## YYYY-MM-DD — Phase X — Short title` followed by a short bullet list of what changed.

When you ship something, add an entry here and update the **Status** line in `CLAUDE.md`.

---

## 2026-05-18 — Phase 1 — Bot renamed to Argus

- User-facing branding **Trenchflow → Argus** (help, group welcome, `/help` command description, founderstest).
- Docs: `CLAUDE.md`, `README.md`.
- `deploy/trenchflow.service` → `deploy/argus.service`; VPS paths `/opt/trenchflow` → `/opt/argus` (rename on server when deploying).

## 2026-05-18 — Performance & reliability fixes

- **Shared DB pool** — one SQLAlchemy engine per process (`db/runtime.py`); scan + alpha feed no longer create/dispose engine 3× per scan.
- **Reused HTTP clients** — Birdeye, DexScreener, Helius keep `httpx.AsyncClient` for connection pooling (`bot/runtime.py` lifecycle).
- **Refresh callback** — answer `callback_query` once (errors use alert; success answers after fetch).
- **First-call line** — DB lookup failures degrade to “first call” instead of dropping the line.
- **Group name** — upsert `groups.name` when title arrives after first anonymous insert.
- **Helius holder RPC** — off by default (`HELIUS_FETCH_HOLDER_COUNT=false`); Birdeye supplies holder count. Saves 1 RPC/scan.
- **Alpha window** — `ALPHA_CROSS_GROUP_WINDOW_MINUTES` in settings (default 30).
- **DB index** — migration `004` on `(group_id, ca, scanned_at)` for first-call lookups.
- **Scan timestamp** — single `scanned_at` for card meta, DB row, and founders feed.
- **ChatMigrated** — use `exc.new_chat_id` (python-telegram-bot API) in founders commands + alpha feed retry.

## 2026-05-18 — Docs — align README / CLAUDE with codebase

- Audited repo vs docs: Birdeye-primary scan, actual commands, services, domain modules, DB tables in use.
- Documented what is **not** implemented (worker, Redis, Jupiter, ratings, buy buttons, prod webhook).
- Corrected README “what it does” (removed roadmap items presented as shipped).

---

## Unreleased

- **Fix holder count** on scan card (Helius `getTokenAccounts` — implemented but not working in prod; revisit).
- Redis 30s CA-card cache (`REDIS_URL` in settings, no client yet).
- Birdeye → DexScreener → Jupiter **market** fallback when Birdeye fails (scan currently hard-requires Birdeye).
- Custom on-chain sniper / fresh-wallet / cluster metrics (Birdeye Trench + fresh % already on card where API returns data).
- Prod webhook (`ENV=prod` — `main.py` raises today).
- Cross-group **threshold** alert (N groups / T min); feed already shows 30m distinct-group count when >1.
- Phase 2: `worker.py`, `/track`, Helius webhooks, `swaps` ingestion, `domain/rating.py`, buy buttons.

## 2026-05-17 — Phase 1 — v1 scan path complete (prod-verified)

- **`/scan` + paste CA** — `domain/ca.py` extract + `bot/handlers/ca_detect.py`; mint-specific `MessageHandler` filter. Verified in prod (groups require BotFather privacy **off**).
- **Birdeye-primary pipeline** — `bot/scan_pipeline.py`: overview, `token_security`, holder-profile (Trench), OHLCV ATH; DexScreener only for DEX Paid + LP `pairAddress` list.
- **Top 10 ex-LP** — `domain/lp_holders.py` + Birdeye `/defi/v3/token/holder`; excludes pump.fun / AMM pool (`pairAddress` = rank-1 “holder”).
- **Trench Alert** — Birdeye holder-profile tags as supply-% tree (`domain/trench_alert.py`); dev tag excluded from Trench, shown as DS in security.
- **Scan card UX** — Phanes-style tree caption; explorer URL row + 🔄/🗑️ (`bot/scan_keyboard.py`); security labels DS/DP; single photo under 1024-char caption.
- **Startup fix** — `ChatMigrated` on founders supergroup id; retry + log hint to update `FOUNDERS_CHAT_ID`.

## 2026-05-16 — Phase 1 — DEX Paid on scan card (verified)

- DexScreener `GET /orders/v1/{chain}/{mint}` — `tokenProfile` + `status: approved` → `🟢 Paid`, else `🔴`.
- **Verified working in prod.**

## 2026-05-16 — Phase 1 — Holder count (not verified — revisit)

- Helius DAS `getTokenAccounts` → `total` wired to subline + security block.
- **Not working reliably in prod** — leave as known issue; fix in a later pass.

## 2026-05-16 — Phase 1 — Alpha feed (founders group)

- Every `/scan` in a group/supergroup/channel is mirrored to `FOUNDERS_CHAT_ID`.
- Alert: group name, token, MC/price/LP/vol at scan, first/since-call line, cross-group count (30m).
- Skips private chats and the founders chat itself. Inline DS/DEF/GT links on the alert.
- `/founderstest` command to verify founders chat connectivity.

## 2026-05-16 — Phase 1 — Repeat-scan caller label

- Migration `003`: `scanner_full_name`, `scanner_username` on `scan_events`.
- Repeat “since call” line shows `Bakardi (@bakardisol)` instead of numeric `User {id}`.

## 2026-05-16 — Phase 1 — First call / since-call PnL

- `/scan` logs `market_cap_usd` + `price_usd` per scan (migration `002`).
- First scan: `🔥 First call … @ $MC`; repeat: `📈 Since call @ $X → $Y (+Z%)` + time since first call.
- Lookup first scan in chat **before** inserting new row.

## 2026-05-16 — Phase 1 — `/scan` CA card (DexScreener + Helius)

- `services/dexscreener.py` — `token-pairs/v1` first (fixes stale MC on graduated pump.fun tokens).
- `domain/scan_card.py` — Phanes-style tree caption; inline link row (`bot/scan_keyboard.py`).
- `services/helius.py` — mint authority, freeze authority, top-10 holder % (when `HELIUS_API_KEY` set).
- `bot/handlers/scan.py` — photo banner + HTML caption.

## 2026-05-15 — Phase 0 — Supabase on VPS (`/dbtest`)

- Initial schema via Alembic (`tokens`, `groups`, `wallets`, `tracked_wallets`, `scan_events`, `swaps`).
- Session pooler `DATABASE_URL` (IPv4) on Mac + Hetzner.
- **`/dbtest` → `DB connected`** verified in Telegram from production VPS.

## 2026-05-15 — Phase 0 — `/vpstest` deploy check

- Added `/vpstest` command (replies `VPS worked`) to verify `git pull` + systemd restarts on the VPS.
- Added `deploy/trenchflow.service` for systemd setup.

## 2026-05-15 — Phase 0 — VPS deploy + GitHub

- Public repo: https://github.com/pwiftdev/Argus-Telegram-Bot (renamed from `Trenchflow_bot`; private docx/assets gitignored).
- Bot runs on Hetzner VPS via systemd; `/ping` works without local Mac running.

## 2026-05-15 — Phase 0 — Dev bot online (`/ping`)

- Renamed project **AlphaScan → Trenchflow** (docs, `Trenchflow_Build_Plan.docx`, `Trenchflow_Proposal.docx`).
- Scaffolded repo layout (`bot/`, `config/`, `services/`, `domain/`, `db/`, `workers/`, `tests/`).
- Added Pydantic settings (`config/settings.py`), structlog logging, `requirements.txt`.
- Implemented `/ping` command (replies `pong`) with dev polling in `main.py`.
- Settings: blank `.env` values treated as unset; `Optional` types for Python 3.9 venv compatibility.
- Unit tests for ping handler and settings parsing.
- **Verified in Telegram:** `/ping` → `pong` with `TELEGRAM_BOT_TOKEN` in `.env`.

---

## Prior

- Project kickoff. Build plan and CLAUDE.md drafted.
