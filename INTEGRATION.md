# Meta Model API integration guide

This project is **fully runnable offline** with mocks. Live Meta models plug in without UI or layout/analytics changes.

## Current state

| Layer | Status |
|-------|--------|
| Upload / presets / canvas / PDF | Done |
| Shapely layout + ROI math | Done |
| Mock SAM / Muse Image / Muse text | Done |
| Live `MetaModelClient` (files + responses, injectable transport) | Done |
| SAM 3.1 segmentation | Live (empty on synthetic samples → mock fallback) |
| Fail-closed uploads | Live SAM miss on non-preset image → 422, no generic panels |
| Flat vs pitched | Presets carry `pitched`; flat skips the south-half cut |
| Muse Image 1.0 render | Live (`image_generation_call.result` → JPEG) |
| Muse Spark 1.3 agent summary | Live |
| Live credentials | Set in local `.env` (gitignored) |

## Switch to live

1. Edit `.env`:

```env
USE_MOCK=false
META_API_KEY=your_key_here
META_API_BASE_URL=https://api.meta.ai/v1
SAM_MODEL=sam-3.1
MUSE_IMAGE_MODEL=muse-image-1.0
MUSE_TEXT_MODEL=muse-spark-1.3
ALLOW_MOCK_FALLBACK=true
```

2. Restart backend:

```bash
cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000
```

3. Probe:

```bash
curl "http://127.0.0.1:8000/api/v1/status?probe=true"
```

4. Run an audit in `/app`. Provider chips should show:
   - `meta-sam-3.1` or `meta-sam-3.1+mock-fallback` (synthetic presets often need fallback)
   - `meta-muse-image-1.0`
   - `meta-muse-spark-1.3`

## Where to edit when OpenAPI differs

Only touch:

`backend/app/services/meta_client.py`

| Method | Purpose |
|--------|---------|
| `ping()` | `GET /models` |
| `upload_file()` | `POST /files` |
| `segment_rooftop()` | SAM 3.1 zero-shot boxes → polygons |
| `render_rooftop_with_panels()` | Muse Image (`image_generation_call`) |
| `engineering_summary()` | Muse Spark text |

Adapters already catch `MetaAPINotReady` / `MetaAPIError` and fall back.

## Do not rewrite

- `layout_engine.py`, `analytics.py`, `pdf_export.py`
- Vue pages / canvas (they consume the same JSON contract)

## Smoke without Meta

```bash
cd backend
../.venv/bin/python scripts/smoke_pipeline.py
```
