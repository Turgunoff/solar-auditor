"""Meta client contract tests — no network; pure helpers, gating, wiring."""

import base64
from io import BytesIO

import pytest
from PIL import Image

from app.core.config import Settings
from app.services.meta_client import (
    MetaAPIError,
    MetaAPINotReady,
    MetaModelClient,
    _box_iou,
    _dedupe_polys,
    _extract_image_bytes,
    _filter_and_merge_boxes,
    _select_primary_roofs,
    _sniff_image_mime,
    _to_jpeg_bytes,
    get_meta_client,
)
from app.services.sam_parse import boxes_to_polygons, extract_output_text


def live_settings(**kw):
    return Settings(use_mock=False, meta_api_key="k", **kw)


def test_not_configured_without_key():
    c = MetaModelClient(Settings(use_mock=False, meta_api_key=""))
    assert not c.configured
    with pytest.raises(MetaAPINotReady):
        c.segment_rooftop("x.jpg", 100, 100)
    with pytest.raises(MetaAPINotReady):
        c.render_rooftop_with_panels("x.jpg", 5)
    with pytest.raises(MetaAPINotReady):
        c.engineering_summary({})


def test_mock_mode_disables_live_even_with_key():
    c = MetaModelClient(Settings(use_mock=True, meta_api_key="k"))
    assert not c.configured
    with pytest.raises(MetaAPINotReady):
        c.engineering_summary({})


def test_live_configured():
    c = get_meta_client(live_settings())
    assert c.configured
    assert c.base_url == "https://api.meta.ai/v1"
    assert "Bearer" in c._auth_headers()["Authorization"]


def test_boxes_to_polygons():
    text = "roof <|box;x1=10;y1=20;x2=110;y2=120;w=640;h=480|> done"
    assert boxes_to_polygons(text) == [[(10.0, 20.0), (110.0, 20.0), (110.0, 120.0), (10.0, 120.0)]]
    assert boxes_to_polygons("no boxes here") == []
    assert boxes_to_polygons("") == []


def test_extract_output_text():
    resp = {
        "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "hi"}]},
            {"type": "image_generation_call", "result": "zzz"},
        ]
    }
    assert extract_output_text(resp) == "hi"
    assert extract_output_text({}) == ""


def test_sam_concept_wiring(monkeypatch):
    c = MetaModelClient(live_settings())
    seen = {}

    def fake_responses(body):
        seen.update(body)
        return {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "x <|box;x1=0;y1=0;x2=50;y2=50;w=100;h=100|>",
                        }
                    ],
                }
            ]
        }

    monkeypatch.setattr(c, "_responses_create", fake_responses)
    polys = c._sam_concept("file-1", "chimney")
    assert seen["model"] == "sam-3.1"
    assert seen["input"][0]["content"][1] == {"type": "input_image", "file_id": "file-1"}
    assert polys == [[(0.0, 0.0), (50.0, 0.0), (50.0, 50.0), (0.0, 50.0)]]


def test_filter_roofs_drops_speckle_and_fullframe():
    W = H = 1000
    speck = [(0, 0), (10, 0), (10, 10), (0, 10)]  # 0.01% of frame
    full = [(0, 0), (900, 0), (900, 900), (0, 900)]  # 81% of frame
    good = [(100, 100), (500, 100), (500, 500), (100, 500)]  # 16%
    out = _filter_and_merge_boxes([speck, full, good], W, H, kind="roof")
    assert out == [good]


def test_filter_obstacles_keeps_canopy_drops_distant_speck():
    W = H = 1000
    roof = [(100, 100), (600, 100), (600, 600), (100, 600)]
    on_roof = [(200, 200), (260, 200), (260, 260), (200, 260)]
    canopy = [(700, 700), (900, 700), (900, 900), (700, 900)]  # 4% off-roof
    speck = [(700, 100), (710, 100), (710, 110), (700, 110)]
    out = _filter_and_merge_boxes(
        [on_roof, canopy, speck], W, H, kind="obstacle", roofs=[roof]
    )
    assert on_roof in out and canopy in out and speck not in out


