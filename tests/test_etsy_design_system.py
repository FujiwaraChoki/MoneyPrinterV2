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
from etsy.design_system import DesignSystemAgent


class EtsyDesignSystemTests(unittest.TestCase):
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
        return run_dir

    def test_design_system_stage_writes_valid_design_artifact(self) -> None:
        agent = DesignSystemAgent(
            text_generator=lambda prompt: {
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
            }
        )
        run_dir = self.make_run_dir_with_product_spec()

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["run_id"], os.path.basename(run_dir))
        self.assertEqual(payload["layout"]["template_name"], "editorial-planner")
        self.assertEqual(payload["palette"]["primary"], "#4F7CAC")
        self.assertEqual(payload["mockup_style"]["scene_style"], "desk-flatlay")

    def test_design_system_stage_normalizes_live_model_payload_shape(self) -> None:
        agent = DesignSystemAgent(
            text_generator=lambda prompt: {
                "design_system_name": "Neuro-Flow Executive Function Framework",
                "version": "1.0.0",
                "core_philosophy": "Low-stimulation, high-clarity, cognitive-load reduction.",
                "palette": {
                    "description": "Muted, low-contrast earth tones.",
                    "swatches": {
                        "background_base": "#F9F7F2",
                        "primary_structural": "#4A5D5E",
                        "secondary_soft": "#A8B5A2",
                        "accent_focus": "#D4A373",
                    },
                },
                "typography": {
                    "font_families": {
                        "headings": {"font_name": "Montserrat"},
                        "body_text": {"font_name": "Open Sans"},
                    }
                },
                "layout": {
                    "description": "Modular, chunked design based on time-blocking principles.",
                    "components": {
                        "time_blocker": "Vertical column with soft-rounded borders.",
                    },
                },
                "mockup_style": {
                    "aesthetic": "Organic Minimalism / Soft Scandi",
                    "environment": {
                        "setting": "A clean wooden desk with soft morning light.",
                    },
                },
            }
        )
        run_dir = self.make_run_dir_with_product_spec()

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["palette"]["primary"], "#4A5D5E")
        self.assertEqual(payload["palette"]["background"], "#F9F7F2")
        self.assertEqual(payload["typography"]["heading_font"], "Montserrat")
        self.assertEqual(payload["typography"]["body_font"], "Open Sans")
        self.assertEqual(payload["layout"]["template_name"], "neuro-flow-executive-function-framework")
        self.assertEqual(payload["layout"]["page_frame_style"], "soft-rounded")
        self.assertEqual(payload["mockup_style"]["background_color"], "#F9F7F2")
        self.assertEqual(payload["mockup_style"]["scene_style"], "organic-minimalism-soft-scandi")

    def test_design_system_infers_template_family_from_product_context_when_missing(self) -> None:
        run_dir = etsy_io.create_run_directory(self.base_dir, "bridal-wellness")
        etsy_io.initialize_run_status(run_dir)
        etsy_io.write_json(
            os.path.join(run_dir, "artifacts", "product_spec.json"),
            {
                "run_id": os.path.basename(run_dir),
                "product_type": "planner",
                "audience": "Boho-style brides seeking holistic wellness and stress management during wedding planning",
                "title_theme": "Ethereal Bridal Wellness & Mindful Planning Sanctuary",
                "page_count": 12,
                "page_size": "LETTER",
                "sections": [
                    {"name": "Mindful Intentions", "purpose": "bridal wellness", "page_span": 4}
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
        agent = DesignSystemAgent(
            text_generator=lambda prompt: {
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
                },
                "mockup_style": {
                    "background_color": "#F4F1EA",
                    "scene_style": "flat-lay-with-dried-eucalyptus-silk-ribbons-and-soft-natural-sunlight-shadows",
                },
            }
        )

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["layout"]["template_family"], "cottagecore")