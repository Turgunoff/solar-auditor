# AI Rooftop Solar Auditor — Hackathon Readiness Analysis and Remaining Work Plan

Date: 2026-10-31. Sources: repo code, `README.md`, `SPEC.html`, `INTEGRATION.md`, `TODO-AUDIT.md`, `DEPLOY.md`, tests and checks re-run that day (backend `45 passed`, mock smoke `PASS`, frontend `4 passed`, build successful).

## Summary — Is it enough for the hackathon?

**As an MVP demo: YES, enough. Provided the live Meta criterion is proven.**

The project closes the full chain: preset/upload/Google Map → segmentation → Shapely panel layout → ROI → agent note → concept render → PDF. Tests are green, Docker deploy and live URL infrastructure are ready, docs are in sync. So a 2–3 minute script can be shown to judges without interruption.

The main risk is not in the code but in the **proof**: the `SPEC.html` requirement — “real Meta Model API (SAM 3.1 + at least one Muse)” — currently falls back to mock on synthetic presets because live SAM returns empty (`INTEGRATION.md`, `TODO-AUDIT.md` §5b: in live mode `residential_gable` FAIL, 502/timeout observed). If judges test live mode on a real satellite crop and only see `mock`/`+mock-fallback` chips, the “Push the Frontier” claim weakens. If this one gap is closed, the project reaches a credible hackathon MVP level; if not — it remains a strong mock demo.

Assessment (out of 10, state on demo day):

| Criterion | Score | Note |
|---|---|---|
| Demo flow completeness | 9/10 | Staged flow, refine, assumptions, PDF, Projects — all present |
| Engineering reliability | 7/10 | Shapely + derate + fail-closed present; no slope/azimuth/shade, honest disclaimer |
| Live Meta proof | 4/10 | Adapters and contract tests present, no live evidence on a real crop |
| Stability / tests | 9/10 | 45 backend + 4 frontend green, CI, rate limit, retention |
| Presentation / deploy | 7/10 | VPS + nginx ready; HTTPS (certbot) and demo video not yet done |

## Current state (verified)

- **Backend (FastAPI):** `app/api/endpoints.py` (550 lines) — health/status/presets, `process/preset|upload|map-upload|refine`, `assumptions/defaults`, `leads`, `export-pdf`. Services: `meta_client.py` (SAM/Muse adapter, injectable transport), `segmentation.py` (mock templates + live SAM + fallback), `layout_engine.py` (south-half cut, flat vs pitched, setback, central roof selection, orientation-aware packing), `analytics.py` (capacity/generation/`DERATE=0.85`/cost/savings/payback, off-grid without battery 400), `render_engine.py` (deterministic overlay + Muse photoreal), `agent_report.py`, `pdf_export.py`.
- **Frontend (Vue 3 + Vite):** 7 pages (landing, `/app`, how-it-works, pricing, projects, contact, setup), canvas layers (roof/obstacle/panel), exclusion-zone drawing, assumptions editor, RenderModal, MapPicker. Build: ~149 KB (gzip ~54 KB).
- **Verification (2026-10-31, on this machine):** backend `45 passed`, `USE_MOCK=true` smoke `PASS` (327/419/710 panels in mock — numbers depend on preset scale, not a quality criterion), frontend `4 passed`, `npm run build` OK.
- **Security/ops:** upload guards (15 MB, 64 px–50 MP), IP rate limit 60/min, 7-day static retention, fail-closed 422 (if live SAM finds no roof, no panels are drawn).
- **Limitations (code level):** project storage only in memory (`app/store.py`) and in the browser (Projects) — PDF may not be found after a server restart; price/sun hours are a single global constant, not location-dependent; pitch/azimuth/shade/tilt are not accounted for; `backend/static` has grown to 37 MB; HTTPS not yet done (`DEPLOY.md`: DNS + certbot pending).

## Strengths (to emphasize to judges)

- Honest engineering: disclaimer, fail-closed, “Muse — concept, layout — truth” principle, no fake precision.
- Adapter architecture: live/mock switching only in `meta_client.py`, UI/layout/analytics contract unchanged; 15+ contract tests run offline.
- Interactive differentiators: exclusion zone → re-packing, live assumptions (battery, on/off-grid), MapPicker (Mercator `meters_per_pixel`).

## Gaps and what to add (by priority)

### P0 — Demo blockers (required before the hackathon)

