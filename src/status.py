import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from termcolor import colored

# Project root used for log file placement
_ROOT_DIR = os.path.dirname(sys.path[0])
_LOG_DIR = os.path.join(_ROOT_DIR, ".mp")

_logger = logging.getLogger("mpv2")
_logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers when the module is re-imported
if not _logger.handlers:
    # Console handler -- always INFO+ with color handled by the functions below
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setLevel(logging.DEBUG)
    _console_handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_console_handler)

    # File handler -- rotates at 5 MB, keeps 3 backups
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        _file_handler = RotatingFileHandler(
            os.path.join(_LOG_DIR, "mpv2.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        _file_handler.setLevel(logging.DEBUG)
        _file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        _logger.addHandler(_file_handler)
    except OSError:
        # .mp dir might not exist yet on very first run; file logging will
        # start working after assert_folder_structure() runs.
        pass


def error(message: str, show_emoji: bool = True) -> None:
    """Prints an error message and logs it at ERROR level."""
    emoji = "X" if show_emoji else ""
    _logger.error(f"{emoji} {message}" if emoji else message)
    # Also print colored to console for backwards compat
    print(colored(f"{emoji} {message}", "red"), file=sys.stderr)


def success(message: str, show_emoji: bool = True) -> None:
    """Prints a success message and logs it at INFO level."""
    emoji = "+" if show_emoji else ""
    display = f"[{emoji}] {message}" if emoji else message
    _logger.info(display)
    print(colored(display, "green"))


def info(message: str, show_emoji: bool = True) -> None:
    """Prints an info message and logs it at INFO level."""
    emoji = "[i]" if show_emoji else ""
    display = f"{emoji} {message}" if emoji else message
    _logger.info(display)
    print(colored(display, "magenta"))


def warning(message: str, show_emoji: bool = True) -> None:
    """Prints a warning message and logs it at WARNING level."""
    emoji = "[!]" if show_emoji else ""
    display = f"{emoji} {message}" if emoji else message
    _logger.warning(display)
    print(colored(display, "yellow"))


def question(message: str, show_emoji: bool = True) -> str:
    """Prints a question message and returns the user's input."""
    emoji = "[?]" if show_emoji else ""
    display = f"{emoji} {message}" if emoji else message
    _logger.info(f"PROMPT: {display}")
    return input(colored(display, "magenta"))


def get_logger() -> logging.Logger:
    """Returns the application logger for direct use in modules that need it."""
    return _logger
