from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Protocol, Tuple

from app.core.config import Settings
from app.services.meta_client import MetaAPIError, MetaAPINotReady, get_meta_client

logger = logging.getLogger(__name__)

Point = Tuple[float, float]
Polygon = List[Point]


@dataclass
class SegmentationOutput:
    roof_polygons: List[Polygon]
    obstacles: List[Polygon]
    provider: str
    latency_ms: int


class SegmentationService(Protocol):
    def segment(
        self,
        image_path: str,
        width: int,
        height: int,
        preset_id: str | None = None,
    ) -> SegmentationOutput: ...


def _scale_poly(poly: List[Tuple[float, float]], w: int, h: int) -> Polygon:
    return [(x * w, y * h) for x, y in poly]


PRESET_TEMPLATES = {
    # Calibrated 2026-10-28 against photorealistic sample_data (1920x1280).
    # If a sample image changes, re-measure roof/skylight quads or overlays drift.
    "residential_gable": {
        "roofs": [
            [(0.16, 0.25), (0.49, 0.17), (0.49, 0.62), (0.14, 0.66)],
            [(0.49, 0.17), (0.83, 0.24), (0.84, 0.66), (0.49, 0.62)],
        ],
        "obstacles": [
            [(0.31, 0.40), (0.38, 0.40), (0.38, 0.52), (0.31, 0.52)],
            [(0.565, 0.455), (0.615, 0.455), (0.615, 0.555), (0.565, 0.555)],
        ],
    },
    "complex_hip": {
        "roofs": [
            [(0.22, 0.18), (0.76, 0.18), (0.67, 0.51), (0.30, 0.51)],
            [(0.26, 0.53), (0.69, 0.53), (0.69, 0.84), (0.26, 0.84)],
        ],
        "obstacles": [
            [(0.43, 0.29), (0.53, 0.29), (0.53, 0.40), (0.43, 0.40)],
            [(0.33, 0.65), (0.40, 0.65), (0.40, 0.75), (0.33, 0.75)],
            [(0.55, 0.65), (0.62, 0.65), (0.62, 0.75), (0.55, 0.75)],
        ],
    },
    "commercial_flat_hvac": {
        "roofs": [
            [(0.18, 0.20), (0.82, 0.20), (0.84, 0.78), (0.16, 0.78)],
        ],
        "obstacles": [
            [(0.26, 0.30), (0.38, 0.30), (0.38, 0.42), (0.26, 0.42)],
            [(0.44, 0.32), (0.56, 0.32), (0.56, 0.44), (0.44, 0.44)],
            [(0.62, 0.30), (0.74, 0.30), (0.74, 0.42), (0.62, 0.42)],
            [(0.32, 0.52), (0.48, 0.52), (0.48, 0.66), (0.32, 0.66)],
            [(0.54, 0.54), (0.70, 0.54), (0.70, 0.68), (0.54, 0.68)],
        ],
    },
}


class MockSegmentor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    def segment(
        self,
        image_path: str,
        width: int,
        height: int,
        preset_id: str | None = None,
    ) -> SegmentationOutput:
        started = time.perf_counter()
        if self.settings and self.settings.mock_latency_ms > 0:
            time.sleep(min(self.settings.mock_latency_ms, 2000) / 1000.0)

        key = preset_id if preset_id in PRESET_TEMPLATES else None
        if key is None:
            template = {
                "roofs": [
                    [(0.15, 0.18), (0.85, 0.18), (0.88, 0.80), (0.12, 0.80)],
                ],
                "obstacles": [
                    [(0.40, 0.35), (0.50, 0.35), (0.50, 0.48), (0.40, 0.48)],
                    [(0.58, 0.50), (0.70, 0.50), (0.70, 0.62), (0.58, 0.62)],
                ],
            }
        else:
            template = PRESET_TEMPLATES[key]

        roofs = [_scale_poly(p, width, height) for p in template["roofs"]]
        obstacles = [_scale_poly(p, width, height) for p in template["obstacles"]]
        latency = int((time.perf_counter() - started) * 1000)
        return SegmentationOutput(
            roof_polygons=roofs,
            obstacles=obstacles,
            provider="mock",
            latency_ms=latency,
        )


class MetaSAMSegmentor:
    def __init__(self, settings: Settings, fallback: MockSegmentor) -> None:
        self.settings = settings
        self.fallback = fallback
        self.client = get_meta_client(settings)

    def segment(
        self,
        image_path: str,
        width: int,
        height: int,
        preset_id: str | None = None,
    ) -> SegmentationOutput:
        started = time.perf_counter()
        try:
            data = self.client.segment_rooftop(image_path, width, height)
            latency = int((time.perf_counter() - started) * 1000)
            return SegmentationOutput(
                roof_polygons=data["roof_polygons"],
                obstacles=data.get("obstacles") or [],
                provider=f"meta-{self.settings.sam_model}",
                latency_ms=latency,
            )
        except (MetaAPINotReady, MetaAPIError) as exc:
            logger.warning("SAM live path unavailable: %s", exc)
            if not self.settings.allow_mock_fallback:
                raise
            result = self.fallback.segment(image_path, width, height, preset_id)
            return SegmentationOutput(
                roof_polygons=result.roof_polygons,
                obstacles=result.obstacles,
                provider=f"meta-{self.settings.sam_model}+mock-fallback",
                latency_ms=result.latency_ms,
            )


def get_segmentation_service(settings: Settings) -> SegmentationService:
    mock = MockSegmentor(settings)
    if settings.mock_forced():
        return mock
    return MetaSAMSegmentor(settings, mock)
