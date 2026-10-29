"""Pipeline regression: a non-roof upload must 422, never panel a face."""

import pytest
from fastapi import HTTPException
from PIL import Image

import app.api.endpoints as endpoints
from app.services.meta_client import MetaAPIError


def _portrait(path):
    img = Image.new("RGB", (400, 600), (120, 90, 70))
    img.save(path)


def test_pipeline_surfaces_422_when_no_roof(tmp_path, monkeypatch):
    img = tmp_path / "face.jpg"
    _portrait(img)

    class DeadSegmentor:
        def segment(self, *a, **k):
            raise MetaAPIError("SAM 3.1 returned no usable roof boxes")

    monkeypatch.setattr(endpoints, "get_segmentation_service", lambda s: DeadSegmentor())
    with pytest.raises(HTTPException) as exc:
        endpoints._run_pipeline(img, "/static/uploads/face.jpg", 0.05, None)
    assert exc.value.status_code == 422
    assert "no usable roof boxes" in exc.value.detail