1. **Live SAM proof:** one full run with `USE_MOCK=false` on a real satellite crop (not synthetic): provider chips `meta-sam-3.1` + `meta-muse-*`, overlay screenshot and `/api/v1/status?probe=true` response saved as evidence. If not possible, state the mode openly in the pitch (“live-first, transparent fallback”) — hiding it is worse.
2. **Demo script and video:** a recorded 90–120 second flow (preset → Run AI Audit → draw zone → Recalculate → PDF) + a 1-page pitch text (based on the `SPEC.html` one-liner). If the live server is down, the video saves the demo.
3. **HTTPS:** point DNS `cyberpitch.uz` to the server + certbot; confirm with health check `https://cyberpitch.uz/api/v1/health` (update the Server map in `DEPLOY.md`).

### P1 — Credibility (if time remains, in order)

4. **Location-dependent assumptions:** city/region selector → `peak_sun_hours` and tariff presets (at least Uzbekistan + global default); visible in the assumptions form, in sync with backend defaults (do not break `test_env_sync`).
5. **PDF hardening:** verify live that layout image + table + disclaimer are in a single file; document the `store.py` memory limit openly (or smallest disk persistence: JSON in the existing static folder).
6. **Empty/error states:** user-language messages for “no roof found”, “0 panels”, network errors and a back-to-preset button (if a judge uploads a random image, the demo must not break).

### P2 — Differentiators (only after P0/P1 are closed)

7. Before/after slider (original image vs concept render), CO2 savings and monthly generation curve (from existing analytics, no new backend needed).
8. Stronger shade/pitch heuristic — only with a simple, explainable rule; do not add complex 3D or a new model.

Do not add (scope protection): auth/payments, full DB, mobile app, new AI models, rewriting the layout engine.

## Goal

By hackathon day, raise the project from a “working mock demo” to a “demo with live Meta evidence, recorded and reachable over HTTPS”, while preserving engineering honesty.

## Success Criteria

- Live SAM + at least one Muse call proven on a real crop (chip + overlay + status response).
- 90–120 s demo video and pitch text ready; main flow uninterrupted in the video.
- `https://cyberpitch.uz/api/v1/health` returns 200.
- Backend `45+` tests and frontend tests/build green; mock smoke `PASS`.
- When a random (non-roof) image is uploaded, the user sees an understandable error and no panels are drawn.

## Approach

Not new features — **proof and packaging** first. First the live path is verified on real data, then that flow is recorded to video, then closed with HTTPS. P1 starts only if P0 evidence exists. Every step follows the `AGENTS.md` rule: when behavior changes, docs are updated in the same commit (endpoint/env → `README.md`/`.env.example`, deploy → `DEPLOY.md` Server map, lesson → `TODO-AUDIT.md`).

## Steps

1. **Live verification (P0-1):** on the server or locally with `USE_MOCK=false` + a real key, run a real satellite crop (captured via Google Map, zoom 19+) through `process/map-upload`; save `status?probe=true`, provider chips and overlay. If it fails: adapt the `meta_client.py` contract to the live response (only that file), record the fallback reason in `TODO-AUDIT.md`. Dependency: subsequent steps rely on this.
2. **Demo packaging (P0-2):** write the script for the verified flow, record video, align pitch text with `SPEC.html` (theme/track/model lines). No new code needed.
3. **HTTPS (P0-3):** DNS → certbot → health check; `DEPLOY.md` updated.
4. **Region presets (P1-4):** `Assumptions` region field (optional), backend defaults, frontend form; `test_env_sync` and existing tests must stay green. If a new env var is added, update `.env.example` + `README.md` table.
5. **PDF/persistence check (P1-5):** open a live PDF; if needed, smallest disk persistence (static JSON instead of `store.py`), with a separate test.
6. **Error states (P1-6):** UI messages for 422/0-panel/network errors; manually check three scenarios.
7. **P2 (optional):** before/after slider and CO2/monthly curve — only from existing JSON, no new endpoint.

## Validation Plan

- Backend: `cd backend && ../.venv/bin/python -m pytest tests -q` — green (currently 45).
- Mock smoke: `cd backend && USE_MOCK=true ../.venv/bin/python scripts/smoke_pipeline.py` — `PASS`.
- Frontend: `cd frontend && npm test` and `npm run build` — green.
- Live: `GET /api/v1/status?probe=true` + audit on a real crop — chips and overlay by eye.
- Deploy: `curl https://cyberpitch.uz/api/v1/health` — 200.
- Manual: non-roof image → understandable error; off-grid without battery → 400 message.

## Risks / Open Questions

- The Meta API schema may have changed: adaptation only in `meta_client.py`, contract tests updated; if time runs out, the fallback is stated openly in the pitch.
- DNS/certbot depends on the domain owner, not the hackathon organizer — if delayed, `http://51.12.209.235:8080` is written into the pitch as the fallback URL.
- Question (non-blocking): is the demo shown on the live server or locally? Default assumption — server primary, local + video fallback. The answer does not change the P0 order, only where live evidence is captured.
