"""
report_service.py

Builds downloadable PDF and DOCX versions of:
1. ATS Diagnostic Report
2. Optimized Resume
"""

import io
import html
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.graphics.shapes import Drawing, Rect

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


BRAND_NAME = "AI Resume Copilot"
REPORT_TITLE = "ATS Diagnostic Report"


# =====================================================================
# COMMON HELPERS
# =====================================================================

def _band_color_hex(value: int) -> str:
    """0-40 red / 40-70 amber / 70-100 green."""
    if value >= 70:
        return "#1FAE6B"
    if value >= 40:
        return "#D97706"
    return "#DC2626"


def _register_fonts():
    return "Helvetica", "Helvetica-Bold"


def _build_styles(body_font, bold_font):
    return {
        "BrandTitle": ParagraphStyle(
            "BrandTitle",
            fontName=bold_font,
            fontSize=26,
            textColor=colors.HexColor("#14161B"),
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            fontName=body_font,
            fontSize=13,
            textColor=colors.HexColor("#6366F1"),
            alignment=TA_CENTER,
        ),
        "Section": ParagraphStyle(
            "Section",
            fontName=bold_font,
            fontSize=14,
            textColor=colors.HexColor("#14161B"),
            spaceBefore=6,
            spaceAfter=8,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName=body_font,
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#14161B"),
        ),
        "Muted": ParagraphStyle(
            "Muted",
            fontName=body_font,
            fontSize=10.5,
            textColor=colors.HexColor("#6B7280"),
        ),
    }


def _score_bar(value: int, width=380, height=16):
    color_hex = _band_color_hex(value)

    d = Drawing(width, height)

    d.add(
        Rect(
            0,
            0,
            width,
            height,
            fillColor=colors.HexColor("#EDEEF3"),
            strokeColor=None,
            rx=6,
            ry=6,
        )
    )

    fill_w = max(
        6,
        width * max(0, min(100, value)) / 100,
    )

    d.add(
        Rect(
            0,
            0,
            fill_w,
            height,
            fillColor=colors.HexColor(color_hex),
            strokeColor=None,
            rx=6,
            ry=6,
        )
    )

    return d


def _bullets(items, styles, empty_text):
    if not items:
        return [
            Paragraph(
                empty_text,
                styles["Muted"],
            )
        ]

    return [
        Paragraph(
            f"•&nbsp;&nbsp;{html.escape(str(text))}",
            styles["Body"],
        )
        for text in items
    ]


# =====================================================================
# PAGE NUMBER CANVAS
# =====================================================================

class _NumberedCanvas(pdfcanvas.Canvas):

    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)

        for state in self._saved_page_states:
            self.__dict__.update(state)

            self._draw_footer(num_pages)

            pdfcanvas.Canvas.showPage(self)

        pdfcanvas.Canvas.save(self)

    def _draw_footer(self, page_count):
        self.saveState()

        self.setFont("Helvetica", 8)
        self.setFillColor(
            colors.HexColor("#9AA0AC")
        )

        self.drawString(
            0.9 * inch,
            0.55 * inch,
            f"{} — {}",
        )

        self.drawRightString(
            LETTER[0] - 0.9 * inch,
            0.55 * inch,
            f"Page {self._pageNumber} of {}",
        )

        self.restoreState()


# =====================================================================
# ATS REPORT PDF
# =====================================================================

