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
from etsy.mockups import MockupAgent
from PIL import Image


class EtsyMockupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir, True)

    def make_run_dir_with_render_manifest(self) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        os.makedirs(os.path.join(run_dir, "product"), exist_ok=True)
        preview_paths = [
            os.path.join(run_dir, "product", "page-preview-1.png"),
            os.path.join(run_dir, "product", "page-preview-2.png"),
            os.path.join(run_dir, "product", "page-preview-3.png"),
        ]
        preview_colors = ["white", "#88B4E7", "#E7A488"]
        for path, color in zip(preview_paths, preview_colors):
            Image.new("RGB", (1200, 1200), color).save(path)
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "render_manifest.json"),
            {
                "run_id": os.path.basename(run_dir),
                "product_files": ["product/budget-planner.pdf"],
                "page_count": 3,
                "page_size": "LETTER",
                "preview_images": [
                    "product/page-preview-1.png",
                    "product/page-preview-2.png",
                    "product/page-preview-3.png",
                ],
                "design_template": "editorial-planner",
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
        return run_dir

    def test_mockup_agent_writes_exactly_five_pngs(self) -> None:
        agent = MockupAgent()
        run_dir = self.make_run_dir_with_render_manifest()

        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        self.assertEqual(manifest["run_id"], os.path.basename(run_dir))
        self.assertEqual(len(manifest["mockup_files"]), 5)
        self.assertIn(manifest["cover_image"], manifest["mockup_files"])
        self.assertEqual(set(manifest["dimensions"].keys()), {"width", "height"})
        for relative_path in manifest["mockup_files"]:
            self.assertTrue(relative_path.endswith(".png"))
            self.assertTrue(os.path.exists(os.path.join(run_dir, relative_path)))

    def test_mockup_agent_uses_inside_page_previews(self) -> None:
        agent = MockupAgent()
        run_dir = self.make_run_dir_with_render_manifest()

        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        cover_path = os.path.join(run_dir, manifest["mockup_files"][0])
        detail_path = os.path.join(run_dir, manifest["mockup_files"][3])

        with Image.open(cover_path) as cover_image, Image.open(detail_path) as detail_image:
            cover_sample = cover_image.getpixel((240, 220))
            detail_sample = detail_image.getpixel((240, 220))

        self.assertNotEqual(cover_sample, detail_sample)

    def test_mockup_stack_scene_shows_multiple_page_layers(self) -> None:
        agent = MockupAgent()
        run_dir = self.make_run_dir_with_render_manifest()
        manifest_path = agent.run(run_dir)
        manifest = etsy_io.read_json(manifest_path)

        stack_path = os.path.join(run_dir, manifest["mockup_files"][4])
        cover_path = os.path.join(run_dir, manifest["mockup_files"][0])

        with Image.open(stack_path) as stack_img, Image.open(cover_path) as cover_img:
            # Stack scene has pages fanned with offsets so its background color
            # is visible in more of the frame — the top-left and bottom-right
            # corners of stack should be the background (lavender), not white page.
            stack_tl = stack_img.getpixel((20, 20))
            cover_tl = cover_img.getpixel((20, 20))

        # Cover top-left corner should differ from stack top-left corner
        self.assertNotEqual(stack_tl, cover_tl)