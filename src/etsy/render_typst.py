"""Typst-based PDF renderer for Etsy digital planners."""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import fitz  # PyMuPDF

from etsy.contracts import validate_design_system_artifact
from etsy.contracts import validate_page_blueprint_artifact
from etsy.contracts import validate_render_manifest
from etsy.io import read_json
from etsy.io import write_json

_TYPST_DIR = os.path.join(os.path.dirname(__file__), "typst")
_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
_MAIN_TYP = os.path.join(_TYPST_DIR, "main.typ")


def _require_typst() -> str:
    """Return path to the typst binary, raising if not found."""
    binary = shutil.which("typst")
    if binary is None:
        raise RuntimeError(
            "typst binary not found on PATH. Install via: brew install typst"
        )
    return binary


def _flatten_design_system(design_system: dict) -> dict:
    """Convert the nested design_system artifact to the flat dict Typst expects."""
    palette = design_system.get("palette", {})
    typography = design_system.get("typography", {})
    layout = design_system.get("layout", {})
    return {
        "primary": palette.get("primary", "#2E5944"),
        "secondary": palette.get("secondary", "#C9A84C"),
        "bg": palette.get("background", "#FAF7F2"),
        "text_dark": "#1A1A1A",
        "text_muted": "#7A7A6A",
        "rule_line": "#D8D4CB",
        "font_heading": typography.get("heading_font", "Playfair Display"),
        "font_body": typography.get("body_font", "DM Sans 9pt"),
        "font_label": "Lato",
        "template_family": layout.get("template_family", "clean-minimal"),
    }


class TypstRenderer:
    def __init__(self) -> None:
        self._typst_bin = _require_typst()
        self._registered_fonts: frozenset[str] = frozenset()

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
        flat_ds = _flatten_design_system(design_system)
        data = {
            "product_spec": product_spec,
            "design_system": flat_ds,
            "page_blueprint": page_blueprint,
        }
        data_json = json.dumps(data, ensure_ascii=False)

        result = subprocess.run(
            [
                self._typst_bin,
                "compile",
                _MAIN_TYP,
                path,
                "--root", os.path.dirname(_TYPST_DIR),  # src/etsy/
                "--font-path", _FONTS_DIR,
                "--input", f"data={data_json}",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"typst compile failed (exit {result.returncode}):\n"
                f"{result.stderr}"
            )

    # ------------------------------------------------------------------ #
    # Preview images                                                       #
    # ------------------------------------------------------------------ #

    def _render_preview_images(self, pdf_path: str, run_dir: str) -> list[str]:
        doc = fitz.open(pdf_path)
        preview_images: list[str] = []
        n_pages = min(4, doc.page_count)
        for i in range(n_pages):
            page = doc[i]
            zoom = 1200 / 612  # scale to ~1200px wide
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            preview_filename = f"page-preview-{i + 1}.png"
            preview_path = os.path.join(run_dir, "product", preview_filename)
            os.makedirs(os.path.join(run_dir, "product"), exist_ok=True)
            pix.save(preview_path)
            preview_images.append(f"product/{preview_filename}")
        doc.close()
        return preview_images
