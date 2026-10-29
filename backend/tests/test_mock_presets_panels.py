"""Mock preset templates must yield panels (tight outlines, no SAM shrink)."""

from app.api.endpoints import PRESETS
from app.core.config import Settings
from app.services.layout_engine import place_panels, usable_area_m2
from app.services.segmentation import PRESET_TEMPLATES, _scale_poly

W, H = 1024, 768


def test_all_mock_presets_yield_panels():
    settings = Settings(use_mock=True)
    for preset in PRESETS:
        t = PRESET_TEMPLATES[preset["id"]]
        mpp = preset["meters_per_pixel"]
        roofs = [[(x * W, y * H) for x, y in p] for p in t["roofs"]]
        obs = [[(x * W, y * H) for x, y in p] for p in t["obstacles"]]
        layout = place_panels(roofs, obs, W, H, mpp, settings, sam_overbox=False)
        assert layout.total_panels > 0, f"no panels for {preset['id']}"
        area = usable_area_m2(
            roofs, obs, mpp, settings, width_px=W, height_px=H, sam_overbox=False
        )
        assert area > 0, f"no usable area for {preset['id']}"


def test_overbox_path_still_erodes():
    """Live SAM path must keep its aggressive handling (regression guard)."""
    settings = Settings(use_mock=True)
    roofs = [[(100, 100), (500, 100), (500, 420), (100, 420)]]
    tight = place_panels(roofs, [], 640, 640, 0.05, settings, sam_overbox=False)
    overbox = place_panels(roofs, [], 640, 640, 0.05, settings, sam_overbox=True)
    assert tight.total_panels >= overbox.total_panels
    assert overbox.total_panels > 0


def test_flat_roof_skips_south_cut():
    """Flat roofs pack the whole surface; pitched keeps the south cut."""
    settings = Settings(use_mock=True)
    roofs = [[(100, 100), (700, 100), (700, 500), (100, 500)]]
    flat = place_panels(roofs, [], 800, 600, 0.05, settings, pitched=False)
    pitched = place_panels(roofs, [], 800, 600, 0.05, settings, pitched=True)
    assert flat.total_panels > pitched.total_panels > 0
