"""WeasyPrint-based PDF renderer for Etsy digital planners."""

from __future__ import annotations

import os
import sys

# macOS: WeasyPrint's cffi bindings look for 'libgobject-2.0-0' at dlopen() time.
# Homebrew installs it at /opt/homebrew/lib/libgobject-2.0.0.dylib.
# Setting DYLD_LIBRARY_PATH before the import lets cffi find it regardless of
# whether the process was started with it in the environment (e.g. from main.py).
if sys.platform == "darwin":
    _homebrew_lib = "/opt/homebrew/lib"
    _current = os.environ.get("DYLD_LIBRARY_PATH", "")
    if _homebrew_lib not in _current.split(":"):
        os.environ["DYLD_LIBRARY_PATH"] = (
            f"{_homebrew_lib}:{_current}" if _current else _homebrew_lib
        )

import fitz  # PyMuPDF
import jinja2
import weasyprint

from etsy.contracts import validate_design_system_artifact
from etsy.contracts import validate_page_blueprint_artifact
from etsy.contracts import validate_render_manifest
from etsy.io import read_json
from etsy.io import write_json

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Map design-system font slugs / names → actual font-family for CSS
_FONT_MAP: dict[str, str] = {
    "helvetica-bold": "Lato",
    "helvetica": "Lato",
    "georgia-bold": "Playfair Display",
    "georgia": "Playfair Display",
    "trebuchet-bold": "Lato",
    "trebuchet": "Lato",
    "times-bold": "Playfair Display",
    "times-roman": "Playfair Display",
    "courier-bold": "Lato",
    "courier": "Lato",
    "playfair display": "Playfair Display",
    "playfair display bold": "Playfair Display",
    "lato": "Lato",
    "lato bold": "Lato",
}


class WeasyPrintRenderer:
    def __init__(self) -> None:
        self._registered_fonts: frozenset[str] = frozenset()
        self._jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(_TEMPLATES_DIR),
            autoescape=False,
        )

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

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

        preview_images = self._render_preview_images(
            os.path.join(run_dir, product_files[0]),
            run_dir,
        )

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

    # ------------------------------------------------------------------ #
    # PDF rendering                                                        #
    # ------------------------------------------------------------------ #

    def _render_pdf(
        self,
        path: str,
        product_spec: dict,
        design_system: dict,
        page_blueprint: dict,
    ) -> None:
        css = self._build_css(design_system)

        title_theme = str(product_spec.get("title_theme") or "Planner")
        audience = str(product_spec.get("audience") or "busy adults")
        sections = product_spec.get("sections", [])
        page_count = product_spec["page_count"]
        palette = design_system["palette"]

        page_pdfs: list[bytes] = []

        # Cover page
        cover_html = self._jinja_env.get_template("cover.html.j2").render(
            css=css,
            title=title_theme,
            audience=audience,
            sections=sections,
            page_count=page_count,
            palette=palette,
        )
        page_pdfs.append(self._html_to_pdf_bytes(cover_html))

        # Content pages
        for page in page_blueprint["pages"]:
            page_html = self._render_page_html(page, product_spec, design_system, css)
            page_pdfs.append(self._html_to_pdf_bytes(page_html))

        merged = self._merge_pdfs(page_pdfs)
        with open(path, "wb") as fh:
            fh.write(merged)

    def _render_page_html(
        self,
        page: dict,
        product_spec: dict,
        design_system: dict,
        css: str,
    ) -> str:
        page_type = str(page.get("page_type") or "worksheet")
        template_name = f"{page_type}.html.j2"
        # Fall back to worksheet if unknown page type
        if not os.path.exists(os.path.join(_TEMPLATES_DIR, template_name)):
            template_name = "worksheet.html.j2"

        title_theme = str(product_spec.get("title_theme") or "Planner")
        audience = str(product_spec.get("audience") or "busy adults")
        page_count = product_spec["page_count"]
        palette = design_system["palette"]

        return self._jinja_env.get_template(template_name).render(
            css=css,
            page_number=page.get("page_number", 1),
            page_count=page_count,
            title=str(page.get("title") or "Overview"),
            section_name=str(page.get("section_name") or "Section"),
            page_type=page_type,
            audience=audience,
            title_theme=title_theme,
            body=page.get("body", []),
            palette=palette,
        )

    def _build_css(self, design_system: dict) -> str:
        palette = design_system["palette"]
        typography = design_system.get("typography", {})
        heading_font = self._resolve_font(typography.get("heading_font"))
        body_font = self._resolve_font(typography.get("body_font"))
        return self._jinja_env.get_template("_base.css.j2").render(
            primary=palette.get("primary", "#4F7CAC"),
            secondary=palette.get("secondary", "#D9C6A5"),
            background=palette.get("background", "#FFF9F1"),
            heading_font=heading_font,
            body_font=body_font,
            fonts_dir=_FONTS_DIR,
        )

    def _resolve_font(self, font_name: str | None) -> str:
        key = str(font_name or "").strip().lower()
        return _FONT_MAP.get(key, "Lato")

    @staticmethod
    def _html_to_pdf_bytes(html: str) -> bytes:
        doc = weasyprint.HTML(string=html).write_pdf()
        return doc  # type: ignore[return-value]

    @staticmethod
    def _merge_pdfs(page_pdfs: list[bytes]) -> bytes:
        if len(page_pdfs) == 1:
            return page_pdfs[0]
        merged_doc = fitz.open()
        for pdf_bytes in page_pdfs:
            page_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            merged_doc.insert_pdf(page_doc)
            page_doc.close()
        merged_bytes: bytes = merged_doc.tobytes()
        merged_doc.close()
        return merged_bytes

    # ------------------------------------------------------------------ #
    # Preview images (extracted from rendered PDF via PyMuPDF)            #
    # ------------------------------------------------------------------ #

    def _render_preview_images(self, pdf_path: str, run_dir: str) -> list[str]:
        doc = fitz.open(pdf_path)
        preview_images: list[str] = []
        n_pages = min(4, doc.page_count)
        for i in range(n_pages):
            page = doc[i]
            # Scale to ~1200px wide (letter page is 8.5in @ 72dpi = 612pt)
            zoom = 1200 / 612
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            preview_filename = f"page-preview-{i + 1}.png"
            preview_path = os.path.join(run_dir, "product", preview_filename)
            os.makedirs(os.path.join(run_dir, "product"), exist_ok=True)
            pix.save(preview_path)
            preview_images.append(f"product/{preview_filename}")
        doc.close()
        return preview_images
