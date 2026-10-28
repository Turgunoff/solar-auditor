from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import Settings
from app.services.disclaimer import DISCLAIMER_FULL


def build_pdf(project: Dict[str, Any], settings: Settings) -> Path:
    project_id = project["project_id"]
    out_path = settings.exports_dir / f"solar-audit-{project_id}.pdf"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
    )
    warn = ParagraphStyle(
        "Warn",
        parent=body,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#9A3412"),
        backColor=colors.HexColor("#FFF7ED"),
        borderPadding=6,
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    story = []
    story.append(Paragraph("Rooftop Solar Feasibility Sketch", title_style))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Project ID: <b>{project_id}</b> · Generated: {ts}", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(DISCLAIMER_FULL.replace("\n", " "), warn))
    story.append(Spacer(1, 10))

    analytics = project["analytics"]
    layout = project["layout"]
    panel_w = settings.panel_width_m
    panel_h = settings.panel_height_m
    n = layout["total_panels"]
    data = [
        ["Metric", "Value"],
        ["System capacity (est.)", f"{analytics['system_capacity_kw']} kWp"],
        ["Annual generation (est.)", f"{analytics['annual_generation_kwh']:,} kWh"],
        ["Estimated cost", f"${analytics['estimated_cost_usd']:,}"],
        ["Annual savings (est.)", f"${analytics['annual_savings_usd']:,}"],
        [
            "Simple payback",
            f"{analytics['roi_years']} years"
            if analytics.get("roi_years") is not None
            else "N/A",
        ],
        ["Panels (layout engine)", str(n)],
        ["Module size", f"{panel_w} × {panel_h} m · {settings.panel_kw * 1000:.0f} W"],
        [
            "Usable area (est.)",
            f"{analytics.get('usable_area_m2') or 0:.1f} m²",
        ],
        [
            "Assumptions",
            f"{settings.peak_sun_hours:.0f} peak-sun-h · "
            f"${settings.tariff_per_kwh_usd:.2f}/kWh · "
            f"${settings.cost_per_kw_usd:.0f}/kWp",
        ],
    ]
    table = Table(data, colWidths=[70 * mm, 90 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    def _static(rel: str) -> Path:
        return settings.static_dir / rel.replace("/static/", "")

    image_path = _static(project.get("image_url") or "")
    layout_url = project.get("layout_url") or project.get("render_url") or ""
    muse_url = project.get("render_url") or ""
    layout_path = _static(layout_url) if layout_url else Path()
    muse_path = _static(muse_url) if muse_url else Path()

    for label, path in (
        ("Before (aerial)", image_path),
        ("Layout engine overlay (BOM visual — trust this count)", layout_path),
    ):
        if path.exists():
            story.append(Paragraph(label, body))
            story.append(RLImage(str(path), width=160 * mm, height=90 * mm, kind="proportional"))
            story.append(Spacer(1, 8))

    if muse_path.exists() and muse_path.resolve() != layout_path.resolve():
        story.append(
            Paragraph(
                "Muse Image concept (photoreal mood only — may differ from BOM)",
                body,
            )
        )
        story.append(RLImage(str(muse_path), width=160 * mm, height=90 * mm, kind="proportional"))
        story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Bill of Materials (layout-engine estimate)</b>", body))
    story.append(
        Paragraph(
            f"• {n} × {settings.panel_kw * 1000:.0f}W PV modules "
            f"({panel_w}×{panel_h} m)<br/>"
            f"• Racking / mounting hardware (allowance)<br/>"
            f"• Inverter &amp; BOS allowance (budget line)<br/>"
            f"<i>Not a procurement BOM — refine after site survey.</i>",
            body,
        )
    )
    story.append(Spacer(1, 10))
    summary = analytics.get("agent_summary") or ""
    story.append(Paragraph("<b>Feasibility notes</b>", body))
    story.append(Paragraph(summary, body))
    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "Solar Auditor · Meta Hackathon demo · Not for construction or financing decisions",
            ParagraphStyle("Footer", parent=body, textColor=colors.grey, fontSize=8),
        )
    )

    doc.build(story)
    return out_path
