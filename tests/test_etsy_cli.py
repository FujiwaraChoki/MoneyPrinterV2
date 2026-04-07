import os
import sys
import unittest
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from etsy.cli import start_etsy_cli


class EtsyCliTests(unittest.TestCase):
    def test_cli_resume_requires_confirmation_before_pipeline_resume(self) -> None:
        with patch(
            "etsy.cli.discover_runs",
            return_value=[
                {
                    "run_id": "run-1",
                    "run_dir": "/tmp/run-1",
                    "status": "failed",
                    "last_successful_stage": "research",
                    "failure_message": "boom",
                }
            ],
        ), patch(
            "etsy.cli.question",
            side_effect=["2", "1", "no"],
        ), patch(
            "etsy.cli.build_etsy_pipeline",
        ) as build_pipeline_mock:
            start_etsy_cli()

        build_pipeline_mock.return_value.resume.assert_not_called()

    def test_cli_new_run_dispatches_to_pipeline(self) -> None:
        with patch(
            "etsy.cli.question",
            side_effect=["1", "budget-planner"],
        ), patch(
            "etsy.cli.build_etsy_pipeline",
        ) as build_pipeline_mock:
            start_etsy_cli()

        build_pipeline_mock.return_value.start_new_run.assert_called_once()

    def test_cli_new_run_reports_completion_and_run_path(self) -> None:
        with patch(
            "etsy.cli.question",
            side_effect=["1", "budget-planner"],
        ), patch(
            "etsy.cli.build_etsy_pipeline",
        ) as build_pipeline_mock, patch(
            "etsy.cli.success",
            create=True,
        ) as success_mock:
            build_pipeline_mock.return_value.start_new_run.return_value = "/tmp/etsy/20260405-200303-budget-planner"

            start_etsy_cli()

        success_mock.assert_any_call(
            "Etsy run completed: /tmp/etsy/20260405-200303-budget-planner"
        )