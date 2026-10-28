"""
Meta Model API client — live wiring for:
  - SAM 3.1  (POST /v1/files + POST /v1/responses)
  - Muse Image 1.0 (Responses / image generation)
  - Muse Spark 1.3 (Responses chat)

Docs: https://dev.meta.ai/docs/
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import Settings
from app.services.sam_parse import boxes_to_polygons, extract_output_text

logger = logging.getLogger(__name__)

Point = Tuple[float, float]
Polygon = List[Point]

ROOF_PROMPTS = (
    "building roof",
    "house rooftop",
    "tiled roof",
    "flat commercial roof",
)
OBSTACLE_PROMPTS = (
    "HVAC unit",
    "air conditioning unit",
    "skylight",
    "chimney",
    "roof vent",
    "tree",
    "tree canopy",
    "trees",
    "courtyard",
    "garden",
    "lawn",
    "parking lot",
)


class MetaAPIError(RuntimeError):
    """Upstream Meta API failure."""


class MetaAPINotReady(RuntimeError):
    """Credentials missing or live client methods not wired yet."""


class MetaModelClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.base_url = settings.meta_api_base_url.rstrip("/")
        self.timeout = settings.meta_timeout_seconds
        # Injected in tests (httpx.MockTransport); None = real network.
        self._transport = transport

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(timeout=timeout, transport=self._transport)

    @property
    def configured(self) -> bool:
        return bool(self.settings.meta_api_key.strip()) and not self.settings.use_mock

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.settings.meta_api_key}"}

    def _json_headers(self) -> Dict[str, str]:
        return {
            **self._auth_headers(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _require_live(self) -> None:
        if not self.settings.meta_api_key.strip():
            raise MetaAPINotReady("META_API_KEY is empty")
        if self.settings.use_mock:
            raise MetaAPINotReady("USE_MOCK=true — live calls disabled")

    def ping(self) -> Dict[str, Any]:
        self._require_live()
        # Cheap authenticated call: list models if available, else tiny responses probe
        url = f"{self.base_url}/models"
        try:
            with self._client(min(30.0, self.timeout)) as client:
                res = client.get(url, headers=self._auth_headers())
            return {
                "ok": res.status_code < 500,
                "status_code": res.status_code,
                "url": url,
                "body_preview": res.text[:240],
            }
        except httpx.HTTPError as exc:
            raise MetaAPIError(f"Ping failed: {exc}") from exc

    def upload_file(self, image_path: str, purpose: str = "user_data") -> str:
        self._require_live()
        path = Path(image_path)
        mime, upload_name = _sniff_image_mime(path)
        url = f"{self.base_url}/files"
        try:
            with self._client(self.timeout) as client:
                with path.open("rb") as fh:
                    res = client.post(
                        url,
                        headers=self._auth_headers(),
                        files={"file": (upload_name, fh, mime)},
                        data={"purpose": purpose},
                    )
        except httpx.HTTPError as exc:
            raise MetaAPIError(f"File upload failed: {exc}") from exc
        if res.status_code >= 400:
            raise MetaAPIError(f"File upload {res.status_code}: {res.text[:400]}")
        data = res.json()
        file_id = data.get("id")
        if not isinstance(file_id, str) or not file_id:
            raise MetaAPIError("Upload response missing file id")
        return file_id

    def _responses_create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/responses"
        try:
            with self._client(self.timeout) as client:
                res = client.post(url, headers=self._json_headers(), json=body)
        except httpx.HTTPError as exc:
            raise MetaAPIError(f"Responses call failed: {exc}") from exc
        if res.status_code >= 400:
            raise MetaAPIError(f"Responses {res.status_code}: {res.text[:500]}")
        try:
            return res.json()
        except ValueError as exc:
            raise MetaAPIError("Responses returned non-JSON") from exc

    def _sam_concept(self, file_id: str, concept: str) -> List[Polygon]:
        """One noun-phrase concept per SAM request (Meta requirement)."""
        body = {
            "model": self.settings.sam_model,
            "stream": False,
            "metadata": {"mask_encoding": "one_bit"},
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": concept},
                        {"type": "input_image", "file_id": file_id},
                    ],
                }
            ],
        }
        data = self._responses_create(body)
        text = extract_output_text(data)
        return boxes_to_polygons(text)

    def segment_rooftop(
        self,
        image_path: str,
        width: int,
        height: int,
    ) -> Dict[str, List[Polygon]]:
        if not self.configured:
            raise MetaAPINotReady(
                "Set USE_MOCK=false and META_API_KEY to enable live SAM 3.1"
            )

        file_id = self.upload_file(image_path)
        roofs: List[Polygon] = []
        obstacles: List[Polygon] = []

        # Collect from multiple prompts then merge — better multi-plane coverage
        for concept in ROOF_PROMPTS:
            try:
                found = self._sam_concept(file_id, concept)
            except MetaAPIError as exc:
                logger.warning("SAM roof prompt %r failed: %s", concept, exc)
                continue
            roofs.extend(found)

        for concept in OBSTACLE_PROMPTS:
            try:
                found = self._sam_concept(file_id, concept)
            except MetaAPIError as exc:
                logger.warning("SAM obstacle prompt %r failed: %s", concept, exc)
                continue
            obstacles.extend(found)

        roofs = _filter_and_merge_boxes(roofs, width, height, kind="roof")
        roofs = _select_primary_roofs(roofs, width, height, max_roofs=1)
        obstacles = _filter_and_merge_boxes(
            obstacles, width, height, kind="obstacle", roofs=roofs
        )

        if not roofs:
            raise MetaAPIError(
                "SAM 3.1 returned no usable roof boxes for this image "
                "(empty matches are valid — zoom closer to one building)."
            )

        return {"roof_polygons": roofs, "obstacles": obstacles}

    def render_rooftop_with_panels(
        self,
        image_path: str,
        panel_count: int,
        roof_hint: str = "",
        photorealize_layout: bool = False,
    ) -> bytes:
        if not self.configured:
            raise MetaAPINotReady(
                "Set USE_MOCK=false and META_API_KEY to enable live Muse Image"
            )

        file_id = self.upload_file(image_path)
        if photorealize_layout:
            prompt = (
                "This aerial already has the approved solar layout drawn as blue "
                f"rectangles ({panel_count} PV modules). Photorealize ONLY those modules "
                "into realistic framed solar panels. Do NOT add, remove, move, or resize "
                "panels. Do NOT put panels on other roofs, trees, yards, or roads. "
                "Keep the same camera, building outlines, and module grid. "
                f"{roof_hint}"
            ).strip()
        else:
            prompt = (
                "Edit this aerial rooftop photo to show neatly installed solar PV panels "
                f"only on the south-facing / sunlit roof planes ({panel_count} modules). "
                "Do not put panels on trees, yards, north-facing slopes, or shaded sides. "
                f"Keep camera angle and building geometry the same. Photoreal. {roof_hint}"
            ).strip()

        # Muse Image via Responses API (image edit / generation styles vary by release)
        body = {
            "model": self.settings.muse_image_model,
            "stream": False,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "file_id": file_id},
                    ],
                }
            ],
        }
        data = self._responses_create(body)
        image_bytes = _extract_image_bytes(data)
        if image_bytes:
            return _to_jpeg_bytes(image_bytes)

        # Fallback: images generations endpoint (if Responses returns text-only)
        b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        gen_body = {
            "model": self.settings.muse_image_model,
            "prompt": prompt,
            "image": f"data:image/jpeg;base64,{b64}",
            "n": 1,
            "size": "1024x1024",
        }
        url = f"{self.base_url}/images/generations"
        try:
            with self._client(self.timeout) as client:
                res = client.post(url, headers=self._json_headers(), json=gen_body)
        except httpx.HTTPError as exc:
            raise MetaAPIError(f"Muse Image generations failed: {exc}") from exc
        if res.status_code >= 400:
            raise MetaAPIError(
                f"Muse Image unavailable ({res.status_code}): {res.text[:400]}"
            )
        payload = res.json()
        out_b64 = (
            payload.get("data", [{}])[0].get("b64_json")
            or payload.get("image_base64")
        )
        if not out_b64:
            raise MetaAPIError("Muse Image response missing image bytes")
        return _to_jpeg_bytes(base64.b64decode(out_b64))

    def engineering_summary(self, facts: Dict[str, Any]) -> str:
        if not self.configured:
            raise MetaAPINotReady(
                "Set USE_MOCK=false and META_API_KEY to enable live Muse Spark"
            )

        user = (
            "Write a 100-140 word rooftop solar FEASIBILITY note (no markdown). "
            "Tone: cautious pre-sales sketch, NOT a stamped engineering report. "
            f"Panels={facts.get('panel_count')} (from 2D layout engine), "
            f"kWp={facts.get('capacity_kw')}, "
            f"kWh/yr={facts.get('annual_kwh')} (fixed peak-sun-hour assumption), "
            f"cost_usd={facts.get('cost_usd')}, savings_usd={facts.get('savings_usd')}, "
            f"simple_payback_years={facts.get('roi_years')}, "
            f"obstacles={facts.get('obstacle_count')}, usable_m2={facts.get('usable_area_m2')}. "
            "State that Muse visuals are concept-only. End with site-survey next steps "
            "(pitch/azimuth, structure, shading, utility)."
        )
        body = {
            "model": self.settings.muse_text_model,
            "stream": False,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": user}],
                }
            ],
        }
        data = self._responses_create(body)
        text = extract_output_text(data)
        if not text:
            # Some responses put text in nested fields
            text = str(data.get("output_text") or "").strip()
        if not text:
            raise MetaAPIError("Muse Spark returned empty text")
        return text


def _sniff_image_mime(path: Path) -> Tuple[str, str]:
    """Return (mime, filename) matching actual bytes so Meta upload validation passes."""
    head = path.read_bytes()[:16]
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", f"{path.stem}.jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", f"{path.stem}.png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp", f"{path.stem}.webp"
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return mime, path.name


def _extract_image_bytes(response: Dict[str, Any]) -> Optional[bytes]:
    """Pull image bytes from Muse Image Responses output.

    Live muse-image-1.0 returns type=image_generation_call with base64 in `result`
    (often WebP). Older shapes put b64 under content parts.
    """
    for item in response.get("output") or []:
        if not isinstance(item, dict):
            continue
        # Muse Image 1.0: image_generation_call.result is raw base64
        if item.get("type") == "image_generation_call":
            result = item.get("result")
            if isinstance(result, str) and result.strip():
                try:
                    return base64.b64decode(result)
                except Exception:
                    logger.warning("Failed to decode image_generation_call.result")
            elif isinstance(result, dict):
                b64 = (
                    result.get("image_base64")
                    or result.get("b64_json")
                    or result.get("data")
                )
                if isinstance(b64, str) and b64:
                    return base64.b64decode(b64)

        for part in item.get("content") or []:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type")
            if ptype in {"output_image", "image", "image_generation_call"}:
                b64 = (
                    part.get("image_base64")
                    or part.get("b64_json")
                    or part.get("result")
                )
                if isinstance(b64, str) and b64:
                    return base64.b64decode(b64)
                url = part.get("image_url") or part.get("url")
                if isinstance(url, str) and url.startswith("data:"):
                    _, _, payload = url.partition(",")
                    return base64.b64decode(payload)
    return None


def _to_jpeg_bytes(raw: bytes) -> bytes:
    """Normalize Muse output (often WebP) to JPEG for /static/renders/*.jpg."""
    from io import BytesIO

    from PIL import Image

    if raw[:3] == b"\xff\xd8\xff":
        return raw
    img = Image.open(BytesIO(raw)).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _box_area(poly: Polygon) -> float:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return max(0.0, max(xs) - min(xs)) * max(0.0, max(ys) - min(ys))


def _box_iou(a: Polygon, b: Polygon) -> float:
    ax = [p[0] for p in a]
    ay = [p[1] for p in a]
    bx = [p[0] for p in b]
    by = [p[1] for p in b]
    ax1, ay1, ax2, ay2 = min(ax), min(ay), max(ax), max(ay)
    bx1, by1, bx2, by2 = min(bx), min(by), max(bx), max(by)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _center(poly: Polygon) -> Tuple[float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _dedupe_polys(polys: List[Polygon], tol: float = 8.0) -> List[Polygon]:
    kept: List[Polygon] = []
    for poly in polys:
        cx, cy = _center(poly)
        duplicate = False
        for other in kept:
            ox, oy = _center(other)
            if abs(cx - ox) < tol and abs(cy - oy) < tol:
                duplicate = True
                break
            if _box_iou(poly, other) > 0.55:
                duplicate = True
                break
        if not duplicate:
            kept.append(poly)
    return kept


def _filter_and_merge_boxes(
    polys: List[Polygon],
    width: int,
    height: int,
    kind: str = "roof",
    roofs: List[Polygon] | None = None,
) -> List[Polygon]:
    """Drop tiny / huge false positives; keep obstacles that overlap roofs."""
    frame = max(float(width * height), 1.0)
    cleaned: List[Polygon] = []
    for poly in polys:
        area = _box_area(poly)
        frac = area / frame
        if kind == "roof":
            # Reject speckles and near-full-frame hallucinations
            if frac < 0.008 or frac > 0.75:
                continue
        else:
            if frac < 0.0004 or frac > 0.28:
                continue
            if roofs:
                # Keep if on/near a roof OR clearly a large canopy (tree) in frame
                on_roof = any(
                    _box_iou(poly, r) > 0.02
                    or _centers_near(poly, r)
                    or _point_in_aabb(_center(poly), r)
                    for r in roofs
                )
                likely_canopy = frac >= 0.012
                if not on_roof and not likely_canopy:
                    continue
        cleaned.append(poly)
    return _dedupe_polys(cleaned, tol=12.0)


def _select_primary_roofs(
    roofs: List[Polygon],
    width: int,
    height: int,
    max_roofs: int = 2,
) -> List[Polygon]:
    """Prefer 1–2 large central building roofs; drop yard/tree false positives."""
    if len(roofs) <= max_roofs:
        return roofs
    cx, cy = width / 2.0, height / 2.0
    diag = max((width**2 + height**2) ** 0.5, 1.0)
    scored: List[Tuple[float, Polygon]] = []
    for poly in roofs:
        area = _box_area(poly)
        px, py = _center(poly)
        dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 / diag
        scored.append((area * ((1.0 - min(dist, 1.0)) ** 1.5), poly))
    scored.sort(key=lambda t: t[0], reverse=True)
    best = scored[0][0] or 1.0
    kept: List[Polygon] = []
    for score, poly in scored:
        if len(kept) >= max_roofs:
            break
        if score < best * 0.2:
            break
        kept.append(poly)
    return kept or [scored[0][1]]


def _centers_near(a: Polygon, b: Polygon, tol: float = 40.0) -> bool:
    ax, ay = _center(a)
    bx, by = _center(b)
    return abs(ax - bx) < tol and abs(ay - by) < tol


def _point_in_aabb(pt: Tuple[float, float], poly: Polygon) -> bool:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x, y = pt
    return min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys)


def get_meta_client(settings: Settings) -> MetaModelClient:
    return MetaModelClient(settings)
