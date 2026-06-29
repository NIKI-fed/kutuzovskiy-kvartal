# Личный кабинет агента — Implementation Plan

## Goal
Hidden agent cabinet (direct URL `/agents` only, no public links). Agents log in with admin-issued credentials, browse houses → flats → flat detail with plan images and a "Оформить заявку" button (visual only, persists nothing).

## Decisions (confirmed)
- **Architecture**: Jinja2 server-rendered templates + Flask signed sessions + `werkzeug` password hashing. New `agents_bp` blueprint at `/agents`.
- **DB**: SQLite (`instance/kutuzov.db`) via `sqlite3` stdlib; per-request connection through Flask `g` + `teardown_appcontext`.
- **Schema**: `agents`, `houses`, `flats` (status available/reserved/sold; `plan_images` JSON array).
- **Seed**: 2 existing houses (Кутузов III кв 2027, Толстой II кв 2028) + ~10 sample flats each + 1 default agent `agent`/`agent123`.
- **Reserve button**: client-side confirmation only.
- **Credentials**: default agent + `scripts/add_agent.py`.

## Routes
- `GET /agents` → redirect to `/agents/houses` (if authed) or `/agents/login`
- `GET/POST /agents/login`, `GET /agents/logout`
- `GET /agents/houses` (protected)
- `GET /agents/houses/<house_id>` (protected)
- `GET /agents/houses/<house_id>/flats/<flat_id>` (protected)

## Files
- `agents/__init__.py` — blueprint, routes, template globals/filters, `init_db()` call hook.
- `agents/db.py` — connection, schema, idempotent `init_db()`, `add_agent()`.
- `templates/agents/{base,login,houses,house,flat}.html`
- `agents/static/css/agents.css`, `agents/static/js/flat.js`
- `scripts/add_agent.py`
- `app.py` — secret_key, register blueprint, `init_db()` at startup.
- `.gitignore` — `instance/`, `*.db`, `__pycache__/`.

## Validation
- `/agents` redirects to login when logged out.
- `agent/agent123` → houses → flats → flat detail → "Оформить заявку" shows confirmation, no DB change.
- Logout works; `/` and `/testing` unchanged with no links added.

## Out of scope / risks
- CSRF protection & brute-force rate limiting (future).
- `SECRET_KEY` must be set via env in production.
