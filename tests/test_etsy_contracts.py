import os
import sys
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


import etsy.contracts as contracts


class EtsyContractsTests(unittest.TestCase):
    def test_validate_research_artifact_rejects_empty_opportunities(self) -> None:
        with self.assertRaisesRegex(ValueError, "opportunities"):
            contracts.validate_research_artifact(
                {
                    "run_id": "run-1",
                    "category": "planner",
                    "opportunities": [],
                    "selected_opportunity": "budget-planner",
                }
            )

    def test_validate_research_artifact_requires_selected_slug_membership(self) -> None:
        with self.assertRaisesRegex(ValueError, "selected_opportunity"):
            contracts.validate_research_artifact(
                {
                    "run_id": "run-1",
                    "category": "planner",
                    "opportunities": [
                        {
                            "idea_slug": "meal-planner",
                            "title": "Meal Planner",
                            "target_buyer": "parents",
                            "problem_solved": "weekly meal planning",
                            "score": 0.9,
                        }
                    ],
                    "selected_opportunity": "budget-planner",
                }
            )

    def test_validate_product_spec_rejects_non_hex_accent_color(self) -> None:
        with self.assertRaisesRegex(ValueError, "accent_color"):
            contracts.validate_product_spec_artifact(
                {
                    "run_id": "run-1",
                    "product_type": "planner",
                    "audience": "students",
                    "title_theme": "Budget",
                    "page_count": 3,
                    "page_size": "LETTER",
                    "sections": [{"name": "Weekly", "purpose": "tracking", "page_span": 3}],
                    "style_notes": {
                        "font_family": "Helvetica",
                        "accent_color": "blue",
                        "spacing_density": "medium",
                        "decor_style": "minimal",
                    },
                    "output_files": ["product/budget-planner.pdf"],
                }
            )

    def test_validate_product_spec_requires_non_empty_sections_and_positive_page_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_count"):
            contracts.validate_product_spec_artifact(
                {
                    "run_id": "run-1",
                    "product_type": "planner",
                    "audience": "students",
                    "title_theme": "Budget",
                    "page_count": 0,
                    "page_size": "LETTER",
                    "sections": [],
                    "style_notes": {
                        "font_family": "Helvetica",
                        "accent_color": "#4F7CAC",
                        "spacing_density": "medium",
                        "decor_style": "minimal",
                    },
                    "output_files": ["product/budget-planner.pdf"],
                }
            )

    def test_validate_run_status_rejects_unknown_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "status"):
            contracts.validate_run_status(
                {
                    "run_id": "run-1",
                    "status": "broken",
                    "current_stage": "research",
                    "last_successful_stage": "",
                    "failure_message": "",
                }
            )

    def test_validate_design_system_artifact_requires_hex_palette(self) -> None:
        with self.assertRaisesRegex(ValueError, "palette"):
            contracts.validate_design_system_artifact(
                {
                    "run_id": "run-1",
                    "palette": {
                        "primary": "blue",
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

    def test_validate_page_blueprint_requires_sequential_pages_and_body(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_number"):
            contracts.validate_page_blueprint_artifact(
                {
                    "run_id": "run-1",
                    "pages": [
                        {
                            "page_number": 2,
                            "page_type": "worksheet",
                            "section_name": "Daily Focus",
                            "title": "Daily Focus",
                            "body": ["Choose a top priority."],
                        }
                    ],
                }
            )

    def test_validate_mockup_manifest_requires_exactly_five_files(self) -> None:
        with self.assertRaisesRegex(ValueError, "mockup_files"):
            contracts.validate_mockup_manifest(
                {
                    "run_id": "run-1",
                    "mockup_files": ["mockups/cover.png"],
                    "cover_image": "mockups/cover.png",
                    "dimensions": {"width": 1600, "height": 1200},
                }
            )

    def test_validate_listing_manifest_requires_expected_files(self) -> None:
        with self.assertRaisesRegex(ValueError, "title_file"):
            contracts.validate_listing_manifest(
                {
                    "run_id": "run-1",
                    "title_file": "listing/titles.md",
                    "description_file": "listing/description.txt",
                    "tags_file": "listing/tags.txt",
                    "checklist_file": "listing/checklist.md",
                }
            )