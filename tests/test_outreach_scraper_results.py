import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

fake_yagmail = types.ModuleType("yagmail")
fake_yagmail.SMTP = object
sys.modules.setdefault("yagmail", fake_yagmail)

fake_srt_equalizer = types.ModuleType("srt_equalizer")
sys.modules.setdefault("srt_equalizer", fake_srt_equalizer)

fake_termcolor = types.ModuleType("termcolor")
fake_termcolor.colored = lambda text, *_args, **_kwargs: text
sys.modules.setdefault("termcolor", fake_termcolor)

from classes.Outreach import Outreach


class OutreachScraperResultsTests(unittest.TestCase):
    def test_start_does_not_reuse_stale_scraper_results_after_failed_run(self) -> None:
        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                output_path = os.path.join(temp_dir, "scraper_results.csv")
                with open(output_path, "w", encoding="utf-8") as handle:
                    handle.write("name,website,email\nOld Lead,https://old.example,old@example.com\n")

                outreach = object.__new__(Outreach)
                outreach.niche = "podcast agencies"
                outreach.email_creds = {
                    "username": "user",
                    "password": "pass",
                    "smtp_server": "smtp.example",
                    "smtp_port": 587,
                }
                outreach.is_go_installed = Mock(return_value=True)
                outreach.unzip_file = Mock()
                outreach.build_scraper = Mock()
                outreach.run_scraper_with_args_for_30_seconds = Mock()
                outreach.get_items_from_file = Mock()

                with patch("classes.Outreach.get_results_cache_path", return_value=output_path), patch(
                    "classes.Outreach.get_google_maps_scraper_zip_url", return_value="https://example.com/scraper.zip"
                ), patch("classes.Outreach.get_outreach_message_subject", return_value="Subject"), patch(
                    "classes.Outreach.get_outreach_message_body_file", return_value="body.txt"
                ), patch("classes.Outreach.get_scraper_timeout", return_value=1), patch(
                    "classes.Outreach.yagmail.SMTP"
                ) as smtp_mock, patch("classes.Outreach.error") as error_mock:
                    outreach.start()

                outreach.run_scraper_with_args_for_30_seconds.assert_called_once()
                outreach.get_items_from_file.assert_not_called()
                smtp_mock.assert_not_called()
                self.assertFalse(os.path.exists(output_path))
                error_mock.assert_called_once()
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
