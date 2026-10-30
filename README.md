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
| `/contact` | Lead form (localStorage MVP) |
| `/setup` | Mock vs Meta API readiness |

## Demo flow

1. From the landing page, click **Open auditor** (`/app`).
2. Choose **Preset 1 / 2 / 3** (or upload an aerial JPG/PNG).
3. Click **Run AI Audit**.
4. Inspect green roof / red obstacles / blue panel grid on the canvas.
5. Open **View 3D Visualization** and **Download PDF Report**.
6. Revisit audits under **Projects**.

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
| `USE_MOCK` | `true` | Force mock adapters |
| `META_API_KEY` | empty | Empty → auto-mock |
| `ALLOW_MOCK_FALLBACK` | `true` | Live path falls back to mock until API wired |

Switching to live Meta Model API should only require env + implementing the HTTP clients inside `segmentation.py` / `render_engine.py` / `agent_report.py` — UI and business logic stay unchanged.

## API

- `GET /api/v1/health`
- `GET /api/v1/presets`
- `POST /api/v1/process/preset` `{ "preset_id": "residential_gable" }`
- `POST /api/v1/process/upload` `multipart file`
- `GET /api/v1/export-pdf/{project_id}`
- Interactive docs: http://localhost:8000/docs

## Hackathon positioning

- **Track:** Indie developer  
- **Theme:** Push the Frontier  
- **Models (adapters ready):** SAM 3.1, Muse Image, Muse Spark/Wonder  

## License

Prototype for hackathon use.
