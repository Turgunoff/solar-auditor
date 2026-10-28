#!/usr/bin/env python3
"""Generate three stylized aerial rooftop sample images for local demos."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "sample_data"
OUT.mkdir(parents=True, exist_ok=True)


def _base(w: int, h: int, ground: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (w, h), ground)
    draw = ImageDraw.Draw(img)
    # faint grid / texture
    for x in range(0, w, 32):
        draw.line([(x, 0), (x, h)], fill=(ground[0] - 8, ground[1] - 6, ground[2] - 6), width=1)
    for y in range(0, h, 32):
        draw.line([(0, y), (w, y)], fill=(ground[0] - 8, ground[1] - 6, ground[2] - 6), width=1)
    return img


def residential_gable() -> None:
    w, h = 1024, 768
    img = _base(w, h, (92, 120, 78))
    d = ImageDraw.Draw(img)
    # house footprint shadow
    d.polygon([(120, 160), (512, 90), (900, 170), (880, 620), (140, 600)], fill=(55, 58, 62))
    # left pitch
    d.polygon([(160, 200), (512, 130), (512, 580), (150, 540)], fill=(140, 92, 72))
    # right pitch
    d.polygon([(512, 130), (860, 200), (870, 540), (512, 580)], fill=(118, 78, 62))
    # ridge
    d.line([(512, 130), (512, 580)], fill=(90, 60, 48), width=3)
    # chimney
    d.rectangle([320, 280, 380, 360], fill=(70, 70, 74))
    d.rectangle([610, 340, 660, 410], fill=(78, 78, 82))
    # driveway hint
    d.rectangle([40, 520, 140, 720], fill=(110, 110, 108))
    img.save(OUT / "residential_gable.jpg", quality=92)


def complex_hip() -> None:
    w, h = 1024, 768
    img = _base(w, h, (86, 112, 74))
    d = ImageDraw.Draw(img)
    d.polygon([(200, 160), (512, 70), (820, 160), (740, 420), (512, 360), (280, 420)], fill=(150, 100, 78))
    d.polygon([(280, 420), (512, 360), (740, 420), (760, 640), (260, 640)], fill=(128, 86, 68))
    d.polygon([(460, 210), (560, 210), (560, 300), (460, 300)], fill=(68, 68, 72))
    d.rectangle([350, 480, 420, 560], fill=(72, 72, 76))
    d.rectangle([600, 480, 680, 560], fill=(72, 72, 76))
    img.save(OUT / "complex_hip.jpg", quality=92)


def commercial_flat() -> None:
    w, h = 1100, 800
    img = _base(w, h, (100, 108, 96))
    d = ImageDraw.Draw(img)
    d.rectangle([80, 90, 1020, 710], fill=(168, 168, 162))
    d.rectangle([90, 100, 1010, 700], fill=(190, 190, 184))
    # HVAC blocks
    units = [
        (220, 220, 380, 340),
        (440, 230, 600, 360),
        (660, 220, 840, 340),
        (300, 440, 520, 580),
        (580, 460, 800, 590),
    ]
    for box in units:
        d.rectangle(box, fill=(90, 96, 104), outline=(60, 64, 70), width=2)
        x0, y0, x1, y1 = box
        d.ellipse([x0 + 20, y0 + 20, x0 + 70, y0 + 70], outline=(200, 200, 205), width=2)
    img.save(OUT / "commercial_flat_hvac.jpg", quality=92)


if __name__ == "__main__":
    residential_gable()
    complex_hip()
    commercial_flat()
    print(f"Wrote samples to {OUT}")
