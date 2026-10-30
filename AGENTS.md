# AGENTS.md — working rules for this repo

## Docs stay in sync (mandatory)

Every behavior change updates the docs in the SAME commit:

| Change type | Docs to touch |
|---|---|
| New/changed endpoint or schema | `README.md` API list, `INTEGRATION.md` if adapter-related |
| New/changed env var or default | `.env.example` + `README.md` config table |
| New user-facing flow or UI surface | `README.md` demo flow / site map |
| New/changed deploy, ports, server paths | `DEPLOY.md` (incl. the Server map table) |
| Bug fix with a lesson | `TODO-AUDIT.md` entry (checked, with date) |

`test_env_sync.py` enforces `.env.example` ↔ `Settings` parity — if it
fails, the docs (or the setting) are wrong, not the test.

`SPEC.html` is the frozen hackathon narrative: update its theme/track/claim
lines when positioning changes, but do not rewrite its structure per fix.

## Tests

- Backend: `cd backend && ../.venv/bin/python -m pytest tests -q` — must be
  green before every commit. New behavior ships with a focused test in
  `backend/tests/` (see `test_mock_presets_panels.py` as example).
- Frontend: `cd frontend && npm test` (vitest) + `npm run build`.
- Mock smoke: `cd backend && USE_MOCK=true ../.venv/bin/python scripts/smoke_pipeline.py`
  must print `PASS`.

## Git

- Small, themed commits; push to `main` when green.
- Never commit `.env` (gitignored — live keys). `.env.example` holds defaults only.
- Never rewrite published history without an explicit user request.

## Deploy (manual)

Server: `/opt/solar-auditor` on `51.12.209.235` (`ozodbek` + key in
`Downloads/iMe Desktop/ozodbek_key.pem`). Update flow:
`git pull origin main && docker compose up -d --build`, then verify
`https://cyberpitch.uz/api/v1/health`. Full map: `DEPLOY.md`.
