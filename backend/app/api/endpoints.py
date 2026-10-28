from __future__ import annotations

import json
import math
import shutil
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image

from app.api.schemas import (
    Dimensions,
    HealthModels,
    HealthResponse,
    LeadIn,
    LeadOut,
    MapCaptureRequest,
    PresetInfo,
    PresetsResponse,
    ProcessRequest,
    ProcessResponse,
    ProviderInfo,
    SegmentationResult,
    StatusResponse,
)
from app.core.config import Settings, get_settings
from app.services.agent_report import get_agent_service
from app.services.analytics import compute_analytics
from app.services.layout_engine import place_panels, usable_area_m2
from app.services.meta_client import MetaAPIError, MetaAPINotReady, get_meta_client
from app.services.pdf_export import build_pdf
from app.services.render_engine import get_render_service
from app.services.segmentation import get_segmentation_service
from app.store import store

router = APIRouter(prefix="/api/v1")

PRESETS = [
    {
        "id": "residential_gable",
        "label": "Preset 1 (Gable)",
        "filename": "residential_gable.jpg",
        "meters_per_pixel": 0.035,
    },
    {
        "id": "complex_hip",
        "label": "Preset 2 (Hip Roof)",
        "filename": "complex_hip.jpg",
        "meters_per_pixel": 0.04,
    },
    {
        "id": "commercial_flat_hvac",
        "label": "Preset 3 (Commercial)",
        "filename": "commercial_flat_hvac.jpg",
        "meters_per_pixel": 0.05,
    },
]


def _provider_labels(settings: Settings) -> ProviderInfo:
    if settings.mock_forced():
        return ProviderInfo(segmentation="mock", render="mock", agent="mock")
    return ProviderInfo(
        segmentation=f"meta-{settings.sam_model}",
        render=f"meta-{settings.muse_image_model}",
        agent=f"meta-{settings.muse_text_model}",
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    labels = _provider_labels(settings)
    pub = settings.public_status()
    return HealthResponse(
        status="ok",
        mode=settings.mode_label(),
        models=HealthModels(
            segmentation=labels.segmentation,
            render=labels.render,
            agent=labels.agent,
        ),
        api_key_present=pub["api_key_present"],
        live_requested=pub["live_requested"],
        allow_mock_fallback=pub["allow_mock_fallback"],
        message=pub["message"],
    )


@router.get("/status", response_model=StatusResponse)
def status(probe: bool = False) -> StatusResponse:
    """Detailed readiness for UI / ops. Optional live ping when probe=true."""
    settings = get_settings()
    pub = settings.public_status()
    ping_info = None
    if probe and settings.live_requested():
        client = get_meta_client(settings)
        try:
            ping_info = client.ping()
        except (MetaAPINotReady, MetaAPIError) as exc:
            ping_info = {"ok": False, "error": str(exc)}

    return StatusResponse(
        status="ok",
        mode=pub["mode"],
        use_mock=pub["use_mock"],
        api_key_present=pub["api_key_present"],
        live_requested=pub["live_requested"],
        allow_mock_fallback=pub["allow_mock_fallback"],
        meta_api_base_url=pub["meta_api_base_url"],
        models=pub["models"],
        ready_for_live=pub["ready_for_live"],
        message=pub["message"],
        ping=ping_info,
        pipeline="live-adapters-armed" if settings.live_requested() else "mock-ready",
    )


@router.get("/presets", response_model=PresetsResponse)
def list_presets() -> PresetsResponse:
    settings = get_settings()
    for preset in PRESETS:
        src = settings.sample_data_dir / preset["filename"]
        dest = settings.uploads_dir / preset["filename"]
        if src.exists() and not dest.exists():
            shutil.copy2(src, dest)

    return PresetsResponse(
        presets=[
            PresetInfo(
                id=p["id"],
                label=p["label"],
                thumbnail_url=f"/static/uploads/{p['filename']}",
                meters_per_pixel=p["meters_per_pixel"],
            )
            for p in PRESETS
        ]
    )


def _run_pipeline(
    image_path,
    image_url: str,
    meters_per_pixel: float,
    preset_id: Optional[str],
) -> ProcessResponse:
    settings = get_settings()
    with Image.open(image_path) as im:
        width, height = im.size

    project_id = f"solar_proj_{uuid.uuid4().hex[:8]}"

    segmentor = get_segmentation_service(settings)
    seg = segmentor.segment(str(image_path), width, height, preset_id)

    # Mock templates are tight outlines; live SAM returns over-inclusive
    # boxes that need the aggressive overbox handling in the layout engine.
    tight_outlines = seg.provider == "mock" or seg.provider.endswith(
        "+mock-fallback"
    )

    layout = place_panels(
        seg.roof_polygons,
        seg.obstacles,
        width,
        height,
        meters_per_pixel,
        settings,
        sam_overbox=not tight_outlines,
    )
    area = usable_area_m2(
        seg.roof_polygons,
        seg.obstacles,
        meters_per_pixel,
        settings,
        width_px=width,
        height_px=height,
        sam_overbox=not tight_outlines,
    )

    analytics = compute_analytics(layout.total_panels, area, settings)
    agent = get_agent_service(settings)
    summary, agent_provider = agent.summarize(
        analytics, layout.total_panels, len(seg.obstacles)
    )
    analytics.agent_summary = summary

    renderer = get_render_service(settings)
    layout_url, render_url, render_provider = renderer.render_after(
        str(image_path),
        layout.panels,
        seg.roof_polygons,
        project_id,
    )

    provider = ProviderInfo(
        segmentation=seg.provider,
        render=render_provider,
        agent=agent_provider,
    )

    response = ProcessResponse(
        project_id=project_id,
        image_url=image_url,
        dimensions=Dimensions(width=width, height=height),
        provider=provider,
        segmentation=SegmentationResult(
            roof_polygons=seg.roof_polygons,
            obstacles=seg.obstacles,
        ),
        layout=layout,
        analytics=analytics,
        layout_url=layout_url,
        render_url=render_url,
    )

    store.put(project_id, json.loads(response.model_dump_json()))
    return response


def _meters_per_pixel(lat: float, zoom: int, scale: int = 2) -> float:
    """Web Mercator meters/pixel at latitude for Google Static Maps scale."""
    meters = 156543.03392 * math.cos(math.radians(lat)) / (2**zoom)
    return meters / scale


# Match frontend MapPicker: district-scale captures produce junk kWp.
MIN_MAP_CAPTURE_ZOOM = 19


def _require_capture_zoom(zoom: int) -> int:
    z = int(zoom)
    if z < MIN_MAP_CAPTURE_ZOOM:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Zoom too far ({z}). Pick a single building at zoom "
                f"{MIN_MAP_CAPTURE_ZOOM}+ (max 21)."
            ),
        )
    return max(MIN_MAP_CAPTURE_ZOOM, min(22, z))


