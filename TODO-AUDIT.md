# Solar Auditor — Gaps and Remaining Work

Analysis date: 2026-10-28. Sources: repo code, `README.md`, `INTEGRATION.md`, tests.

## 1. Overall status

The MVP works end to end: preset/upload → segmentation → Shapely layout → ROI → render → PDF.
The AI layer is mock-first, live Meta API adapters are written, but not yet verified end to end with a live key.

## 2. Critical (demo/blocking)

- [x] `.env` checked: `USE_MOCK=false` + live `META_API_KEY` present (correction:
      the earlier “no key” conclusion was wrong — `.env` is gitignored so the key
      was not visible). So the mode is deliberately live. Remaining work: verify live mode
      with `/api/status?probe=true` + smoke (because the sandbox blocks port binding,
      verification uses `smoke_pipeline.py` instead of a server).
- [x] Working tree committed (task 1) — all subsequent fixes are also committed
      at each step.
- [x] `pytest` installed, 5/5 tests green (`test_layout_sun_face` + new
      `test_mock_presets_panels`). Adding to CI remains.
- [x] Mock 0-panel regression fixed (2026-10-28): the old layout produced 46/53/194 panels,
      the new SAM-AABB logic (20% shrink + south cut + 1 roof) had dropped it to 0/0/2.
      A `sam_overbox` flag was added to `place_panels`/`usable_area_m2`;
      the endpoint disables it for the mock provider. Mock smoke: 26/29/193, PASS.
      Live path unchanged (complex_hip live 30 panels preserved).
- [x] `feature-hip.jpg`: no references in `frontend/src` or `public`
      (grep empty) — no 404 risk, safe to delete.

## 3. Backend gaps

- [!] On synthetic presets SAM returns empty in live mode → mock fallback
      (expected state, noted in `INTEGRATION.md`). A live demo needs a real satellite
      crop — this is an external data issue, not solvable in code.
- [x] Fail-closed uploads (2026-10-28): if live SAM finds no roof, it returns 422 instead of
      drawing panels on a generic box (`segmentation.py` + `endpoints.py`).
      Pipeline regression test (`test_pipeline_no_roof.py`) + live verification in production:
      honest error for a non-roof image, no panels. 38/38 green.
- [x] Flat roofs fully covered (2026-10-29): on the commercial preset panels only landed on half
      the roof — the cause was the `COMMERCIAL_FLAT_M2` threshold not working at preset
      scale. Presets now carry a `pitched` flag,
      and the south cut is skipped on flat roofs. Live test: 2 → 988 panels
      (pure `meta-sam-3.1`), overlay visually confirmed. 39/39 green.
- [x] Preset 3 incomplete SAM mask + packing strip (2026-11-02): the live mask
      stopped mid-warehouse, leaving HVAC outside — a large empty white zone inside the green contour. `expand_flat_mask_roofs` builds a hull with HVAC;
      rim HVAC pad + aerial bright-membrane snap (lower ~167 px membrane);
      `_pack_oriented` 4-phase offset; flat mask envelope + medium keepout.
      Live Preset 3: 553 → 667 → 828 → ~1050+ panels (full white roof).
- [x] Refine flow + noise filter (2026-10-29): 1) Analyze → draw zone →
      Place panels (`POST /api/v1/process/refine`, user boxes clipped to the roof
      ); 2) large off-roof obstacles (parking/road/grass) not touching the roof are now
      dropped — only on-roof or canopy touching the roof remains. Live
      verification: refine returned 48 panels. 41/41 backend + 4/4 frontend green.
- [x] Assumptions editor (2026-10-29): `Assumptions` — panel power/size,
      $/kW, tariff, sun hours, battery (kWh + $/kWh), on/off-grid.
      Off-grid without battery returns 400. `GET /api/v1/assumptions/defaults`
      seeds the UI, Recalculate recomputes via refine. Live test:
      60 panels, off-grid + 10 kWh ($3000) correct. 45/45 + 4/4 green.
- [x] `derate` added to analytics (2026-10-28): `DERATE=0.85` default
      (inverter/soiling/wiring losses), in `.env.example`. The frontend does not duplicate
      the formula — it only shows API numbers. Shade/slope not yet included.
- [x] Boundary tests added (2026-10-28): below/above `COMMERCIAL_FLAT_M2`
      (south-half vs full), shrink branches (20% vs setback). 13/13 tests green,
      mock smoke PASS.
- [x] `meta_client` contract tests added (2026-10-28):
      `test_meta_client_contract.py` — 15 tests, no network. Gating
      (`NotReady` states), SAM box parsing, `_sam_concept` wiring (fake response),
      filter boundaries (speckle/full-frame/canopy), dedupe, IoU, image-bytes
      extraction, mime sniff, JPEG conversion. 28/28 green.
- [x] HTTP error map covered (2026-10-28): `transport` parameter added to `MetaModelClient`
      (default `None` = live network, behavior unchanged);
      tests with `MockTransport` for 502/non-JSON/upload-400/missing-id. 31/31
      green, mock smoke PASS.
- [x] Render retention closed with the cleanup above (startup hook + script).
- [x] Upload validation strengthened (2026-10-28): empty file rejected,
      min 64px / max 50MP size limits, limits moved to `Settings`
      (`MAX_UPLOAD_MB` etc. in `.env.example`). Rate limit not yet present.
