from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

Point = Tuple[float, float]
Polygon = List[Point]


class Dimensions(BaseModel):
    width: int
    height: int


class SegmentationResult(BaseModel):
    roof_polygons: List[Polygon]
    obstacles: List[Polygon]


class PanelDimensions(BaseModel):
    width: float
    height: float


class Panel(BaseModel):
    id: int
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0


class LayoutResult(BaseModel):
    total_panels: int
    panel_dimensions: PanelDimensions
    panels: List[Panel]


class AnalyticsResult(BaseModel):
    system_capacity_kw: float
    annual_generation_kwh: float
    estimated_cost_usd: float
    annual_savings_usd: float
    roi_years: Optional[float] = None
    agent_summary: str = ""
    usable_area_m2: Optional[float] = None


class ProviderInfo(BaseModel):
    segmentation: str
    render: str
    agent: str


class ProcessRequest(BaseModel):
    preset_id: str = Field(..., examples=["residential_gable"])


class LeadIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=160)
    company: str = Field(default="", max_length=160)
    message: str = Field(..., min_length=1, max_length=4000)


class LeadOut(BaseModel):
    ok: bool = True
    stored: str = "server"


class MapCaptureRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    zoom: int = Field(20, ge=19, le=22)
    size: int = Field(640, ge=320, le=640)


class ProcessResponse(BaseModel):
    project_id: str
    image_url: str
    dimensions: Dimensions
    provider: ProviderInfo
    segmentation: SegmentationResult
    layout: LayoutResult
    analytics: AnalyticsResult
    # Deterministic packing overlay — source of truth for module count visuals
    layout_url: str = ""
    # Muse photoreal concept (or same as layout_url if Muse unavailable)
    render_url: str


class PresetInfo(BaseModel):
    id: str
    label: str
    thumbnail_url: str
    meters_per_pixel: float


class PresetsResponse(BaseModel):
    presets: List[PresetInfo]


class HealthModels(BaseModel):
    segmentation: str
    render: str
    agent: str


class HealthResponse(BaseModel):
    status: str
    mode: str
    models: HealthModels
    api_key_present: bool = False
    live_requested: bool = False
    allow_mock_fallback: bool = True
    message: str = ""


class StatusResponse(BaseModel):
    status: str
    mode: str
    use_mock: bool
    api_key_present: bool
    live_requested: bool
    allow_mock_fallback: bool
    meta_api_base_url: str
    models: dict
    ready_for_live: bool
    message: str
    ping: Optional[dict] = None
    pipeline: str = "mock-ready"
