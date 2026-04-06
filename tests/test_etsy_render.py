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


class EtsyRenderTests(unittest.TestCase):
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
        renderer = PdfRenderer()
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
        renderer = PdfRenderer()

        self.assertTrue(hasattr(renderer, "_registered_fonts"))
        self.assertIsInstance(renderer._registered_fonts, (set, frozenset))
        if os.path.exists("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"):
            self.assertIn("Georgia-Bold", renderer._registered_fonts)

    def test_renderer_writes_non_placeholder_pdf_bytes(self) -> None:
        renderer = PdfRenderer()
        run_dir = self.make_run_dir_with_product_spec()

        renderer.run(run_dir)

        pdf_path = os.path.join(run_dir, "product", "budget-planner.pdf")
        with open(pdf_path, "rb") as handle:
            pdf_bytes = handle.read()

        self.assertGreater(len(pdf_bytes), 500)
        self.assertIn(b"startxref", pdf_bytes)
        self.assertIn(b"/Type /Page", pdf_bytes)

    def test_renderer_writes_multiple_page_preview_images(self) -> None:
        renderer = PdfRenderer()
        run_dir = self.make_run_dir_with_product_spec()

        manifest_path = renderer.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        self.assertGreaterEqual(len(manifest["preview_images"]), 3)
        self.assertTrue(any(path.endswith("page-preview-1.png") for path in manifest["preview_images"]))
        self.assertTrue(any(path.endswith("page-preview-2.png") for path in manifest["preview_images"]))

    def test_weasyprint_importable(self):
        import weasyprint  # noqa: F401
        import jinja2      # noqa: F401
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