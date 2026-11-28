import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from classes import Outreach as outreach


class OutreachRecipientTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(temp.name)
        self.csv_path = Path(temp.name) / "results.csv"
        self.csv_path.write_text(
            'title,website,notes\n"Test Hotel, Ltd.",https://hotel.example,old@example.org\n',
            encoding="utf-8",
        )
        template = Path(temp.name) / "message.html"
        template.write_text("<p>Hello {{COMPANY_NAME}}</p>", encoding="utf-8")
        self.runner = outreach.Outreach.__new__(outreach.Outreach)
        self.runner.niche = "hotel"
        self.runner.email_creds = dict(
            username="sender@example.org", password="unused", smtp_server="smtp.example",
            smtp_port=587,
        )
        self.enterContext(patch.multiple(
            self.runner,
            is_go_installed=Mock(return_value=True),
            unzip_file=Mock(),
            build_scraper=Mock(),
            run_scraper_with_args_for_30_seconds=Mock(),
        ))
        for name, value in {
            "get_google_maps_scraper_zip_url": "unused",
            "get_results_cache_path": str(self.csv_path),
            "get_outreach_message_subject": "Hello {{COMPANY_NAME}}",
            "get_outreach_message_body_file": str(template),
            "get_scraper_timeout": 1,
        }.items():
            self.enterContext(patch.object(outreach, name, return_value=value))
        self.enterContext(patch.object(outreach.time, "sleep"))
        self.web = self.enterContext(patch.object(outreach.requests, "get"))
        self.web.return_value = Mock(status_code=200, text="Contact desk@example.org")
        self.smtp = self.enterContext(patch.object(outreach.yagmail, "SMTP"))
        self.ask = self.enterContext(patch.object(outreach, "question", create=True))

    def test_approved_discovered_address_not_stale_csv_value(self):
        self.ask.return_value = "yes"
        self.runner.start()
        self.web.assert_called_once_with("https://hotel.example")
        self.assertIn("desk@example.org", self.ask.call_args.args[0])
        self.smtp.return_value.send.assert_called_once_with(
            to="desk@example.org",
            subject="Hello Test Hotel, Ltd.",
            contents="<p>Hello Test Hotel, Ltd.</p>",
        )
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            self.assertEqual(list(csv.reader(handle))[1][-1], "desk@example.org")

    def test_default_no_does_not_connect_to_smtp(self):
        self.ask.return_value = ""
        self.runner.start()
        self.ask.assert_called_once()
        self.smtp.assert_not_called()

    def test_no_discovered_address_does_not_use_an_unrelated_field(self):
        self.web.return_value.text = "No contact listed"
        self.runner.start()
        self.ask.assert_not_called()
        self.smtp.assert_not_called()

    def test_end_of_input_does_not_connect_to_smtp(self):
        self.ask.side_effect = EOFError
        self.runner.start()
        self.smtp.assert_not_called()
