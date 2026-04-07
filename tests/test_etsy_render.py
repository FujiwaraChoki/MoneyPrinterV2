import os
import shutil
import sys
import tempfile
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


import etsy.io as etsy_io
from etsy.render import PdfRenderer

try:
    from etsy.render_weasyprint import WeasyPrintRenderer as _WeasyPrintRenderer
    _WEASYPRINT_AVAILABLE = True
except ImportError:
    _WeasyPrintRenderer = None  # type: ignore
    _WEASYPRINT_AVAILABLE = False

try:
    from etsy.render_typst import TypstRenderer as _TypstRenderer
    _TYPST_AVAILABLE = True
except ImportError:
    _TypstRenderer = None  # type: ignore
    _TYPST_AVAILABLE = False


class EtsyRenderTests(unittest.TestCase):
    renderer_class = PdfRenderer

    def setUp(self) -> None:
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir, True)

    def make_run_dir_with_product_spec(self) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "product_spec.json"),
            {
                "run_id": os.path.basename(run_dir),
                "product_type": "planner",
                "audience": "busy adults",
                "title_theme": "Budget Planner",
                "page_count": 3,
                "page_size": "LETTER",
                "sections": [
                    {"name": "Monthly Overview", "purpose": "budget planning", "page_span": 3}
                ],
                "style_notes": {
                    "font_family": "Helvetica",
                    "accent_color": "#4F7CAC",
                    "spacing_density": "medium",
                    "decor_style": "minimal",
                },
                "output_files": ["product/budget-planner.pdf"],
            },
        )
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "design_system.json"),
            {
                "run_id": os.path.basename(run_dir),
                "palette": {
                    "primary": "#4F7CAC",
                    "secondary": "#D9C6A5",
                    "background": "#FFF9F1",
                },
                "typography": {
                    "heading_font": "Helvetica-Bold",
                    "body_font": "Helvetica",
                },
                "layout": {
                    "template_name": "editorial-planner",
                    "header_style": "banner",
                    "page_frame_style": "rounded-border",
                },
                "mockup_style": {
                    "background_color": "#F4EFE7",
                    "scene_style": "desk-flatlay",
                },
            },
        )
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "page_blueprint.json"),
            {
                "run_id": os.path.basename(run_dir),
                "pages": [
                    {
                        "page_number": 1,
                        "page_type": "worksheet",
                        "section_name": "Monthly Overview",
                        "title": "Monthly Overview",
                        "body": [
                            "Define your financial goal for the month.",
                            "List bills and due dates.",
                            "Capture wins and adjustments.",
                        ],
                    },
                    {
                        "page_number": 2,
                        "page_type": "tracker",
                        "section_name": "Monthly Overview",
                        "title": "Expense Tracking",
                        "body": [
                            "Record category totals.",
                            "Compare planned versus actual.",
                            "Mark one action for next week.",
                        ],
                    },
                    {
                        "page_number": 3,
                        "page_type": "reflection",
                        "section_name": "Monthly Overview",
                        "title": "Review & Reset",
                        "body": [
                            "Summarize what worked.",
                            "Note one spending trigger.",
                            "Choose a reset step.",
                        ],
                    },
                ],
            },
        )
        return run_dir

    def test_renderer_writes_pdf_and_render_manifest(self) -> None:
        renderer = self.renderer_class()
        run_dir = self.make_run_dir_with_product_spec()

        manifest_path = renderer.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        self.assertEqual(manifest["run_id"], os.path.basename(run_dir))
        self.assertTrue(os.path.exists(os.path.join(run_dir, "product", "budget-planner.pdf")))
        self.assertEqual(manifest["product_files"], ["product/budget-planner.pdf"])
        self.assertEqual(manifest["page_count"], 3)
        self.assertEqual(manifest["page_size"], "LETTER")
        self.assertEqual(manifest["design_template"], "editorial-planner")
        self.assertTrue(manifest["preview_images"])
        for relative_path in manifest["preview_images"]:
            self.assertTrue(os.path.exists(os.path.join(run_dir, relative_path)))

    def test_renderer_stores_registered_fonts_attribute(self) -> None:
        renderer = self.renderer_class()

        self.assertTrue(hasattr(renderer, "_registered_fonts"))
        self.assertIsInstance(renderer._registered_fonts, (set, frozenset))
        if os.path.exists("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"):
            self.assertIn("Georgia-Bold", renderer._registered_fonts)

    def test_renderer_writes_non_placeholder_pdf_bytes(self) -> None:
        renderer = self.renderer_class()
        run_dir = self.make_run_dir_with_product_spec()

        renderer.run(run_dir)

        pdf_path = os.path.join(run_dir, "product", "budget-planner.pdf")
        with open(pdf_path, "rb") as handle:
            pdf_bytes = handle.read()

        self.assertGreater(len(pdf_bytes), 500)
        self.assertIn(b"startxref", pdf_bytes)
        self.assertIn(b"/Type /Page", pdf_bytes)

    def test_renderer_writes_multiple_page_preview_images(self) -> None:
        renderer = self.renderer_class()
        run_dir = self.make_run_dir_with_product_spec()

        manifest_path = renderer.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        self.assertGreaterEqual(len(manifest["preview_images"]), 3)
        self.assertTrue(any(path.endswith("page-preview-1.png") for path in manifest["preview_images"]))
        self.assertTrue(any(path.endswith("page-preview-2.png") for path in manifest["preview_images"]))

    def test_weasyprint_importable(self):
        import fitz        # noqa: F401

    def test_font_files_exist(self):
        import pathlib
        fonts_dir = pathlib.Path(__file__).parent.parent / "src" / "etsy" / "fonts"
        for name in [
            "PlayfairDisplay-Regular.ttf",
            "PlayfairDisplay-Bold.ttf",
            "Lato-Regular.ttf",
            "Lato-Bold.ttf",
        ]:
            self.assertTrue((fonts_dir / name).exists(), f"Missing font: {name}")


