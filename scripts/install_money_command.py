import os
import stat
from pathlib import Path


COMMAND_NAME = "money"
LOCAL_BIN_DIRNAME = ".local/bin"
RC_BLOCK_BEGIN = "# >>> moneyprinter launcher >>>"
RC_BLOCK_END = "# <<< moneyprinter launcher <<<"


def build_launcher_script(root_dir: str) -> str:
    resolved_root = Path(root_dir).resolve()
    setup_script = resolved_root / "scripts" / "setup_local.sh"

    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f'ROOT_DIR="{resolved_root}"',
            'if [[ ! -x "$ROOT_DIR/venv/bin/python" ]]; then',
            f'  echo "MoneyPrinter is not set up yet. Run: bash {setup_script}" >&2',
            "  exit 1",
            "fi",
            'cd "$ROOT_DIR"',
            'exec "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/src/main.py" "$@"',
            "",
        ]
    )


def build_path_block() -> str:
    return "\n".join(
        [
            RC_BLOCK_BEGIN,
            'export PATH="$HOME/.local/bin:$PATH"',
            RC_BLOCK_END,
            "",
        ]
    )


def update_shell_rc(existing_text: str) -> str:
    normalized = existing_text or ""
    block = build_path_block()

    if RC_BLOCK_BEGIN in normalized and RC_BLOCK_END in normalized:
        return normalized

    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    if normalized and not normalized.endswith("\n\n"):
        normalized += "\n"

    return normalized + block


def install_money_command(root_dir: str, home_dir: str, shell_rc_path: str) -> Path:
    home_path = Path(home_dir).expanduser().resolve()
    bin_dir = home_path / LOCAL_BIN_DIRNAME
    bin_dir.mkdir(parents=True, exist_ok=True)

    launcher_path = bin_dir / COMMAND_NAME
    launcher_path.write_text(build_launcher_script(root_dir), encoding="utf-8")

    current_mode = launcher_path.stat().st_mode
    launcher_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    rc_path = Path(shell_rc_path).expanduser()
    existing_text = rc_path.read_text(encoding="utf-8") if rc_path.exists() else ""
    updated_text = update_shell_rc(existing_text)
    if updated_text != existing_text:
        rc_path.parent.mkdir(parents=True, exist_ok=True)
        rc_path.write_text(updated_text, encoding="utf-8")

    return launcher_path


def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    home_dir = os.environ.get("HOME", str(Path.home()))
    shell_rc_path = os.environ.get("MONEY_SHELL_RC_PATH", str(Path(home_dir) / ".zshrc"))

    launcher_path = install_money_command(str(root_dir), home_dir, shell_rc_path)

    print(f"[setup] Installed command: {launcher_path}")
    print("[setup] Open a new shell or run: source ~/.zshrc")
    print("[setup] You can now start MoneyPrinter with: money")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())