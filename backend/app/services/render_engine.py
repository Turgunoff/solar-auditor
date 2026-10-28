from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import List, Protocol, Sequence, Tuple

from PIL import Image, ImageDraw

from app.api.schemas import Panel
from app.core.config import Settings
from app.services.meta_client import MetaAPIError, MetaAPINotReady, get_meta_client

logger = logging.getLogger(__name__)

Point = Tuple[float, float]


def draw_layout_overlay(
    image_path: str,
    panels: List[Panel],
    roof_polygons: Sequence[Sequence[Point]],
    out_path: Path,
) -> Path:
    """Deterministic aerial + packed modules (source of truth for BOM visuals)."""
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    for poly in roof_polygons:
        if len(poly) >= 3:
            draw.polygon([(p[0], p[1]) for p in poly], outline=(16, 185, 129, 220), width=3)
            draw.polygon([(p[0], p[1]) for p in poly], fill=(16, 185, 129, 36))

    for panel in panels:
        cx, cy = panel.x, panel.y
        hw, hh = panel.width / 2.0, panel.height / 2.0
        rad = math.radians(panel.rotation or 0.0)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        world = []
        for dx, dy in corners:
            world.append(
                (
                    cx + dx * cos_a - dy * sin_a,
                    cy + dx * sin_a + dy * cos_a,
                )
            )
        draw.polygon(
            world,
            fill=(30, 64, 175, 170),
            outline=(191, 219, 254, 240),
        )

    composed = Image.alpha_composite(img, overlay).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    composed.save(out_path, quality=92)
    return out_path


def _roof_hint(roof_polygons: Sequence[Sequence[Point]], panel_count: int) -> str:
    if not roof_polygons:
        return f"Exactly {panel_count} modules already marked in blue."
    xs = [p[0] for poly in roof_polygons for p in poly]
    ys = [p[1] for poly in roof_polygons for p in poly]
    return (
        f"Exactly {panel_count} blue rectangles are the approved module layout. "
        f"Roof bbox ~[{min(xs):.0f},{min(ys):.0f}]–[{max(xs):.0f},{max(ys):.0f}] px. "
        "Do not invent panels on other buildings, trees, or yards."
    )


class RenderService(Protocol):
    def render_after(
        self,
        image_path: str,
        panels: List[Panel],
        roof_polygons: Sequence[Sequence[Point]],
        project_id: str,
    ) -> tuple[str, str, str]:
        """Returns (layout_url, muse_or_concept_url, provider)."""
        ...


class MockRenderEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def render_after(
        self,
        image_path: str,
        panels: List[Panel],
        roof_polygons: Sequence[Sequence[Point]],
        project_id: str,
    ) -> tuple[str, str, str]:
        layout_name = f"{project_id}_layout.jpg"
        layout_path = self.settings.renders_dir / layout_name
        draw_layout_overlay(image_path, panels, roof_polygons, layout_path)
        url = f"/static/renders/{layout_name}"
        # Mock: concept == layout
        return url, url, "mock"


class MuseImageRenderEngine:
    def __init__(self, settings: Settings, fallback: MockRenderEngine) -> None:
        self.settings = settings
        self.fallback = fallback
        self.client = get_meta_client(settings)

    def render_after(
        self,
        image_path: str,
        panels: List[Panel],
        roof_polygons: Sequence[Sequence[Point]],
        project_id: str,
    ) -> tuple[str, str, str]:
        layout_name = f"{project_id}_layout.jpg"
        muse_name = f"{project_id}_muse.jpg"
        layout_path = self.settings.renders_dir / layout_name
        muse_path = self.settings.renders_dir / muse_name
        draw_layout_overlay(image_path, panels, roof_polygons, layout_path)
        layout_url = f"/static/renders/{layout_name}"

        try:
            image_bytes = self.client.render_rooftop_with_panels(
                str(layout_path),  # feed laid-out aerial so Muse follows BOM
                panel_count=len(panels),
                roof_hint=_roof_hint(roof_polygons, len(panels)),
                photorealize_layout=True,
            )
            muse_path.write_bytes(image_bytes)
            muse_url = f"/static/renders/{muse_name}"
            return layout_url, muse_url, f"meta-{self.settings.muse_image_model}"
        except (MetaAPINotReady, MetaAPIError) as exc:
            logger.warning("Muse Image live path unavailable: %s", exc)
            if not self.settings.allow_mock_fallback:
                raise
            return (
                layout_url,
                layout_url,
                f"meta-{self.settings.muse_image_model}+layout-fallback",
            )


def get_render_service(settings: Settings) -> RenderService:
    mock = MockRenderEngine(settings)
    if settings.mock_forced():
        return mock
    return MuseImageRenderEngine(settings, mock)
