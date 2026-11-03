# Demo package — AI Rooftop Solar Auditor

Hackathon: Meta Global AI Developer Hackathon · Track: Indie developer · Theme: Push the Frontier.
Live URL: https://cyberpitch.uz (fallback: http://51.12.209.235:8080).
One-liner: “Upload a rooftop photo → Meta SAM segments usable area → auto panel layout + Muse photoreal after + ROI PDF in under a minute.”

## Preparation (10 minutes before the demo)

1. Open `https://cyberpitch.uz/api/v1/health`: `mode: live`, all three models should be `meta-*`.
2. Refresh `/app` in the browser and leave Preset 1 staged (Run not clicked yet).
3. Fallback: a local `USE_MOCK=true` copy of the same flow.

## Live evidence (2026-10-31, this repo)

- `GET https://api.meta.ai/v1/models` → 200, listing `sam-3.1`, `muse-spark-1.3`, `muse-wonder-1.0`.
- Live smoke (`USE_MOCK=false`): all three presets `seg=meta-sam-3.1` (pure live, no fallback) — 124 / 160 / 988 panels, `PASS`.
- One full audit (`solar_proj_0dcc2d3c`): segmentation `meta-sam-3.1`, render `meta-muse-image-1.0`, agent `meta-muse-spark-1.3`; 124 panels, 49.6 kWp.
- Production: `https://cyberpitch.uz/api/v1/health` → 200, `mode: live`.

## Pitch (1 page)

**Problem.** A solar panel seller spends hours on manual measurement for every roof; the customer waits weeks for a quote.

**Solution.** AI Rooftop Solar Auditor: upload a single aerial photo or map crop. Meta SAM 3.1 segments the roof and obstacles, the geometric engine (Shapely) places panels on the southern face with setbacks, Muse Image shows the “after” state photorealistically, and Muse Spark writes a cautious engineering note. The result — panel count, kWp, annual generation, price, payback and a PDF report.

**Why now / why Meta.** SAM's zero-shot segmentation works on any roof without a trained custom model; Muse makes the sales conversation visual. All three models sit behind a single adapter layer (`meta_client.py`), and in mock mode the full demo also runs without internet.

**Honesty.** This is not a bankable report: the numbers rest on strict assumptions, and the disclaimer is present on every screen and in the PDF. If no roof is found, the system does not silently draw panels.

**Next step.** Regional sun/tariff presets (available), on-site verification with an installer, then the quote flow.

## Short answers to judge questions

- “Does AI invent the numbers?” — No. Deterministic geometry places the panels; AI is for segmentation, visuals, and text.
- “Live or mock?” — The default mode is live (`meta-sam-3.1` chips on screen). If the network drops, the fallback label is shown openly.
- “How accurate is it?” — This is a feasibility sketch: scale comes from the map/preset, generation from a sun-hours assumption. Bankable calculations require an on-site survey — the product does not hide this.
