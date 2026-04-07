import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


import etsy.io as etsy_io
from etsy.design_system import DesignSystemAgent
from etsy.listing_package import ListingPackageAgent
from etsy.mockups import MockupAgent
from etsy.page_blueprint import PageBlueprintAgent
from etsy.product_spec import ProductSpecAgent
from etsy.render import PdfRenderer
from etsy.research import ResearchAgent
from etsy.pipeline import EtsyPipeline


class EtsyPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base_dir, True)

    def make_existing_run(self, last_successful_stage: str, status: str) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        etsy_io.update_run_status(
            run_dir,
            status=status,
            current_stage=last_successful_stage,
            last_successful_stage=last_successful_stage,
            failure_message="boom" if status == "failed" else "",
        )
        return run_dir

    def make_run_dir(self) -> str:
        run_dir = etsy_io.create_run_directory(self.base_dir, "budget-planner")
        etsy_io.initialize_run_status(run_dir)
        return run_dir

    def make_run_dir_with_research(self) -> str:
        run_dir = self.make_run_dir()
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
        return run_dir

    def test_resume_uses_first_incomplete_stage(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock())
        run_dir = self.make_existing_run(last_successful_stage="research", status="failed")

        with patch.object(pipeline, "run_stage", return_value=None) as run_stage_mock:
            pipeline.resume(run_dir)

        run_stage_mock.assert_any_call("product_spec", run_dir)

    def test_new_run_executes_stages_in_order(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock())

        with patch.object(pipeline, "run_stage", return_value=None) as run_stage_mock:
            pipeline.start_new_run(self.base_dir, "budget-planner")

        self.assertEqual(
            [call.args[0] for call in run_stage_mock.call_args_list[:4]],
            ["research", "product_spec", "design_system", "page_blueprint"],
        )

    def test_resume_discovery_lists_runs_in_reverse_chronological_order(self) -> None:
        first_dir = os.path.join(self.base_dir, "20260405-110000-a")
        second_dir = os.path.join(self.base_dir, "20260405-120000-b")
        malformed_dir = os.path.join(self.base_dir, "malformed")

        for path in (first_dir, second_dir, malformed_dir):
            os.makedirs(os.path.join(path, "artifacts"), exist_ok=True)

        etsy_io.write_json(
            os.path.join(first_dir, "artifacts", "run_status.json"),
            {
                "run_id": "20260405-110000-a",
                "status": "failed",
                "current_stage": "research",
                "last_successful_stage": "research",
                "failure_message": "first",
            },
        )
        etsy_io.write_json(
            os.path.join(second_dir, "artifacts", "run_status.json"),
            {
                "run_id": "20260405-120000-b",
                "status": "failed",
                "current_stage": "research",
                "last_successful_stage": "research",
                "failure_message": "second",
            },
        )

        runs = etsy_io.discover_runs(self.base_dir)

        self.assertEqual([run["run_id"] for run in runs], ["20260405-120000-b", "20260405-110000-a"])
        self.assertFalse(any(run["run_id"] == "malformed" for run in runs))

    def test_run_status_updates_after_successful_stage(self) -> None:
        run_dir = self.make_run_dir()
        research_agent = Mock(run=Mock(return_value=os.path.join(run_dir, "artifacts", "research.json")))
        pipeline = EtsyPipeline(research_agent, Mock(), Mock(), Mock(), Mock(), Mock(), Mock())

        pipeline.run_stage("research", run_dir)

        status = etsy_io.read_json(os.path.join(run_dir, "artifacts", "run_status.json"))
        self.assertEqual(status["current_stage"], "research")
        self.assertEqual(status["last_successful_stage"], "research")

    def test_failed_stage_marks_run_failed_and_sets_failure_message(self) -> None:
        pipeline = EtsyPipeline(Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock())
        run_dir = self.make_run_dir()

        with patch.object(pipeline.research_agent, "run", side_effect=ValueError("bad research artifact")):
            with self.assertRaisesRegex(ValueError, "bad research artifact"):
                pipeline.run_stage("research", run_dir)

        status = etsy_io.read_json(os.path.join(run_dir, "artifacts", "run_status.json"))
        self.assertEqual(status["status"], "failed")
        self.assertIn("bad research artifact", status["failure_message"])

    def test_research_stage_writes_valid_research_artifact(self) -> None:
        agent = ResearchAgent(
            text_generator=lambda prompt: {
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
            }
        )
        run_dir = self.make_run_dir()

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["run_id"], os.path.basename(run_dir))
        self.assertEqual(payload["category"], "planner")
        self.assertTrue(payload["opportunities"])
        self.assertIn(payload["selected_opportunity"], [item["idea_slug"] for item in payload["opportunities"]])

    def test_research_stage_normalizes_live_model_payload_shape(self) -> None:
        agent = ResearchAgent(
            text_generator=lambda prompt: {
                "category": "Digital Productivity Tools",
                "opportunities": [
                    {
                        "rank": 1,
                        "type": "planner",
                        "niche": "ADHD Neurodivergent Daily Planning",
                        "search_volume": "High",
                        "competition": "Medium",
                        "profit_potential": "High",
                    },
                    {
                        "rank": 2,
                        "type": "tracker",
                        "niche": "Micro-Habit & Dopamine Reward Tracking",
                        "search_volume": "Medium",
                        "competition": "Low",
                        "profit_potential": "Medium",
                    },
                ],
                "selected_opportunity": {
                    "rank": 1,
                    "type": "planner",
                    "niche": "ADHD Neurodivergent Daily Planning",
                    "strategy": "Focus on high-contrast visuals and low-friction layouts.",
                },
            }
        )
        run_dir = self.make_run_dir()

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["category"], "planner")
        self.assertEqual(payload["selected_opportunity"], "adhd-neurodivergent-daily-planning")
        self.assertEqual(payload["opportunities"][0]["idea_slug"], "adhd-neurodivergent-daily-planning")
        self.assertEqual(payload["opportunities"][0]["title"], "ADHD Neurodivergent Daily Planning")

    def test_research_stage_normalizes_alternate_ideas_key_and_missing_selection(self) -> None:
        agent = ResearchAgent(
            text_generator=lambda prompt: {
                "category": "Printable productivity bundles",
                "ideas": [
                    {
                        "title": "Wedding Budget Planner",
                        "target_buyer": "engaged couples",
                        "problem_solved": "track venue, vendor, and decor spending",
                        "score": 0.88,
                    },
                    {
                        "title": "Move Prep Checklist",
                        "target_buyer": "busy households",
                        "problem_solved": "organize a home move without missed tasks",
                        "score": 0.61,
                    },
                ],
            }
        )
        run_dir = self.make_run_dir()

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["selected_opportunity"], "wedding-budget-planner")
        self.assertEqual(payload["opportunities"][0]["idea_slug"], "wedding-budget-planner")
        self.assertEqual(payload["category"], "planner")

    def test_research_stage_falls_back_to_first_ranked_opportunity_when_selection_misses(self) -> None:
        agent = ResearchAgent(
            text_generator=lambda prompt: {
                "category": "planner",
                "opportunities": [
                    {
                        "idea_slug": "adhd-daily-planner",
                        "title": "ADHD Daily Planner",
                        "target_buyer": "neurodivergent adults",
                        "problem_solved": "reduce planning overwhelm",
                        "score": 0.95,
                    },
                    {
                        "idea_slug": "executive-function-checklist",
                        "title": "Executive Function Checklist",
                        "target_buyer": "students",
                        "problem_solved": "stay on top of routines",
                        "score": 0.72,
                    },
                ],
                "selected_opportunity": "ADHD planner for adults",
            }
        )
        run_dir = self.make_run_dir()

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["selected_opportunity"], "adhd-daily-planner")
        self.assertEqual(payload["opportunities"][0]["idea_slug"], "adhd-daily-planner")

    def test_product_spec_stage_writes_valid_product_spec(self) -> None:
        run_dir = self.make_run_dir_with_research()
        agent = ProductSpecAgent(
            text_generator=lambda prompt: {
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
            }
        )

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["run_id"], os.path.basename(run_dir))
        self.assertEqual(payload["product_type"], "planner")
        self.assertEqual(payload["title_theme"], "Budget Planner")
        self.assertGreater(payload["page_count"], 0)
        self.assertEqual(set(payload["sections"][0].keys()), {"name", "purpose", "page_span"})
        self.assertEqual(payload["output_files"], ["product/budget-planner.pdf"])
        self.assertEqual(payload["style_notes"]["accent_color"], "#4F7CAC")

    def test_product_spec_stage_normalizes_live_model_payload_shape(self) -> None:
        run_dir = self.make_run_dir_with_research()
        agent = ProductSpecAgent(
            text_generator=lambda prompt: {
                "opportunity_id": "adhd-neurodivergent-daily-planning",
                "product_type": "Digital Planner / Printable PDF",
                "audience": {
                    "primary": "Neurodivergent adults with ADHD",
                    "secondary": "Students and professionals seeking executive function support",
                },
                "title_theme": "Low-Dopamine/Low-Stimulation Executive Function Daily Planner",
                "page_count": 12,
                "page_size": ["A4", "US Letter", "A5"],
                "sections": [
                    {
                        "section_name": "Daily Focus & Prioritization",
                        "elements": [
                            "Top 3 Non-Negotiables",
                            "Brain Dump area",
                            "Dopamine Menu",
                        ],
                    },
                    {
                        "section_name": "Time Management",
                        "elements": ["Time-blocking schedule"],
                    },
                ],
                "style_notes": {
                    "aesthetic": "Minimalist, clean, and decluttered",
                    "color_palette": "Muted tones, pastel or earth tones",
                    "typography": "Sans-serif, highly legible, generous white space",
                    "ux_design": "Reduce visual clutter and use clear hierarchies.",
                },
                "output_files": [
                    "Daily_Planner_US_Letter.pdf",
                    "Daily_Planner_A4.pdf",
                ],
            }
        )

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["product_type"], "planner")
        self.assertEqual(payload["audience"], "Neurodivergent adults with ADHD")
        self.assertEqual(payload["page_size"], "LETTER")
        self.assertEqual(payload["sections"][0]["name"], "Daily Focus & Prioritization")
        self.assertTrue(all(path.startswith("product/") for path in payload["output_files"]))
        self.assertRegex(payload["style_notes"]["accent_color"], r"^#[0-9A-Fa-f]{6}$")

    def test_design_system_stage_writes_valid_design_artifact(self) -> None:
        run_dir = self.make_run_dir()
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

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(payload["run_id"], os.path.basename(run_dir))
        self.assertEqual(payload["layout"]["template_name"], "editorial-planner")

    def test_page_blueprint_stage_writes_valid_page_artifact(self) -> None:
        run_dir = self.make_run_dir()
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
                    {"name": "Monthly Overview", "purpose": "budget planning", "page_span": 2},
                    {"name": "Review", "purpose": "reflection", "page_span": 1},
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

        agent = PageBlueprintAgent(
            text_generator=lambda prompt: {
                "pages": [
                    {
                        "page_number": 1,
                        "page_type": "worksheet",
                        "section_name": "Monthly Overview",
                        "title": "Monthly Overview",
                        "body": ["Set your target.", "Track fixed costs.", "List priorities."],
                    },
                    {
                        "page_number": 2,
                        "page_type": "tracker",
                        "section_name": "Monthly Overview",
                        "title": "Expense Tracking",
                        "body": ["Log each purchase.", "Mark category.", "Review remaining budget."],
                    },
                    {
                        "page_number": 3,
                        "page_type": "reflection",
                        "section_name": "Review",
                        "title": "Month-End Review",
                        "body": ["Highlight wins.", "Identify one lesson.", "Choose a next step."],
                    },
                ]
            }
        )

        artifact_path = agent.run(run_dir)
        payload = etsy_io.read_json(artifact_path)

        self.assertEqual(len(payload["pages"]), 3)
        self.assertEqual(payload["pages"][0]["title"], "Monthly Overview")
        self.assertEqual(payload["pages"][2]["page_type"], "reflection")

    def test_concrete_pipeline_completes_end_to_end_with_stubbed_generators(self) -> None:
        pipeline = EtsyPipeline(
            ResearchAgent(
                text_generator=lambda prompt: {
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
                }
            ),
            ProductSpecAgent(
                text_generator=lambda prompt: {
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
                }
            ),
            DesignSystemAgent(
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
            ),
            PageBlueprintAgent(
                text_generator=lambda prompt: {
                    "pages": [
                        {
                            "page_number": 1,
                            "page_type": "worksheet",
                            "section_name": "Monthly Overview",
                            "title": "Monthly Overview",
                            "body": ["Set your target.", "List top bills.", "Capture a key note."],
                        },
                        {
                            "page_number": 2,
                            "page_type": "tracker",
                            "section_name": "Monthly Overview",
                            "title": "Expense Tracking",
                            "body": ["Log each purchase.", "Compare plan and actual.", "Mark one adjustment."],
                        },
                        {
                            "page_number": 3,
                            "page_type": "reflection",
                            "section_name": "Monthly Overview",
                            "title": "Review & Reset",
                            "body": ["Summarize the month.", "Name one win.", "Choose the next step."],
                        },
                    ]
                }
            ),
            PdfRenderer(),
            MockupAgent(),
            ListingPackageAgent(),
        )

        run_dir = pipeline.start_new_run(self.base_dir, "budget-planner")

        status = etsy_io.read_json(os.path.join(run_dir, "artifacts", "run_status.json"))
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["last_successful_stage"], "listing_package")
        self.assertTrue(os.path.exists(os.path.join(run_dir, "artifacts", "listing_manifest.json")))