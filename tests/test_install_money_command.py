import importlib
import os
import shutil
import stat
import sys
import tempfile
import unittest


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

install_money_command = importlib.import_module("install_money_command")


class InstallMoneyCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="money-command-test-")
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

    def test_build_launcher_script_points_to_repo_venv_and_main(self) -> None:
        script = install_money_command.build_launcher_script("/tmp/mpv2")
        expected_root = os.path.realpath("/tmp/mpv2")

        self.assertIn(f'ROOT_DIR="{expected_root}"', script)
        self.assertIn('exec "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/src/main.py" "$@"', script)
        self.assertIn(f'bash {expected_root}/scripts/setup_local.sh', script)

    def test_update_shell_rc_adds_path_block_once(self) -> None:
        updated = install_money_command.update_shell_rc("export EDITOR=vim\n")
        updated_again = install_money_command.update_shell_rc(updated)

        self.assertIn('export PATH="$HOME/.local/bin:$PATH"', updated)
        self.assertEqual(updated, updated_again)
        self.assertEqual(updated.count(install_money_command.RC_BLOCK_BEGIN), 1)

    def test_install_money_command_creates_executable_and_updates_shell_rc(self) -> None:
        home_dir = os.path.join(self.temp_dir, "home")
        rc_path = os.path.join(home_dir, ".zshrc")

        launcher_path = install_money_command.install_money_command(
            "/repo/root",
            home_dir,
            rc_path,
        )

        self.assertTrue(os.path.exists(launcher_path))
        self.assertTrue(os.stat(launcher_path).st_mode & stat.S_IXUSR)

        with open(launcher_path, "r", encoding="utf-8") as handle:
            contents = handle.read()

        self.assertIn('ROOT_DIR="/repo/root"', contents)
        self.assertIn('exec "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/src/main.py" "$@"', contents)

        with open(rc_path, "r", encoding="utf-8") as handle:
            shell_rc = handle.read()

        self.assertIn('export PATH="$HOME/.local/bin:$PATH"', shell_rc)


if __name__ == "__main__":
    unittest.main()