- [x] Retention cleanup added (2026-10-28): `services/cleanup.py` +
      startup hook (`main.py`) + `scripts/cleanup_static.py`. Uploads/renders/exports
      older than 7 days are deleted, `.gitkeep` preserved. Currently 82 files/~25MB
      collected — 0 deleted because all are new. 8/8 tests green,
      mock smoke PASS.

## 4. Frontend gaps

- [x] Frontend tests added (see section 5): vitest + `api.test.js`, 3/3 green.
- [x] Keyless Maps fallback checked and improved (see section 5).
- [x] three.js lazy-loaded, build measured (see section 5).
- [x] Contact form wired to backend (see section 5).

## 5. Docs/config

- [x] Doc contradiction resolved (2026-10-28): README now says live-first +
      fallback, `.env.example` comments explain both modes.
      The “key in `.env`” state in `INTEGRATION.md` confirmed.
- [x] Frontend: three.js lazy load (`RenderModal` → async 3D tab). Main chunk
      680KB → 138KB (gzip 188→50KB); 3D in a separate 545KB chunk, loaded only when needed.
- [x] Keyless Maps: button hidden (`mapsEnabled`), mandatory message in user
      language — directs to preset/upload.
- [x] Contact form wired to backend (2026-10-28): `POST /api/leads` →
      `exports/leads.jsonl`; frontend sends to server, localStorage fallback offline
      . Covered by `test_leads.py`. 33/33 tests green, frontend build OK.
- [x] `.env` sync: `test_env_sync.py` — every key in `.env.example`
      must match a `Settings` field (frontend-only keys on an allowlist).
- [x] `SPEC.html` lightly checked: the `/api/*` paths it shows match the router
      (`health`, `presets`, `process`, `export-pdf`). Deep semantic audit not done.
- [x] Rate limit added (2026-10-28): `RateLimitMiddleware` — on `/api/process/*`
      and `/api/leads`, 60/min per IP (configurable), returns 429.
      Covered by `test_rate_limit.py`.
- [x] CI added (2026-10-28): `.github/workflows/ci.yml` — backend pytest +
      mock smoke + frontend build/test.
- [x] Frontend tests (2026-10-28): vitest + `api.test.js` (3 tests: health,
      submitLead, error message). `npm test` green. 36/36 backend, smoke PASS.

## 5b. Smoke result (2026-10-28)

Full output of `scripts/smoke_pipeline.py` (2026-10-28):
`mode: live`, key installed, fallback enabled.
- `complex_hip`: 30 panels, 12.0 kW, `seg=meta-sam-3.1` (pure live!) — OK.
- `commercial_flat_hvac`: 2 panels (suspiciously few), mock fallback — OK.
- `residential_gable`: 0 panels, `ok=False` — FAIL. Cause: live SAM on the synthetic
  image finds no roof (“no usable roof boxes”), fallback also yields 0 panels.
  `502 Bad Gateway` / timeout errors were also observed on live API calls
  (Muse text/image, obstacle prompts).
- Overall: **FAIL (1)**. Unit tests did not run because `pytest` was not installed.

## 6. Recommended order

1. Lock the demo mode (`USE_MOCK` decision) + commit the dirty tree.
2. Install `pytest` and make tests green; add `smoke_pipeline.py` to CI.
3. Upload validation + render cleanup.
4. `derate` and boundary tests for analytics.
5. Live contract test for `meta_client` against a mock server.
6. Frontend build size + keyless Maps fallback check.
- [x] Hackathon readiness (2026-10-31): live evidence obtained — `smoke_pipeline.py`
      in live mode, all three presets `meta-sam-3.1` (124/160/988 panels, PASS),
      one audit returned all three providers live; `cyberpitch.uz`
      HTTPS 200 (live). `DEMO.md` script/pitch written, `DEPLOY.md`
      updated. Region presets (UZ/US/EU: sun+tariff, exact field
      precedence) + project disk persistence (PDF survives restart) + friendly
      error messages added; tests: `test_region_presets.py`,
      `test_store_persist.py`, `friendlyError.test.js`.
- [x] SAM masks wired (2026-10-31): previously only AABB boxes were used,
      so on skewed buildings panels spilled into yards/trees. Now
      real mask contours are decoded with `meta-sam-parser==0.1.0` (Python 3.11)
      (`sam_parse.masks_to_polygons`, test: `test_sam_masks.py`).
      Live confirmation: on a long skewed building panels follow the roof axis, without leaving the roof
      ; live presets PASS (49/56/216).
- [x] Mask-based gentle layout (2026-10-31): the 20% erosion + wide obstacle zone
      written for AABBs no longer applies to real mask contours
      (the `mask_outlines` flag is propagated from segmentation to refine
      ). The south-half rule is kept on pitched roofs, but a roof type
      selector (Pitched/Flat) was added. Live E2E on a long building: pitched 150,
      flat 304 panels, all inside the roof.
- [x] MapPicker Places API (New) (2026-11-02): legacy `places.Autocomplete`
      raised `LegacyApiNotActivatedMapError` on new projects (the old Places no longer appears in Cloud Console
      ). Migrated to `PlaceAutocompleteElement` +
      `importLibrary('places')`; the key must have a **Places API (New)**
      restriction.
- [x] Muse guide + medium keepout (2026-11-02): when Muse was given a green roof fill
      it invented a new scene (pool/tennis court) — now a panels-only
      guide + strict prompt. HVAC keepout is medium in mask mode (density
      preserved, does not hug equipment); fat keepout in AABB mode.
