import importlib
import os
import sys
import unittest
from types import SimpleNamespace


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class YouTubePillowCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_modules = {
            "classes.YouTube": sys.modules.pop("classes.YouTube", None),
            "llm_provider": sys.modules.pop("llm_provider", None),
        }
        self.youtube_module = importlib.import_module("classes.YouTube")
        self.addCleanup(self.restore_modules)

    def restore_modules(self) -> None:
        sys.modules.pop("classes.YouTube", None)
        sys.modules.pop("llm_provider", None)
        for module_name, module in self._original_modules.items():
            if module is not None:
                sys.modules[module_name] = module

    def test_ensure_pillow_antialias_compatibility_adds_missing_alias(self) -> None:
        image_module = SimpleNamespace(
            Resampling=SimpleNamespace(LANCZOS="lanczos"),
        )

        self.youtube_module._ensure_pillow_antialias_compatibility(image_module)

        self.assertEqual(image_module.ANTIALIAS, image_module.Resampling.LANCZOS)


if __name__ == "__main__":
    unittest.main()
