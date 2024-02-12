from config import ROOT_DIR
from termcolor import colored

def print_banner() -> None:
    """
    Prints the introductory ASCII Art Banner.

    Returns:
        None
    """
    with open(f"{ROOT_DIR}/assets/banner.txt", "r") as file:
        print(colored(file.read(), "green"))
