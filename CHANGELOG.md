# Changelog

All notable changes to Trenchflow. One line per shipped feature. Newest first.

Format: `## YYYY-MM-DD — Phase X — Short title` followed by a short bullet list of what changed.

When you ship something, add an entry here and update the **Status** line in `CLAUDE.md`.

---

## Unreleased

- Prod webhook (`ENV=prod`, domain + HTTPS).
- Phase 1: `/scan` + CA card (DexScreener → Birdeye → Helius).

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