@router.post("/process/map", response_model=ProcessResponse)
def process_map(body: MapCaptureRequest) -> ProcessResponse:
    """Server-side Static Maps fetch (works only if key has no HTTP-referrer restriction)."""
    settings = get_settings()
    key = settings.google_maps_api_key.strip()
    if not key:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_MAPS_API_KEY is not set in .env",
        )
    body = body.model_copy(update={"zoom": _require_capture_zoom(body.zoom)})

    scale = 2
    size = body.size
    url = (
        "https://maps.googleapis.com/maps/api/staticmap"
        f"?center={body.lat},{body.lng}"
        f"&zoom={body.zoom}"
        f"&size={size}x{size}"
        f"&scale={scale}"
        f"&maptype=satellite"
        f"&key={key}"
    )
    try:
        with httpx.Client(timeout=60.0) as client:
            res = client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Maps fetch failed: {exc}") from exc

    if res.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Google Static Maps {res.status_code}: {res.text[:240]}",
        )
    ctype = (res.headers.get("content-type") or "").lower()
    if "image" not in ctype:
        raise HTTPException(
            status_code=502,
            detail=f"Maps returned non-image ({ctype}): {res.text[:200]}",
        )

    dest_name = f"map_{uuid.uuid4().hex[:10]}.jpg"
    dest = settings.uploads_dir / dest_name
    try:
        from io import BytesIO

        with Image.open(BytesIO(res.content)) as im:
            im.convert("RGB").save(dest, format="JPEG", quality=92)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=f"Corrupt map image: {exc}") from exc

    mpp = _meters_per_pixel(body.lat, body.zoom, scale=scale)
    image_url = f"/static/uploads/{dest_name}"
    return _run_pipeline(dest, image_url, mpp, preset_id=None)


