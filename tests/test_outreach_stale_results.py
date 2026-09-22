import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

sys.modules.setdefault("srt_equalizer", types.SimpleNamespace())
sys.modules.setdefault("yagmail", types.SimpleNamespace(SMTP=lambda **kwargs: None))
sys.modules.setdefault("requests", types.SimpleNamespace(get=lambda *args, **kwargs: None))
sys.modules.setdefault("termcolor", types.SimpleNamespace(colored=lambda text, *_args, **_kwargs: text))

from classes.Outreach import Outreach


class OutreachStaleResultsTests(unittest.TestCase):
    def test_start_removes_stale_results_before_running_scraper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stale_output_path = os.path.join(temp_dir, "scraper_results.csv")
            niche_path = os.path.join(temp_dir, "niche.txt")

            with open(stale_output_path, "w", encoding="utf-8") as handle:
                handle.write("company,website\nOld Lead,https://old.example\n")

            outreach = Outreach.__new__(Outreach)
            outreach.niche = "plumbers in hanoi"
            outreach.email_creds = {
                "username": "user@example.com",
                "password": "secret",
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
            }

            run_calls = []
            error_messages = []

            def fake_run(args: str, timeout: int) -> None:
                run_calls.append((args, timeout))
                self.assertFalse(
                    os.path.exists(stale_output_path),
                    "stale scraper output should be deleted before the scraper runs",
                )

            with patch("classes.Outreach.get_results_cache_path", return_value=stale_output_path), \
                patch("classes.Outreach.get_google_maps_scraper_zip_url", return_value="https://example.com/scraper.zip"), \
                patch("classes.Outreach.get_outreach_message_subject", return_value="Hello {{COMPANY_NAME}}"), \
                patch("classes.Outreach.get_outreach_message_body_file", return_value=os.path.join(temp_dir, "body.txt")), \
                patch("classes.Outreach.get_scraper_timeout", return_value=30), \
                patch.object(outreach, "is_go_installed", return_value=True), \
                patch.object(outreach, "unzip_file"), \
                patch.object(outreach, "build_scraper"), \
                patch.object(outreach, "run_scraper_with_args_for_30_seconds", side_effect=fake_run), \
                patch("classes.Outreach.error", side_effect=error_messages.append), \
                patch("classes.Outreach.requests.get"):
                cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    outreach.start()
                finally:
                    os.chdir(cwd)

            self.assertEqual(len(run_calls), 1)
            self.assertFalse(os.path.exists(stale_output_path))
            self.assertFalse(os.path.exists(niche_path))
            self.assertEqual(
                error_messages,
                [
                    f" => Scraper output not found at {stale_output_path}. Check scraper logs and configuration."
                ],
            )


if __name__ == "__main__":
    unittest.main()