def test_select_primary_roofs_prefers_central():
    W = H = 1000
    central = [(400, 400), (700, 400), (700, 700), (400, 700)]
    edge = [(0, 0), (300, 0), (300, 300), (0, 300)]
    far = [(900, 900), (990, 900), (990, 990), (900, 990)]
    out = _select_primary_roofs([edge, far, central], W, H, max_roofs=1)
    assert out == [central]


def test_dedupe_merges_near_duplicates():
    a = [(0, 0), (100, 0), (100, 100), (0, 100)]
    b = [(2, 2), (102, 2), (102, 102), (2, 102)]
    c = [(500, 500), (600, 500), (600, 600), (500, 600)]
    assert _dedupe_polys([a, b, c]) == [a, c]


def test_box_iou_bounds():
    a = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert _box_iou(a, list(a)) == 1.0
    b = [(20, 20), (30, 20), (30, 30), (20, 30)]
    assert _box_iou(a, b) == 0.0


def test_extract_image_bytes_generation_call():
    raw = base64.b64encode(b"fakepng").decode()
    resp = {"output": [{"type": "image_generation_call", "result": raw}]}
    assert _extract_image_bytes(resp) == b"fakepng"
    assert _extract_image_bytes({"output": [{"type": "message"}]}) is None


def test_extract_image_bytes_data_url():
    raw = base64.b64encode(b"img").decode()
    resp = {
        "output": [
            {
                "type": "other",
                "content": [{"type": "image", "image_url": f"data:image/png;base64,{raw}"}],
            }
        ]
    }
    assert _extract_image_bytes(resp) == b"img"


def test_sniff_mime_and_jpeg_passthrough(tmp_path):
    jpg = tmp_path / "a.bin"
    jpg.write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    mime, name = _sniff_image_mime(jpg)
    assert mime == "image/jpeg" and name == "a.jpg"
    assert _to_jpeg_bytes(b"\xff\xd8\xffabc") == b"\xff\xd8\xffabc"


def test_to_jpeg_converts_png():
    buf = BytesIO()
    Image.new("RGB", (8, 8), "red").save(buf, format="PNG")
    out = _to_jpeg_bytes(buf.getvalue())
    assert out[:3] == b"\xff\xd8\xff"


def test_upload_fallback_fails_closed_on_no_roof(monkeypatch):
    """Live SAM failure on a non-preset image must not yield generic boxes."""
    from app.services.segmentation import MetaSAMSegmentor, MockSegmentor

    settings = live_settings()
    seg = MetaSAMSegmentor(settings, MockSegmentor(settings))

    def boom(_path, _w, _h):
        raise MetaAPIError("SAM 3.1 returned no usable roof boxes")

    monkeypatch.setattr(seg.client, "segment_rooftop", boom)
    # Preset runs still fall back to calibrated templates.
    out = seg.segment("x.jpg", 1024, 768, "residential_gable")
    assert out.provider.endswith("+mock-fallback")
    assert len(out.roof_polygons) == 2
    # Uploads / map captures raise instead of drawing panels on anything.
    with pytest.raises(MetaAPIError, match="no usable roof boxes"):
        seg.segment("x.jpg", 1024, 768, None)


def _transport_client(handler):
    import httpx

    return MetaModelClient(live_settings(), transport=httpx.MockTransport(handler))


def test_responses_500_maps_to_api_error():
    def handler(request):
        import httpx

        return httpx.Response(502, text="bad gateway")

    c = _transport_client(handler)
    with pytest.raises(MetaAPIError, match="502"):
        c._responses_create({"model": "x"})


def test_responses_non_json_maps_to_api_error():
    def handler(request):
        import httpx

        return httpx.Response(200, text="not json")

    c = _transport_client(handler)
    with pytest.raises(MetaAPIError, match="non-JSON"):
        c._responses_create({"model": "x"})


def test_upload_400_and_missing_id(tmp_path):
    import httpx

    img = tmp_path / "r.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 10)

    def bad(_request):
        return httpx.Response(400, text="nope")

    with pytest.raises(MetaAPIError, match="400"):
        _transport_client(bad).upload_file(str(img))

    def noid(_request):
        return httpx.Response(200, json={})

    with pytest.raises(MetaAPIError, match="missing file id"):
        _transport_client(noid).upload_file(str(img))

    def ok(_request):
        return httpx.Response(200, json={"id": "file-9"})

    assert _transport_client(ok).upload_file(str(img)) == "file-9"
