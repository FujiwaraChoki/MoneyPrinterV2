from termcolor import colored

def error(message: str, show_emoji: bool = True) -> None:
    """
    Prints an error message.

    Args:
        message (str): The error message
        show_emoji (bool): Whether to show the emoji

    Returns:
        None
    """
    emoji = "❌" if show_emoji else ""
    print(colored(f"{emoji} {message}", "red"))

def success(message: str, show_emoji: bool = True) -> None:
    """
    Prints a success message.

    Args:
        message (str): The success message
        show_emoji (bool): Whether to show the emoji

    Returns:
        None
    """
    emoji = "✅" if show_emoji else ""
    print(colored(f"{emoji} {message}", "green"))

def info(message: str, show_emoji: bool = True) -> None:
    """
    Prints an info message.

    Args:
        message (str): The info message
        show_emoji (bool): Whether to show the emoji

    Returns:
        None
    """
    emoji = "ℹ️" if show_emoji else ""
    print(colored(f"{emoji} {message}", "magenta"))

def warning(message: str, show_emoji: bool = True) -> None:
    """
    Prints a warning message.

    Args:
        message (str): The warning message
        show_emoji (bool): Whether to show the emoji

    Returns:
        None
    """
    emoji = "⚠️" if show_emoji else ""
    print(colored(f"{emoji} {message}", "yellow"))

def question(message: str, show_emoji: bool = True) -> str:
    """
    Prints a question message and returns the user's input.

    Args:
        message (str): The question message
        show_emoji (bool): Whether to show the emoji

    Returns:
        user_input (str): The user's input
    """
    emoji = "❓" if show_emoji else ""
    return input(colored(f"{emoji} {message}", "magenta"))
