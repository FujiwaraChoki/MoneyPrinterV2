import os

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from etsy.contracts import validate_design_system_artifact
from etsy.contracts import validate_mockup_manifest
from etsy.io import read_json
from etsy.io import write_json

_FONT_PATHS = {
    "heading": "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "subheading": "/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf",
    "body": "/System/Library/Fonts/Supplemental/Trebuchet MS.ttf",
}


def _load_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(_FONT_PATHS[key], size)
    except Exception:
        return ImageFont.load_default(size=size)


class MockupAgent:
    def run(self, run_dir: str) -> str:
        render_manifest = read_json(os.path.join(run_dir, "artifacts", "render_manifest.json"))
        design_system = read_json(os.path.join(run_dir, "artifacts", "design_system.json"))
        validate_design_system_artifact(design_system)
        base_images = []
        for preview_relative_path in render_manifest["preview_images"]:
            preview_path = os.path.join(run_dir, preview_relative_path)
            with Image.open(preview_path) as preview_image:
                base_images.append(preview_image.convert("RGB"))

        mockup_specs = [
            ("listing-cover.png", "Cover", design_system["mockup_style"]["background_color"], 0),
            ("listing-flatlay.png", "Flat Lay", design_system["palette"]["background"], 1),
            ("listing-desk.png", "Desk View", design_system["palette"]["secondary"], 2),
            ("listing-detail.png", "Detail", "#eef3e8", 1),
            ("listing-stack.png", "Stack", "#f2e8ee", 2),
        ]

        mockup_files = []
        for filename, label, background_color, preview_index in mockup_specs:
            base_image = base_images[min(preview_index, len(base_images) - 1)]
            mockup_image = self._build_mockup(
                base_image,
                base_images,
                label,
                background_color,
                design_system["layout"]["template_name"],
                design_system["mockup_style"]["scene_style"],
                design_system["palette"]["primary"],
            )
            output_path = os.path.join(run_dir, "mockups", filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            mockup_image.save(output_path)
            mockup_files.append(os.path.relpath(output_path, run_dir))

        manifest = {
            "run_id": os.path.basename(run_dir),
            "mockup_files": mockup_files,
            "cover_image": mockup_files[0],
            "dimensions": {
                "width": 1600,
                "height": 1200,
            },
        }
        validate_mockup_manifest(manifest)
        manifest_path = os.path.join(run_dir, "artifacts", "mockup_manifest.json")
        write_json(manifest_path, manifest)
        return manifest_path

    def _build_mockup(
        self,
        base_image: Image.Image,
        all_images: list,
        label: str,
        background_color: str,
        template_name: str,
        scene_style: str,
        primary_color: str,
    ) -> Image.Image:
        if label == "Cover":
            return self._build_cover_scene(base_image, background_color, template_name, primary_color)
        elif label == "Flat Lay":
            return self._build_flatlay_scene(base_image, all_images, background_color, primary_color)
        elif label == "Desk View":
            return self._build_desk_scene(base_image, background_color, template_name, primary_color)
        elif label == "Detail":
            return self._build_detail_scene(base_image, background_color)
        else:
            return self._build_stack_scene(base_image, all_images, background_color, primary_color)

    # ------------------------------------------------------------------
    # Scene 1 — Cover: page centered-left, product info right panel
    # ------------------------------------------------------------------
    def _build_cover_scene(
        self,
        base_image: Image.Image,
        background_color: str,
        template_name: str,
        primary_color: str,
    ) -> Image.Image:
        canvas = Image.new("RGB", (1600, 1200), background_color)
        drawer = ImageDraw.Draw(canvas)

        page = base_image.copy()
        page.thumbnail((780, 900))
        pw, ph = page.size
        pad = 24
        frame_left = 140
        frame_top = (1200 - ph - pad * 2) // 2

        # Drop shadow
        _paste_shadow(drawer, frame_left + 14, frame_top + 14, pw + pad * 2, ph + pad * 2, radius=20, color="#c4bcb4")
        # White card
        drawer.rounded_rectangle(
            (frame_left, frame_top, frame_left + pw + pad * 2, frame_top + ph + pad * 2),
            radius=20, fill="white", outline="#e0d8ce", width=3,
        )
        canvas.paste(page, (frame_left + pad, frame_top + pad))

        # Right info panel
        rx = frame_left + pw + pad * 2 + 64
        fh1 = _load_font("heading", 38)
        fh2 = _load_font("subheading", 20)
        fbody = _load_font("body", 17)
        fbadge = _load_font("subheading", 13)

        # Accent line
        drawer.rectangle((rx, 148, rx + 5, 1052), fill=primary_color)
        rx += 28

        # Badge
        _draw_badge(drawer, rx, 200, "DIGITAL DOWNLOAD", fbadge, primary_color)

        # Title
        title_text = template_name.replace("-", " ").title()
        _draw_wrapped_text(drawer, title_text, rx, 274, fh1, max_chars=16, fill="#1a1614", line_gap=50)

        # Benefits
        benefits = ["✓  Instant Download", "✓  Print at Home", "✓  US Letter + A4 sizes"]
        for i, b in enumerate(benefits):
            drawer.text((rx, 490 + i * 52), b, font=fh2, fill="#3d352e")

        drawer.rectangle((rx, 710, rx + 360, 712), fill="#c8c0b8")
        drawer.text((rx, 730), "Printable PDF — ready to use", font=fbody, fill="#7a726a")
        drawer.text((rx, 762), "No subscription required", font=fbody, fill="#7a726a")

        return canvas

    # ------------------------------------------------------------------
    # Scene 2 — Flat Lay: two pages at opposing angles, overhead view
    # ------------------------------------------------------------------
    def _build_flatlay_scene(
        self,
        base_image: Image.Image,
        all_images: list,
        background_color: str,
        primary_color: str,
    ) -> Image.Image:
        canvas = Image.new("RGB", (1600, 1200), background_color)
        drawer = ImageDraw.Draw(canvas)

        fh2 = _load_font("subheading", 22)
        fbody = _load_font("body", 17)
        fbadge = _load_font("subheading", 13)

        # Back page (use second image if available)
        back_src = all_images[1] if len(all_images) > 1 else base_image
        back = back_src.copy()
        back.thumbnail((660, 760))
        back_rot = back.rotate(-10, expand=True, fillcolor=background_color)
        bx = 210 - (back_rot.width - back.width) // 2
        by = 90 - (back_rot.height - back.height) // 2
        _paste_shadow(drawer, bx + 10, by + 10, back_rot.width, back_rot.height, radius=16, color="#b8b0a6")
        canvas.paste(back_rot, (bx, by))

        # Main page rotated +7°
        main = base_image.copy()
        main.thumbnail((740, 860))
        main_rot = main.rotate(7, expand=True, fillcolor=background_color)
        mx = 108 - (main_rot.width - main.width) // 2
        my = 108 - (main_rot.height - main.height) // 2
        _paste_shadow(drawer, mx + 12, my + 12, main_rot.width, main_rot.height, radius=18, color="#a8a09a")
        canvas.paste(main_rot, (mx, my))

        # Right text
        rx = 1078
        _draw_badge(drawer, rx, 200, "FLAT LAY VIEW", fbadge, primary_color)
        drawer.text((rx, 290), "Every page printed", font=fh2, fill="#4a4038")
        drawer.text((rx, 326), "clean and crisp.", font=fh2, fill="#4a4038")
        drawer.text((rx, 398), "Professional layout — no", font=fbody, fill="#6a6059")
        drawer.text((rx, 428), "blurry fonts, ever.", font=fbody, fill="#6a6059")
        _draw_badge(drawer, rx, 510, "PRINTABLE", fbadge, primary_color)
        drawer.text((rx, 604), "US Letter + A4 included", font=fbody, fill="#6a6059")
        drawer.text((rx, 634), "in every download.", font=fbody, fill="#6a6059")

        return canvas

    # ------------------------------------------------------------------
    # Scene 3 — Desk View: slight tilt, lifestyle copy
    # ------------------------------------------------------------------
    def _build_desk_scene(
        self,
        base_image: Image.Image,
        background_color: str,
        template_name: str,
        primary_color: str,
    ) -> Image.Image:
        canvas = Image.new("RGB", (1600, 1200), background_color)
        drawer = ImageDraw.Draw(canvas)

        # Subtle desk texture via horizontal bands
        r0, g0, b0 = _hex_to_rgb(background_color)
        for row in range(15):
            y = row * 80
            mod = 6 if row % 2 == 0 else 0
            band = (max(0, r0 - mod), max(0, g0 - mod), max(0, b0 - mod))
            drawer.rectangle((0, y, 1600, y + 80), fill=band)

        fh1 = _load_font("heading", 42)
        fh2 = _load_font("subheading", 22)
        fbody = _load_font("body", 17)
        fbadge = _load_font("subheading", 13)

        # Page at -3° tilt
        page = base_image.copy()
        page.thumbnail((760, 880))
        page_rot = page.rotate(3, expand=True, fillcolor=background_color)
        px = 110
        py = (1200 - page_rot.height) // 2
        _paste_shadow(drawer, px + 14, py + 14, page_rot.width, page_rot.height, radius=20, color="#b0a898")
        canvas.paste(page_rot, (px, py))

        # Right panel copy
        rx = 1048
        _draw_badge(drawer, rx, 190, "DESK COMPANION", fbadge, primary_color)
        drawer.text((rx, 295), "YOUR NEW", font=fh1, fill="#1a1614")
        drawer.text((rx, 350), "DAILY RITUAL", font=fh1, fill=primary_color)
        drawer.text((rx, 450), "Wake up with a plan.", font=fh2, fill="#5e574f")
        drawer.text((rx, 490), "Track it. Own it.", font=fh2, fill="#5e574f")

        # Dot grid decoration
        for row in range(4):
            for col in range(7):
                cx = rx + col * 30
                cy = 594 + row * 30
                drawer.ellipse((cx, cy, cx + 9, cy + 9), fill="#c8c0b8")

        drawer.rectangle((rx, 730, rx + 370, 732), fill="#b8b0a6")
        drawer.text((rx, 752), "Print once. Use every day.", font=fbody, fill="#7a726a")
        _draw_badge(drawer, rx, 810, "INSTANT DOWNLOAD", fbadge, primary_color)

        return canvas

    # ------------------------------------------------------------------
    # Scene 4 — Detail: cropped zoom into page content with annotation
    # ------------------------------------------------------------------
    def _build_detail_scene(
        self,
        base_image: Image.Image,
        background_color: str,
    ) -> Image.Image:
        canvas = Image.new("RGB", (1600, 1200), background_color)
        drawer = ImageDraw.Draw(canvas)

        fh1 = _load_font("heading", 36)
        fh2 = _load_font("subheading", 20)
        fbody = _load_font("body", 17)
        fbadge = _load_font("subheading", 13)

        # Crop upper-left content zone and scale up for a sharp close-up
        sw, sh = base_image.size
        cx0, cy0 = int(sw * 0.05), int(sh * 0.05)
        cx1, cy1 = int(sw * 0.70), int(sh * 0.70)
        cropped = base_image.crop((cx0, cy0, cx1, cy1))
        target_w = 900
        target_h = int((cy1 - cy0) * target_w / (cx1 - cx0))
        zoomed = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        zy = max(0, (1200 - target_h) // 2)

        _paste_shadow(drawer, 8, zy + 8, target_w, target_h, radius=0, color="#c0b8b0")
        canvas.paste(zoomed, (0, zy))

        # Right side annotation panel
        rx = 960
        drawer.text((rx, 198), "INSIDE LOOK →", font=fh1, fill="#1a1614")
        drawer.rectangle((rx, 252, rx + 300, 255), fill="#1a1614")
        drawer.text((rx, 278), "See every detail before", font=fh2, fill="#5e574f")
        drawer.text((rx, 312), "you print.", font=fh2, fill="#5e574f")
        drawer.text((rx, 378), "Clean layout.", font=fbody, fill="#3d352e")
        drawer.text((rx, 410), "Plenty of writing space.", font=fbody, fill="#3d352e")
        drawer.text((rx, 442), "Thoughtful, intentional", font=fbody, fill="#3d352e")
        drawer.text((rx, 474), "design on every page.", font=fbody, fill="#3d352e")

        _draw_badge(drawer, rx, 570, "PRINT-READY", fbadge, "#4a7c59")
        drawer.text((rx, 660), "Designed at 300 DPI.", font=fbody, fill="#7a726a")
        drawer.text((rx, 692), "Prints perfectly at home.", font=fbody, fill="#7a726a")

        return canvas

    # ------------------------------------------------------------------
    # Scene 5 — Stack: fanned pages showing the full set
    # ------------------------------------------------------------------
    def _build_stack_scene(
        self,
        base_image: Image.Image,
        all_images: list,
        background_color: str,
        primary_color: str,
    ) -> Image.Image:
        canvas = Image.new("RGB", (1600, 1200), background_color)
        drawer = ImageDraw.Draw(canvas)

        fh1 = _load_font("heading", 40)
        fh2 = _load_font("subheading", 22)
        fbody = _load_font("body", 17)
        fbadge = _load_font("subheading", 13)

        thumb_size = (580, 700)
        anchor_x, anchor_y = 260, 148

        # Prepare up to 3 page thumbnails (back→front order)
        sources = []
        for i in range(min(3, len(all_images))):
            thumb = all_images[-(i + 1)].copy()
            thumb.thumbnail(thumb_size)
            sources.append(thumb)
        while len(sources) < 3:
            sources.append(sources[-1])

        # fan offsets: index 0 = back, 2 = front
        fan_offsets = [(60, 55), (32, 28), (0, 0)]
        fan_angles = [-9, -4, 0]
        shadow_colors = ["#b4aca4", "#bcb4ac", "#c8c2bc"]

        for idx in range(3):
            src = sources[idx]
            ox, oy = fan_offsets[idx]
            rotated = src.rotate(fan_angles[idx], expand=True, fillcolor=background_color)
            rx_off = (rotated.width - src.width) // 2
            ry_off = (rotated.height - src.height) // 2
            px = anchor_x + ox - rx_off
            py = anchor_y + oy - ry_off
            _paste_shadow(drawer, px + 10, py + 10, rotated.width, rotated.height, radius=14, color=shadow_colors[idx])
            canvas.paste(rotated, (px, py))

        # Right panel
        rx = 1052
        _draw_badge(drawer, rx, 188, "COMPLETE SET", fbadge, primary_color)
        drawer.text((rx, 272), "BUNDLE", font=fh1, fill="#1a1614")
        drawer.text((rx, 324), "INCLUDED", font=fh1, fill=primary_color)
        drawer.rectangle((rx, 382, rx + 340, 385), fill="#c0b8b0")
        page_count = len(all_images)
        drawer.text((rx, 408), f"{page_count} unique pages,", font=fh2, fill="#5e574f")
        drawer.text((rx, 446), "designed to work", font=fh2, fill="#5e574f")
        drawer.text((rx, 484), "together.", font=fh2, fill="#5e574f")
        _draw_badge(drawer, rx, 560, "ALL PAGES SHOWN", fbadge, primary_color)
        drawer.text((rx, 652), "Print as many copies as", font=fbody, fill="#7a726a")
        drawer.text((rx, 684), "you need. Forever.", font=fbody, fill="#7a726a")

        return canvas


# ---------------------------------------------------------------------------
# Module-level drawing helpers
# ---------------------------------------------------------------------------

def _paste_shadow(drawer: ImageDraw.ImageDraw, sx: int, sy: int, w: int, h: int, radius: int = 16, color: str = "#c4bcb4") -> None:
    """Draw a solid drop shadow rectangle on the canvas before pasting the image."""
    if radius > 0:
        drawer.rounded_rectangle((sx, sy, sx + w, sy + h), radius=radius, fill=color)
    else:
        drawer.rectangle((sx, sy, sx + w, sy + h), fill=color)


def _draw_badge(drawer: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont, color: str) -> None:
    """Pill-shaped accent badge with centered text."""
    w = len(text) * 10 + 36
    drawer.rounded_rectangle((x, y, x + w, y + 34), radius=9, fill=color)
    drawer.text((x + 18, y + 7), text, font=font, fill="white")


def _draw_wrapped_text(
    drawer: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    max_chars: int = 16,
    fill: str = "#1a1614",
    line_gap: int = 50,
) -> None:
    """Simple word-wrap by character budget."""
    words = text.split()
    line = ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) > max_chars and line:
            drawer.text((x, y), line, font=font, fill=fill)
            y += line_gap
            line = word
        else:
            line = candidate
    if line:
        drawer.text((x, y), line, font=font, fill=fill)


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)