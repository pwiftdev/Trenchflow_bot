# Changelog

All notable changes to Trenchflow. One line per shipped feature. Newest first.

Format: `## YYYY-MM-DD — Phase X — Short title` followed by a short bullet list of what changed.

When you ship something, add an entry here and update the **Status** line in `CLAUDE.md`.

---

## Unreleased

- Prod webhook deploy on VPS.
- Supabase Postgres + first Alembic migration.

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
