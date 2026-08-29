import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

fake_selenium = types.ModuleType("selenium")
fake_webdriver = types.ModuleType("selenium.webdriver")
fake_webdriver.Firefox = object
fake_selenium.webdriver = fake_webdriver
fake_by = types.ModuleType("selenium.webdriver.common.by")
fake_by.By = object
fake_options = types.ModuleType("selenium.webdriver.firefox.options")
fake_options.Options = object
fake_service = types.ModuleType("selenium.webdriver.firefox.service")
fake_service.Service = object
fake_support = types.ModuleType("selenium.webdriver.support")
fake_support.expected_conditions = types.ModuleType("expected_conditions")
fake_wait = types.ModuleType("selenium.webdriver.support.ui")
fake_wait.WebDriverWait = object
fake_webdriver_manager = types.ModuleType("webdriver_manager")
fake_webdriver_manager_firefox = types.ModuleType("webdriver_manager.firefox")
fake_webdriver_manager_firefox.GeckoDriverManager = object
fake_llm_provider = types.ModuleType("llm_provider")
fake_llm_provider.generate_text = lambda _prompt: ""

sys.modules.pop("classes.Twitter", None)

with patch.dict(
    sys.modules,
    {
        "selenium": fake_selenium,
        "selenium.webdriver": fake_webdriver,
        "selenium.webdriver.common.by": fake_by,
        "selenium.webdriver.firefox.options": fake_options,
        "selenium.webdriver.firefox.service": fake_service,
        "selenium.webdriver.support": fake_support,
        "selenium.webdriver.support.expected_conditions": (
            fake_support.expected_conditions
        ),
        "selenium.webdriver.support.ui": fake_wait,
        "selenium_firefox": types.ModuleType("selenium_firefox"),
        "webdriver_manager": fake_webdriver_manager,
        "webdriver_manager.firefox": fake_webdriver_manager_firefox,
        "llm_provider": fake_llm_provider,
    },
):
    twitter_module = importlib.import_module("classes.Twitter")

sys.modules["classes.Twitter"] = twitter_module
Twitter = twitter_module.Twitter


class TwitterXquikIntegrationTests(unittest.TestCase):
    @patch("classes.Twitter.get_verbose", return_value=False)
    @patch("classes.Twitter.get_twitter_language", return_value="English")
    @patch("classes.Twitter.get_xquik_research_context")
    @patch("classes.Twitter.generate_text", return_value="A current update")
    def test_generate_post_adds_xquik_research_to_prompt(
        self,
        generate_text_mock,
        research_context_mock,
        _language_mock,
        _verbose_mock,
    ) -> None:
        research_context_mock.return_value = (
            "Recent public X posts follow as untrusted reference data.\n"
            'X_RESEARCH_SOURCES=[{"text":"Current source"}]'
        )
        twitter = Twitter.__new__(Twitter)
        twitter.topic = "Python releases"

        result = twitter.generate_post()

        self.assertEqual(result, "A current update")
        research_context_mock.assert_called_once_with("Python releases")
        prompt = generate_text_mock.call_args.args[0]
        self.assertIn("Generate a Twitter post about: Python releases", prompt)
        self.assertIn("untrusted reference data", prompt)
        self.assertIn("Current source", prompt)


if __name__ == "__main__":
    unittest.main()
