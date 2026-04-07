import json
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


class EtsyIoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

    def test_create_run_directory_creates_expected_subfolders(self) -> None:
        run_dir = etsy_io.create_run_directory(self.temp_dir, "budget-planner")

        self.assertRegex(os.path.basename(run_dir), r"^\d{8}-\d{6}-budget-planner$")
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "artifacts")))
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "product")))
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "mockups")))
        self.assertTrue(os.path.isdir(os.path.join(run_dir, "listing")))

    def test_initialize_run_status_writes_in_progress_payload(self) -> None:
        run_dir = etsy_io.create_run_directory(self.temp_dir, "budget-planner")
        status_path = etsy_io.initialize_run_status(run_dir)

        with open(status_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["run_id"], os.path.basename(run_dir))
        self.assertEqual(payload["status"], "in_progress")
        self.assertEqual(payload["current_stage"], "")
        self.assertEqual(payload["last_successful_stage"], "")
        self.assertEqual(payload["failure_message"], "")

    def test_write_json_and_read_json_round_trip(self) -> None:
        target_path = os.path.join(self.temp_dir, "example.json")

        etsy_io.write_json(target_path, {"hello": "world"})

        self.assertEqual(etsy_io.read_json(target_path), {"hello": "world"})