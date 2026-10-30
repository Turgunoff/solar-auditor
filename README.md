# AI Rooftop Solar Auditor & Engineering Engine

Meta Global AI Developer Hackathon MVP — aerial rooftop audit with SAM 3.1 / Muse adapters (mock-first locally), Shapely panel layout, ROI analytics, and PDF export.

Full technical specification: [`SPEC.html`](./SPEC.html)

## Quick start

### Backend (FastAPI · port 8000)

```bash
cd /Users/eldor/Projects/solar-auditor
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp -n .env.example .env
python backend/scripts/generate_samples.py   # if sample images missing
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vue 3 + Vite · port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` and `/static` to the backend.

### Site map

| Route | Page |
|-------|------|
| `/` | Marketing landing |
| `/app` | Live auditor engine |
| `/how-it-works` | Product pipeline |
| `/pricing` | Plans + waitlist |
| `/projects` | Browser-saved audits |
| `/contact` | Lead form (server JSONL + browser fallback) |
| `/setup` | Mock vs Meta API readiness |

## Demo flow

1. From the landing page, click **Open auditor** (`/app`).
2. Choose a source: **Preset 1 / 2 / 3**, upload an aerial JPG/PNG (drag & drop), or pick on Google Map — this only stages a preview, nothing is analyzed yet.
3. Review the preview, then click **Run AI Audit**.
4. Inspect green roof / red obstacles / blue panel grid on the canvas.
5. Optional: **Draw exclusion zone** → **Place panels** to re-pack around your zones.
6. Optional: **Estimate settings** — panel size/power, prices, tariff, battery, on/off-grid → **Recalculate**.
7. Open **Preview Concept Render** and **Download PDF Report**.
8. Revisit audits under **Projects**.

## Meta API (live-first, mock fallback)

Default is **live** (`USE_MOCK=false` + `META_API_KEY` in `.env`, gitignored):
if a live call fails, the pipeline falls back to mocks per layer
(`ALLOW_MOCK_FALLBACK=true`). For a fully offline demo set `USE_MOCK=true`.
Details: [`INTEGRATION.md`](./INTEGRATION.md).

```bash
# offline smoke
cd backend && ../.venv/bin/python scripts/smoke_pipeline.py
```

## Configuration

See `.env.example`. Important flags:

| Variable | Default | Meaning |
|----------|---------|---------|
| `USE_MOCK` | `false` | `true` = fully offline mock demo |
| `META_API_KEY` | empty | Empty → auto-mock |
| `ALLOW_MOCK_FALLBACK` | `true` | Failed live calls fall back to mock |
| `DERATE` | `0.85` | System loss factor |
| `BATTERY_PRICE_PER_KWH_USD` | `300.0` | Default storage price |
| `MAX_UPLOAD_MB` / `MIN_UPLOAD_PX` / `MAX_UPLOAD_MP` | `15` / `64` / `50.0` | Upload guards |
| `STATIC_RETENTION_DAYS` | `7` | Static cleanup window |
| `RATE_LIMIT_PER_MINUTE` | `60` | Per-IP limit on process/lead endpoints |

## API (`/api/v1`)

- `GET /api/v1/health`, `GET /api/v1/status?probe=true`
- `GET /api/v1/presets`
- `POST /api/v1/process/preset` `{ "preset_id": "residential_gable" }`
- `POST /api/v1/process/upload` `multipart file`
- `POST /api/v1/process/map-upload` (Static Maps capture + lat/lng/zoom)
- `POST /api/v1/process/refine` (re-pack with `user_boxes` + `assumptions`)
- `GET /api/v1/assumptions/defaults`
- `POST /api/v1/leads`
- `GET /api/v1/export-pdf/{project_id}`
- Interactive docs: http://localhost:8000/docs

Uploads where live SAM finds no roof return **422** (fail-closed) instead of
panels on arbitrary content.

## Tests

```bash
cd backend && ../.venv/bin/python -m pytest tests -q   # 45 tests
cd frontend && npm test                                 # vitest
```

## Hackathon positioning

- **Track:** Indie developer  
- **Theme:** Push the Frontier  
- **Models (adapters ready):** SAM 3.1, Muse Image, Muse Spark/Wonder  

## License

Prototype for hackathon use.
