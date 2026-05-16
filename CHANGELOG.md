# Changelog

All notable changes to Trenchflow. One line per shipped feature. Newest first.

Format: `## YYYY-MM-DD — Phase X — Short title` followed by a short bullet list of what changed.

When you ship something, add an entry here and update the **Status** line in `CLAUDE.md`.

---

## Unreleased

- Auto-detect CA paste in group messages (regex + base58 validate).
- Birdeye price fallback; Redis 30s CA-card cache.
- Holder count, sniper %, fresh-wallet %, cluster count on card (Helius-heavy).
- Prod webhook (`ENV=prod`, domain + HTTPS).
- Cross-group scan threshold → founders console.

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

- Public repo: https://github.com/pwiftdev/Trenchflow_bot (private docx/assets gitignored).
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
