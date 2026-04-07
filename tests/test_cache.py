import importlib
import json
import os
import shutil
import sys
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config_dir = os.path.join(
            ROOT_DIR,
            "tests",
            ".config-fixtures",
            self.__class__.__name__,
            self._testMethodName,
        )
        shutil.rmtree(self.config_dir, ignore_errors=True)
        os.makedirs(os.path.join(self.config_dir, ".mp"), exist_ok=True)
        self.addCleanup(shutil.rmtree, self.config_dir, True)

        self._original_root_dir = config.ROOT_DIR
        config.ROOT_DIR = self.config_dir
        self.addCleanup(self.restore_modules)

        self._original_cache = sys.modules.pop("cache", None)
        self.cache = importlib.import_module("cache")

    def restore_modules(self) -> None:
        config.ROOT_DIR = self._original_root_dir
        sys.modules.pop("cache", None)
        if self._original_cache is not None:
            sys.modules["cache"] = self._original_cache

    def write_youtube_accounts(self, accounts: list[dict]) -> None:
        with open(
            os.path.join(self.config_dir, ".mp", "youtube.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump({"accounts": accounts}, handle, indent=4)

    def read_youtube_accounts(self) -> list[dict]:
        with open(
            os.path.join(self.config_dir, ".mp", "youtube.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            return json.load(handle)["accounts"]

    def test_get_accounts_migrates_legacy_youtube_niche_to_weird_business(self) -> None:
        self.write_youtube_accounts(
            [
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "strange real events, unexplained cases, disasters, and historical incidents that sound fictional",
                    "language": "english",
                }
            ]
        )

        accounts = self.cache.get_accounts("youtube")

        self.assertEqual(
            accounts[0]["niche"],
            "weird business / internet / creator-economy micro-doc Shorts",
        )
        self.assertEqual(
            self.read_youtube_accounts()[0]["niche"],
            "weird business / internet / creator-economy micro-doc Shorts",
        )

    def test_get_accounts_preserves_non_legacy_youtube_niche(self) -> None:
        self.write_youtube_accounts(
            [
                {
                    "id": "yt-1",
                    "nickname": "channel",
                    "firefox_profile": "/tmp/firefox",
                    "niche": "finance",
                    "language": "english",
                }
            ]
        )

        accounts = self.cache.get_accounts("youtube")

        self.assertEqual(accounts[0]["niche"], "finance")
        self.assertEqual(self.read_youtube_accounts()[0]["niche"], "finance")


if __name__ == "__main__":
    unittest.main()