@router.post("/process/map-upload", response_model=ProcessResponse)
async def process_map_upload(
    file: UploadFile = File(...),
    lat: float = Form(0.0),
    lng: float = Form(0.0),
    zoom: int = Form(20),
) -> ProcessResponse:
    """Accept browser-fetched Static Maps image (HTTP-referrer–safe) + geo for scale."""
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {settings.max_upload_mb}MB)",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty map image")

    dest_name = f"map_{uuid.uuid4().hex[:10]}.jpg"
    dest = settings.uploads_dir / dest_name
    try:
        from io import BytesIO

        with Image.open(BytesIO(data)) as im:
            im.convert("RGB").save(dest, format="JPEG", quality=92)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Corrupt map image: {exc}") from exc

    z = _require_capture_zoom(int(zoom or 20))
    mpp = (
        _meters_per_pixel(float(lat), z, scale=2)
        if -90 <= lat <= 90
        else settings.default_meters_per_pixel
    )
    image_url = f"/static/uploads/{dest_name}"
    return _run_pipeline(dest, image_url, mpp, preset_id=None)


@router.post("/process/preset", response_model=ProcessResponse)
def process_preset(body: ProcessRequest) -> ProcessResponse:
    settings = get_settings()
    preset = next((p for p in PRESETS if p["id"] == body.preset_id), None)
    if preset is None:
        raise HTTPException(status_code=400, detail="Unknown preset_id")

    src = settings.sample_data_dir / preset["filename"]
    if not src.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Sample image missing: {preset['filename']}",
        )

    dest_name = f"{body.preset_id}_{uuid.uuid4().hex[:6]}.jpg"
    dest = settings.uploads_dir / dest_name
    shutil.copy2(src, dest)
    image_url = f"/static/uploads/{dest_name}"
    return _run_pipeline(dest, image_url, preset["meters_per_pixel"], body.preset_id)


@router.post("/process/upload", response_model=ProcessResponse)
async def process_upload(file: UploadFile = File(...)) -> ProcessResponse:
    settings = get_settings()
    name = (file.filename or "").lower()
    ok_mime = file.content_type in {"image/jpeg", "image/png", "image/jpg", None}
    ok_ext = name.endswith(".jpg") or name.endswith(".jpeg") or name.endswith(".png")
    if not ok_ext and not (file.content_type in {"image/jpeg", "image/png", "image/jpg"}):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG images are supported")
    if not ok_mime and not ok_ext:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG images are supported")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {settings.max_upload_mb}MB)",
        )

    ext = ".png" if name.endswith(".png") else ".jpg"
    dest_name = f"upload_{uuid.uuid4().hex[:10]}{ext}"
    dest = settings.uploads_dir / dest_name
    dest.write_bytes(data)

    try:
        with Image.open(dest) as im:
            im.verify()
        with Image.open(dest) as im:
            width, height = im.size
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Corrupt image: {exc}") from exc
    if min(width, height) < settings.min_upload_px:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Image too small (min {settings.min_upload_px}px per side)",
        )
    if width * height > settings.max_upload_mp * 1_000_000:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Image too large (max {settings.max_upload_mp}MP)",
        )

    image_url = f"/static/uploads/{dest_name}"
    return _run_pipeline(
        dest, image_url, settings.default_meters_per_pixel, preset_id=None
    )


@router.post("/leads", response_model=LeadOut)
def submit_lead(body: LeadIn) -> LeadOut:
    """Store a contact lead server-side (JSONL) instead of browser-only."""
    settings = get_settings()
    if "@" not in body.email or "." not in body.email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Invalid email")
    from datetime import datetime, timezone

    record = {
        "at": datetime.now(timezone.utc).isoformat(),
        **json.loads(body.model_dump_json()),
    }
    settings.ensure_dirs()
    leads_path = settings.exports_dir / "leads.jsonl"
    with leads_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return LeadOut()


@router.get("/export-pdf/{project_id}")
def export_pdf(project_id: str) -> FileResponse:
    settings = get_settings()
    project = store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    pdf_path = build_pdf(project, settings)
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"solar-audit-{project_id}.pdf",
    )
