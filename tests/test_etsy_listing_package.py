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
from etsy.listing_package import ListingPackageAgent


class EtsyListingPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir, True)

    def make_run_dir_with_mockups(self) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "research.json"),
            {
                "run_id": os.path.basename(run_dir),
                "category": "planner",
                "opportunities": [
                    {
                        "idea_slug": "budget-planner",
                        "title": "Budget Planner",
                        "target_buyer": "busy adults",
                        "problem_solved": "monthly budgeting",
                        "score": 0.92,
                    }
                ],
                "selected_opportunity": "budget-planner",
            },
        )
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
            os.path.join(run_dir, "artifacts", "render_manifest.json"),
            {
                "run_id": os.path.basename(run_dir),
                "product_files": ["product/budget-planner.pdf"],
                "page_count": 3,
                "page_size": "LETTER",
                "preview_images": ["product/budget-planner-preview.png"],
                "design_template": "editorial-planner",
            },
        )
        mockup_files = []
        for index in range(5):
            relative_path = f"mockups/mockup-{index + 1}.png"
            absolute_path = os.path.join(run_dir, relative_path)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, "wb") as handle:
                handle.write(b"png")
            mockup_files.append(relative_path)
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "mockup_manifest.json"),
            {
                "run_id": os.path.basename(run_dir),
                "mockup_files": mockup_files,
                "cover_image": mockup_files[0],
                "dimensions": {"width": 1600, "height": 1200},
            },
        )
        return run_dir

    def test_listing_package_writes_listing_files_and_manifest(self) -> None:
        agent = ListingPackageAgent()
        run_dir = self.make_run_dir_with_mockups()

        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        self.assertEqual(manifest["run_id"], os.path.basename(run_dir))
        for key in ("title_file", "description_file", "tags_file", "checklist_file"):
            relative_path = manifest[key]
            absolute_path = os.path.join(run_dir, relative_path)
            self.assertTrue(os.path.exists(absolute_path))
            with open(absolute_path, "r", encoding="utf-8") as handle:
                self.assertTrue(handle.read().strip())

        with open(os.path.join(run_dir, manifest["title_file"]), "r", encoding="utf-8") as handle:
            self.assertGreaterEqual(len([line for line in handle.read().splitlines() if line.strip()]), 3)

    def test_listing_package_builds_structured_description_copy(self) -> None:
        agent = ListingPackageAgent()
        run_dir = self.make_run_dir_with_mockups()

        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        with open(os.path.join(run_dir, manifest["description_file"]), "r", encoding="utf-8") as handle:
            description = handle.read()

        self.assertIn("WHAT'S INCLUDED", description)
        self.assertIn("WHY YOU'LL LOVE IT", description)
        self.assertIn("HOW TO USE", description)
        self.assertIn("3-page LETTER", description)
        self.assertIn("Monthly Overview", description)