def generate_pdf_bytes(
    result: dict,
    resume_filename: str,
) -> bytes:

    body_font, bold_font = _register_fonts()
    styles = _build_styles(
        body_font,
        bold_font,
    )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        title=REPORT_TITLE,
    )

    story = []

    # TITLE PAGE
    story.append(Spacer(1, 1.3 * inch))

    story.append(
        Paragraph(
            BRAND_NAME,
            styles["BrandTitle"],
        )
    )

    story.append(
        Paragraph(
            REPORT_TITLE,
            styles["Subtitle"],
        )
    )

    story.append(Spacer(1, 0.5 * inch))

    story.append(
        HRFlowable(
            width="100%",
            color=colors.HexColor("#E1E4EA"),
            thickness=1,
        )
    )

    story.append(Spacer(1, 0.35 * inch))

    name = result.get("name") or "Candidate"
    email = result.get("email") or "Not provided"

    generated = datetime.now().strftime(
        "%B %d, %Y  •  %I:%M %p"
    )

    meta_table = Table(
        [
            ["Candidate", html.escape(str(name))],
            ["Email", html.escape(str(email))],
            ["Resume File", html.escape(str(resume_filename or "N/A"))],
            ["Generated", generated],
        ],
        colWidths=[
            1.6 * inch,
            4.0 * inch,
        ],
    )

    meta_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    bold_font,
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    body_font,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#6B7280"),
                ),
                (
                    "TEXTCOLOR",
                    (1, 0),
                    (1, -1),
                    colors.HexColor("#14161B"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(meta_table)
    story.append(PageBreak())

    # OVERVIEW
    ats = result.get("ats_score", 0)
    match = result.get("match_percentage", 0)

    matching = result.get("matching_skills") or []
    missing = result.get("missing_skills") or []

    story.append(
        Paragraph(
            "Overview",
            styles["Section"],
        )
    )

    story.append(
        Paragraph(
            f"ATS Score — {}/100",
            styles["Body"],
        )
    )

    story.append(Spacer(1, 4))
    story.append(_score_bar(ats))
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f"Match Percentage — {}%",
            styles["Body"],
        )
    )

    story.append(Spacer(1, 4))
    story.append(_score_bar(match))
    story.append(Spacer(1, 16))

    kpi_table = Table(
        [
            [
                "ATS Score",
                "Match %",
                "Skills Matched",
                "Skills Missing",
            ],
            [
                str(ats),
                f"{}%",
                str(len(matching)),
                str(len(missing)),
            ],
        ],
        colWidths=[
            1.2 * inch
        ] * 4,
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    bold_font,
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    body_font,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#F1F2FA"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E1E4EA"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # AI SUMMARY
    story.append(
        Paragraph(
            "AI Summary",
            styles["Section"],
        )
    )

    story.append(
        Paragraph(
            html.escape(str(result.get("summary") or "No summary generated.")),
            styles["Body"],
        )
    )

    story.append(Spacer(1, 16))

    # MATCHING SKILLS
    story.append(
        Paragraph(
            "Matching Skills",
            styles["Section"],
        )
    )

    story.extend(
        _bullets(
            matching,
            styles,
            "No matching skills identified.",
        )
    )

    story.append(Spacer(1, 16))

    # MISSING SKILLS
    story.append(
        Paragraph(
            "Missing Skills",
            styles["Section"],
        )
    )

    story.extend(
        _bullets(
            missing,
            styles,
            "No missing skills.",
        )
    )

    story.append(Spacer(1, 16))

    # STRENGTHS
    story.append(
        Paragraph(
            "Strengths",
            styles["Section"],
        )
    )

    story.extend(
        _bullets(
            result.get("strengths") or [],
            styles,
            "None listed.",
        )
    )

    story.append(Spacer(1, 16))

    # WEAKNESSES
    story.append(
        Paragraph(
            "Weaknesses",
            styles["Section"],
        )
    )

    story.extend(
        _bullets(
            result.get("weaknesses") or [],
            styles,
            "None listed.",
        )
    )

    story.append(Spacer(1, 16))

    # SUGGESTIONS
    story.append(
        Paragraph(
            "Suggestions",
            styles["Section"],
        )
    )

    suggestions = result.get("suggestions") or []

    if suggestions:
        for i, suggestion in enumerate(suggestions, start=1):
            story.append(
                Paragraph(
                    f"{}. {html.escape(str(suggestion))}",
                    styles["Body"],
                )
            )
            story.append(Spacer(1, 4))
    else:
        story.append(
            Paragraph(
                "None listed.",
                styles["Muted"],
            )
        )

    doc.build(
        story,
        canvasmaker=_NumberedCanvas,
    )

    buffer.seek(0)
    return buffer.getvalue()


# =====================================================================
# DOCX ATS REPORT
# =====================================================================

def _add_page_number_field(paragraph):
    run = paragraph.add_run()

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"

    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def _set_cell_shading(cell, hex_color: str):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


def _add_score_bar(doc, label: str, value: int, segments: int = 20):
    p = doc.add_paragraph()
    run = p.add_run(f"{} — {}/100")
    run.bold = True

    filled = round(segments * max(0, min(100, value)) / 100)
    fill_color = _band_color_hex(value).lstrip("#")

    table = doc.add_table(rows=1, cols=segments)
    table.autofit = False

    for i in range(segments):
        cell = table.cell(0, i)
        cell.width = Cm(0.32)
        _set_cell_shading(
            cell,
            fill_color if i < filled else "E5E7F0",
        )

    doc.add_paragraph()


def generate_docx_bytes(
    result: dict,
    resume_filename: str,
) -> bytes:

    doc = Document()
    section = doc.sections[0]

    section.page_width = Inches(8.5)
    section.page_height = Inches(11)

    header_p = section.header.paragraphs[0]
    header_run = header_p.add_run(f"{} — {}")
    header_run.font.size = Pt(9)
    header_run.font.color.rgb = RGBColor(0x67, 0x6E, 0x7C)

    footer_p = section.footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_p.add_run("Page ").font.size = Pt(9)
    _add_page_number_field(footer_p)

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(BRAND_NAME)
    title_run.font.size = Pt(28)
    title_run.font.bold = True

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle_p.add_run(REPORT_TITLE)
    subtitle_run.font.size = Pt(14)
    subtitle_run.font.color.rgb = RGBColor(0x63, 0x66, 0xF1)

    doc.add_paragraph()

    name = result.get("name") or "Candidate"
    email = result.get("email") or "Not provided"
    generated = datetime.now().strftime("%B %d, %Y  •  %I:%M %p")

    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.style = "Light List Accent 1"

    meta_rows = [
        ("Candidate", name),
        ("Email", email),
        ("Resume File", resume_filename or "N/A"),
        ("Generated", generated),
    ]

    for i, (label, value) in enumerate(meta_rows):
        meta_table.cell(i, 0).text = label
        meta_table.cell(i, 1).text = str(value)

    doc.add_page_break()

    ats = result.get("ats_score", 0)
    match = result.get("match_percentage", 0)
    matching = result.get("matching_skills") or []
    missing = result.get("missing_skills") or []

    doc.add_heading("Overview", level=1)

    kpi_table = doc.add_table(rows=2, cols=4)
    kpi_table.style = "Light Grid Accent 1"

    headers = [
        "ATS Score",
        "Match %",
        "Skills Matched",
        "Skills Missing",
    ]

    values = [
        str(ats),
        f"{}%",
        str(len(matching)),
        str(len(missing)),
    ]

    for i, header in enumerate(headers):
        kpi_table.cell(0, i).text = header

    for i, value in enumerate(values):
        kpi_table.cell(1, i).text = value

    doc.add_paragraph()

    _add_score_bar(doc, "ATS Score", ats)
    _add_score_bar(doc, "Match Percentage", match)

    doc.add_heading("AI Summary", level=1)
    doc.add_paragraph(result.get("summary") or "No summary generated.")

    doc.add_heading("Matching Skills", level=1)
    if matching:
        for item in matching:
            doc.add_paragraph(item, style="List Bullet")
    else:
        doc.add_paragraph("No matching skills identified.")

    doc.add_heading("Missing Skills", level=1)
    if missing:
        for item in missing:
            doc.add_paragraph(item, style="List Bullet")
    else:
        doc.add_paragraph("No missing skills.")

    doc.add_heading("Strengths", level=1)
    for item in result.get("strengths") or []:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("Weaknesses", level=1)
    for item in result.get("weaknesses") or []:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("Suggestions", level=1)
    for i, item in enumerate(result.get("suggestions") or [], start=1):
        doc.add_paragraph(f"{}. {}")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# =====================================================================
# OPTIMIZED RESUME PDF
# =====================================================================

def generate_optimized_resume_pdf(
    data: dict,
    candidate_name: str = "",
) -> bytes:
    """
    Generate ATS-friendly optimized resume PDF.

    Supported schema fields:
    - name
    - contact (or email, phone, location, linkedin, portfolio)
    - professional_summary (or summary)
    - technical_skills (dict of category -> list/str) or skills (list of dicts)
    - experience (list of dicts: title, company, duration, location, bullets)
    - projects (list of dicts: name, duration, technologies, bullets)
    - education (list of dicts: degree, institution, dates, location)
    - certifications (list of str or dicts)
    """

    if not isinstance(data, dict):
        data = {}

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=45,
        leftMargin=45,
        topMargin=42,
        bottomMargin=45,
        title=(
            f"{candidate_name or data.get('name') or 'Candidate'}"
            " - Optimized Resume"
        ),
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "OptimizedResumeName",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=4,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1A365D"),
    )

    contact_style = ParagraphStyle(
        "OptimizedResumeContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=6,
    )

    section_style = ParagraphStyle(
        "OptimizedResumeSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=4,
        textColor=colors.HexColor("#1A365D"),
    )

    body_style = ParagraphStyle(
        "OptimizedResumeBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=12.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=3,
    )

    bullet_style = ParagraphStyle(
        "OptimizedResumeBullet",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-7,
        spaceAfter=2,
    )

    entry_heading_style = ParagraphStyle(
        "OptimizedResumeEntryHeading",
        parent=body_style,
        fontName="Helvetica",
        fontSize=9.4,
        leading=12,
        spaceBefore=3,
        spaceAfter=2,
        textColor=colors.HexColor("#1A202C"),
    )

    story = []

    # 1. CANDIDATE NAME
    name_val = str(data.get("name") or candidate_name or "Candidate").strip()
    story.append(Paragraph(html.escape(name_val), name_style))

    # 2. CONTACT INFORMATION
    contact_parts = []
    contact_info = data.get("contact")
    if isinstance(contact_info, dict):
        for key in ["email", "phone", "location", "linkedin", "portfolio"]:
            val = contact_info.get(key)
            if val and str(val).strip():
                contact_parts.append(str(val).strip())

    for key in ["email", "phone", "location", "linkedin", "portfolio"]:
        val = data.get(key)
        if val and str(val).strip() and str(val).strip() not in contact_parts:
            contact_parts.append(str(val).strip())

    if contact_parts:
        escaped_parts = [html.escape(p) for p in contact_parts]
        story.append(Paragraph(" | ".join(escaped_parts), contact_style))

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.HexColor("#CBD5E0"),
            spaceAfter=6,
            spaceBefore=2,
        )
    )

    # 3. PROFESSIONAL SUMMARY
    summary = str(
        data.get("professional_summary") or data.get("summary") or ""
    ).strip()
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(Paragraph(html.escape(summary), body_style))

    # 4. TECHNICAL SKILLS
    tech_skills = data.get("technical_skills")
    skills_to_render = {}

    if isinstance(tech_skills, dict) and tech_skills:
        for cat, items in tech_skills.items():
            if not cat or not items:
                continue
            if isinstance(items, (list, tuple)):
                clean_items = [str(x).strip() for x in items if str(x).strip()]
                if clean_items:
                    skills_to_render[str(cat).strip()] = ", ".join(clean_items)
            elif isinstance(items, str) and items.strip():
                skills_to_render[str(cat).strip()] = items.strip()
    elif isinstance(data.get("skills"), list):
        for item in data.get("skills"):
            if isinstance(item, dict):
                cat = item.get("category") or "Skills"
                raw_items = item.get("skills") or []
                if isinstance(raw_items, (list, tuple)):
                    clean_items = [str(x).strip() for x in raw_items if str(x).strip()]
                    if clean_items:
                        skills_to_render[str(cat).strip()] = ", ".join(clean_items)

    if skills_to_render:
        story.append(Paragraph("TECHNICAL SKILLS", section_style))
        for cat, skill_str in skills_to_render.items():
            line = f"<b>{html.escape(cat)}:</b> {html.escape(skill_str)}"
            story.append(Paragraph(line, body_style))

    # 5. EXPERIENCE
    experience = data.get("experience")
    if isinstance(experience, list) and experience:
        valid_exp = [e for e in experience if isinstance(e, dict)]
        if valid_exp:
            story.append(Paragraph("EXPERIENCE", section_style))
            for entry in valid_exp:
                title = str(entry.get("title") or "").strip()
                company = str(entry.get("company") or "").strip()
                duration = str(entry.get("duration") or entry.get("dates") or "").strip()
                location = str(entry.get("location") or "").strip()

                header_parts = []
                if title and company:
                    header_parts.append(f"<b>{html.escape(title)}</b> — {html.escape(company)}")
                elif title:
                    header_parts.append(f"<b>{html.escape(title)}</b>")
                elif company:
                    header_parts.append(f"<b>{html.escape(company)}</b>")

                meta_parts = []
                if location:
                    meta_parts.append(html.escape(location))
                if duration:
                    meta_parts.append(html.escape(duration))

                full_header = " — ".join(header_parts)
                if meta_parts:
                    if full_header:
                        full_header += " | " + " | ".join(meta_parts)
                    else:
                        full_header = " | ".join(meta_parts)

                if full_header:
                    story.append(Paragraph(full_header, entry_heading_style))

                bullets = entry.get("bullets") or entry.get("description") or []
                if isinstance(bullets, (list, tuple)):
                    for bullet in bullets:
                        b_str = str(bullet).strip()
                        if b_str:
                            story.append(Paragraph(f"• {html.escape(b_str)}", bullet_style))
                story.append(Spacer(1, 2))

    # 6. PROJECTS
    projects = data.get("projects")
    if isinstance(projects, list) and projects:
        valid_proj = [p for p in projects if isinstance(p, dict)]
        if valid_proj:
            story.append(Paragraph("PROJECTS", section_style))
            for proj in valid_proj:
                p_name = str(proj.get("name") or proj.get("title") or "").strip()
                duration = str(proj.get("duration") or proj.get("dates") or "").strip()
                tech = proj.get("technologies") or proj.get("tech_stack") or ""
                if isinstance(tech, (list, tuple)):
                    tech = ", ".join([str(x).strip() for x in tech if str(x).strip()])
                tech = str(tech).strip()

                parts = []
                if p_name:
                    parts.append(f"<b>{html.escape(p_name)}</b>")
                if duration:
                    parts.append(html.escape(duration))
                if tech:
                    parts.append(f"<i>{html.escape(tech)}</i>")

                if parts:
                    story.append(Paragraph(" | ".join(parts), entry_heading_style))

                bullets = proj.get("bullets") or proj.get("description") or []
                if isinstance(bullets, (list, tuple)):
                    for bullet in bullets:
                        b_str = str(bullet).strip()
                        if b_str:
                            story.append(Paragraph(f"• {html.escape(b_str)}", bullet_style))
                story.append(Spacer(1, 2))

    # 7. EDUCATION
    education = data.get("education")
    if isinstance(education, list) and education:
        valid_edu = [e for e in education if isinstance(e, dict)]
        if valid_edu:
            story.append(Paragraph("EDUCATION", section_style))
            for item in valid_edu:
                degree = str(item.get("degree") or "").strip()
                institution = str(item.get("institution") or "").strip()
                dates = str(item.get("dates") or item.get("duration") or "").strip()
                location = str(item.get("location") or "").strip()

                parts = []
                if degree:
                    parts.append(f"<b>{html.escape(degree)}</b>")
                if institution:
                    parts.append(html.escape(institution))
                if dates:
                    parts.append(html.escape(dates))
                if location:
                    parts.append(html.escape(location))

                if parts:
                    story.append(Paragraph(" | ".join(parts), body_style))

    # 8. CERTIFICATIONS
    certifications = data.get("certifications")
    if isinstance(certifications, (list, tuple)) and certifications:
        clean_certs = []
        for cert in certifications:
            if isinstance(cert, str) and cert.strip():
                clean_certs.append(cert.strip())
            elif isinstance(cert, dict):
                c_name = cert.get("name") or cert.get("title") or ""
                if c_name:
                    clean_certs.append(str(c_name).strip())

        if clean_certs:
            story.append(Paragraph("CERTIFICATIONS", section_style))
            for cert in clean_certs:
                story.append(Paragraph(f"• {html.escape(cert)}", bullet_style))

    # FOOTER
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        footer_name = candidate_name or data.get("name") or "Candidate"
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(45, 25, f"{} — Optimized Resume")
        canvas.drawRightString(LETTER[0] - 45, 25, f"Page {document.page}")
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    buffer.seek(0)
    return buffer.getvalue()