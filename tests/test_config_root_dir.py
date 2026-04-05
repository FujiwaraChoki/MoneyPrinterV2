import importlib.util
import os
import sys
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, "src", "config.py")


class ConfigRootDirTests(unittest.TestCase):
    def test_root_dir_uses_module_location_when_sys_path_zero_is_empty(self) -> None:
        spec = importlib.util.spec_from_file_location("config_root_dir_test", CONFIG_PATH)
        module = importlib.util.module_from_spec(spec)

        original_sys_path_zero = sys.path[0]
        self.addCleanup(self.restore_sys_path_zero, original_sys_path_zero)
        sys.path[0] = ""

        spec.loader.exec_module(module)

        self.assertEqual(module.ROOT_DIR, ROOT_DIR)

    def restore_sys_path_zero(self, value: str) -> None:
        sys.path[0] = value


if __name__ == "__main__":
    unittest.main()
