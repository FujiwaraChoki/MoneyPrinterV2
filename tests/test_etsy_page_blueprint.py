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
from etsy.page_blueprint import PageBlueprintAgent


class EtsyPageBlueprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir, True)

    def make_run_dir(self) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "focus-planner")
        etsy_io.initialize_run_status(run_dir)
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "product_spec.json"),
            {
                "run_id": os.path.basename(run_dir),
                "product_type": "planner",
                "audience": "adults with ADHD",
                "title_theme": "Focus Planner",
                "page_count": 4,
                "page_size": "LETTER",
                "sections": [
                    {"name": "Daily Focus", "purpose": "planning priorities", "page_span": 2},
                    {"name": "Time Blocks", "purpose": "schedule management", "page_span": 1},
                    {"name": "Reflection", "purpose": "reflection", "page_span": 1},
                ],
                "style_notes": {
                    "font_family": "Helvetica",
                    "accent_color": "#4F7CAC",
                    "spacing_density": "medium",
                    "decor_style": "minimal",
                },
                "output_files": ["product/focus-planner.pdf"],
            },
        )
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "design_system.json"),
            {
                "run_id": os.path.basename(run_dir),
                "palette": {"primary": "#4F7CAC", "secondary": "#D9C6A5", "background": "#FFF9F1"},
                "typography": {"heading_font": "Helvetica-Bold", "body_font": "Helvetica"},
                "layout": {"template_name": "editorial-planner", "header_style": "banner", "page_frame_style": "rounded-border"},
                "mockup_style": {"background_color": "#F4EFE7", "scene_style": "desk-flatlay"},
            },
        )
        return run_dir

    def test_page_blueprint_agent_falls_back_to_product_spec_structure(self) -> None:
        run_dir = self.make_run_dir()
        agent = PageBlueprintAgent(text_generator=lambda prompt: {"unexpected": True})

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(len(payload["pages"]), 4)
        self.assertEqual(payload["pages"][0]["section_name"], "Daily Focus")
        self.assertEqual(payload["pages"][2]["page_type"], "schedule")
        self.assertTrue(payload["pages"][3]["body"])

    def test_page_blueprint_agent_normalizes_richer_live_payload_shape(self) -> None:
        run_dir = self.make_run_dir()
        agent = PageBlueprintAgent(
            text_generator=lambda prompt: {
                "pages": [
                    {
                        "page_kind": "worksheet",
                        "section": "Daily Focus",
                        "headline": "Morning Reset",
                        "prompts": [
                            "Choose the one task that matters most.",
                            "List two backup tasks.",
                        ],
                        "checklist": [
                            "Add a break block.",
                            "Mark your first start time.",
                        ],
                    },
                    {
                        "page_kind": "reflection",
                        "section": "Reflection",
                        "headline": "Shutdown Notes",
                        "reflection_questions": [
                            "What worked better than expected?",
                            "What felt heavy today?",
                        ],
                    },
                ]
            }
        )

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["pages"][0]["title"], "Morning Reset")
        self.assertEqual(payload["pages"][0]["page_type"], "worksheet")
        self.assertIn("Choose the one task that matters most.", payload["pages"][0]["body"])
        self.assertEqual(payload["pages"][1]["page_type"], "reflection")
        self.assertIn("What worked better than expected?", payload["pages"][1]["body"])

    def test_blueprint_prompt_includes_few_shot_example(self) -> None:
        run_dir = self.make_run_dir()
        product_spec = etsy_io.read_json(os.path.join(run_dir, "artifacts", "product_spec.json"))
        design_system = etsy_io.read_json(os.path.join(run_dir, "artifacts", "design_system.json"))
        agent = PageBlueprintAgent(text_generator=lambda p: {"pages": []})

        prompt = agent._build_prompt(product_spec, design_system)

        self.assertIn('"page_type"', prompt)
        self.assertIn('"schedule"', prompt)
        self.assertIn('"tracker"', prompt)
        self.assertIn('"reflection"', prompt)
        self.assertIn('4-5', prompt)