@unittest.skipUnless(_WEASYPRINT_AVAILABLE, "render_weasyprint not yet implemented")
class WeasyPrintRenderTests(EtsyRenderTests):
    """Run the full EtsyRenderTests suite with WeasyPrintRenderer."""

    renderer_class = _WeasyPrintRenderer  # type: ignore

    def test_renderer_stores_registered_fonts_attribute(self) -> None:
        # WeasyPrintRenderer uses bundled fonts, not registered system fonts
        renderer = self.renderer_class()
        self.assertTrue(hasattr(renderer, "_registered_fonts"))
        self.assertIsInstance(renderer._registered_fonts, (set, frozenset))

    def test_renderer_writes_non_placeholder_pdf_bytes(self) -> None:
        # WeasyPrint serializes /Type/Page without a space; override to accept both forms.
        renderer = self.renderer_class()
        run_dir = self.make_run_dir_with_product_spec()

        renderer.run(run_dir)

        pdf_path = os.path.join(run_dir, "product", "budget-planner.pdf")
        with open(pdf_path, "rb") as handle:
            pdf_bytes = handle.read()

        self.assertGreater(len(pdf_bytes), 500)
        self.assertIn(b"startxref", pdf_bytes)
        # WeasyPrint writes /Type/Page (no space); ReportLab writes /Type /Page
        self.assertTrue(
            b"/Type/Page" in pdf_bytes or b"/Type /Page" in pdf_bytes,
            "Expected /Type/Page or /Type /Page in PDF bytes",
        )

@unittest.skipUnless(_TYPST_AVAILABLE, "render_typst requires typst binary")
class TypstRenderTests(EtsyRenderTests):
    """Run the full EtsyRenderTests suite with TypstRenderer."""

    renderer_class = _TypstRenderer  # type: ignore

    def test_typst_binary_found(self) -> None:
        import shutil
        self.assertIsNotNone(shutil.which("typst"), "typst binary not on PATH")

    def test_renderer_stores_registered_fonts_attribute(self) -> None:
        renderer = self.renderer_class()
        self.assertTrue(hasattr(renderer, "_registered_fonts"))
        self.assertIsInstance(renderer._registered_fonts, frozenset)

    def test_weasyprint_importable(self):
        # Not applicable for Typst renderer — just check fitz is present
        import fitz  # noqa: F401

    def test_typst_cover_uses_family_specific_heading_copy(self) -> None:
        import fitz

        renderer = self.renderer_class()
        run_dir = self.make_run_dir_with_product_spec()

        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "product_spec.json"),
            {
                "run_id": os.path.basename(run_dir),
                "product_type": "planner",
                "audience": "Boho-style brides seeking holistic wellness and stress management during wedding planning",
                "title_theme": "Ethereal Bridal Wellness & Mindful Planning Sanctuary",
                "page_count": 6,
                "page_size": "LETTER",
                "sections": [
                    {"name": "Mindful Intentions", "purpose": "Setting emotional goals and wedding vision alignment", "page_span": 2},
                    {"name": "Holistic Health Tracker", "purpose": "Monitoring sleep, hydration, nutrition, and movement", "page_span": 2},
                    {"name": "Ritual & Self-Care Log", "purpose": "Scheduling daily affirmations and skincare rituals", "page_span": 2},
                ],
                "style_notes": {
                    "font_family": "Playfair Display and Montserrat",
                    "accent_color": "#D4AF37",
                    "spacing_density": "airy",
                    "decor_style": "bohemian botanical with line-art wildflowers and earthy terracotta tones",
                },
                "output_files": ["product/bridal-wellness.pdf"],
            },
        )
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "design_system.json"),
            {
                "run_id": os.path.basename(run_dir),
                "palette": {
                    "primary": "#D4AF37",
                    "secondary": "#E8D7BC",
                    "background": "#F9F7F2",
                },
                "typography": {
                    "heading_font": "Cinzel Decorative",
                    "body_font": "Montserrat Light",
                },
                "layout": {
                    "template_name": "ethereal-wellness-sanctuary-planner",
                    "header_style": "minimalist-serif-with-botanical-line-art-accents",
                    "page_frame_style": "delicate-gold-foil-thin-border-with-organic-leaf-motifs",
                    "template_family": "cottagecore",
                },
                "mockup_style": {
                    "background_color": "#F4F1EA",
                    "scene_style": "flat-lay-with-dried-eucalyptus-silk-ribbons-and-soft-natural-sunlight-shadows",
                },
            },
        )

        manifest_path = renderer.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)
        pdf_path = os.path.join(run_dir, manifest["product_files"][0])

        document = fitz.open(pdf_path)
        try:
            first_page_text = document[0].get_text()
        finally:
            document.close()

        self.assertIn("Ethereal Bridal Wellness", first_page_text)
        self.assertIn("GatheredInside", first_page_text.replace(" ", ""))
