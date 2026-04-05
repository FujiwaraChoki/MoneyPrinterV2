import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


def load_cache_module(root_dir: str):
    spec = importlib.util.spec_from_file_location(
        "cache_under_test", SRC_DIR / "cache.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load cache module")

    fake_config = types.ModuleType("config")
    fake_config.ROOT_DIR = root_dir

    previous_config = sys.modules.get("config")
    sys.modules["config"] = fake_config

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_config is None:
            sys.modules.pop("config", None)
        else:
            sys.modules["config"] = previous_config


class CacheRecoveryTests(unittest.TestCase):
    def test_get_accounts_recovers_from_corrupted_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / ".mp"
            cache_dir.mkdir()
            cache_path = cache_dir / "twitter.json"
            cache_path.write_text('{"accounts": [', encoding="utf-8")

            cache = load_cache_module(temp_dir)

            self.assertEqual(cache.get_accounts("twitter"), [])
            self.assertEqual(
                json.loads(cache_path.read_text(encoding="utf-8")),
                {"accounts": []},
            )

    def test_get_products_recovers_from_corrupted_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / ".mp"
            cache_dir.mkdir()
            cache_path = cache_dir / "afm.json"
            cache_path.write_text('{"products": [', encoding="utf-8")

            cache = load_cache_module(temp_dir)

            self.assertEqual(cache.get_products(), [])
            self.assertEqual(
                json.loads(cache_path.read_text(encoding="utf-8")),
                {"products": []},
            )


if __name__ == "__main__":
    unittest.main()
