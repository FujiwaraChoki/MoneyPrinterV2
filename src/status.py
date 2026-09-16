import sys

from termcolor import colored


def _supports_unicode_output() -> bool:
    encoding = getattr(sys.stdout, "encoding", None) or ""
    try:
        "x".encode(encoding)
        "✓".encode(encoding)
        return True
    except Exception:
        return False


def _prefix(unicode_symbol: str, ascii_symbol: str, show_emoji: bool) -> str:
    if not show_emoji:
        return ""
    return unicode_symbol if _supports_unicode_output() else ascii_symbol


def error(message: str, show_emoji: bool = True) -> None:
    prefix = _prefix("✖", "[x]", show_emoji)
    print(colored(f"{prefix} {message}".strip(), "red"))


def success(message: str, show_emoji: bool = True) -> None:
    prefix = _prefix("✔", "[+]", show_emoji)
    print(colored(f"{prefix} {message}".strip(), "green"))


def info(message: str, show_emoji: bool = True) -> None:
    prefix = _prefix("i", "[i]", show_emoji)
    print(colored(f"{prefix} {message}".strip(), "magenta"))


def warning(message: str, show_emoji: bool = True) -> None:
    prefix = _prefix("!", "[!]", show_emoji)
    print(colored(f"{prefix} {message}".strip(), "yellow"))


def question(message: str, show_emoji: bool = True) -> str:
    prefix = _prefix("?", "[?]", show_emoji)
    return input(colored(f"{prefix} {message}".strip(), "magenta"))
