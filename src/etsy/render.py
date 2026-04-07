import os

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from etsy.contracts import validate_design_system_artifact
from etsy.contracts import validate_page_blueprint_artifact
from etsy.contracts import validate_render_manifest
from etsy.io import read_json
from etsy.io import write_json

_SYSTEM_FONTS = {
    "Georgia-Bold": "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "Georgia": "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "Trebuchet-Bold": "/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf",
    "Trebuchet": "/System/Library/Fonts/Supplemental/Trebuchet MS.ttf",
}


class PdfRenderer:
    def __init__(self) -> None:
        self._registered_fonts = self._register_fonts()

    def run(self, run_dir: str) -> str:
        product_spec = read_json(os.path.join(run_dir, "artifacts", "product_spec.json"))
        design_system = read_json(os.path.join(run_dir, "artifacts", "design_system.json"))
        page_blueprint = read_json(os.path.join(run_dir, "artifacts", "page_blueprint.json"))
        validate_design_system_artifact(design_system)
        validate_page_blueprint_artifact(page_blueprint)

        product_files = product_spec["output_files"]
        for relative_path in product_files:
            absolute_path = os.path.join(run_dir, relative_path)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            self._render_pdf(absolute_path, product_spec, design_system, page_blueprint)

        preview_images = self._render_preview_images(run_dir, product_spec, design_system, page_blueprint)

        manifest = {
            "run_id": os.path.basename(run_dir),
            "product_files": product_files,
            "page_count": product_spec["page_count"],
            "page_size": product_spec["page_size"],
            "preview_images": preview_images,
            "design_template": design_system["layout"]["template_name"],
        }
        validate_render_manifest(manifest)
        manifest_path = os.path.join(run_dir, "artifacts", "render_manifest.json")
        write_json(manifest_path, manifest)
        return manifest_path

    def _render_preview_images(self, run_dir: str, product_spec: dict, design_system: dict, page_blueprint: dict) -> list[str]:
        preview_images = []
        preview_pages = page_blueprint["pages"][: max(3, min(4, len(page_blueprint["pages"]))) ]

        for index, page in enumerate(preview_pages, start=1):
            preview_path = os.path.join(run_dir, "product", f"page-preview-{index}.png")
            image = Image.new("RGB", (1200, 1200), design_system["palette"]["background"])
            drawer = ImageDraw.Draw(image)
            self._draw_preview_page(drawer, image.size, product_spec, design_system, page)
            image.save(preview_path)
            preview_images.append(os.path.relpath(preview_path, run_dir))

        return preview_images

    def _render_pdf(self, path: str, product_spec: dict, design_system: dict, page_blueprint: dict) -> None:
        page_size_name = str(product_spec.get("page_size") or "LETTER").upper()
        page_dimensions = LETTER if page_size_name == "LETTER" else A4
        page_width, page_height = page_dimensions

        palette = design_system["palette"]
        heading_font = self._resolve_font(design_system["typography"].get("heading_font"), bold=True)
        body_font = self._resolve_font(design_system["typography"].get("body_font"), bold=False)
        title_theme = str(product_spec.get("title_theme") or "Printable Planner")
        audience = str(product_spec.get("audience") or "busy adults")
        sections = product_spec.get("sections", [])
        pages = page_blueprint["pages"]
        page_count = len(pages)

        pdf = canvas.Canvas(path, pagesize=page_dimensions)

        # Dedicated cover page before all content pages
        self._draw_cover(
            pdf, page_width, page_height, title_theme, audience, sections, page_count, palette, heading_font, body_font
        )
        pdf.showPage()

        for page in pages:
            self._draw_page(
                pdf,
                page_width,
                page_height,
                page["page_number"],
                page_count,
                title_theme,
                audience,
                page,
                palette,
                heading_font,
                body_font,
            )
            pdf.showPage()

        pdf.save()

    # ------------------------------------------------------------------ #
    # PDF cover page                                                       #
    # ------------------------------------------------------------------ #

    def _draw_cover(
        self, pdf, w, h, title, audience, sections, page_count, palette, heading_font, body_font
    ) -> None:
        primary = self._hex_to_color(palette.get("primary"), colors.HexColor("#4F7CAC"))
        secondary = self._hex_to_color(palette.get("secondary"), colors.HexColor("#D9C6A5"))
        bg = self._hex_to_color(palette.get("background"), colors.HexColor("#FFF9F1"))
        margin = 54

        # Page background
        pdf.setFillColor(bg)
        pdf.rect(0, 0, w, h, fill=1, stroke=0)

        # Hero band  — top 54 % of page
        hero_bottom = int(h * 0.46)
        pdf.setFillColor(primary)
        pdf.rect(0, hero_bottom, w, h - hero_bottom, fill=1, stroke=0)

        # Accent strip at bottom of hero
        pdf.setFillColor(secondary)
        pdf.rect(0, hero_bottom - 10, w, 10, fill=1, stroke=0)

        # Centered title in hero
        band_cy = (h + hero_bottom) / 2
        pdf.setFillColor(colors.white)
        pdf.setFont(heading_font, 32)
        cover_title = self._fit_text(pdf, title, heading_font, 32, w - margin * 2 - 32)
        pdf.drawCentredString(w / 2, band_cy + 36, cover_title)

        # Audience tagline
        pdf.setFont(body_font, 14)
        pdf.setFillColor(colors.HexColor("#D6E8F6"))
        tagline = self._fit_text(pdf, f"Designed for {audience}", body_font, 14, w - margin * 2 - 32)
        pdf.drawCentredString(w / 2, band_cy + 4, tagline)

        # Badge: page count + instant download
        badge_text = f"{page_count} pages  |  Instant Digital Download"
        badge_w = pdf.stringWidth(badge_text, body_font, 10) + 32
        badge_x = (w - badge_w) / 2
        badge_y = band_cy - 38
        pdf.setFillColor(colors.HexColor("#2A5A8A"))
        pdf.roundRect(badge_x, badge_y - 12, badge_w, 26, 8, fill=1, stroke=0)
        pdf.setFont(body_font, 10)
        pdf.setFillColor(colors.white)
        pdf.drawCentredString(w / 2, badge_y - 2, badge_text)

        # "WHAT'S INSIDE" section
        section_top_y = hero_bottom - 22
        pdf.setFont(heading_font, 10)
        pdf.setFillColor(primary)
        pdf.drawCentredString(w / 2, section_top_y, "W H A T ' S   I N S I D E")

        # Divider
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1.5)
        pdf.line(margin + 36, section_top_y - 10, w - margin - 36, section_top_y - 10)

        bullet_y = section_top_y - 36
        for section in sections[:5]:
            if isinstance(section, dict):
                name = str(section.get("name") or "Section")
                purpose = str(section.get("purpose") or "")
            else:
                name = str(section)
                purpose = ""
            pdf.setFont(heading_font, 12)
            pdf.setFillColor(primary)
            pdf.drawString(margin + 48, bullet_y, ">")
            pdf.setFont(body_font, 12)
            pdf.setFillColor(colors.HexColor("#1E293B"))
            name_fitted = self._fit_text(pdf, name, body_font, 12, w - margin * 2 - 66)
            pdf.drawString(margin + 66, bullet_y, name_fitted)
            if purpose:
                pdf.setFont(body_font, 9)
                pdf.setFillColor(colors.HexColor("#64748B"))
                purpose_fitted = self._fit_text(pdf, purpose, body_font, 9, w - margin * 2 - 66)
                pdf.drawString(margin + 66, bullet_y - 13, purpose_fitted)
                bullet_y -= 13
            bullet_y -= 30

        # Info box
        info_y = 96
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1)
        pdf.roundRect(margin, info_y, w - margin * 2, 48, 10, fill=1, stroke=1)
        pdf.setFont(body_font, 10)
        pdf.setFillColor(colors.HexColor("#475569"))
        pdf.drawString(margin + 16, info_y + 28, "Print at home  .  A4 & Letter compatible  .  Personal planning use")
        pdf.setFont(heading_font, 10)
        pdf.setFillColor(primary)
        pdf.drawRightString(w - margin - 16, info_y + 28, "MoneyPrinter+ Digital Download")

        # Footer
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1)
        pdf.line(margin, 66, w - margin, 66)
        pdf.setFont(body_font, 8)
        pdf.setFillColor(colors.HexColor("#94A3B8"))
        pdf.drawString(margin, 46, "Digital file only - no physical product will ship.")
        pdf.drawRightString(w - margin, 46, "Thank you for your purchase!")

    # ------------------------------------------------------------------ #
    # PDF content page                                                     #
    # ------------------------------------------------------------------ #

    def _draw_page(
        self,
        pdf: canvas.Canvas,
        page_width: float,
        page_height: float,
        page_number: int,
        page_count: int,
        title_theme: str,
        audience: str,
        page: dict,
        palette: dict,
        heading_font: str,
        body_font: str,
    ) -> None:
        margin = 54
        primary = self._hex_to_color(palette.get("primary"), colors.HexColor("#4F7CAC"))
        secondary = self._hex_to_color(palette.get("secondary"), colors.HexColor("#D9C6A5"))
        bg = self._hex_to_color(palette.get("background"), colors.HexColor("#FFF9F1"))

        # Page background
        pdf.setFillColor(bg)
        pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        # Header bar
        header_h = 76
        header_bottom = page_height - header_h
        pdf.setFillColor(primary)
        pdf.rect(0, header_bottom, page_width, header_h, fill=1, stroke=0)

        pdf.setFillColor(colors.white)
        pdf.setFont(body_font, 10)
        theme_label = self._fit_text(pdf, title_theme, body_font, 10, (page_width / 2) - margin - 16)
        pdf.drawString(margin, header_bottom + 50, theme_label)
        pdf.setFont(heading_font, 18)
        page_title_text = str(page.get("title") or "Overview")
        page_title_max = page_width - margin * 4 - 80
        page_title_fitted = self._fit_text(pdf, page_title_text, heading_font, 18, page_title_max)
        pdf.drawCentredString(page_width / 2, header_bottom + 48, page_title_fitted)
        pdf.setFont(body_font, 10)
        pdf.drawRightString(page_width - margin, header_bottom + 50, f"{page_number} / {page_count}")

        # Sub-header strip
        sub_h = 34
        sub_bottom = header_bottom - sub_h
        pdf.setFillColor(secondary)
        pdf.rect(0, sub_bottom, page_width, sub_h, fill=1, stroke=0)

        page_type = str(page.get("page_type") or "worksheet")
        badge_label = page_type.upper()
        badge_text_w = pdf.stringWidth(badge_label, body_font, 9) + 22
        pdf.setFillColor(primary)
        pdf.roundRect(margin, sub_bottom + 7, badge_text_w, 18, 5, fill=1, stroke=0)
        pdf.setFont(body_font, 9)
        pdf.setFillColor(colors.white)
        pdf.drawString(margin + 10, sub_bottom + 11, badge_label)

        section_name = str(page.get("section_name") or "Overview")
        pdf.setFont(body_font, 10)
        pdf.setFillColor(colors.HexColor("#334155"))
        section_fitted = self._fit_text(pdf, section_name, body_font, 10, page_width - margin * 2 - badge_text_w - 24)
        pdf.drawRightString(page_width - margin, sub_bottom + 11, section_fitted)

        # Content zone
        content_top = sub_bottom - 8
        content_bottom = 100
        content_height = content_top - content_bottom

        self._draw_page_layout(
            pdf, page_width, margin, content_top, content_bottom,
            content_height, page_width - margin * 2, page, heading_font, body_font, primary, secondary,
        )

        # Footer
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1)
        pdf.line(margin, 84, page_width - margin, 84)
        pdf.setFont(body_font, 8)
        pdf.setFillColor(colors.HexColor("#94A3B8"))
        pdf.drawString(margin, 64, "Instant digital download for personal planning use")
        pdf.drawRightString(page_width - margin, 64, "MoneyPrinter+ Generator")
        pdf.setFont(body_font, 7)
        pdf.setFillColor(colors.HexColor("#CBD5E1"))
        pdf.drawString(margin, 46, f"Designed for {audience[:72]}")

    def _draw_page_layout(
        self, pdf, page_width, margin, content_top, content_bottom,
        content_height, content_width, page, heading_font, body_font, primary, secondary,
    ) -> None:
        left = margin
        page_type = str(page.get("page_type") or "worksheet")
        body_lines = page.get("body", [])

        if page_type == "schedule":
            self._draw_schedule_layout(
                pdf, left, content_bottom, content_width, content_height,
                body_lines, heading_font, body_font, primary, secondary,
            )
        elif page_type == "tracker":
            self._draw_tracker_layout(
                pdf, left, content_bottom, content_width, content_height,
                body_lines, heading_font, body_font, primary, secondary,
            )
        elif page_type == "reflection":
            self._draw_reflection_layout(
                pdf, left, content_bottom, content_width, content_height,
                body_lines, heading_font, body_font, primary, secondary,
            )
        else:
            self._draw_worksheet_layout(
                pdf, left, content_bottom, content_width, content_height,
                body_lines, heading_font, body_font, primary, secondary,
            )

    # ------------------------------------------------------------------ #
    # Layout renderers                                                     #
    # ------------------------------------------------------------------ #

    def _draw_schedule_layout(
        self, pdf, left, bottom, width, height, lines, heading_font, body_font, primary, secondary
    ) -> None:
        priority_h = 88
        top = bottom + height
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1)
        pdf.roundRect(left, top - priority_h, width, priority_h - 6, 10, fill=1, stroke=1)
        pdf.setFont(heading_font, 11)
        pdf.setFillColor(primary)
        pdf.drawString(left + 14, top - 24, "TODAY'S PRIORITIES")
        for i in range(3):
            py = top - 48 - i * 20
            pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
            pdf.setLineWidth(0.8)
            pdf.circle(left + 24, py, 5, stroke=1, fill=0)
            pdf.line(left + 38, py, left + width - 18, py)

        time_labels = ["6:00 AM", "8:00 AM", "10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM", "6:00 PM", "8:00 PM"]
        slot_top = top - priority_h
        slot_h = (slot_top - bottom) / len(time_labels)
        time_col = 76

        for i, label in enumerate(time_labels):
            row_y = slot_top - (i + 1) * slot_h
            if i % 2 == 0:
                pdf.setFillColor(colors.HexColor("#F8FAFC"))
                pdf.rect(left + time_col, row_y, width - time_col, slot_h - 1, fill=1, stroke=0)
            pdf.setFont(heading_font, 9)
            pdf.setFillColor(primary)
            pdf.drawString(left + 4, row_y + slot_h / 2 - 4, label)
            pdf.setStrokeColor(secondary)
            pdf.setLineWidth(1.5)
            pdf.line(left + time_col - 4, row_y, left + time_col - 4, row_y + slot_h - 1)
            pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
            pdf.setLineWidth(0.7)
            pdf.line(left + time_col, row_y + slot_h - 1, left + width, row_y + slot_h - 1)
            if i < len(lines):
                pdf.setFont(body_font, 9)
                pdf.setFillColor(colors.HexColor("#475569"))
                body_max_w = width - time_col - 18
                line_text = self._fit_text(pdf, str(lines[i]), body_font, 9, body_max_w)
                pdf.drawString(left + time_col + 8, row_y + slot_h / 2 - 4, line_text)

    def _draw_tracker_layout(
        self, pdf, left, bottom, width, height, lines, heading_font, body_font, primary, secondary
    ) -> None:
        days = ["M", "T", "W", "T", "F", "S", "S"]
        habit_col = 188
        circle_col_w = (width - habit_col - 48) / 7

        hdr_y = bottom + height - 24
        pdf.setFont(heading_font, 10)
        pdf.setFillColor(primary)
        pdf.drawString(left + 8, hdr_y, "HABIT")
        for j, day in enumerate(days):
            cx = left + habit_col + (j + 0.5) * circle_col_w
            pdf.drawCentredString(cx, hdr_y, day)
        pdf.drawCentredString(left + width - 24, hdr_y, "#")

        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1.5)
        pdf.line(left, hdr_y - 6, left + width, hdr_y - 6)

        row_area_h = height - 52
        row_h = row_area_h / 5
        for i in range(5):
            row_y = bottom + height - 52 - (i + 1) * row_h
            if i % 2 == 0:
                pdf.setFillColor(colors.HexColor("#F8FAFC"))
                pdf.rect(left, row_y, width, row_h - 2, fill=1, stroke=0)
            habit_raw = str(lines[i]) if i < len(lines) else f"Habit {i + 1}"
            habit = self._fit_text(pdf, habit_raw, body_font, 10, habit_col - 16)
            pdf.setFont(body_font, 10)
            pdf.setFillColor(colors.HexColor("#1E293B"))
            pdf.drawString(left + 8, row_y + row_h / 2 - 4, habit)
            for j in range(7):
                cx = left + habit_col + (j + 0.5) * circle_col_w
                cy = row_y + row_h / 2
                pdf.setStrokeColor(secondary)
                pdf.setLineWidth(1.2)
                pdf.circle(cx, cy, 9, stroke=1, fill=0)
            pdf.setStrokeColor(secondary)
            pdf.roundRect(left + width - 40, row_y + 4, 32, row_h - 8, 4, stroke=1, fill=0)
            pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
            pdf.setLineWidth(0.5)
            pdf.line(left, row_y - 1, left + width, row_y - 1)

        note_h = height - 52 - 5 * row_h - 8
        if note_h > 22:
            pdf.setFillColor(colors.white)
            pdf.setStrokeColor(secondary)
            pdf.setLineWidth(1)
            pdf.roundRect(left, bottom + 2, width, note_h, 6, fill=1, stroke=1)
            pdf.setFont(heading_font, 9)
            pdf.setFillColor(primary)
            pdf.drawString(left + 10, bottom + note_h - 14, "WEEKLY INTENTION:")

    def _draw_reflection_layout(
        self, pdf, left, bottom, width, height, lines, heading_font, body_font, primary, secondary
    ) -> None:
        questions = (list(lines) + [f"Reflection question {i + 1}" for i in range(3)])[:3]
        box_h = (height - 12) / 3
        line_gap = 22

        for i, question in enumerate(questions):
            bx_y = bottom + height - (i + 1) * box_h
            pdf.setFillColor(colors.white)
            pdf.setStrokeColor(secondary)
            pdf.setLineWidth(1)
            pdf.roundRect(left, bx_y + 4, width, box_h - 8, 10, fill=1, stroke=1)
            pdf.setFont(heading_font, 10)
            pdf.setFillColor(primary)
            q_full = f"Q{i + 1}.  {str(question)}"
            q_lines = self._split_text(pdf, q_full, heading_font, 10, width - 28)[:2]
            q_start_y = bx_y + box_h - 22
            for qi, ql in enumerate(q_lines):
                pdf.drawString(left + 14, q_start_y - qi * 14, ql)
            q_used = len(q_lines) * 14
            pdf.setStrokeColor(colors.HexColor("#D1D5DB"))
            pdf.setLineWidth(0.8)
            for j in range(4):
                line_y = bx_y + box_h - 22 - q_used - 8 - j * line_gap
                if line_y > bx_y + 12:
                    pdf.line(left + 14, line_y, left + width - 14, line_y)

    def _draw_worksheet_layout(
        self, pdf, left, bottom, width, height, lines, heading_font, body_font, primary, secondary
    ) -> None:
        gap = 12
        z1_h = int(height * 0.42)
        z2_h = int(height * 0.37)
        z3_h = height - z1_h - z2_h - gap * 2

        # Zone 1: Priorities
        z1_y = bottom + z2_h + z3_h + gap * 2
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1)
        pdf.roundRect(left, z1_y, width, z1_h, 12, fill=1, stroke=1)
        pdf.setFont(heading_font, 11)
        pdf.setFillColor(primary)
        pdf.drawString(left + 16, z1_y + z1_h - 20, "TODAY'S TOP PRIORITIES")
        row_spacing = (z1_h - 44) / 5
        for i in range(5):
            task_y = z1_y + z1_h - 44 - i * row_spacing
            pdf.setFont(heading_font, 11)
            pdf.setFillColor(primary)
            pdf.drawString(left + 14, task_y, str(i + 1))
            pdf.setStrokeColor(secondary)
            pdf.setLineWidth(1)
            pdf.circle(left + 28, task_y + 4, 6, stroke=1, fill=0)
            pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
            pdf.setLineWidth(0.8)
            pdf.line(left + 42, task_y, left + width - 14, task_y)
            if i < len(lines):
                pdf.setFont(body_font, 9)
                pdf.setFillColor(colors.HexColor("#64748B"))
                hint_max = width - 60
                hint = self._fit_text(pdf, str(lines[i]), body_font, 9, hint_max)
                # Draw hint text 12pt ABOVE the writing line so descenders clear it
                pdf.drawString(left + 46, task_y + 12, hint)

        # Zone 2: Notes
        z2_y = bottom + z3_h + gap
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(secondary)
        pdf.setLineWidth(1)
        pdf.roundRect(left, z2_y, width, z2_h, 12, fill=1, stroke=1)
        pdf.setFont(heading_font, 11)
        pdf.setFillColor(primary)
        pdf.drawString(left + 16, z2_y + z2_h - 20, "NOTES  &  BRAIN DUMP")
        pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
        pdf.setLineWidth(0.7)
        n_lines = int((z2_h - 38) / 22)
        for j in range(n_lines):
            ly = z2_y + z2_h - 38 - j * 22
            if ly > z2_y + 6:
                pdf.line(left + 16, ly, left + width - 16, ly)

        # Zone 3: Win of the day
        z3_y = bottom
        pdf.setFillColor(primary)
        pdf.setStrokeColor(primary)
        pdf.roundRect(left, z3_y, width, z3_h, 12, fill=1, stroke=0)
        pdf.setFont(heading_font, 10)
        pdf.setFillColor(colors.white)
        pdf.drawString(left + 16, z3_y + z3_h - 16, "TODAY'S WIN  *")
        pdf.setStrokeColor(colors.white)
        pdf.setLineWidth(0.8)
        for j in range(2):
            ly = z3_y + z3_h - 32 - j * 20
            if ly > z3_y + 4:
                pdf.line(left + 16, ly, left + width - 16, ly)

    # ------------------------------------------------------------------ #
    # Preview image (PNG) per-page renderer                               #
    # ------------------------------------------------------------------ #

    def _draw_preview_page(
        self,
        drawer: ImageDraw.ImageDraw,
        image_size: tuple[int, int],
        product_spec: dict,
        design_system: dict,
        page: dict,
    ) -> None:
        width, height = image_size
        primary = design_system["palette"]["primary"]
        secondary = design_system["palette"]["secondary"]
        page_type = str(page.get("page_type") or "worksheet")
        title_theme = str(product_spec.get("title_theme") or "Planner")
        page_title = str(page.get("title") or "Overview")
        body_lines = page.get("body", [])

        try:
            fnt_h2 = ImageFont.truetype(_SYSTEM_FONTS["Georgia-Bold"], 38)
            fnt_b1 = ImageFont.truetype(_SYSTEM_FONTS["Trebuchet-Bold"], 30)
            fnt_b2 = ImageFont.truetype(_SYSTEM_FONTS["Trebuchet"], 24)
            fnt_sm = ImageFont.truetype(_SYSTEM_FONTS["Trebuchet"], 20)
        except (IOError, OSError):
            fnt_h2 = fnt_b1 = fnt_b2 = fnt_sm = ImageFont.load_default()

        # Page frame
        drawer.rounded_rectangle((32, 32, width - 32, height - 32), radius=24, outline=secondary, width=6, fill="white")

        # Header band
        drawer.rectangle((32, 32, width - 32, 172), fill=primary)
        title_px = self._pil_fit_text(title_theme, fnt_h2, width - 76 - 76)
        drawer.text((76, 62), title_px, font=fnt_h2, fill="white")

        # Page-type badge
        badge_label = page_type.upper()
        try:
            badge_w = int(fnt_sm.getlength(badge_label)) + 28
        except Exception:
            badge_w = len(badge_label) * 15 + 28
        drawer.rounded_rectangle((76, 134, 76 + badge_w, 162), radius=8, fill=secondary)
        drawer.text((86, 136), badge_label, font=fnt_sm, fill=primary)

        # Sub-header strip
        drawer.rectangle((32, 172, width - 32, 216), fill=secondary)
        page_title_px = self._pil_fit_text(page_title, fnt_b1, width - 76 - 76)
        drawer.text((76, 178), page_title_px, font=fnt_b1, fill=primary)

        # Content area
        cy0, cy1 = 234, height - 90

        if page_type == "schedule":
            slots = body_lines if body_lines else [
                "6:00 AM", "8:00 AM", "10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM", "6:00 PM", "8:00 PM"
            ]
            n = min(8, len(slots))
            row_h = (cy1 - cy0) / n
            for i, slot in enumerate(slots[:n]):
                ry = int(cy0 + i * row_h)
                if i % 2 == 0:
                    drawer.rectangle((76, ry, width - 76, int(ry + row_h - 3)), fill="#F8FAFC")
                drawer.text((84, int(ry + row_h / 4)), self._pil_fit_text(str(slot), fnt_b2, 140), font=fnt_b2, fill=primary)
                drawer.line((240, int(ry + row_h - 4), width - 84, int(ry + row_h - 4)), fill="#E2E8F0", width=2)
                drawer.line((232, ry, 232, int(ry + row_h)), fill=secondary, width=3)

        elif page_type == "tracker":
            days = ["M", "T", "W", "T", "F", "S", "S"]
            hab_col = 380
            d_col_w = (width - 200 - hab_col) // 7
            drawer.text((84, cy0 + 8), "HABIT", font=fnt_sm, fill=primary)
            for j, d in enumerate(days):
                cx = int(hab_col + (j + 0.5) * d_col_w)
                drawer.text((cx - 8, cy0 + 8), d, font=fnt_b2, fill=primary)
            drawer.line((76, cy0 + 48, width - 76, cy0 + 48), fill=secondary, width=3)
            habits = body_lines if body_lines else [f"Habit {i + 1}" for i in range(5)]
            row_h = (cy1 - cy0 - 60) // 5
            for i in range(5):
                ry = cy0 + 60 + i * row_h
                if i % 2 == 0:
                    drawer.rectangle((76, ry, width - 76, ry + row_h - 3), fill="#F8FAFC")
                habit_raw = str(habits[i]) if i < len(habits) else f"Habit {i + 1}"
                habit_name = self._pil_fit_text(habit_raw, fnt_b2, hab_col - 84 - 8)
                drawer.text((84, int(ry + row_h * 0.25)), habit_name, font=fnt_b2, fill="#1E293B")
                for j in range(7):
                    cx = int(hab_col + (j + 0.5) * d_col_w)
                    cy_c = int(ry + row_h / 2)
                    drawer.ellipse((cx - 16, cy_c - 16, cx + 16, cy_c + 16), outline=secondary, width=3)

        elif page_type == "reflection":
            questions = body_lines if body_lines else [f"Reflection question {i + 1}" for i in range(3)]
            q_box_h = (cy1 - cy0) // 3
            for i in range(3):
                qy = cy0 + i * q_box_h
                drawer.rounded_rectangle((76, qy + 8, width - 76, qy + q_box_h - 8), radius=12, outline=secondary, width=3)
                q_raw = str(questions[i]) if i < len(questions) else f"Question {i + 1}"
                q_text = self._pil_fit_text(f"Q{i + 1}. {q_raw}", fnt_b2, width - 96 - 96)
                drawer.text((96, qy + 22), q_text, font=fnt_b2, fill=primary)
                for j in range(3):
                    ly = qy + 84 + j * 38
                    if ly < qy + q_box_h - 16:
                        drawer.line((96, ly, width - 96, ly), fill="#D1D5DB", width=2)

        else:  # worksheet
            z1h = int((cy1 - cy0) * 0.42)
            z2h = int((cy1 - cy0) * 0.36)
            z3h = (cy1 - cy0) - z1h - z2h - 24

            drawer.rounded_rectangle((76, cy0, width - 76, cy0 + z1h), radius=14, outline=secondary, width=3)
            drawer.text((94, cy0 + 12), "TODAY'S TOP PRIORITIES", font=fnt_sm, fill=primary)
            priorities = body_lines[:5] if body_lines else []
            for i in range(5):
                ty = cy0 + 56 + i * (z1h - 72) // 5
                drawer.ellipse((92, ty - 11, 118, ty + 11), outline=secondary, width=2)
                drawer.line((128, ty, width - 96, ty), fill="#CBD5E1", width=2)
                if i < len(priorities):
                    hint_px = self._pil_fit_text(str(priorities[i]), fnt_sm, width - 96 - 134)
                    drawer.text((134, ty - 14), hint_px, font=fnt_sm, fill="#64748B")

            z2y = cy0 + z1h + 14
            drawer.rounded_rectangle((76, z2y, width - 76, z2y + z2h), radius=14, outline=secondary, width=3)
            drawer.text((94, z2y + 12), "NOTES  &  BRAIN DUMP", font=fnt_sm, fill=primary)
            for j in range(5):
                ly = z2y + 56 + j * (z2h - 64) // 5
                drawer.line((94, ly, width - 96, ly), fill="#E2E8F0", width=2)

            z3y = z2y + z2h + 10
            if z3h > 30:
                drawer.rounded_rectangle((76, z3y, width - 76, z3y + z3h), radius=14, fill=primary)
                drawer.text((94, z3y + 10), "TODAY'S WIN  *", font=fnt_sm, fill="white")

        # Footer
        drawer.line((76, height - 68, width - 76, height - 68), fill=secondary, width=3)
        drawer.text((76, height - 56), "MoneyPrinter+ Digital Download", font=fnt_sm, fill="#94A3B8")

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _fit_text(self, pdf: canvas.Canvas, text: str, font_name: str, size: float, max_w: float) -> str:
        """Return as much of *text* as fits in *max_w* pts, breaking on word boundaries with '…'."""
        if pdf.stringWidth(text, font_name, size) <= max_w:
            return text
        words = text.split()
        for n in range(len(words) - 1, 0, -1):
            candidate = " ".join(words[:n]) + "\u2026"
            if pdf.stringWidth(candidate, font_name, size) <= max_w:
                return candidate
        # Last resort: shorten first word character by character
        s = words[0] if words else text
        while s and pdf.stringWidth(s + "\u2026", font_name, size) > max_w:
            s = s[:-1]
        return (s + "\u2026") if s else ""

    def _split_text(self, pdf: canvas.Canvas, text: str, font_name: str, size: float, max_w: float) -> list:
        """Word-wrap *text* into a list of lines each fitting within *max_w* pts."""
        from reportlab.lib.utils import simpleSplit
        return simpleSplit(text, font_name, size, max_w) or [""]

    @staticmethod
    def _pil_fit_text(text: str, font, max_px: int) -> str:
        """Return as much of *text* as fits in *max_px* pixels (PIL font), word-boundary aware."""
        try:
            if font.getlength(text) <= max_px:
                return text
            words = text.split()
            for n in range(len(words) - 1, 0, -1):
                candidate = " ".join(words[:n]) + "\u2026"
                if font.getlength(candidate) <= max_px:
                    return candidate
            s = words[0] if words else text
            while s and font.getlength(s + "\u2026") > max_px:
                s = s[:-1]
            return (s + "\u2026") if s else ""
        except Exception:
            return text

    def _register_fonts(self) -> set:
        registered: set[str] = set()
        for name, path in _SYSTEM_FONTS.items():
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    registered.add(name)
                except Exception:
                    pass
        return registered

    def _resolve_font(self, font_name: str | None, bold: bool) -> str:
        if bold and "Georgia-Bold" in self._registered_fonts:
            return "Georgia-Bold"
        if not bold and "Trebuchet" in self._registered_fonts:
            return "Trebuchet"
        normalized = str(font_name or "").strip().lower()
        if "times" in normalized:
            return "Times-Bold" if bold else "Times-Roman"
        if "courier" in normalized:
            return "Courier-Bold" if bold else "Courier"
        return "Helvetica-Bold" if bold else "Helvetica"

    def _hex_to_color(self, value: str | None, default):
        try:
            return colors.HexColor(str(value or ""))
        except ValueError:
            return default

    # Keep for backward compatibility with any direct callers or tests
    def _draw_panel(
        self,
        pdf: canvas.Canvas,
        left: float,
        bottom: float,
        width: float,
        height: float,
        heading: str,
        lines: list[str],
        heading_font: str,
        body_font: str,
        primary_color,
        secondary_color,
    ) -> None:
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(secondary_color)
        pdf.roundRect(left, bottom, width, height, 14, fill=1, stroke=1)
        pdf.setFillColor(primary_color)
        pdf.setFont(heading_font, 13)
        pdf.drawString(left + 16, bottom + height - 24, heading)
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        for index in range(6):
            y = bottom + height - 52 - index * 28
            pdf.line(left + 16, y, left + width - 16, y)
        pdf.setFont(body_font, 10)
        pdf.setFillColor(colors.HexColor("#64748B"))
        for index, line in enumerate(lines[:3]):
            pdf.drawString(left + 16, bottom + height - 46 - index * 28, str(line)[:42])
