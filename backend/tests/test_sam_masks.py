"""SAM mask tokens decode to real (non-rectangular) polygons."""

from app.services.sam_parse import boxes_to_polygons, masks_to_polygons

# Official parser example: 5x5 one_bit mask inside a 100x100 frame.
SAM_TEXT = (
    "0<|box;x1=10;y1=20;x2=15;y2=25;w=100;h=100|>"
    "<|mask;x=0;y=0;data=5,5,!!!!!(QO(0lu8?|>"
)


def test_mask_polygon_fits_inside_box():
    polys = masks_to_polygons(SAM_TEXT)
    assert len(polys) == 1
    xs = [p[0] for p in polys[0]]
    ys = [p[1] for p in polys[0]]
    assert min(xs) >= 10 and max(xs) <= 15
    assert min(ys) >= 20 and max(ys) <= 25
    # Decoded shape is not the full 5x5 box.
    assert 0 < len(polys[0]) >= 4


def test_box_only_text_falls_back_to_aabb():
    text = "0<|box;x1=1;y1=2;x2=11;y2=22;w=100;h=100|>"
    assert masks_to_polygons(text) == boxes_to_polygons(text)
    assert masks_to_polygons(text)[0] == [(1.0, 2.0), (11.0, 2.0), (11.0, 22.0), (1.0, 22.0)]


def test_garbage_text_yields_nothing():
    assert masks_to_polygons("no tokens here") == []
