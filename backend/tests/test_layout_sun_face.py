"""Sun-facing half + central roof selection."""

from app.core.config import Settings
from app.services.layout_engine import place_panels, sun_facing_region
from shapely.geometry import Polygon


def test_sun_facing_keeps_south_half_for_residential():
    # ~320 m² campus/pitched AABB → south half
    mpp = 0.05
    geom = Polygon([(0, 0), (400, 0), (400, 320), (0, 320)])
    south = sun_facing_region(geom, mpp)
    assert south.area < geom.area * 0.6
    assert south.centroid.y > geom.centroid.y


def test_large_flat_keeps_full():
    mpp = 0.05
    # 60m x 60m = 3600 m² commercial
    geom = Polygon([(0, 0), (1200, 0), (1200, 1200), (0, 1200)])
    full = sun_facing_region(geom, mpp)
    assert abs(full.area - geom.area) < 1.0


def test_place_panels_not_on_north_half():
    settings = Settings(use_mock=True)
    # One big residential roof box
    roofs = [[(100, 100), (500, 100), (500, 420), (100, 420)]]
    layout = place_panels(roofs, [], 640, 640, 0.05, settings)
    assert layout.total_panels > 0
    cy = (100 + 420) / 2
    # All panel centers should sit on the south half (y >= ridge)
    northish = [p for p in layout.panels if p.y < cy - 5]
    assert len(northish) == 0, f"panels on north slope: {len(northish)}"
