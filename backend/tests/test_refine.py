"""Refine endpoint: user exclusion boxes reduce packing without new segmentation."""

import app.api.endpoints as endpoints
from app.api.schemas import RefineRequest
from app.services.segmentation import PRESET_TEMPLATES

W, H = 1024, 768


def _body(extra_boxes=None, **kw):
    t = PRESET_TEMPLATES["commercial_flat_hvac"]
    mpp = 0.05
    return RefineRequest(
        roof_polygons=[[(x * W, y * H) for x, y in p] for p in t["roofs"]],
        obstacles=[[(x * W, y * H) for x, y in p] for p in t["obstacles"]],
        user_boxes=extra_boxes or [],
        width_px=W,
        height_px=H,
        meters_per_pixel=mpp,
        sam_overbox=False,
        **kw,
    )


def test_refine_without_boxes_packs():
    res = endpoints.refine_layout(_body())
    assert res.layout.total_panels > 0
    assert res.analytics.system_capacity_kw > 0


def test_refine_user_box_excludes_area():
    full = endpoints.refine_layout(_body())
    # Box over the top quarter of the frame must remove panels.
    strip = [[[0, 0], [W, 0], [W, H / 4], [0, H / 4]]]
    cut = endpoints.refine_layout(_body(extra_boxes=strip))
    assert 0 < cut.layout.total_panels < full.layout.total_panels
    # Box entirely off-roof changes nothing and never errors.
    far = [[[0, 0], [10, 0], [10, 10], [0, 10]]]
    same = endpoints.refine_layout(_body(extra_boxes=far))
    assert same.layout.total_panels == full.layout.total_panels
